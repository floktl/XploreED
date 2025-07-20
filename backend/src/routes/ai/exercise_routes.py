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
import os
import redis

logger = logging.getLogger(__name__)

# Connect to Redis (host from env, default 'localhost')
redis_url = os.getenv('REDIS_URL')
if redis_url:
    redis_client = redis.from_url(redis_url, decode_responses=True)
else:
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

@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id):
    """Evaluate a submitted exercise block and save results."""
    import time
    start_time = time.time()
    username = require_user()
    print(f"[Exercise Submit] Starting submission for user {username}, block {block_id}", flush=True)

    data = request.get_json() or {}
    # logger.info(f"Received submission data for user {username}: {json.dumps(data, indent=2)}")

    exercises, answers, error = parse_submission_data(data)
    if error:
        logger.error(f"Parse submission data error for user {username}: {error}")
        return jsonify({"msg": error}), 400

    print(f"[Exercise Submit] Parsed data, evaluating {len(exercises)} exercises", flush=True)

    # Evaluate first exercise immediately for fast feedback
    first_exercise = exercises[0] if exercises else None
    first_answer = answers.get(str(first_exercise.get("id")), "") if first_exercise else ""

    print(f"[Exercise Submit] Evaluating first exercise immediately", flush=True)
    first_eval_start = time.time()
    first_evaluation = None
    if first_exercise and first_answer:
        # Evaluate just the first exercise
        first_evaluation = evaluate_answers_with_ai([first_exercise], {str(first_exercise.get("id")): first_answer})
        if first_evaluation and first_evaluation.get("results"):
            first_result = first_evaluation["results"][0]
            # Process the first result with basic data
            correct_answer = first_result.get("correct_answer")
            is_correct = False
            # Use the same logic as compile_score_summary for all exercise types
            ua = _strip_final_punct(first_answer).strip().lower()
            ca = _strip_final_punct(correct_answer).strip().lower()
            # Normalize umlauts for both answers
            ua = _normalize_umlauts(ua)
            ca = _normalize_umlauts(ca)
            is_correct = ua == ca

            first_result_with_details = {
                "id": first_result.get("id"),
                "correct_answer": correct_answer,
                "alternatives": [],
                "explanation": "",
                "is_correct": is_correct
            }
        else:
            first_result_with_details = None
    else:
        first_result_with_details = None

    first_eval_end = time.time()
    print(f"[Exercise Submit] First exercise evaluation took {first_eval_end - first_eval_start:.2f}s", flush=True)

    # Capture the Flask app before starting background thread
    from flask import current_app
    app = current_app._get_current_object()

    # Start background task to evaluate remaining exercises
    from threading import Thread
    def background_task():
        with app.app_context():
            _evaluate_remaining_exercises_async(username, block_id, exercises, answers, first_result_with_details)

    Thread(target=background_task, daemon=True).start()

    # Return immediate result with first exercise
    immediate_results = []
    if first_result_with_details:
        immediate_results.append(first_result_with_details)

    # Add placeholder results for remaining exercises
    for i, ex in enumerate(exercises[1:], 1):
        immediate_results.append({
            "id": ex.get("id"),
            "correct_answer": "",
            "alternatives": [],
            "explanation": "",
            "is_correct": None,  # Will be updated when background processing completes
            "loading": True  # Flag to show loading state
        })

    total_time = time.time() - start_time
    print(f"[Exercise Submit] Immediate response time: {total_time:.2f}s", flush=True)

    return jsonify({
        "pass": False,  # Will be updated in background
        "summary": {"correct": 0, "total": len(exercises), "mistakes": []},  # Will be updated in background
        "results": immediate_results,
        "streaming": True  # Flag to indicate this is a streaming response
    })


