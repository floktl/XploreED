"""
AI Feedback Helper Functions

This module contains helper functions for AI feedback operations that are used
by the AI feedback routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
import os
import json
import random
import uuid
import redis # type: ignore
import re
from typing import Dict, Any, List, Optional, Tuple

from core.services.import_service import *
from features.ai.evaluation.exercise_evaluator import (
    evaluate_answers_with_ai,
    process_ai_answers
)
from features.ai.generation.helpers import (
    _adjust_gapfill_results,
    generate_feedback_prompt
)
from core.database.connection import fetch_topic_memory

# Cached feedback data
FEEDBACK_FILE = [
    {
        "id": "fb1",
        "title": "Feedback After Set 1",
        "instructions": "Here are notes on your first round of exercises.",
        "type": "mixed",
        "feedbackPrompt": "You mixed up some plural forms like 'wir sind' and 'sie sind'. Review the pronouns before continuing.",
        "created_at": "2025-06-12T09:00:00Z"
    },
    {
        "id": "fb2",
        "title": "Feedback After Set 2",
        "instructions": "Comments on your second round of practice.",
        "type": "mixed",
        "feedbackPrompt": "Great improvement! Keep an eye on word order in translations and continue practicing.",
        "created_at": "2025-06-12T09:10:00Z"
    }
]


logger = logging.getLogger(__name__)

# Connect to Redis (host from env, default 'localhost')
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


def get_feedback_progress(session_id: str) -> Dict[str, Any]:
    """
    Get the current progress of AI feedback generation.

    Args:
        session_id: The feedback session ID

    Returns:
        Dictionary containing progress information
    """
    try:
        progress_json = redis_client.get(f"feedback_progress:{session_id}")
        if not progress_json:
            return {"error": "Session not found"}

        progress = json.loads(progress_json)
        logger.debug(f"Feedback progress for session {session_id}: {progress['percentage']}% - {progress['status']}")
        return progress

    except Exception as e:
        logger.error(f"Error getting feedback progress: {e}")
        return {"error": "Failed to get progress"}


def create_feedback_session() -> str:
    """
    Create a new feedback generation session.

    Returns:
        Session ID for the new feedback session
    """
    try:
        session_id = str(uuid.uuid4())
        progress = {
            "percentage": 0,
            "status": "Starting feedback generation...",
            "step": "init",
            "completed": False
        }
        redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
        logger.info(f"Created feedback session: {session_id}")
        return session_id

    except Exception as e:
        logger.error(f"Error creating feedback session: {e}")
        raise


def update_feedback_progress(session_id: str, percentage: int, status: str, step: str) -> bool:
    """
    Update the progress of AI feedback generation.

    Args:
        session_id: The feedback session ID
        percentage: Progress percentage (0-100)
        status: Status message
        step: Current step

    Returns:
        True if update was successful, False otherwise
    """
    try:
        progress_json = redis_client.get(f"feedback_progress:{session_id}")
        if progress_json:
            progress = json.loads(progress_json)
            progress.update({
                "percentage": percentage,
                "status": status,
                "step": step
            })
            redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
            logger.debug(f"Updated feedback progress for session {session_id}: {percentage}% - {status}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error updating feedback progress: {e}")
        return False


def generate_feedback_with_progress(username: str, answers: Dict[str, str],
                                  exercise_block: Optional[Dict] = None) -> str:
    """
    Generate AI feedback with progress tracking.

    Args:
        username: The username
        answers: Dictionary of user answers
        exercise_block: Optional exercise block data

    Returns:
        Session ID for the feedback generation
    """
    try:
        session_id = create_feedback_session()

        def run_feedback_generation():
            try:
                update_feedback_progress(session_id, 10, "Analyzing your answers...", "analyzing")

                if not exercise_block or not isinstance(exercise_block, dict) or not exercise_block.get("exercises") or not isinstance(exercise_block.get("exercises"), list) or len(exercise_block.get("exercises")) == 0:
                    update_feedback_progress(session_id, 99, "No valid exercise block or exercises provided", "error")
                    logger.error(f"Feedback error: Invalid or missing exercise_block: {exercise_block}")

                    # Always write error result to Redis
                    error_result = {
                        "feedbackPrompt": "Error: No valid exercise block or exercises provided.",
                        "summary": {},
                        "results": [],
                        "ready": True,
                        "error": "No valid exercise block or exercises provided."
                    }
                    _store_feedback_result(session_id, error_result)
                    _mark_feedback_complete(session_id, error_result)
                    return

                all_exercises = exercise_block.get("exercises", [])
                update_feedback_progress(session_id, 30, "Evaluating answers with AI...", "evaluating")

                try:
                    evaluation = evaluate_answers_with_ai(all_exercises, answers)
                    evaluation = _adjust_gapfill_results(all_exercises, answers, evaluation)
                except Exception as e:
                    update_feedback_progress(session_id, 99, f"AI evaluation error: {str(e)}", "error")
                    logger.error(f"AI evaluation failed: {e}")
                    error_result = {
                        "feedbackPrompt": f"Error: AI evaluation failed: {e}",
                        "summary": {},
                        "results": [],
                        "ready": True,
                        "error": f"AI evaluation failed: {e}"
                    }
                    _store_feedback_result(session_id, error_result)
                    _mark_feedback_complete(session_id, error_result)
                    return

                if not evaluation:
                    update_feedback_progress(session_id, 99, "AI evaluation failed", "error")
                    logger.error("AI evaluation returned None")
                    error_result = {
                        "feedbackPrompt": "Error: AI evaluation failed.",
                        "summary": {},
                        "results": [],
                        "ready": True,
                        "error": "AI evaluation failed."
                    }
                    _store_feedback_result(session_id, error_result)
                    _mark_feedback_complete(session_id, error_result)
                    return

                update_feedback_progress(session_id, 50, "Processing evaluation results...", "processing")
                summary = _process_evaluation_summary(all_exercises, answers, evaluation)

                update_feedback_progress(session_id, 70, "Fetching your vocabulary and progress data...", "fetching_data")
                try:
                    vocab_data = _fetch_user_vocabulary(username)
                    topic_data = _fetch_user_topic_memory(username)
                except Exception as e:
                    update_feedback_progress(session_id, 99, f"Data fetch error: {str(e)}", "error")
                    logger.error(f"Data fetch failed: {e}")
                    error_result = {
                        "feedbackPrompt": f"Error: Data fetch failed: {e}",
                        "summary": {},
                        "results": [],
                        "ready": True,
                        "error": f"Data fetch failed: {e}"
                    }
                    _store_feedback_result(session_id, error_result)
                    _mark_feedback_complete(session_id, error_result)
                    return

                update_feedback_progress(session_id, 85, "Generating personalized feedback...", "generating_feedback")
                try:
                    feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)
                except Exception as e:
                    update_feedback_progress(session_id, 99, f"Feedback generation error: {str(e)}", "error")
                    logger.error(f"Feedback generation failed: {e}")
                    error_result = {
                        "feedbackPrompt": f"Error: Feedback generation failed: {e}",
                        "summary": summary,
                        "results": evaluation.get("results", []),
                        "ready": True,
                        "error": f"Feedback generation failed: {e}"
                    }
                    _store_feedback_result(session_id, error_result)
                    _mark_feedback_complete(session_id, error_result)
                    return

                update_feedback_progress(session_id, 95, "Updating your learning progress...", "updating_progress")
                try:
                    run_in_background(
                        process_ai_answers,
                        username,
                        str(exercise_block.get("lessonId", "feedback")),
                        answers,
                        {"exercises": all_exercises},
                    )
                except Exception as e:
                    logger.error(f"process_ai_answers failed: {e}")

                update_feedback_progress(session_id, 99, "Feedback generation complete!", "complete")
                result = {
                    "feedbackPrompt": feedback_prompt,
                    "summary": summary,
                    "results": evaluation.get("results", []),
                    "ready": True
                }
                _store_feedback_result(session_id, result)
                _mark_feedback_complete(session_id, result)

            except Exception as e:
                update_feedback_progress(session_id, 99, f"Error: {str(e)}", "error")
                logger.error(f"Uncaught exception in feedback generation: {e}")
                error_result = {
                    "feedbackPrompt": f"Error: {e}",
                    "summary": {},
                    "results": [],
                    "ready": True,
                    "error": str(e)
                }
                _store_feedback_result(session_id, error_result)
                _mark_feedback_complete(session_id, error_result)
            finally:
                _ensure_feedback_completion(session_id)

        run_in_background(run_feedback_generation)
        return session_id

    except Exception as e:
        logger.error(f"Error generating feedback with progress: {e}")
        raise


def get_feedback_result(session_id: str) -> Dict[str, Any]:
    """
    Get the final result of AI feedback generation.

    Args:
        session_id: The feedback session ID

    Returns:
        Dictionary containing feedback result
    """
    try:
        result_json = redis_client.get(f"feedback_result:{session_id}")
        if not result_json:
            logger.warning(f"Feedback session {session_id} not found or not ready")
            return {"error": "Session not found or not ready"}

        result = json.loads(result_json)
        if not result.get("ready"):
            logger.debug(f"Feedback session {session_id} not completed yet")
            return {"error": "Generation not complete"}

        logger.debug(f"Retrieved feedback result for session {session_id}")
        return result

    except Exception as e:
        logger.error(f"Error getting feedback result: {e}")
        return {"error": "Failed to get result"}


def get_cached_feedback_list() -> List[Dict[str, Any]]:
    """
    Get the list of cached AI feedback entries.

    Returns:
        List of cached feedback entries
    """
    try:
        logger.debug(f"Retrieved {len(FEEDBACK_FILE)} cached feedback entries")
        return FEEDBACK_FILE

    except Exception as e:
        logger.error(f"Error getting cached feedback list: {e}")
        return []


def get_cached_feedback_item(feedback_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single cached feedback item by ID.

    Args:
        feedback_id: The feedback item ID

    Returns:
        Feedback item or None if not found
    """
    try:
        feedback_data = get_cached_feedback_list()
        item = next((fb for fb in feedback_data if str(fb.get("id")) == str(feedback_id)), None)

        if item:
            logger.debug(f"Retrieved cached feedback item {feedback_id}")
        else:
            logger.warning(f"Cached feedback item {feedback_id} not found")

        return item

    except Exception as e:
        logger.error(f"Error getting cached feedback item: {e}")
        return None


