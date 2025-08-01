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
from typing import Optional, Dict, Any, List

from flask import current_app  # type: ignore

from core.database.connection import (
    select_one, select_rows, insert_row, update_row, delete_rows,
    fetch_one, fetch_all, fetch_custom, execute_query, get_connection
)
from features.ai.memory.level_manager import check_auto_level_up
from features.ai.evaluation import evaluate_answers_with_ai, process_ai_answers
from features.ai.memory.logger import topic_memory_logger

logger = logging.getLogger(__name__)


def save_exercise_submission_async(
    username: str,
    block_id: str,
    answers: dict,
    exercises: list,
    exercise_block: Optional[Dict[Any, Any]] = None,
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

        except Exception as e:
            logger.error(f"Error processing exercise submission for user {username}: {e}")
            logger.error(traceback.format_exc())

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
        evaluation = evaluate_answers_with_ai(exercises, answers, "strict")

        if not evaluation:
            logger.warning("AI evaluation failed")
            return None, {}

        # Compile score summary
        summary = compile_score_summary(exercises, answers, {})

        logger.info(f"Successfully evaluated exercises")
        return evaluation, summary

    except Exception as e:
        logger.error(f"Error evaluating exercises: {e}")
        return None, {}


def parse_submission_data(data: dict) -> tuple[list, dict, str | None]:
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

    except Exception as e:
        logger.error(f"Error parsing submission data: {e}")
        return [], {}, None


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
            exercise_id = str(i + 1)
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

    except Exception as e:
        logger.error(f"Error compiling score summary: {e}")
        return {
            "total": 0,
            "correct": 0,
            "incorrect": 0,
            "skipped": 0,
            "accuracy": 0,
            "mistakes": []
        }


def log_exercise_event(event_type: str, username: str, details: Optional[Dict[Any, Any]] = None):
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

    except Exception as e:
        logger.error(f"Error fetching vocab and topic data for user {username}: {e}")
        return [], []


def get_ai_exercises():
    """
    Get AI-generated exercises.

    Returns:
        List of AI exercises
    """
    try:
        # Get current user
        username = require_user()

        # Get user's current exercise block
        current_block = fetch_one(
            "ai_exercise_blocks",
            "WHERE username = ? AND status = 'current'",
            (username,)
        )

        if current_block:
            logger.info(f"Retrieved current exercise block for user: {username}")
            return current_block

        # Generate new exercises if no current block
        logger.info(f"No current block found, generating new exercises for user: {username}")

        from .exercise_creation import generate_training_exercises
        new_block = generate_training_exercises(username)

        if new_block:
            # Mark as current
            update_row(
                "ai_exercise_blocks",
                {"status": "current"},
                "id = ?",
                (new_block["id"],)
            )

            logger.info(f"Generated and set new current block for user: {username}")
            return new_block
        else:
            logger.warning(f"Failed to generate new exercises for user: {username}")
            return None

    except Exception as e:
        logger.error(f"Error getting AI exercises: {e}")
        return None


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