@ai_bp.route("/ai-exercise/<block_id>/results", methods=["GET"])
def get_ai_exercise_results(block_id):
    """Get the latest results for an exercise block, including alternatives and explanations."""
    username = require_user()
    result_key = f"exercise_result:{username}:{block_id}"
    result_json = redis_client.get(result_key)
    if not result_json:
        return jsonify({
            "status": "processing",
            "message": "Alternatives and explanations are being generated in the background"
        })
    enhanced_data = json.loads(result_json)
    ready_index = enhanced_data.get("ready_index", 1)
    results = enhanced_data.get("results", [])
    exercise_order = enhanced_data.get("exercise_order", [r.get("id") for r in results])
    # Build a mapping from id to result
    result_map = {str(r.get("id")): r for r in results}
    visible_results = []
    for idx, ex_id in enumerate(exercise_order):
        res = result_map.get(str(ex_id), {})
        base = {
            "id": res.get("id", ex_id),
            "is_correct": res.get("is_correct"),
            "correct_answer": res.get("correct_answer"),
        }
        if idx < ready_index:
            visible_results.append({
                **base,
                "alternatives": res.get("alternatives", []),
                "explanation": res.get("explanation", ""),
                "loading": False
            })
        else:
            visible_results.append({
                **base,
                "alternatives": [],
                "explanation": "",
                "loading": True
            })
    return jsonify({
        "status": "processing" if ready_index < len(visible_results) else "complete",
        "results": visible_results,
        "pass": enhanced_data.get("pass", False),
        "summary": enhanced_data.get("summary", {})
    })


def _evaluate_remaining_exercises_async(username, block_id, exercises, answers, first_result):
    """Background task to evaluate remaining exercises and update results."""
    import time
    bg_start = time.time()
    print(f"[Background] Starting evaluation of remaining exercises for user {username}", flush=True)

    try:
        # Evaluate all exercises (including the first one again for consistency)
        eval_start = time.time()
        evaluation, id_map = evaluate_exercises(exercises, answers)
        eval_end = time.time()
        print(f"[Background] Full evaluation took {eval_end - eval_start:.2f}s", flush=True)

        if not evaluation:
            print(f"[Background] Evaluation failed for user {username}", flush=True)
            return

        # Process basic results first (fast)
        basic_start = time.time()
        print(f"[Background] Processing basic results for {len(evaluation.get('results', []))} results", flush=True)
        basic_results = []
        for i, res in enumerate(evaluation.get("results", [])):
            try:
                correct_answer = res.get("correct_answer")
                ex = next((e for e in exercises if str(e.get("id")) == str(res.get("id"))), None)
                user_answer = answers.get(str(res.get("id")), "")

                # Use the same logic as compile_score_summary for all exercise types
                is_correct = False
                ua = _strip_final_punct(user_answer).strip().lower()
                ca = _strip_final_punct(correct_answer).strip().lower()
                ua = _normalize_umlauts(ua)
                ca = _normalize_umlauts(ca)
                is_correct = ua == ca

                basic_result = {
                    "id": res.get("id"),
                    "correct_answer": correct_answer,
                    "alternatives": [],
                    "explanation": "",
                    "is_correct": is_correct
                }
                basic_results.append(basic_result)

            except Exception as e:
                print(f"[Background] Error processing basic result {i}: {e}", flush=True)
                basic_results.append(res)

        # Store basic results in Redis with ready=False
        result_key = f"exercise_result:{username}:{block_id}"
        exercise_ids = [str(ex.get("id")) for ex in exercises]
        redis_client.set(result_key, json.dumps({
            "results": basic_results,
            "pass": bool(evaluation.get("pass")),
            "summary": {"correct": 0, "total": len(exercises), "mistakes": []},
            "ready_index": 1,  # Only the first result is ready initially
            "exercise_order": exercise_ids
        }))
        basic_end = time.time()
        print(f"[Background] Basic results stored in {basic_end - basic_start:.2f}s for user {username}", flush=True)

        # Generate summary (fast)
        feedback_start = time.time()
        print(f"[Background] Generating summary", flush=True)
        try:
            summary = compile_score_summary(exercises, answers, id_map)
            passed = bool(evaluation.get("pass"))

            # Save exercise submission
            save_exercise_submission_async(username, block_id, answers, exercises)

            # Prefetch next exercises
            run_in_background(prefetch_next_exercises, username)

            # Update with summary data
            partial = json.loads(redis_client.get(result_key))
            partial.update({
                "pass": passed,
                "summary": summary
            })
            redis_client.set(result_key, json.dumps(partial))

            feedback_end = time.time()
            print(f"[Background] Summary generated in {feedback_end - feedback_start:.2f}s for user {username}", flush=True)

        except Exception as e:
            print(f"[Background] Error generating summary: {e}", flush=True)

        # Now add alternatives and explanations in parallel (optional, don't block)
        print(f"[Background] Starting parallel alternatives/explanations generation", flush=True)
        print(f"[Background] About to call _add_alternatives_and_explanations_parallel for {len(basic_results)} results", flush=True)
        print(f"[Background] Basic results: {basic_results}", flush=True)

        # Start the alternatives/explanations task in a new thread with app context
        from threading import Thread
        from flask import current_app
        app = current_app._get_current_object()

        def alternatives_task():
            with app.app_context():
                _add_alternatives_and_explanations_parallel(username, block_id, basic_results, exercises, answers)

        Thread(target=alternatives_task, daemon=True).start()
        print(f"[Background] Background task for alternatives/explanations started", flush=True)

        # Test if background task is working by adding a simple marker
        test_key = f"{username}_{block_id}_test"
        redis_client.set(test_key, json.dumps({"test": "background_task_started", "timestamp": time.time()}))
        print(f"[Background] Added test marker: {test_key}", flush=True)

        bg_end = time.time()
        print(f"[Background] Main processing completed in {bg_end - bg_start:.2f}s for user {username}", flush=True)

    except Exception as e:
        print(f"[Background] Error in _evaluate_remaining_exercises_async: {e}", flush=True)


