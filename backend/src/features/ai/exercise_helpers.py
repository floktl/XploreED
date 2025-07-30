"""
AI Exercise Helper Functions

This module contains helper functions for AI exercise operations that are used
by the AI exercise routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
import re
import os
import redis
import json
import time
from typing import Dict, Any, List, Optional, Tuple

from core.services.import_service import *
from features.ai.evaluation.exercise_evaluator import (
    evaluate_answers_with_ai,
    generate_alternative_answers,
    generate_explanation
)
from features.ai.generation.exercise_generator import evaluate_exercises
from features.ai.exercise_helpers import compile_score_summary, save_exercise_submission_async, run_in_background
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from features.ai.generation.exercise_generator import prefetch_next_exercises
from features.ai.generation.helpers import _adjust_gapfill_results


logger = logging.getLogger(__name__)

# Connect to Redis (host from env, default 'localhost')
redis_url = os.getenv('REDIS_URL')
if redis_url:
    redis_client = redis.from_url(redis_url, decode_responses=True)
else:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


def check_gap_fill_correctness(exercise: dict, user_answer: str, correct_answer: str) -> bool:
    """
    Check if a gap-fill answer is correct based on grammatical context.

    Args:
        exercise: The exercise dictionary containing question and type
        user_answer: The user's submitted answer
        correct_answer: The correct answer for comparison

    Returns:
        True if the answer is correct, False otherwise
    """
    try:
        # Get the question text to understand the context
        question = exercise.get("question", "").lower()
        user_ans = user_answer.lower().strip()
        correct_ans = correct_answer.lower().strip()

        logger.debug(f"Checking gap-fill: question='{question}', user='{user_ans}', correct='{correct_ans}'")

        # First try exact match
        if user_ans == correct_ans:
            logger.debug("Exact match found")
            return True

        # Check for common German grammar patterns
        # Pattern 1: Personal pronouns with verb conjugation
        if "habe" in question or "habe " in question:
            # "____ habe einen Hund" - should be "Ich" (1st person singular)
            if user_ans in ["ich", "i"] and correct_ans in ["ich", "i"]:
                logger.debug("Correct 1st person singular with 'habe'")
                return True
            elif user_ans in ["du", "d"] and correct_ans in ["ich", "i"]:
                logger.debug("Wrong: 'du' with 'habe' should be 'ich'")
                return False

        if "bist" in question or "bist " in question:
            # "____ bist glücklich" - should be "Du" (2nd person singular)
            if user_ans in ["du", "d"] and correct_ans in ["du", "d"]:
                logger.debug("Correct 2nd person singular with 'bist'")
                return True
            elif user_ans in ["ich", "i"] and correct_ans in ["du", "d"]:
                logger.debug("Wrong: 'ich' with 'bist' should be 'du'")
                return False

        if "ist" in question or "ist " in question:
            # "____ ist ein Student" - could be "Er", "Sie", "Es" (3rd person singular)
            if user_ans in ["er", "sie", "es"] and correct_ans in ["er", "sie", "es"]:
                logger.debug("Correct 3rd person singular with 'ist'")
                return True

        if "sind" in question or "sind " in question:
            # "____ sind Studenten" - could be "Sie" (3rd person plural) or "Wir" (1st person plural)
            if user_ans in ["sie", "wir"] and correct_ans in ["sie", "wir"]:
                logger.debug("Correct plural with 'sind'")
                return True

        # Pattern 2: Verb conjugation in translations
        if "sein" in user_ans and "sind" in correct_ans:
            # "Sie sein Studenten" vs "Sie sind Studenten"
            logger.debug("Wrong: 'sein' should be 'sind' for plural")
            return False

        if "haben" in user_ans and "hat" in correct_ans:
            # "Er haben" vs "Er hat"
            logger.debug("Wrong: 'haben' should be 'hat' for 3rd person singular")
            return False

        # Pattern 3: Article agreement
        if user_ans in ["der", "die", "das"] and correct_ans in ["der", "die", "das"]:
            # Check if the article matches the gender of the noun
            # This is a simplified check - in practice, you'd need a more sophisticated system
            logger.debug("Article check passed")
            return True

        # If no specific patterns match, fall back to exact comparison
        logger.debug("No specific pattern matched, using exact comparison")
        return user_ans == correct_ans

    except Exception as e:
        logger.error(f"Error checking gap-fill correctness: {e}")
        return False


def parse_submission_data(data: Dict[str, Any]) -> Tuple[List[Dict], Dict[str, str], Optional[str]]:
    """
    Parse submission data from request.

    Args:
        data: The request data dictionary

    Returns:
        Tuple of (exercises, answers, error_message)
    """
    try:
        # Handle both direct format and exercise_block format
        exercises = data.get("exercises", [])
        answers = data.get("answers", {})

        # If exercises are not directly in data, check exercise_block
        if not exercises:
            exercise_block = data.get("exercise_block", {})
            if isinstance(exercise_block, dict):
                exercises = exercise_block.get("exercises", [])

        if not exercises:
            return [], {}, "No exercises provided"

        if not answers:
            return [], {}, "No answers provided"

        return exercises, answers, None

    except Exception as e:
        logger.error(f"Error parsing submission data: {e}")
        return [], {}, f"Error parsing data: {str(e)}"


def evaluate_first_exercise(exercises: List[Dict], answers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Evaluate the first exercise immediately for fast feedback.

    Args:
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers

    Returns:
        Evaluation result for the first exercise or None
    """
    try:
        if not exercises:
            return None

        first_exercise = exercises[0]
        first_answer = answers.get(str(first_exercise.get("id")), "")

        if not first_answer:
            return None

        # Evaluate just the first exercise
        first_evaluation = evaluate_answers_with_ai([first_exercise], {str(first_exercise.get("id")): first_answer})

        if not first_evaluation or not first_evaluation.get("results"):
            return None

        first_result = first_evaluation["results"][0]
        correct_answer = first_result.get("correct_answer")

        # Use the same logic as compile_score_summary for all exercise types
        is_correct = False
        ua = _strip_final_punct(first_answer).strip().lower()
        ca = _strip_final_punct(correct_answer).strip().lower()
        # Normalize umlauts for both answers
        ua = _normalize_umlauts(ua)
        ca = _normalize_umlauts(ca)

        # Improved grading logic
        if ua == ca:
            is_correct = True
        else:
            # For gap-fill exercises, check if the answer makes grammatical sense
            exercise_type = first_exercise.get("type", "")
            if exercise_type == "gap-fill":
                is_correct = check_gap_fill_correctness(first_exercise, ua, ca)
            else:
                # For other exercise types, use exact match
                is_correct = ua == ca

        first_result_with_details = {
            "id": first_result.get("id"),
            "correct_answer": correct_answer,
            "alternatives": [],
            "explanation": "",
            "is_correct": is_correct
        }

        logger.info(f"First exercise evaluation complete - Correct: {is_correct}")
        return first_result_with_details

    except Exception as e:
        logger.error(f"Error evaluating first exercise: {e}")
        return None


