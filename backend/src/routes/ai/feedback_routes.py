"""Routes serving AI feedback data."""

import os
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
import redis

# Connect to Redis (host from env, default 'localhost')
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

def _normalize_umlauts(s):
    # Accept ae == ä, oe == ö, ue == ü (and vice versa)
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    s = s.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    return s

def _strip_final_punct(s):
    s = s.strip()
    if s and s[-1] in ".?":
        return s[:-1].strip()
    return s

@ai_bp.route("/ai-feedback/progress/<session_id>", methods=["GET"])
def get_feedback_progress(session_id):
    print("\033[92m[ENTER] get_feedback_progress\033[0m", flush=True)
    """Get the current progress of AI feedback generation."""
    username = require_user()
    progress_json = redis_client.get(f"feedback_progress:{session_id}")
    if not progress_json:
        return jsonify({"error": "Session not found"}), 404
    progress = json.loads(progress_json)
    # print(f"[Feedback Progress] Frontend requested progress for session {session_id}: {progress['percentage']}% - {progress['status']} - Completed: {progress.get('completed', False)}")
    print("\033[91m[EXIT] get_feedback_progress\033[0m", flush=True)
    return jsonify(progress)

@ai_bp.route("/ai-feedback/generate-with-progress", methods=["POST"])
def generate_ai_feedback_with_progress():
    print("\033[93m[ENTER] generate_ai_feedback_with_progress\033[0m", flush=True)
    """Generate AI feedback with progress tracking."""
    username = require_user()
    session_id = str(uuid.uuid4())
    progress = {
        "percentage": 0,
        "status": "Starting feedback generation...",
        "step": "init",
        "completed": False
    }
    redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block")
    def update_progress(percentage, status, step):
        progress_json = redis_client.get(f"feedback_progress:{session_id}")
        if progress_json:
            progress = json.loads(progress_json)
            progress.update({
                "percentage": percentage,
                "status": status,
                "step": step
            })
            redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
    def run_feedback_generation():
        try:
            update_progress(10, "Analyzing your answers...", "analyzing")
            if not exercise_block or not isinstance(exercise_block, dict) or not exercise_block.get("exercises") or not isinstance(exercise_block.get("exercises"), list) or len(exercise_block.get("exercises")) == 0:
                update_progress(99, "No valid exercise block or exercises provided", "error")
                import logging
                logging.getLogger(__name__).error(f"Feedback error: Invalid or missing exercise_block: {exercise_block}", flush=True)
                # Always write error result to Redis
                error_result = {
                    "feedbackPrompt": "Error: No valid exercise block or exercises provided.",
                    "summary": {},
                    "results": [],
                    "ready": True,
                    "error": "No valid exercise block or exercises provided."
                }
                redis_client.set(f"feedback_result:{session_id}", json.dumps(error_result))
                progress_json = redis_client.get(f"feedback_progress:{session_id}")
                if progress_json:
                    progress = json.loads(progress_json)
                    progress["result"] = error_result
                    progress["completed"] = True
                    redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
                return
            all_exercises = exercise_block.get("exercises", [])
            update_progress(30, "Evaluating answers with AI...", "evaluating")
            try:
                evaluation = evaluate_answers_with_ai(all_exercises, answers)
                evaluation = _adjust_gapfill_results(all_exercises, answers, evaluation)
            except Exception as e:
                update_progress(99, f"AI evaluation error: {str(e)}", "error")
                print(f"[Feedback Error] AI evaluation failed: {e}", flush=True)
                error_result = {
                    "feedbackPrompt": f"Error: AI evaluation failed: {e}",
                    "summary": {},
                    "results": [],
                    "ready": True,
                    "error": f"AI evaluation failed: {e}"
                }
                redis_client.set(f"feedback_result:{session_id}", json.dumps(error_result))
                progress_json = redis_client.get(f"feedback_progress:{session_id}")
                if progress_json:
                    progress = json.loads(progress_json)
                    progress["result"] = error_result
                    progress["completed"] = True
                    redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
                return
            if not evaluation:
                update_progress(99, "AI evaluation failed", "error")
                print(f"[Feedback Error] AI evaluation returned None", flush=True)
                error_result = {
                    "feedbackPrompt": "Error: AI evaluation failed.",
                    "summary": {},
                    "results": [],
                    "ready": True,
                    "error": "AI evaluation failed."
                }
                redis_client.set(f"feedback_result:{session_id}", json.dumps(error_result))
                progress_json = redis_client.get(f"feedback_progress:{session_id}")
                if progress_json:
                    progress = json.loads(progress_json)
                    progress["result"] = error_result
                    progress["completed"] = True
                    redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
                return
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
                user_ans = _strip_final_punct(user_ans)
                correct_ans = _strip_final_punct(correct_ans)
                user_ans = _normalize_umlauts(user_ans)
                correct_ans = _normalize_umlauts(correct_ans)
                if user_ans == correct_ans:
                    summary["correct"] += 1
                else:
                    summary["mistakes"].append({
                        "question": ex.get("question"),
                        "your_answer": user_ans,
                        "correct_answer": correct_ans,
                    })
            update_progress(70, "Fetching your vocabulary and progress data...", "fetching_data")
            try:
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
            except Exception as e:
                update_progress(99, f"Data fetch error: {str(e)}", "error")
                print(f"[Feedback Error] Data fetch failed: {e}", flush=True)
                error_result = {
                    "feedbackPrompt": f"Error: Data fetch failed: {e}",
                    "summary": {},
                    "results": [],
                    "ready": True,
                    "error": f"Data fetch failed: {e}"
                }
                redis_client.set(f"feedback_result:{session_id}", json.dumps(error_result))
                progress_json = redis_client.get(f"feedback_progress:{session_id}")
                if progress_json:
                    progress = json.loads(progress_json)
                    progress["result"] = error_result
                    progress["completed"] = True
                    redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
                return
            update_progress(85, "Generating personalized feedback...", "generating_feedback")
            try:
                feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)
            except Exception as e:
                update_progress(99, f"Feedback generation error: {str(e)}", "error")
                print(f"[Feedback Error] Feedback generation failed: {e}", flush=True)
                error_result = {
                    "feedbackPrompt": f"Error: Feedback generation failed: {e}",
                    "summary": summary,
                    "results": evaluation.get("results", []),
                    "ready": True,
                    "error": f"Feedback generation failed: {e}"
                }
                redis_client.set(f"feedback_result:{session_id}", json.dumps(error_result))
                progress_json = redis_client.get(f"feedback_progress:{session_id}")
                if progress_json:
                    progress = json.loads(progress_json)
                    progress["result"] = error_result
                    progress["completed"] = True
                    redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
                return
            update_progress(95, "Updating your learning progress...", "updating_progress")
            try:
                run_in_background(
                    process_ai_answers,
                    username,
                    str(exercise_block.get("lessonId", "feedback")),
                    answers,
                    {"exercises": all_exercises},
                )
            except Exception as e:
                print(f"[Feedback Error] process_ai_answers failed: {e}", flush=True)
            update_progress(99, "Feedback generation complete!", "complete")
            result = {
                "feedbackPrompt": feedback_prompt,
                "summary": summary,
                "results": evaluation.get("results", []),
                "ready": True
            }
            redis_client.set(f"feedback_result:{session_id}", json.dumps(result))
            progress_json = redis_client.get(f"feedback_progress:{session_id}")
            if progress_json:
                progress = json.loads(progress_json)
                progress["result"] = result
                progress["completed"] = True
                redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
        except Exception as e:
            update_progress(99, f"Error: {str(e)}", "error")
            print(f"[Feedback Error] Uncaught exception: {e}", flush=True)
            error_result = {
                "feedbackPrompt": f"Error: {e}",
                "summary": {},
                "results": [],
                "ready": True,
                "error": str(e)
            }
            redis_client.set(f"feedback_result:{session_id}", json.dumps(error_result))
            progress_json = redis_client.get(f"feedback_progress:{session_id}")
            if progress_json:
                progress = json.loads(progress_json)
                progress["result"] = error_result
                progress["completed"] = True
                redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
        finally:
            # Guarantee that progress is marked completed and feedback_result is set, even if something above failed silently
            progress_json = redis_client.get(f"feedback_progress:{session_id}")
            result_json = redis_client.get(f"feedback_result:{session_id}")
            if progress_json:
                progress = json.loads(progress_json)
                progress["completed"] = True
                if not progress.get("result") and result_json:
                    progress["result"] = json.loads(result_json)
                redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
            elif result_json:
                # If progress is missing but result exists, create a minimal progress
                progress = {"completed": True, "result": json.loads(result_json)}
                redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
    run_in_background(run_feedback_generation)
    print("\033[91m[EXIT] generate_ai_feedback_with_progress\033[0m", flush=True)
    return jsonify({"session_id": session_id})