def _add_alternatives_and_explanations_parallel(username, block_id, basic_results, exercises, answers):
    """Background task to add alternatives and explanations in sequential order."""
    import time
    parallel_start = time.time()
    print(f"[Background] 🚀 SEQUENTIAL FUNCTION CALLED for user {username}", flush=True)
    print(f"[Background] Processing exercises in order to maintain sequence!", flush=True)
    print(f"[Background] Received {len(basic_results)} basic results to process", flush=True)

    try:
        # Process exercises sequentially to maintain order
        for i, res in enumerate(basic_results):
            try:
                print(f"[Background] 🎯 Processing exercise {i+1}/{len(basic_results)} in order", flush=True)

                correct_answer = res.get("correct_answer")
                ex = next((e for e in exercises if str(e.get("id")) == str(res.get("id"))), None)
                user_answer = answers.get(str(res.get("id")), "")

                enhanced_result = dict(res)

                # Generate alternatives (simple, no parallel processing for now)
                try:
                    print(f"[Background] Generating alternatives for result {i} (exercise {i+1})", flush=True)
                    alternatives = generate_alternative_answers(correct_answer)[:3] if correct_answer else []
                    enhanced_result["alternatives"] = alternatives if isinstance(alternatives, list) else []
                    print(f"[Background] Generated {len(enhanced_result['alternatives'])} alternatives for result {i}", flush=True)
                except Exception as e:
                    print(f"[Background] Error generating alternatives for result {i}: {e}", flush=True)
                    enhanced_result["alternatives"] = []

                # Generate explanation (simple, no parallel processing for now)
                try:
                    print(f"[Background] Generating explanation for result {i} (exercise {i+1})", flush=True)
                    question = ex.get("question") if ex else ""
                    explanation = generate_explanation(question, user_answer, correct_answer) if correct_answer else ""
                    enhanced_result["explanation"] = explanation if isinstance(explanation, str) else ""
                    print(f"[Background] Generated explanation for result {i} (length: {len(enhanced_result['explanation'])}): {enhanced_result['explanation'][:100]}...", flush=True)
                except Exception as e:
                    print(f"[Background] Error generating explanation for result {i}: {e}", flush=True)
                    enhanced_result["explanation"] = ""

                # Update the stored results immediately after each exercise is processed
                result_key = f"exercise_result:{username}:{block_id}"
                partial = json.loads(redis_client.get(result_key))
                current_results = partial["results"]
                if i < len(current_results):
                    current_results[i] = enhanced_result
                partial["results"] = current_results
                # Increment ready_index after each exercise is processed
                partial["ready_index"] = i + 1  # Reveal up to this exercise (1-based)
                redis_client.set(result_key, json.dumps(partial))
                # Add a short delay for smooth reveal
                time.sleep(0.7)

            except Exception as e:
                print(f"[Background] Error processing result {i}: {e}", flush=True)
                import traceback
                traceback.print_exc()

        # After all are processed, set ready=True
        result_key = f"exercise_result:{username}:{block_id}"
        partial = json.loads(redis_client.get(result_key))
        redis_client.set(result_key, json.dumps(partial))
        print(f"[Background] All alternatives/explanations processed and ready flag set for user {username}", flush=True)

    except Exception as e:
        print(f"[Background] ❌ CRITICAL ERROR in _add_alternatives_and_explanations_parallel: {e}", flush=True)
        import traceback
        traceback.print_exc()

        # Store error information so frontend knows something went wrong
        error_key = f"{username}_{block_id}"
        redis_client.set(error_key, json.dumps({"error": str(e), "error_timestamp": time.time()}))


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
