"""
XplorED - Exercise Processing Module

This module provides exercise processing and evaluation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Processing Components:
- Exercise Evaluation: Process and evaluate exercise submissions
- Data Processing: Process submission data and results
- Async Processing: Handle background exercise processing
- Result Compilation: Compile and format exercise results

For detailed architecture information, see: docs/backend_structure.md
"""

import json
import logging
import traceback
from threading import Thread
from datetime import datetime
from typing import Optional, List

from flask import current_app  # type: ignore

from core.database.connection import (
    select_one, select_rows, insert_row, update_row, delete_rows,
    fetch_one, fetch_all, fetch_custom, execute_query, get_connection,
    fetch_topic_memory
)
from features.ai.memory.level_manager import check_auto_level_up
from features.ai.evaluation import evaluate_answers_with_ai, process_ai_answers
from features.ai.memory.logger import topic_memory_logger
from shared.exceptions import DatabaseError, AIEvaluationError, ProcessingError
from api.middleware.auth import require_user
from shared.types import AnalyticsData

logger = logging.getLogger(__name__)


def save_exercise_submission_async(
    username: str,
    block_id: str,
    answers: dict,
    exercises: list,
    exercise_block: Optional[AnalyticsData] = None,
) -> None:
    """
    Save exercise submission asynchronously.

    Args:
        username: The username
        block_id: The exercise block ID
        answers: User's answers
        exercises: List of exercises
        exercise_block: Optional exercise block data
    """
    def run():
        try:
            logger.info(f"Processing exercise submission for user: {username}, block: {block_id}")

            # Process AI answers
            results = process_ai_answers(
                username=username,
                block_id=block_id,
                answers=answers,
                exercise_block=exercise_block
            )

            # Store results
            for result in results:
                result["username"] = username
                result["block_id"] = block_id
                result["submitted_at"] = datetime.now().isoformat()

                insert_row("exercise_results", result)

            # Check for auto level up
            if check_auto_level_up(username):
                logger.info(f"User {username} auto-leveled up!")

            logger.info(f"Successfully processed exercise submission for user: {username}")

        except ProcessingError:
            raise
        except DatabaseError:
            raise
        except AIEvaluationError:
            raise
        except Exception as e:
            logger.error(f"Error processing exercise submission for user {username}: {e}")
            logger.error(traceback.format_exc())
            raise ProcessingError(f"Error processing exercise submission: {str(e)}")

    # Run in background thread
    thread = Thread(target=run, daemon=True)
    thread.start()


def evaluate_exercises(exercises: list, answers: dict) -> tuple[dict | None, dict]:
    """
    Evaluate exercises using AI.

    Args:
        exercises: List of exercises
        answers: User's answers

    Returns:
        Tuple of (evaluation results, score summary)
    """
    try:
        logger.info(f"Evaluating {len(exercises)} exercises")

        # Evaluate with AI
        logger.info(f"Calling evaluate_answers_with_ai with {len(exercises)} exercises")
        evaluation = evaluate_answers_with_ai(exercises, answers, "strict")
        logger.info(f"AI evaluation result: {evaluation}")

        if not evaluation:
            logger.warning("AI evaluation failed")
            return None, {}

        # Compile score summary
        summary = compile_score_summary(exercises, answers, {})
        logger.info(f"Score summary: {summary}")

        logger.info(f"Successfully evaluated exercises")
        return evaluation, summary

    except ProcessingError:
        raise
    except Exception as e:
        logger.error(f"Error evaluating exercises: {e}")
        raise AIEvaluationError(f"Error evaluating exercises: {str(e)}")


def parse_ai_submission_data(data: dict) -> tuple[list, dict, str | None]:
    """
    Parse exercise submission data.

    Args:
        data: Submission data

    Returns:
        Tuple of (exercises, answers, block_id)
    """
    try:
        exercises = data.get("exercises", [])
        answers = data.get("answers", {})
        block_id = data.get("block_id")

        logger.debug(f"Parsed submission data: {len(exercises)} exercises, {len(answers)} answers")
        return exercises, answers, block_id

    except ProcessingError:
        raise
    except Exception as e:
        logger.error(f"Error parsing submission data: {e}")
        raise DatabaseError(f"Error parsing submission data: {str(e)}")


def compile_score_summary(exercises: list, answers: dict, id_map: dict) -> dict:
    """
    Compile a score summary from exercise results.

    Args:
        exercises: List of exercises
        answers: User's answers
        id_map: ID mapping

    Returns:
        Score summary dictionary
    """
    try:
        total_exercises = len(exercises)
        correct_answers = 0
        incorrect_answers = 0
        skipped_answers = 0
        mistakes = []

        for i, exercise in enumerate(exercises):
            exercise_id = str(exercise.get("id", i + 1))  # Use actual exercise ID or fallback to index
            user_answer = answers.get(exercise_id, "").strip()
            correct_answer = exercise.get("correctAnswer", "")

            if not user_answer:
                skipped_answers += 1
                continue

            # Check if answer is correct
            is_correct = user_answer.lower() == correct_answer.lower()

            if is_correct:
                correct_answers += 1
            else:
                incorrect_answers += 1
                mistakes.append({
                    "question": exercise.get("question", ""),
                    "your_answer": user_answer,
                    "correct_answer": correct_answer
                })

        accuracy = (correct_answers / total_exercises * 100) if total_exercises > 0 else 0

        summary = {
            "total": total_exercises,
            "correct": correct_answers,
            "incorrect": incorrect_answers,
            "skipped": skipped_answers,
            "accuracy": round(accuracy, 2),
            "mistakes": mistakes[:3]  # Limit to first 3 mistakes
        }

        logger.debug(f"Compiled score summary: {accuracy:.2f}% accuracy")
        return summary

    except ProcessingError:
        raise
    except Exception as e:
        logger.error(f"Error compiling score summary: {e}")
        raise DatabaseError(f"Error compiling score summary: {str(e)}")


