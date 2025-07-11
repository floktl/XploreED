"""Exercise related AI endpoints."""

from app.imports.imports import ai_bp
from flask import request, jsonify # type: ignore
from .helpers.helpers import (
    evaluate_answers_with_ai,
    _adjust_gapfill_results,
    process_ai_answers,
    generate_feedback_prompt
)
from utils.helpers.helper import run_in_background, require_user
from .helpers.exercise_helpers import (
    prefetch_next_exercises,
    fetch_vocab_and_topic_data,
    compile_score_summary,
    save_exercise_submission_async,
    evaluate_exercises,
    parse_submission_data,
)

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