def generate_ai_feedback_simple(username: str, answers: Dict[str, str],
                            exercise_block: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate AI feedback without progress tracking.

    Args:
        username: The username
        answers: Dictionary of user answers
        exercise_block: Optional exercise block data

    Returns:
        Dictionary containing feedback result
    """
    try:
        if exercise_block:
            all_exercises = exercise_block.get("exercises", [])
            evaluation = evaluate_answers_with_ai(all_exercises, answers)
            evaluation = _adjust_gapfill_results(all_exercises, answers, evaluation)
            id_map = {
                str(r.get("id")): r.get("correct_answer")
                for r in evaluation.get("results", [])
            } if evaluation else {}

            summary = _process_evaluation_summary(all_exercises, answers, evaluation)
            vocab_data = _fetch_user_vocabulary(username)
            topic_data = _fetch_user_topic_memory(username)
            feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

            # Update topic memory asynchronously with the final evaluation results
            run_in_background(
                process_ai_answers,
                username,
                str(exercise_block.get("lessonId", "feedback")),
                answers,
                {"exercises": all_exercises},
            )

            return {
                "feedbackPrompt": feedback_prompt,
                "summary": summary,
                "results": evaluation.get("results", []),
            }

        # Fallback to random cached feedback
        feedback_data = get_cached_feedback_list()
        feedback = random.choice(feedback_data) if feedback_data else {}
        return feedback

    except Exception as e:
        logger.error(f"Error generating AI feedback: {e}")
        return {"error": str(e)}


def _process_evaluation_summary(exercises: List[Dict], answers: Dict[str, str],
                            evaluation: Dict) -> Dict[str, Any]:
    """
    Process evaluation results into a summary.

    Args:
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        evaluation: Evaluation result

    Returns:
        Dictionary containing evaluation summary
    """
    try:
        id_map = {
            str(r.get("id")): r.get("correct_answer")
            for r in evaluation.get("results", [])
        }

        summary = {"correct": 0, "total": len(exercises), "mistakes": []}
        for ex in exercises:
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

        return summary

    except Exception as e:
        logger.error(f"Error processing evaluation summary: {e}")
        return {"correct": 0, "total": 0, "mistakes": []}


def _fetch_user_vocabulary(username: str) -> List[Dict[str, Any]]:
    """
    Fetch user vocabulary data.

    Args:
        username: The username

    Returns:
        List of vocabulary entries
    """
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

        return vocab_data

    except Exception as e:
        logger.error(f"Error fetching user vocabulary: {e}")
        return []


def _fetch_user_topic_memory(username: str) -> List[Dict[str, Any]]:
    """
    Fetch user topic memory data.

    Args:
        username: The username

    Returns:
        List of topic memory entries
    """
    try:
        topic_rows = fetch_topic_memory(username)
        topic_data = [dict(row) for row in topic_rows] if topic_rows else []
        return topic_data

    except Exception as e:
        logger.error(f"Error fetching user topic memory: {e}")
        return []


def _store_feedback_result(session_id: str, result: Dict[str, Any]) -> None:
    """
    Store feedback result in Redis.

    Args:
        session_id: The feedback session ID
        result: The feedback result to store
    """
    try:
        redis_client.set(f"feedback_result:{session_id}", json.dumps(result))
        logger.debug(f"Stored feedback result for session {session_id}")

    except Exception as e:
        logger.error(f"Error storing feedback result: {e}")


def _mark_feedback_complete(session_id: str, result: Dict[str, Any]) -> None:
    """
    Mark feedback generation as complete.

    Args:
        session_id: The feedback session ID
        result: The feedback result
    """
    try:
        progress_json = redis_client.get(f"feedback_progress:{session_id}")
        if progress_json:
            progress = json.loads(progress_json)
            progress["result"] = result
            progress["completed"] = True
            redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
            logger.debug(f"Marked feedback complete for session {session_id}")

    except Exception as e:
        logger.error(f"Error marking feedback complete: {e}")


def _ensure_feedback_completion(session_id: str) -> None:
    """
    Ensure feedback completion is properly marked.

    Args:
        session_id: The feedback session ID
    """
    try:
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

        logger.debug(f"Ensured feedback completion for session {session_id}")

    except Exception as e:
        logger.error(f"Error ensuring feedback completion: {e}")


def _strip_final_punct(text: str) -> str:
    """Strip final punctuation from text."""
    return re.sub(r'[.!?]+$', '', text)


def _normalize_umlauts(text: str) -> str:
    """Normalize umlauts in text."""
    return text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