def create_immediate_results(exercises: List[Dict], first_result: Optional[Dict]) -> List[Dict[str, Any]]:
    """
    Create immediate results for all exercises.

    Args:
        exercises: List of exercise dictionaries
        first_result: Result for the first exercise

    Returns:
        List of immediate results
    """
    try:
        immediate_results = []

        if first_result:
            immediate_results.append(first_result)

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

        return immediate_results

    except Exception as e:
        logger.error(f"Error creating immediate results: {e}")
        return []


def evaluate_remaining_exercises_async(username: str, block_id: str, exercises: List[Dict],
                                     answers: Dict[str, str], first_result: Optional[Dict],
                                     exercise_block: Optional[Dict] = None) -> None:
    """
    Background task to evaluate remaining exercises and update results.

    Args:
        username: The username
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        first_result: Result for the first exercise
        exercise_block: Optional exercise block data
    """
    try:
        bg_start = time.time()
        logger.info(f"Starting evaluation of remaining exercises for user {username}")

        # Evaluate all exercises (including the first one again for consistency)
        evaluation, id_map = evaluate_exercises(exercises, answers)
        if not evaluation:
            logger.error(f"Evaluation failed for user {username}")
            return

        # Process basic results first (fast)
        basic_results = _process_basic_results(evaluation, exercises, answers)

        # Store basic results in Redis with ready=False
        _store_basic_results(username, block_id, exercises, basic_results, evaluation)

        # Generate summary and save submission
        _process_evaluation_summary(username, block_id, exercises, answers, id_map, evaluation, exercise_block)

        # Start the alternatives/explanations task in a new thread
        _start_alternatives_task(username, block_id, basic_results, exercises, answers)

        # Test if background task is working by adding a simple marker
        test_key = f"{username}_{block_id}_test"
        redis_client.set(test_key, json.dumps({"test": "background_task_started", "timestamp": time.time()}))

        logger.info(f"Background evaluation completed for user {username} in {time.time() - bg_start:.2f}s")

    except Exception as e:
        logger.error(f"Error in evaluate_remaining_exercises_async: {e}")


