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
from typing import List, Optional, Tuple

from features.ai.generation.exercise_processing import evaluate_exercises
from shared.text_utils import _normalize_umlauts, _strip_final_punct
from features.ai.generation.feedback_helpers import _adjust_gapfill_results
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from external.redis import redis_client
from shared.exceptions import DatabaseError
from shared.types import ExerciseList, ExerciseAnswers, EvaluationResult, AnalyticsData, BlockResult

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
        exercises = data.get("exercises", [])
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

        # Check if it's a gap-fill exercise
        if first_exercise.get("type") == "gap_fill":
            correct_answer = first_exercise.get("correct_answer", "")
            is_correct = check_gap_fill_correctness(first_exercise, user_answer, correct_answer)

            result = {
                "exercise_id": exercise_id,
                "type": "gap_fill",
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "feedback": "Correct!" if is_correct else f"Incorrect. The correct answer is: {correct_answer}"
            }

            logger.info(f"First exercise evaluation complete: {'correct' if is_correct else 'incorrect'}")
            return result

        # For other exercise types, return basic info
        result = {
            "exercise_id": exercise_id,
            "type": first_exercise.get("type", "unknown"),
            "user_answer": user_answer,
            "status": "submitted"
        }

        logger.info(f"First exercise submitted for AI evaluation")
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
                # Use the actual first result
                results.append(first_result)
            else:
                # Create placeholder for other exercises
                results.append({
                    "exercise_id": exercise_id,
                    "type": exercise.get("type", "unknown"),
                    "status": "pending",
                    "message": "Evaluation in progress..."
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
        redis_client.setex_json(result_key, 300, initial_results)  # 5 minutes TTL

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

    except Exception as e:
        logger.error(f"Error evaluating exercises for block {block_id}: {e}")
        raise DatabaseError(f"Error evaluating exercises for block {block_id}: {str(e)}")


def _process_evaluation_results(username: str, block_id: str, exercises: ExerciseList,
                               answers: ExerciseAnswers, evaluation: AnalyticsData,
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
        redis_client.setex_json(result_key, 3600, evaluation)  # 1 hour TTL

        # Store results in database if exercise block exists
        if exercise_block:
            # Update exercise block with results
            update_row(
                "exercise_blocks",
                {"results": json.dumps(evaluation)},
                "WHERE block_id = ?",
                (block_id,)
            )

                # Generate AI feedback
        try:
            logger.info(f"Starting AI feedback generation for block {block_id}")
            from features.ai.feedback.feedback_generation import generate_ai_feedback_simple
            feedback_result = generate_ai_feedback_simple(username, answers, exercise_block)

            logger.info(f"Feedback generation result for block {block_id}: {feedback_result}")

            if feedback_result and "error" not in feedback_result:
                # Store feedback in Redis
                feedback_key = f"exercise_feedback:{username}:{block_id}"
                redis_client.setex_json(feedback_key, 3600, feedback_result)  # 1 hour TTL

                logger.info(f"Successfully generated and stored AI feedback for block {block_id}")
            else:
                logger.warning(f"Failed to generate AI feedback for block {block_id}: {feedback_result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error generating AI feedback for block {block_id}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

        logger.info(f"Successfully processed evaluation results for block {block_id}")

    except Exception as e:
        logger.error(f"Error processing evaluation results for block {block_id}: {e}")
        raise DatabaseError(f"Error processing evaluation results for block {block_id}: {str(e)}")