@ai_bp.route("/ai-feedback/result/<session_id>", methods=["GET"])
def get_feedback_result(session_id):
    print("\033[95m[ENTER] get_feedback_result\033[0m", flush=True)
    """Get the final result of AI feedback generation."""
    username = require_user()
    # print(f"[Feedback Result] Frontend requested result for session {session_id}")
    result_json = redis_client.get(f"feedback_result:{session_id}")
    if not result_json:
        print(f"[Feedback Result] Session {session_id} not found or not ready")
        return jsonify({"error": "Session not found or not ready"}), 404
    result = json.loads(result_json)
    if not result.get("ready"):
        print(f"[Feedback Result] Session {session_id} not completed yet")
        return jsonify({"error": "Generation not complete"}), 400
    print("\033[91m[EXIT] get_feedback_result\033[0m", flush=True)
    return jsonify(result)

@ai_bp.route("/ai-feedback", methods=["GET"])
def get_ai_feedback():
    print("\033[91m[ENTER] get_ai_feedback\033[0m", flush=True)
    """Return the list of cached AI feedback entries."""
    username = require_user()
    # print("Fetching AI feedback for:", username, flush=True)

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    print("\033[91m[EXIT] get_ai_feedback\033[0m", flush=True)
    return jsonify(feedback_data)


@ai_bp.route("/ai-feedback/<feedback_id>", methods=["GET"])
def get_ai_feedback_item(feedback_id):
    print("\033[96m[ENTER] get_ai_feedback_item\033[0m", flush=True)
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
    print("\033[91m[EXIT] get_ai_feedback_item\033[0m", flush=True)
    return jsonify(item)


@ai_bp.route("/ai-feedback", methods=["POST"])
def generate_ai_feedback():
    print("\033[94m[ENTER] generate_ai_feedback\033[0m", flush=True)
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
            # Ignore final . or ? for all exercise types
            user_ans = _strip_final_punct(user_ans)
            correct_ans = _strip_final_punct(correct_ans)
            # Normalize umlauts for both answers
            user_ans = _normalize_umlauts(user_ans)
            correct_ans = _normalize_umlauts(correct_ans)
            if user_ans == correct_ans:
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

        print("\033[91m[EXIT] generate_ai_feedback\033[0m", flush=True)
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
    print("\033[91m[EXIT] generate_ai_feedback\033[0m", flush=True)
    return jsonify(feedback)
