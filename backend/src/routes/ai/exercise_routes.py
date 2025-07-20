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

# Global storage for enhanced results (in production, use Redis or database)
_enhanced_results = {}

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

    # Start background task to evaluate remaining exercises
    run_in_background(
        _evaluate_remaining_exercises_async,
        username,
        block_id,
        exercises,
        answers,
        first_result_with_details
    )

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

    result_key = f"{username}_{block_id}"
    print(f"[Results Endpoint] Checking for results with key: {result_key}", flush=True)
    print(f"[Results Endpoint] Available keys: {list(_enhanced_results.keys())}", flush=True)

    if result_key in _enhanced_results:
        enhanced_data = _enhanced_results[result_key]
        print(f"[Results Endpoint] Found data for {username}: {enhanced_data.keys()}", flush=True)

        # Log the actual results to see what's in them
        results = enhanced_data.get("results", [])
        print(f"[Results Endpoint] Number of results: {len(results)}", flush=True)

                # Check if alternatives and explanations are actually generated for ALL exercises
        all_enhanced = True
        for i, result in enumerate(results):
            alternatives_count = len(result.get('alternatives', []))
            explanation_length = len(result.get('explanation', ''))
            print(f"[Results Endpoint] Result {i}: id={result.get('id')}, alternatives={alternatives_count}, explanation_length={explanation_length}", flush=True)

            if alternatives_count == 0 and explanation_length == 0:
                all_enhanced = False

        # Only return "complete" if ALL exercises have enhanced content
        if all_enhanced:
            print(f"[Results Endpoint] Returning complete results - ALL exercises have enhanced content", flush=True)
            return jsonify({
                "status": "complete",
                "results": enhanced_data.get("results", []),
                "pass": enhanced_data.get("pass", False),
                "summary": enhanced_data.get("summary", {})
            })
        else:
            print(f"[Results Endpoint] Results found but not all exercises have enhanced content yet, returning processing status", flush=True)
            return jsonify({
                "status": "processing",
                "message": "Alternatives and explanations are being generated in the background"
            })
    else:
        print(f"[Results Endpoint] No data found for key: {result_key}", flush=True)
        return jsonify({
            "status": "processing",
            "message": "Alternatives and explanations are being generated in the background"
        })


def _add_alternatives_and_explanations_async(username, block_id, exercises, answers, basic_results):
    """Background task to add alternatives and explanations to results."""
    print(f"[Background] Starting alternatives/explanations for user {username}", flush=True)

    enhanced_results = []
    for i, res in enumerate(basic_results):
        try:
            correct_answer = res.get("correct_answer")
            ex = next((e for e in exercises if str(e.get("id")) == str(res.get("id"))), None)
            user_answer = answers.get(str(res.get("id")), "")

            enhanced_result = dict(res)

            # Generate alternatives (optional, don't block if it fails)
            try:
                alternatives = generate_alternative_answers(correct_answer)[:3] if correct_answer else []
                if isinstance(alternatives, list):
                    enhanced_result["alternatives"] = alternatives
                else:
                    enhanced_result["alternatives"] = []
            except Exception as e:
                print(f"[Background] Failed to generate alternatives for result {i}: {e}", flush=True)
                enhanced_result["alternatives"] = []

            # Generate explanation (optional, don't block if it fails)
            try:
                question = ex.get("question") if ex else ""
                explanation = generate_explanation(question, user_answer, correct_answer) if correct_answer else ""
                if isinstance(explanation, str):
                    enhanced_result["explanation"] = explanation
                else:
                    enhanced_result["explanation"] = ""
            except Exception as e:
                print(f"[Background] Failed to generate explanation for result {i}: {e}", flush=True)
                enhanced_result["explanation"] = ""

            enhanced_results.append(enhanced_result)

        except Exception as e:
            print(f"[Background] Error processing result {i}: {e}")
            enhanced_results.append(res)  # Keep original result if processing fails

    # Store the enhanced results
    result_key = f"{username}_{block_id}"
    _enhanced_results[result_key] = enhanced_results

    print(f"[Background] Completed alternatives/explanations for user {username}, stored {len(enhanced_results)} results", flush=True)


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

        # Store basic results immediately so frontend can show them
        result_key = f"{username}_{block_id}"
        _enhanced_results[result_key] = {
            "results": basic_results,
            "pass": bool(evaluation.get("pass")),
            "summary": {"correct": 0, "total": len(exercises), "mistakes": []}
        }
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
            _enhanced_results[result_key].update({
                "pass": passed,
                "summary": summary
            })

            feedback_end = time.time()
            print(f"[Background] Summary generated in {feedback_end - feedback_start:.2f}s for user {username}", flush=True)

        except Exception as e:
            print(f"[Background] Error generating summary: {e}", flush=True)

        # Now add alternatives and explanations in parallel (optional, don't block)
        print(f"[Background] Starting parallel alternatives/explanations generation", flush=True)
        print(f"[Background] About to call _add_alternatives_and_explanations_parallel for {len(basic_results)} results", flush=True)
        run_in_background(
            _add_alternatives_and_explanations_parallel,
            username,
            block_id,
            basic_results,
            exercises,
            answers
        )
        print(f"[Background] Background task for alternatives/explanations started", flush=True)

        bg_end = time.time()
        print(f"[Background] Main processing completed in {bg_end - bg_start:.2f}s for user {username}", flush=True)

    except Exception as e:
        print(f"[Background] Error in _evaluate_remaining_exercises_async: {e}", flush=True)


