"""Exercise related AI endpoints."""

import logging
import json
from app.imports.imports import ai_bp
from flask import request, jsonify # type: ignore
from .helpers.helpers import (
    _adjust_gapfill_results,
    generate_feedback_prompt
)
from .helpers.ai_evaluation_helpers import evaluate_answers_with_ai, process_ai_answers, generate_alternative_answers, generate_explanation
from utils.helpers.helper import run_in_background, require_user
from .helpers.exercise_helpers import (
    prefetch_next_exercises,
    fetch_vocab_and_topic_data,
    compile_score_summary,
    save_exercise_submission_async,
    evaluate_exercises,
    parse_submission_data,
)
import re

logger = logging.getLogger(__name__)

@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id):
    """Evaluate a submitted exercise block and save results."""
    username = require_user()
    logger.info(f"Exercise submission request for user {username}, block {block_id}")

    # print("Session ID:", session_id, "Username:", username, flush=True)

    data = request.get_json() or {}
    logger.info(f"Received submission data for user {username}: {json.dumps(data, indent=2)}")
    # print("✅ Received submission data (JSON):\n", json.dumps(data, indent=2), flush=True)

    exercises, answers, error = parse_submission_data(data)
    if error:
        logger.error(f"Parse submission data error for user {username}: {error}")
        print(f"❌ {error}", flush=True)
        return jsonify({"msg": error}), 400

    logger.info(f"Parsed submission for user {username}: {len(exercises)} exercises, {len(answers)} answers")
    # print(f"📚 Number of exercises received: {len(exercises)}", flush=True)

    logger.info(f"Evaluating exercises for user {username}")
    evaluation, id_map = evaluate_exercises(exercises, answers)
    if not evaluation:
        logger.error(f"Evaluation failed for user {username} - no evaluation returned")
        print("❌ Evaluation failed — no evaluation returned", flush=True)
        return jsonify({"msg": "Evaluation failed"}), 500

    logger.info(f"Evaluation successful for user {username}")
    summary = compile_score_summary(exercises, answers, id_map)
    logger.info(f"Summary for user {username}: {summary}")

    logger.info(f"Fetching vocab and topic data for user {username}")
    vocab_data, topic_data = fetch_vocab_and_topic_data(username)
    logger.info(f"Got {len(vocab_data)} vocab and {len(topic_data)} topic entries for user {username}")

    feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)
    logger.info(f"Generated feedback prompt for user {username}")

    logger.info(f"Saving exercise submission for user {username}")
    save_exercise_submission_async(username, block_id, answers, exercises)
    passed = bool(evaluation.get("pass"))

    logger.info(f"Running prefetch next exercises for user {username}")
    run_in_background(prefetch_next_exercises, username)

    logger.info(f"Exercise submission completed for user {username}, passed={passed}")

    # Add robust per-exercise explanations and alternatives
    any_is_correct = False
    results_with_details = []
    for res in evaluation.get("results", []):
        correct_answer = res.get("correct_answer")
        ex = next((e for e in exercises if str(e.get("id")) == str(res.get("id"))), None)
        user_answer = answers.get(str(res.get("id")), "")
        # Use the same logic as compile_score_summary for translation exercises
        is_correct = False
        if ex and ex.get("type") == "translation":
            from .helpers.exercise_helpers import _strip_final_punct
            ua = _strip_final_punct(user_answer)
            ca = _strip_final_punct(correct_answer)
            is_correct = str(ua).strip().lower() == str(ca).strip().lower()
        else:
            is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
        # Generate up to 3 alternatives using AI, fallback to []
        try:
            alternatives = generate_alternative_answers(correct_answer)[:3] if correct_answer else []
            if not isinstance(alternatives, list):
                alternatives = []
        except Exception:
            alternatives = []
        # Generate explanation using AI, fallback to ""
        try:
            question = ex.get("question") if ex else ""
            explanation = generate_explanation(question, user_answer, correct_answer) if correct_answer else ""
            if not isinstance(explanation, str):
                explanation = ""
        except Exception:
            explanation = ""
        # If backend says incorrect, but AI feedback says correct, double-check with AI
        ai_feedback_says_correct = False
        if not is_correct and ex and ex.get("type") == "translation":
            if re.search(r"user'?s answer is correct", explanation, re.IGNORECASE):
                # Ask AI for a final yes/no
                from utils.ai.ai_api import send_prompt
                followup_prompt = {
                    "role": "user",
                    "content": f"""
Given the following:
- Question: {question}
- User's answer: {user_answer}
- Correct answer: {correct_answer}
- AI feedback: {explanation}

Is the user's answer correct? Only reply with true or false.
"""
                }
                try:
                    resp = send_prompt("You are a helpful German teacher.", followup_prompt, temperature=0.0)
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip().lower()
                        if "true" in content:
                            is_correct = True
                except Exception:
                    pass
        if is_correct:
            any_is_correct = True
        res_with_details = dict(res)
        res_with_details["correct_answer"] = correct_answer
        res_with_details["alternatives"] = alternatives
        res_with_details["explanation"] = explanation
        res_with_details["is_correct"] = is_correct
        results_with_details.append(res_with_details)
    # If any translation exercise is now correct, update the 'pass' status
    if any_is_correct:
        passed = True
    return jsonify({
        "feedbackPrompt": feedback_prompt,
        "pass": passed,
        "summary": summary,
        "results": results_with_details,
    })


@ai_bp.route("/ai-exercise/<block_id>/argue", methods=["POST"])
def argue_ai_exercise(block_id):
    """Reevaluate answers when the student wants to argue with the AI."""
    username = require_user()

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block") or {}
    exercises = exercise_block.get("exercises", [])

    evaluation = evaluate_answers_with_ai(exercises, answers, mode="argue")
    evaluation = _adjust_gapfill_results(exercises, answers, evaluation)
    if not evaluation:
        return jsonify({"msg": "Evaluation failed"}), 500

    # Update topic memory asynchronously with the reevaluated results
    run_in_background(
        process_ai_answers,
        username,
        str(block_id),
        answers,
        {"exercises": exercises},
    )

    return jsonify(evaluation)