def log_exercise_event(event_type: str, username: str, details: Optional[AnalyticsData] = None):
    """
    Log exercise-related events.

    Args:
        event_type: Type of event
        username: The username
        details: Optional event details
    """
    try:
        event_data = {
            "event_type": event_type,
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }

        insert_row("exercise_events", event_data)
        logger.debug(f"Logged exercise event: {event_type} for user {username}")

    except Exception as e:
        logger.error(f"Error logging exercise event: {e}")
        raise DatabaseError(f"Error logging exercise event: {str(e)}")


def log_ai_user_data(username: str, context: str):
    """
    Log AI user data.

    Args:
        username: The username
        context: Context for logging
    """
    try:
        data = {
            "username": username,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

        insert_row("ai_user_data", data)
        logger.debug(f"Logged AI user data for user {username}: {context}")

    except Exception as e:
        logger.error(f"Error logging AI user data: {e}")
        raise DatabaseError(f"Error logging AI user data: {str(e)}")


def log_vocab_log(username: str, context: str):
    """
    Log vocabulary learning events.

    Args:
        username: The username
        context: Context for logging
    """
    try:
        data = {
            "username": username,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

        insert_row("vocab_log", data)
        logger.debug(f"Logged vocabulary event for user {username}: {context}")

    except Exception as e:
        logger.error(f"Error logging vocabulary event: {e}")
        raise DatabaseError(f"Error logging vocab log: {str(e)}")


def fetch_vocab_and_topic_data(username: str) -> tuple[list, list]:
    """
    Fetch vocabulary and topic memory data for a user.

    Args:
        username: The username

    Returns:
        Tuple of (vocabulary data, topic memory data)
    """
    try:
        # Fetch vocabulary data
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

        # Fetch topic memory data
        topic_rows = fetch_topic_memory(username)
        topic_memory = [dict(row) for row in topic_rows] if isinstance(topic_rows, list) else []

        logger.debug(f"Fetched data for user {username}: {len(vocab_data)} vocab items, {len(topic_memory)} topic items")
        return vocab_data, topic_memory

    except ProcessingError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error fetching vocab and topic data for user {username}: {e}")
        raise DatabaseError(f"Error fetching vocab and topic data: {str(e)}")


def get_ai_exercises(payload=None):
    """
    Get AI-generated exercises.

    Args:
        payload (dict, optional): Additional parameters for exercise generation
            - answers (dict, optional): Previous answers to consider for next block
            - force_new (bool, optional): Force generation of new block

    Returns:
        List of AI exercises
    """
    try:
        # Get current user
        username = require_user()

        # Check if we should force generation of new block
        force_new = payload and payload.get('force_new', False)
        previous_answers = payload.get('answers', {}) if payload else {}

        # If answers are provided, we want a new block (user is continuing)
        if previous_answers:
            force_new = True

        if not force_new:
            # Get user's current exercise block from ai_user_data table
            current_block = fetch_one(
                "ai_user_data",
                "WHERE username = ?",
                (username,)
            )

            if current_block and current_block.get("exercises"):
                try:
                    import json
                    exercises_data = json.loads(current_block["exercises"])
                    if exercises_data and exercises_data.get("exercises"):
                        logger.info(f"Retrieved current exercise block for user: {username}")
                        return exercises_data
                except (json.JSONDecodeError, TypeError):
                    logger.error(f"Error parsing exercises JSON for user {username}")

        # Generate new exercises if no current block exists or force_new is True
        logger.info(f"Generating new exercises for user: {username}")

        # Generate new exercises using the existing function
        from .exercise_creation import _generate_blocks_for_existing_user, _generate_blocks_for_new_user

        # Check if user is new or existing
        user_row = fetch_one("users", "WHERE username = ?", (username,))

        if user_row:
            # Existing user
            new_block = _generate_blocks_for_existing_user(username)
        else:
            # New user
            new_block = _generate_blocks_for_new_user(username)

        if new_block:
            logger.info(f"Generated new exercise block for user: {username}")
            return new_block
        else:
            logger.warning(f"Failed to generate new exercises for user: {username}")
            return None

    except ProcessingError:
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting AI exercises: {e}")
        raise DatabaseError(f"Error getting AI exercises: {str(e)}")


def print_db_exercise_blocks(username, parent_str, parent_function=None):
    """
    Print exercise blocks for debugging.

    Args:
        username: The username
        parent_str: Parent string for logging
        parent_function: Parent function name
    """
    try:
        # Get current and next blocks
        current_block = fetch_one(
            "ai_exercise_blocks",
            "WHERE username = ? AND status = 'current'",
            (username,)
        )

        next_block = fetch_one(
            "ai_exercise_blocks",
            "WHERE username = ? AND status = 'next'",
            (username,)
        )

        logger.debug(f"Exercise blocks for user {username}:")
        if current_block:
            logger.debug(f"  Current: {current_block.get('id')} - {current_block.get('title', 'No title')}")
        if next_block:
            logger.debug(f"  Next: {next_block.get('id')} - {next_block.get('title', 'No title')}")

    except Exception as e:
        logger.error(f"Error printing exercise blocks: {e}")
        raise DatabaseError(f"Error printing DB exercise blocks: {str(e)}")
