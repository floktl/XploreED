"""Exercise related AI endpoints."""

import json
import random
import datetime
import os
from flask import request, jsonify, current_app

from . import ai_bp, EXERCISE_TEMPLATE
from .helpers import (
    generate_new_exercises,
    prefetch_next_exercises,
    evaluate_answers_with_ai,
    _adjust_gapfill_results,
    fetch_topic_memory,
    store_user_ai_data,
    process_ai_answers,
    generate_feedback_prompt
)
from database import select_rows, fetch_one, insert_row
from utils.spaced_repetition.vocab_utils import split_and_clean, save_vocab, review_vocab_word, extract_words
from utils.helpers.helper import run_in_background, session_manager
from utils.spaced_repetition.level_utils import check_auto_level_up


def get_ai_exercises():
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
    username = require_user()
    # print("Session ID:", session_id, "Username:", username, flush=True)

    data = request.get_json() or {}
    # print("✅ Received submission data (JSON):\n", json.dumps(data, indent=2), flush=True)

    answers = data.get("answers", {})
    # print("📝 Extracted answers:", json.dumps(answers, indent=2), flush=True)

    exercise_block = data.get("exercise_block")
    if not exercise_block or not isinstance(exercise_block, dict):
        print("❌ Missing or invalid exercise_block!", flush=True)
        return jsonify({"msg": "Invalid or missing exercise block."}), 400

    # print("📦 Extracted exercise block:", json.dumps(exercise_block, indent=2), flush=True)

    exercises = exercise_block.get("exercises")
    if not exercises or not isinstance(exercises, list):
        print("❌ No exercises found in exercise_block!", flush=True)
        return jsonify({"msg": "No exercises found to evaluate."}), 400

    # print(f"📚 Number of exercises received: {len(exercises)}", flush=True)

    # AI Evaluation
    evaluation = evaluate_answers_with_ai(exercises, answers)
    # print("🤖 Raw evaluation result from AI (before adjustment):\n", json.dumps(evaluation, indent=2), flush=True)

    # Adjust gap fill results
    evaluation = _adjust_gapfill_results(exercises, answers, evaluation)
    # print("🔧 Evaluation after gapfill adjustment:\n", json.dumps(evaluation, indent=2), flush=True)

    if not evaluation:
        print("❌ Evaluation failed — no evaluation returned", flush=True)
        return jsonify({"msg": "Evaluation failed"}), 500

    # Mapping correct answers to exercises
    id_map = {str(r.get("id")): r.get("correct_answer") for r in evaluation.get("results", [])}
    # print("🗺️ ID → Correct Answer Map:", json.dumps(id_map, indent=2), flush=True)

    for ex in exercises:
        cid = str(ex.get("id"))
        if cid in id_map:
            ex["correctAnswer"] = id_map[cid]
        # print(f"✅ Updated exercise {cid} with correct answer: {id_map.get(cid)}", flush=True)

    # Score summary
    mistakes = []
    correct = 0
    for ex in exercises:
        cid = str(ex.get("id"))
        user_ans = answers.get(cid, "")
        correct_ans = id_map.get(cid, "")
        # print(f"🔍 Checking answer for {cid}: user='{user_ans}' vs correct='{correct_ans}'", flush=True)
        if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
            correct += 1
            # print(f"✅ Correct for {cid}", flush=True)
        else:
            # print(f"❌ Mistake for {cid}", flush=True)
            mistakes.append({
                "question": ex.get("question"),
                "your_answer": user_ans,
                "correct_answer": correct_ans,
            })

    summary = {"correct": correct, "total": len(exercises), "mistakes": mistakes}
    # print("📊 Final summary:\n", json.dumps(summary, indent=2), flush=True)


    vocab_rows = select_rows(
        "vocab_log",
        columns=["vocab", "translation"],
        where="username = ?",
        params=(username,),
    )
    vocab_data = [
        {"word": row["vocab"], "translation": row.get("translation")}
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_data = [dict(row) for row in topic_rows] if topic_rows else []

    feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

    def _background_save():
        try:
            process_ai_answers(
                username,
                str(block_id),
                answers,
                {"exercises": exercises},
            )
            check_auto_level_up(username)
            insert_row(
                "exercise_submissions",
                {
                    "username": username,
                    "block_id": str(block_id),
                    "answers": json.dumps(answers),
                },
            )
            # print("Successfully inserted submission", flush=True)
        except Exception as e:
            current_app.logger.error("Failed to save exercise submission: %s", e)

    run_in_background(_background_save)

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