def _add_alternatives_and_explanations_parallel(username, block_id, basic_results, exercises, answers):
    """Background task to add alternatives and explanations in parallel."""
    import time
    parallel_start = time.time()
    print(f"[Background] 🚀 PARALLEL FUNCTION CALLED for user {username}", flush=True)
    print(f"[Background] This confirms the background task is running!", flush=True)

    try:
        enhanced_results = []
        for i, res in enumerate(basic_results):
            try:
                correct_answer = res.get("correct_answer")
                ex = next((e for e in exercises if str(e.get("id")) == str(res.get("id"))), None)
                user_answer = answers.get(str(res.get("id")), "")

                enhanced_result = dict(res)

                # Generate alternatives and explanations in parallel (with timeouts)
                import concurrent.futures
                import threading

                alternatives = []
                explanation = ""

                def get_alternatives():
                    try:
                        print(f"[Background] Generating alternatives for result {i}", flush=True)
                        alts = generate_alternative_answers(correct_answer)[:3] if correct_answer else []
                        result = alts if isinstance(alts, list) else []
                        print(f"[Background] Generated {len(result)} alternatives for result {i}: {result}", flush=True)
                        return result
                    except Exception as e:
                        print(f"[Background] Error generating alternatives for result {i}: {e}", flush=True)
                        return []

                def get_explanation():
                    try:
                        print(f"[Background] Generating explanation for result {i}", flush=True)
                        question = ex.get("question") if ex else ""
                        expl = generate_explanation(question, user_answer, correct_answer) if correct_answer else ""
                        result = expl if isinstance(expl, str) else ""
                        print(f"[Background] Generated explanation for result {i} (length: {len(result)}): {result[:100]}...", flush=True)
                        return result
                    except Exception as e:
                        print(f"[Background] Error generating explanation for result {i}: {e}", flush=True)
                        return ""

                # Run both in parallel with 3-second timeout each
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    future_alternatives = executor.submit(get_alternatives)
                    future_explanation = executor.submit(get_explanation)

                    try:
                        alternatives = future_alternatives.result(timeout=3)
                    except Exception as e:
                        print(f"[Background] Timeout/error getting alternatives for result {i}: {e}", flush=True)
                        alternatives = []

                    try:
                        explanation = future_explanation.result(timeout=3)
                    except Exception as e:
                        print(f"[Background] Timeout/error getting explanation for result {i}: {e}", flush=True)
                        explanation = ""

                enhanced_result["alternatives"] = alternatives
                enhanced_result["explanation"] = explanation
                enhanced_results.append(enhanced_result)
                print(f"[Background] Enhanced result {i}: {len(alternatives)} alternatives, {len(explanation)} chars explanation", flush=True)

                # Update the stored results immediately after each exercise is processed
                result_key = f"{username}_{block_id}"
                if result_key in _enhanced_results:
                    # Get current results and update only this specific result
                    current_results = _enhanced_results[result_key]["results"]
                    if i < len(current_results):
                        current_results[i] = enhanced_result
                        print(f"[Background] ✅ UPDATED result {i} immediately for user {username}", flush=True)
                    else:
                        print(f"[Background] ❌ ERROR: Result index {i} out of range for user {username}", flush=True)

            except Exception as e:
                print(f"[Background] Error processing result {i}: {e}", flush=True)
                enhanced_results.append(res)

        # Final update with all results (for consistency)
        result_key = f"{username}_{block_id}"
        if result_key in _enhanced_results:
            _enhanced_results[result_key]["results"] = enhanced_results
            parallel_end = time.time()
            print(f"[Background] ✅ FINAL UPDATE: All alternatives/explanations completed for user {username} in {parallel_end - parallel_start:.2f}s", flush=True)
            print(f"[Background] Final results for {username}: {len(enhanced_results)} results", flush=True)
            for i, result in enumerate(enhanced_results):
                print(f"[Background] Final result {i}: {len(result.get('alternatives', []))} alternatives, {len(result.get('explanation', ''))} chars explanation", flush=True)
        else:
            print(f"[Background] ❌ ERROR: Result key {result_key} not found in _enhanced_results", flush=True)

    except Exception as e:
        print(f"[Background] ❌ CRITICAL ERROR in _add_alternatives_and_explanations_parallel: {e}", flush=True)
        import traceback
        traceback.print_exc()


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
