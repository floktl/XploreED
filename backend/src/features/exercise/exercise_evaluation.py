"""
XplorED - Exercise Evaluation Module

This module provides exercise evaluation and processing functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Evaluation Components:
- Answer Validation: Check gap-fill correctness and parse submission data
- Exercise Processing: Evaluate exercises and create immediate results
- Async Evaluation: Handle asynchronous exercise evaluation and AI processing

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import re
import os
import json
import time
from datetime import datetime
from typing import List, Optional, Tuple, Any

from features.ai.generation.exercise_processing import evaluate_exercises
from shared.text_utils import _normalize_umlauts, _strip_final_punct
from features.ai.generation.feedback_helpers import _adjust_gapfill_results
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from external.redis import redis_client
from shared.exceptions import DatabaseError
from shared.types import ExerciseList, ExerciseAnswers, EvaluationResult, AnalyticsData, BlockResult
from features.ai.prompts import alternative_answers_prompt, explanation_prompt
from external.mistral.client import send_prompt
from shared.text_utils import _extract_json as extract_json

logger = logging.getLogger(__name__)

# Import the function from AI evaluation to avoid circular imports
from features.ai.evaluation import check_gap_fill_correctness


def parse_submission_data(data: AnalyticsData) -> Tuple[ExerciseList, ExerciseAnswers, Optional[str]]:
    """
    Parse submission data to extract exercises, answers, and block ID.

    Args:
        data: The submission data dictionary

    Returns:
        Tuple of (exercises, answers, block_id)
    """
    try:
        # Check if exercises are in the root level or nested in exercise_block
        exercises = data.get("exercises", [])
        if not exercises and "exercise_block" in data:
            exercise_block = data.get("exercise_block", {})
            exercises = exercise_block.get("exercises", [])
            logger.debug(f"Extracted exercises from exercise_block: {len(exercises)} exercises")

        answers = data.get("answers", {})
        block_id = data.get("block_id")

        logger.debug(f"Parsed submission: {len(exercises)} exercises, {len(answers)} answers, block_id: {block_id}")
        return exercises, answers, block_id

    except Exception as e:
        logger.error(f"Error parsing submission data: {e}")
        raise DatabaseError(f"Error parsing submission data: {str(e)}")


def evaluate_first_exercise(exercises: ExerciseList, answers: ExerciseAnswers) -> EvaluationResult:
    """
    Evaluate the first exercise immediately for quick feedback.

    Args:
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers

    Returns:
        Evaluation result for the first exercise or None if no exercises
    """
    try:
        if not exercises:
            logger.warning("No exercises provided for evaluation")
            return None

        first_exercise = exercises[0]
        exercise_id = str(first_exercise.get("id", 0))
        user_answer = answers.get(exercise_id, "")

        if not user_answer:
            logger.warning(f"No answer provided for first exercise {exercise_id}")
            return None

        logger.info(f"Evaluating first exercise {exercise_id}")

        # Normalize type naming across sources (e.g., 'gap-fill' vs 'gap_fill')
        raw_type = str(first_exercise.get("type", "unknown"))
        normalized_type = raw_type.replace("_", "-")

        # Use consistent correct answer key (API may send 'correctAnswer')
        correct_answer = first_exercise.get("correctAnswer", first_exercise.get("correct_answer", ""))

        # Determine correctness for immediate feedback
        if normalized_type == "gap-fill":
            # For gap-fill, use contextual correctness check
            is_correct = check_gap_fill_correctness(first_exercise, user_answer, correct_answer)
        else:
            # Fallback: simple normalized string comparison
            try:
                from shared.text_utils import _normalize_umlauts, _strip_final_punct  # lazy import
                ua = _normalize_umlauts(_strip_final_punct(str(user_answer)).strip().lower())
                ca = _normalize_umlauts(_strip_final_punct(str(correct_answer)).strip().lower())
            except Exception:
                ua = str(user_answer).strip().lower()
                ca = str(correct_answer).strip().lower()
            is_correct = ua == ca if ca else False

        # Return a result aligned with the enhanced results format
        result = {
            "id": exercise_id,                 # frontend expects 'id'
            "exercise_id": exercise_id,        # backward compatibility
            "type": normalized_type,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            # Do not hardcode textual feedback; leave it for AI-enhanced results
            "feedback": "",
            "alternatives": [],
            "explanation": "",
        }

        logger.info(
            f"First exercise evaluation complete: {'correct' if is_correct else 'incorrect'} (type={normalized_type})"
        )
        return result

    except Exception as e:
        logger.error(f"Error evaluating first exercise: {e}")
        raise DatabaseError(f"Error evaluating first exercise: {str(e)}")


def create_immediate_results(exercises: ExerciseList, first_result: Optional[AnalyticsData]) -> ExerciseList:
    """
    Create immediate results list with first exercise result and placeholders.

    Args:
        exercises: List of exercise dictionaries
        first_result: Result of the first exercise evaluation

    Returns:
        List of exercise results
    """
    try:
        results = []

        for i, exercise in enumerate(exercises):
            exercise_id = str(exercise.get("id", i))

            if i == 0 and first_result:
                # Ensure the first result includes a stable 'id' field
                normalized_first = dict(first_result)
                if "id" not in normalized_first:
                    normalized_first["id"] = exercise_id
                if "exercise_id" not in normalized_first:
                    normalized_first["exercise_id"] = exercise_id
                # Normalize type naming
                if "type" in normalized_first and isinstance(normalized_first["type"], str):
                    normalized_first["type"] = normalized_first["type"].replace("_", "-")
                results.append(normalized_first)
            else:
                # Create placeholder for other exercises (consistent shape with enhanced results)
                placeholder_correct = exercise.get("correctAnswer", exercise.get("correct_answer", ""))
                results.append({
                    "id": exercise_id,
                    "exercise_id": exercise_id,
                    "type": str(exercise.get("type", "unknown")).replace("_", "-"),
                    "status": "pending",
                    "is_correct": None,
                    "correct_answer": placeholder_correct,
                    "user_answer": "",
                    "alternatives": [],
                    "explanation": "",
                    "message": "Evaluation in progress...",
                })

        logger.info(f"Created immediate results for {len(exercises)} exercises")
        return results

    except Exception as e:
        logger.error(f"Error creating immediate results: {e}")
        raise DatabaseError(f"Error creating immediate results: {str(e)}")


def evaluate_remaining_exercises_async(username: str, block_id: str, exercises: ExerciseList,
                                     answers: ExerciseAnswers, first_result: Optional[AnalyticsData],
                                     exercise_block: Optional[BlockResult] = None) -> None:
    """
    Start asynchronous evaluation of remaining exercises.

    Args:
        username: The username
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        first_result: Result of the first exercise evaluation
        exercise_block: Optional exercise block data
    """
    try:
        logger.info(f"Starting async evaluation for block {block_id}")

        # Create initial results list
        initial_results = create_immediate_results(exercises, first_result)

        # Store initial results in Redis
        result_key = f"exercise_result:{username}:{block_id}"
        redis_client.setex_json(result_key, 300, initial_results)  # type: ignore[arg-type]  # 5 minutes TTL

        # Start background evaluation
        _evaluate_all_exercises(username, block_id, exercises, answers, initial_results, exercise_block)

    except Exception as e:
        logger.error(f"Error starting async evaluation for block {block_id}: {e}")
        raise DatabaseError(f"Error starting async evaluation for block {block_id}: {str(e)}")


def _evaluate_all_exercises(username: str, block_id: str, exercises: ExerciseList,
                           answers: ExerciseAnswers, initial_results: ExerciseList,
                           exercise_block: Optional[BlockResult]) -> None:
    """
    Evaluate all exercises and update results.

    Args:
        username: The username
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        initial_results: Initial results list
        exercise_block: Optional exercise block data
    """
    try:
        logger.info(f"Evaluating all exercises for block {block_id}")

        # Use AI to evaluate all exercises
        logger.info(f"Calling evaluate_exercises with {len(exercises)} exercises and {len(answers)} answers")
        evaluation = evaluate_exercises(exercises, answers)
        logger.info(f"Evaluation result: {evaluation}")

        # Process the evaluation results
        _process_evaluation_results(username, block_id, exercises, answers, evaluation, exercise_block)

        # Process AI answers to update topic memory and vocabulary
        try:
            logger.info(f"Processing AI answers for topic memory and vocabulary updates")
            from features.ai.evaluation.exercise_processing import process_ai_answers

            # Create proper exercise_block structure for process_ai_answers
            exercise_block_for_processing = {
                "exercises": exercises,
                "topic": exercise_block.get("topic", "general") if exercise_block else "general"
            }

            logger.info(f"Calling process_ai_answers with exercise_block: {exercise_block_for_processing}")
            result = process_ai_answers(username, block_id, answers, exercise_block_for_processing)
            logger.info(f"Successfully processed AI answers for topic memory and vocabulary. Result: {result}")
        except ImportError as e:
            logger.error(f"Import error in topic memory processing: {e}")
            # Don't fail the whole process if there's an import error
        except Exception as e:
            logger.error(f"Error processing AI answers for topic memory: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Don't fail the whole process if topic memory processing fails

    except Exception as e:
        logger.error(f"Error evaluating exercises for block {block_id}: {e}")
        raise DatabaseError(f"Error evaluating exercises for block {block_id}: {str(e)}")


def _process_evaluation_results(username: str, block_id: str, exercises: ExerciseList,
                               answers: ExerciseAnswers, evaluation: Any,
                               exercise_block: Optional[BlockResult]) -> None:
    """
    Process evaluation results and update storage.

    Args:
        username: The username
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        evaluation: Evaluation results from AI
        exercise_block: Optional exercise block data
    """
    try:
        logger.info(f"Processing evaluation results for block {block_id}")

        # Update results in Redis
        result_key = f"exercise_result:{username}:{block_id}"
        redis_client.setex_json(result_key, 3600, evaluation)  # type: ignore[arg-type]  # 1 hour TTL

        # Enrich results with AI-generated alternatives and explanations (non-blocking best-effort)
        try:
            eval_results_only = evaluation[0] if isinstance(evaluation, tuple) else evaluation
            if isinstance(eval_results_only, dict):
                # Map exercises by id
                exercise_map = {str(e.get("id")): e for e in exercises}
                for ex_id, res in eval_results_only.items():
                    ex = exercise_map.get(str(ex_id), {})
                    question = ex.get("question", "")
                    correct = ex.get("correctAnswer", ex.get("correct_answer", res.get("correct_answer", "")))

                    # Alternatives
                    try:
                        if correct:
                            alt_resp = send_prompt(
                                "You are a helpful German teacher.",
                                alternative_answers_prompt(correct),
                                temperature=0.3,
                            )
                            if alt_resp.status_code == 200:
                                content = alt_resp.json()["choices"][0]["message"]["content"].strip()
                                alts = extract_json(content)
                                if isinstance(alts, list):
                                    res["alternatives"] = alts[:3]
                    except Exception:
                        pass

                    # Explanation
                    try:
                        if question and correct:
                            expl_resp = send_prompt(
                                "You are a helpful German linguist.",
                                explanation_prompt(question, correct),
                                temperature=0.3,
                            )
                            if expl_resp.status_code == 200:
                                expl = expl_resp.json()["choices"][0]["message"]["content"].strip()
                                res["explanation"] = expl
                    except Exception:
                        pass

                # Write enriched version back to Redis so the frontend can pick it up on next poll
                try:
                    enriched = (eval_results_only, evaluation[1]) if isinstance(evaluation, tuple) else eval_results_only
                    redis_client.setex_json(result_key, 3600, enriched)  # type: ignore[arg-type]
                except Exception:
                    pass
        except Exception:
            # Safe guard: enrichment is best-effort
            pass

        # Store results in ai_exercise_results table
        try:
            # evaluation is a tuple (evaluation_results, summary), extract the first element
            evaluation_results = evaluation[0] if isinstance(evaluation, tuple) else evaluation

            result_data = {
                "block_id": block_id,
                "username": username,
                "results": json.dumps(evaluation_results),
                "summary": json.dumps({"total": len(exercises), "correct": sum(1 for r in evaluation_results.values() if r.get("correct", False)), "incorrect": sum(1 for r in evaluation_results.values() if not r.get("correct", True)), "accuracy": (sum(1 for r in evaluation_results.values() if r.get("correct", False)) / len(exercises)) * 100 if exercises else 0}),
                "ai_feedback": json.dumps({"status": "completed", "message": "Evaluation completed successfully"}),
                "created_at": datetime.now().isoformat()
            }

            # Check if result already exists
            existing = select_one("ai_exercise_results", columns="block_id", where="block_id = ? AND username = ?", params=(block_id, username))
            if existing:
                update_row("ai_exercise_results", result_data, "block_id = ? AND username = ?", (block_id, username))
                logger.info(f"Updated existing results for block {block_id}")
            else:
                insert_row("ai_exercise_results", result_data)
                logger.info(f"Stored new results for block {block_id}")
        except Exception as e:
            logger.error(f"Error storing results in database: {e}")
            # Continue without failing the whole process

        # Generate AI feedback
        try:
            print(f"🔄 Starting AI feedback generation for block {block_id}")
            from features.ai.feedback.feedback_generation import generate_ai_feedback_simple

            # Create a proper exercise_block structure for the feedback function
            exercise_block_for_feedback = {
                "exercises": exercises,
                "block_id": block_id,
                "username": username
            }

            feedback_result = generate_ai_feedback_simple(username, answers, exercise_block_for_feedback)

            print(f"📊 Feedback generation result for block {block_id}: {feedback_result}")

            if feedback_result and "error" not in feedback_result:
                # Store feedback in Redis
                feedback_key = f"exercise_feedback:{username}:{block_id}"
                redis_client.setex_json(feedback_key, 3600, feedback_result)  # 1 hour TTL

                print(f"✅ Successfully generated and stored AI feedback for block {block_id}")
            else:
                print(f"⚠️ Failed to generate AI feedback for block {block_id}: {feedback_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Error generating AI feedback for block {block_id}: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")

        logger.info(f"Successfully processed evaluation results for block {block_id}")

    except Exception as e:
        logger.error(f"Error processing evaluation results for block {block_id}: {e}")
        raise DatabaseError(f"Error processing evaluation results for block {block_id}: {str(e)}")
