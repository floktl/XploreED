"""Routes serving AI feedback data."""

import json
import random
import uuid
from flask import request, jsonify  # type: ignore

from . import ai_bp, FEEDBACK_FILE
from .helpers.helpers import (
    _adjust_gapfill_results,
    fetch_topic_memory,
    generate_feedback_prompt
)
from .helpers.ai_evaluation_helpers import evaluate_answers_with_ai, process_ai_answers
from database import select_rows
from utils.helpers.helper import run_in_background, require_user

# Store progress for each feedback generation session
feedback_progress = {}

@ai_bp.route("/ai-feedback/progress/<session_id>", methods=["GET"])
def get_feedback_progress(session_id):
    """Get the current progress of AI feedback generation."""
    username = require_user()

    if session_id not in feedback_progress:
        return jsonify({"error": "Session not found"}), 404

    progress = feedback_progress[session_id]
    return jsonify(progress)

@ai_bp.route("/ai-feedback/generate-with-progress", methods=["POST"])
def generate_ai_feedback_with_progress():
    """Generate AI feedback with progress tracking."""
    username = require_user()

    # Create a unique session ID
    session_id = str(uuid.uuid4())
    feedback_progress[session_id] = {
        "percentage": 0,
        "status": "Starting feedback generation...",
        "step": "init",
        "completed": False
    }

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block")

    def update_progress(percentage, status, step):
        if session_id in feedback_progress:
            feedback_progress[session_id].update({
                "percentage": percentage,
                "status": status,
                "step": step
            })

    def run_feedback_generation():
        try:
            # Step 1: Analyzing answers (10%)
            update_progress(10, "Analyzing your answers...", "analyzing")

            if not exercise_block:
                update_progress(100, "No exercise block provided", "error")
                return

            all_exercises = exercise_block.get("exercises", [])

            # Step 2: Evaluating with AI (30%)
            update_progress(30, "Evaluating answers with AI...", "evaluating")
            evaluation = evaluate_answers_with_ai(all_exercises, answers)
            evaluation = _adjust_gapfill_results(all_exercises, answers, evaluation)

            if not evaluation:
                update_progress(100, "AI evaluation failed", "error")
                return

            # Step 3: Processing results (50%)
            update_progress(50, "Processing evaluation results...", "processing")
            id_map = {
                str(r.get("id")): r.get("correct_answer")
                for r in evaluation.get("results", [])
            }

            summary = {"correct": 0, "total": len(all_exercises), "mistakes": []}
            for ex in all_exercises:
                cid = str(ex.get("id"))
                user_ans = answers.get(cid, "")
                correct_ans = id_map.get(cid, "")
                if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
                    summary["correct"] += 1
                else:
                    summary["mistakes"].append({
                        "question": ex.get("question"),
                        "your_answer": user_ans,
                        "correct_answer": correct_ans,
                    })

            # Step 4: Fetching user data (70%)
            update_progress(70, "Fetching your vocabulary and progress data...", "fetching_data")

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

            # Step 5: Generating feedback (85%)
            update_progress(85, "Generating personalized feedback...", "generating_feedback")
            feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

            # Step 6: Updating topic memory (95%)
            update_progress(95, "Updating your learning progress...", "updating_progress")
            run_in_background(
                process_ai_answers,
                username,
                str(exercise_block.get("lessonId", "feedback")),
                answers,
                {"exercises": all_exercises},
            )

            # Step 7: Complete (100%)
            update_progress(100, "Feedback generation complete!", "complete")

            # Store the result
            feedback_progress[session_id]["result"] = {
                "feedbackPrompt": feedback_prompt,
                "summary": summary,
                "results": evaluation.get("results", []),
            }
            feedback_progress[session_id]["completed"] = True

        except Exception as e:
            update_progress(100, f"Error: {str(e)}", "error")
            feedback_progress[session_id]["error"] = str(e)

    # Run the feedback generation in background
    run_in_background(run_feedback_generation)

    return jsonify({"session_id": session_id})

@ai_bp.route("/ai-feedback/result/<session_id>", methods=["GET"])
def get_feedback_result(session_id):
    """Get the final result of AI feedback generation."""
    username = require_user()

    if session_id not in feedback_progress:
        return jsonify({"error": "Session not found"}), 404

    progress = feedback_progress[session_id]

    if not progress.get("completed"):
        return jsonify({"error": "Generation not complete"}), 400

    result = progress.get("result")
    if not result:
        return jsonify({"error": "No result available"}), 400

    # Clean up the session
    del feedback_progress[session_id]

    return jsonify(result)

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
