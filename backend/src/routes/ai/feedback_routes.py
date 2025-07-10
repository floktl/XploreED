"""Routes serving AI feedback data."""

import json
import random
from flask import request, jsonify  # type: ignore

from . import ai_bp, FEEDBACK_FILE
from .helpers import (
    evaluate_answers_with_ai,
    _adjust_gapfill_results,
    fetch_topic_memory,
    process_ai_answers,
    generate_feedback_prompt
)

from database import select_rows
from utils.helpers.helper import run_in_background, require_user
from utils.data.json_utils import extract_json


@ai_bp.route("/ai-feedback", methods=["GET"])
def get_ai_feedback():
    """Return the list of cached AI feedback entries."""
    username = require_user()
    # print("Fetching AI feedback for:", username, flush=True)

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    return jsonify(feedback_data)


@ai_bp.route("/ai-feedback/<feedback_id>", methods=["GET"])
def get_ai_feedback_item(feedback_id):
    """Return a single cached feedback item by ID."""
    username = require_user()
    # print(f"User '{username}' requested feedback ID {feedback_id}", flush=True)

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    item = next((fb for fb in feedback_data if str(fb.get("id")) == str(feedback_id)), None)
    if not item:
        return jsonify({"msg": "Feedback not found"}), 404
    return jsonify(item)


@ai_bp.route("/ai-feedback", methods=["POST"])
def generate_ai_feedback():
    """Generate AI feedback from submitted exercise results."""
    username = require_user()
    # print("Generating feedback for user:", username, flush=True)

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block")
    # print("Feedback generation data:", data, flush=True)

    if exercise_block:
        all_exercises = exercise_block.get("exercises", [])
        evaluation = evaluate_answers_with_ai(all_exercises, answers)
        evaluation = _adjust_gapfill_results(all_exercises, answers, evaluation)
        id_map = {
            str(r.get("id")): r.get("correct_answer")
            for r in evaluation.get("results", [])
        } if evaluation else {}

        summary = {"correct": 0, "total": len(all_exercises), "mistakes": []}
        for ex in all_exercises:
            cid = str(ex.get("id"))
            user_ans = answers.get(cid, "")
            correct_ans = id_map.get(cid, "")
            if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
                summary["correct"] += 1
            else:
                summary["mistakes"].append(
                    {
                        "question": ex.get("question"),
                        "your_answer": user_ans,
                        "correct_answer": correct_ans,
                    }
                )

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
                "word": row["vocab"],
                "translation": row.get("translation"),
            }
            for row in vocab_rows
        ] if vocab_rows else []

        topic_rows = fetch_topic_memory(username)
        topic_data = [dict(row) for row in topic_rows] if topic_rows else []

        feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

        # Update topic memory asynchronously with the final evaluation results
        run_in_background(
            process_ai_answers,
            username,
            str(exercise_block.get("lessonId", "feedback")),
            answers,
            {"exercises": all_exercises},
        )

        return jsonify({
            "feedbackPrompt": feedback_prompt,
            "summary": summary,
            "results": evaluation.get("results", []),
        })

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    feedback = random.choice(feedback_data) if feedback_data else {}
    return jsonify(feedback)