def _process_basic_results(evaluation: Dict, exercises: List[Dict], answers: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Process basic results from evaluation.

    Args:
        evaluation: The evaluation result
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers

    Returns:
        List of processed basic results
    """
    try:
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

                # Improved grading logic
                if ua == ca:
                    is_correct = True
                else:
                    # For gap-fill exercises, check if the answer makes grammatical sense
                    exercise_type = ex.get("type", "") if ex else ""
                    if exercise_type == "gap-fill":
                        is_correct = check_gap_fill_correctness(ex, ua, ca)
                    else:
                        # For other exercise types, use exact match
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
                logger.error(f"Error processing basic result {i}: {e}")
                basic_results.append(res)

        return basic_results

    except Exception as e:
        logger.error(f"Error processing basic results: {e}")
        return []


def _store_basic_results(username: str, block_id: str, exercises: List[Dict],
                        basic_results: List[Dict], evaluation: Dict) -> None:
    """
    Store basic results in Redis.

    Args:
        username: The username
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        basic_results: List of basic results
        evaluation: The evaluation result
    """
    try:
        result_key = f"exercise_result:{username}:{block_id}"
        exercise_ids = [str(ex.get("id")) for ex in exercises]
        result = {
            "results": basic_results,
            "pass": bool(evaluation.get("pass")),
            "summary": {"correct": 0, "total": len(exercises), "mistakes": []},
            "ready_index": 1,  # Only the first result is ready initially
            "exercise_order": exercise_ids
        }
        redis_client.set(result_key, json.dumps(result))
        logger.debug(f"Wrote evaluation result for user={username} block_id={block_id}")

    except Exception as e:
        logger.error(f"Error storing basic results: {e}")


def _process_evaluation_summary(username: str, block_id: str, exercises: List[Dict],
                              answers: Dict[str, str], id_map: Dict, evaluation: Dict,
                              exercise_block: Optional[Dict]) -> None:
    """
    Process evaluation summary and save submission.

    Args:
        username: The username
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        id_map: Exercise ID mapping
        evaluation: The evaluation result
        exercise_block: Optional exercise block data
    """
    try:
        summary = compile_score_summary(exercises, answers, id_map)
        passed = bool(evaluation.get("pass"))

        # Save exercise submission with exercise block
        logger.debug(f"Exercise block passed to save_exercise_submission_async: topic='{exercise_block.get('topic') if exercise_block else 'None'}'")
        save_exercise_submission_async(username, block_id, answers, exercises, exercise_block)

        # Prefetch next exercises
        run_in_background(prefetch_next_exercises, username)

        # Update with summary data
        result_key = f"exercise_result:{username}:{block_id}"
        partial = json.loads(redis_client.get(result_key))
        partial.update({
            "pass": passed,
            "summary": summary
        })
        redis_client.set(result_key, json.dumps(partial))

    except Exception as e:
        logger.error(f"Error generating summary: {e}")


def _start_alternatives_task(username: str, block_id: str, basic_results: List[Dict],
                           exercises: List[Dict], answers: Dict[str, str]) -> None:
    """
    Start the alternatives/explanations task in a new thread.

    Args:
        username: The username
        block_id: The exercise block ID
        basic_results: List of basic results
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
    """
    try:
        from threading import Thread
        from flask import current_app # type: ignore
        app = current_app._get_current_object()

        def alternatives_task():
            with app.app_context():
                add_alternatives_and_explanations_parallel(username, block_id, basic_results, exercises, answers)

        Thread(target=alternatives_task, daemon=True).start()

    except Exception as e:
        logger.error(f"Error starting alternatives task: {e}")


def add_alternatives_and_explanations_parallel(username: str, block_id: str, basic_results: List[Dict],
                                             exercises: List[Dict], answers: Dict[str, str]) -> None:
    """
    Background task to add alternatives and explanations in sequential order.

    Args:
        username: The username
        block_id: The exercise block ID
        basic_results: List of basic results
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
    """
    try:
        parallel_start = time.time()
        logger.info(f"Starting alternatives and explanations generation for user {username}")

        # Process exercises sequentially to maintain order
        for i, res in enumerate(basic_results):
            try:
                enhanced_result = _enhance_single_result(res, exercises, answers, i)
                _update_stored_results(username, block_id, enhanced_result, i)
                # Add a short delay for smooth reveal
                time.sleep(0.7)

            except Exception as e:
                logger.error(f"Error processing result {i}: {e}")
                import traceback
                traceback.print_exc()

        logger.info(f"Alternatives and explanations completed for user {username} in {time.time() - parallel_start:.2f}s")

    except Exception as e:
        logger.error(f"Critical error in add_alternatives_and_explanations_parallel: {e}")
        import traceback
        traceback.print_exc()

        # Store error information so frontend knows something went wrong
        error_key = f"{username}_{block_id}"
        redis_client.set(error_key, json.dumps({"error": str(e), "error_timestamp": time.time()}))


def _enhance_single_result(res: Dict, exercises: List[Dict], answers: Dict[str, str], index: int) -> Dict[str, Any]:
    """
    Enhance a single result with alternatives and explanations.

    Args:
        res: The result to enhance
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        index: The result index

    Returns:
        Enhanced result dictionary
    """
    try:
        ex = next((e for e in exercises if str(e.get("id")) == str(res.get("id"))), None)
        if not ex:
            logger.error(f"Exercise not found for result {index} with id {res.get('id')}")
            return res

        # Use the correct answer from the original exercise, not from the result
        correct_answer = ex.get("correctAnswer", "")
        user_answer = answers.get(str(res.get("id")), "")
        enhanced_result = dict(res)

        # Generate alternatives
        try:
            alternatives = generate_alternative_answers(correct_answer)[:3] if correct_answer else []
            enhanced_result["alternatives"] = alternatives if isinstance(alternatives, list) else []
        except Exception as e:
            logger.error(f"Error generating alternatives for result {index}: {e}")
            enhanced_result["alternatives"] = []

        # Generate explanation
        try:
            question = ex.get("question") if ex else ""
            explanation = generate_explanation(question, user_answer, correct_answer) if correct_answer else ""
            enhanced_result["explanation"] = explanation if isinstance(explanation, str) else ""
        except Exception as e:
            logger.error(f"Error generating explanation for result {index}: {e}")
            enhanced_result["explanation"] = ""

        return enhanced_result

    except Exception as e:
        logger.error(f"Error enhancing single result {index}: {e}")
        return res


def _update_stored_results(username: str, block_id: str, enhanced_result: Dict, index: int) -> None:
    """
    Update stored results with enhanced result.

    Args:
        username: The username
        block_id: The exercise block ID
        enhanced_result: The enhanced result
        index: The result index
    """
    try:
        result_key = f"exercise_result:{username}:{block_id}"
        partial = json.loads(redis_client.get(result_key))
        current_results = partial["results"]
        if index < len(current_results):
            current_results[index] = enhanced_result
        partial["results"] = current_results
        # Increment ready_index after each exercise is processed
        partial["ready_index"] = index + 1  # Reveal up to this exercise (1-based)
        redis_client.set(result_key, json.dumps(partial))



    except Exception as e:
        logger.error(f"Error updating stored results: {e}")


def get_exercise_results(username: str, block_id: str) -> Dict[str, Any]:
    """
    Get the latest results for an exercise block, including alternatives and explanations.

    Args:
        username: The username
        block_id: The exercise block ID

    Returns:
        Dictionary containing exercise results
    """
    try:
        result_key = f"exercise_result:{username}:{block_id}"
        result_json = redis_client.get(result_key)

        if not result_json:
            return {
                "status": "processing",
                "message": "Alternatives and explanations are being generated in the background"
            }

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

        final_status = "processing" if ready_index < len(visible_results) else "complete"

        return {
            "status": final_status,
            "results": visible_results,
            "pass": enhanced_data.get("pass", False),
            "summary": enhanced_data.get("summary", {})
        }

    except Exception as e:
        logger.error(f"Error getting exercise results: {e}")
        return {
            "status": "error",
            "message": "Error retrieving results"
        }


def argue_exercise_evaluation(block_id: str, exercises: List[Dict], answers: Dict[str, str],
                            exercise_block: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Reevaluate answers when the student wants to argue with the AI.

    Args:
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        exercise_block: Optional exercise block data

    Returns:
        Dictionary containing reevaluation results
    """
    try:
        evaluation = evaluate_answers_with_ai(exercises, answers, mode="argue")
        evaluation = _adjust_gapfill_results(exercises, answers, evaluation)

        if not evaluation:
            return {"error": "Evaluation failed"}

        return evaluation

    except Exception as e:
        logger.error(f"Error arguing exercise evaluation: {e}")
        return {"error": str(e)}


def get_topic_memory_status(username: str, block_id: str) -> Dict[str, Any]:
    """
    Check if topic memory processing is complete for a given block.

    Args:
        username: The username
        block_id: The exercise block ID

    Returns:
        Dictionary containing topic memory status
    """
    try:
        # Check in-memory completion tracking
        try:
            from flask import current_app # type: ignore
        except ImportError:
            current_app = None
        completion_key = f"{username}:{block_id}"

        if hasattr(current_app, 'topic_memory_completion'):
            completed = current_app.topic_memory_completion.get(completion_key, False)
            if completed:
                # Remove the flag after checking
                del current_app.topic_memory_completion[completion_key]
        else:
            completed = False

        return {
            "completed": completed,
            "block_id": block_id,
            "username": username
        }

    except Exception as e:
        logger.error(f"Error checking topic memory status: {e}")
        return {"completed": False, "error": str(e)}


def _strip_final_punct(text: str) -> str:
    """Strip final punctuation from text."""
    return re.sub(r'[.!?]+$', '', text)


def _normalize_umlauts(text: str) -> str:
    """Normalize umlauts in text."""
    return text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
