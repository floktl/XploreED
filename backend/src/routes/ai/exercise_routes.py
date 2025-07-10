"""Exercise related AI endpoints."""

import json
import random
from flask import request, jsonify

from . import ai_bp, EXERCISE_TEMPLATE
from .helpers import (
    generate_new_exercises,
    prefetch_next_exercises,
    evaluate_answers_with_ai,
    _adjust_gapfill_results,
    fetch_topic_memory,
    process_ai_answers,
    generate_feedback_prompt
)
from database import select_rows, fetch_one
from utils.spaced_repetition.vocab_utils import split_and_clean, save_vocab, review_vocab_word, extract_words
from utils.helpers.helper import run_in_background, require_user
from .exercise_helpers import (
    fetch_vocab_and_topic_data,
    compile_score_summary,
    save_exercise_submission_async,
    evaluate_exercises,
    parse_submission_data,
)


def get_ai_exercises():
    """Return a new AI-generated exercise block for the user."""
    username = require_user()
    # print("Session ID:", session_id, flush=True)
    # print("Username:", username, flush=True)

    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = select_rows(
        "vocab_log",
        columns=[
            "vocab",
            "translation",
            "interval_days",
            "next_review",
            "ef",
            "repetitions",
            "last_review",
        ],
        where="username = ?",
        params=(username,),
    )

    vocab_data = [
        {
            "type": "string",
            "word": row["vocab"],
            "translation": row.get("translation"),
            "sm2_interval": row.get("interval_days"),
            "sm2_due_date": row.get("next_review"),
            "sm2_ease": row.get("ef"),
            "repetitions": row.get("repetitions"),
            "sm2_last_review": row.get("last_review"),
            "quality": 0,
        }
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    try:
        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level
        )
    except ValueError as e:
        print("[ai-exercise]", e, flush=True)
        return jsonify({"error": "Mistral error"}), 500
    if not ai_block or not ai_block.get("exercises"):
        return jsonify({"error": "Mistral error"}), 500

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]

    # remove solutions before sending to client
    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    return jsonify(ai_block)


@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id):
    """Evaluate a submitted exercise block and save results."""
    username = require_user()
    # print("Session ID:", session_id, "Username:", username, flush=True)

    data = request.get_json() or {}
    # print("✅ Received submission data (JSON):\n", json.dumps(data, indent=2), flush=True)

    exercises, answers, error = parse_submission_data(data)
    if error:
        print(f"❌ {error}", flush=True)
        return jsonify({"msg": error}), 400

    # print(f"📚 Number of exercises received: {len(exercises)}", flush=True)

    evaluation, id_map = evaluate_exercises(exercises, answers)
    if not evaluation:
        print("❌ Evaluation failed — no evaluation returned", flush=True)
        return jsonify({"msg": "Evaluation failed"}), 500

    summary = compile_score_summary(exercises, answers, id_map)

    vocab_data, topic_data = fetch_vocab_and_topic_data(username)

    feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

    save_exercise_submission_async(username, block_id, answers, exercises)
    passed = bool(evaluation.get("pass"))
    run_in_background(prefetch_next_exercises, username)

    return jsonify({
        "feedbackPrompt": feedback_prompt,
        "pass": passed,
        "summary": summary,
        "results": evaluation.get("results", []),
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




