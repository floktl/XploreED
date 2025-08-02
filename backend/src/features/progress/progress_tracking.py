"""
XplorED - Progress Tracking Module

This module provides core progress tracking functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Progress Tracking Components:
- Lesson Progress: Track lesson and block completion
- Exercise Progress: Track exercise performance and scores
- Vocabulary Progress: Track vocabulary learning progress
- Game Progress: Track game performance and levels

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import Dict, Optional, Any, List, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query

logger = logging.getLogger(__name__)


def track_lesson_progress(username: str, lesson_id: int, block_id: str, completed: bool) -> bool:
    """
    Track progress for a specific lesson block.

    Args:
        username: The username to track progress for
        lesson_id: The lesson ID
        block_id: The block ID to track
        completed: Whether the block is completed

    Returns:
        True if progress was tracked successfully, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        if not block_id:
            raise ValueError("Block ID is required")

        logger.info(f"Tracking lesson progress for user {username}, lesson {lesson_id}, block {block_id}")

        # Use UPSERT to handle both insert and update cases
        success = execute_query("""
            INSERT INTO lesson_progress (user_id, lesson_id, block_id, completed, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, lesson_id, block_id)
            DO UPDATE SET completed = excluded.completed, updated_at = excluded.updated_at
        """, (username, lesson_id, block_id, int(completed), datetime.datetime.utcnow()))

        if success:
            logger.info(f"Successfully tracked lesson progress for user {username}, lesson {lesson_id}, block {block_id}")
        else:
            logger.error(f"Failed to track lesson progress for user {username}, lesson {lesson_id}, block {block_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error tracking lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error tracking lesson progress for user {username}, lesson {lesson_id}, block {block_id}: {e}")
        return False


def track_exercise_progress(username: str, block_id: str, score: float, total_questions: int) -> bool:
    """
    Track progress for exercise completion.

    Args:
        username: The username to track progress for
        block_id: The exercise block ID
        score: The score achieved
        total_questions: Total number of questions

    Returns:
        True if progress was tracked successfully, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not block_id:
            raise ValueError("Block ID is required")

        if score < 0 or total_questions <= 0:
            raise ValueError("Valid score and total questions are required")

        logger.info(f"Tracking exercise progress for user {username}, block {block_id}")

        # Calculate completion percentage
        completion_percentage = (score / total_questions) * 100 if total_questions > 0 else 0

        # Track exercise progress
        progress_data = {
            "username": username,
            "block_id": block_id,
            "score": score,
            "total_questions": total_questions,
            "completion_percentage": completion_percentage,
            "completed_at": datetime.datetime.utcnow().isoformat(),
            "activity_type": "exercise"
        }

        success = insert_row("activity_progress", progress_data)

        if success:
            logger.info(f"Successfully tracked exercise progress for user {username}, block {block_id}")
        else:
            logger.error(f"Failed to track exercise progress for user {username}, block {block_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error tracking exercise progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error tracking exercise progress for user {username}, block {block_id}: {e}")
        return False


def track_vocabulary_progress(username: str, word: str, correct: bool, repetitions: int) -> bool:
    """
    Track progress for vocabulary learning.

    Args:
        username: The username to track progress for
        word: The vocabulary word
        correct: Whether the answer was correct
        repetitions: Number of repetitions

    Returns:
        True if progress was tracked successfully, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not word:
            raise ValueError("Word is required")

        if repetitions < 0:
            raise ValueError("Valid repetitions count is required")

        logger.info(f"Tracking vocabulary progress for user {username}, word {word}")

        # Track vocabulary progress
        progress_data = {
            "username": username,
            "word": word,
            "correct": int(correct),
            "repetitions": repetitions,
            "reviewed_at": datetime.datetime.utcnow().isoformat(),
            "activity_type": "vocabulary"
        }

        success = insert_row("vocabulary_progress", progress_data)

        if success:
            logger.info(f"Successfully tracked vocabulary progress for user {username}, word {word}")
        else:
            logger.error(f"Failed to track vocabulary progress for user {username}, word {word}")

        return success

    except ValueError as e:
        logger.error(f"Validation error tracking vocabulary progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error tracking vocabulary progress for user {username}, word {word}: {e}")
        return False


def track_game_progress(username: str, game_type: str, score: float, level: int) -> bool:
    """
    Track progress for game completion.

    Args:
        username: The username to track progress for
        game_type: The type of game
        score: The score achieved
        level: The game level

    Returns:
        True if progress was tracked successfully, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not game_type:
            raise ValueError("Game type is required")

        if score < 0 or level < 0:
            raise ValueError("Valid score and level are required")

        logger.info(f"Tracking game progress for user {username}, game {game_type}, level {level}")

        # Track game progress
        progress_data = {
            "username": username,
            "game_type": game_type,
            "score": score,
            "level": level,
            "completed_at": datetime.datetime.utcnow().isoformat(),
            "activity_type": "game"
        }

        success = insert_row("game_progress", progress_data)

        if success:
            logger.info(f"Successfully tracked game progress for user {username}, game {game_type}, level {level}")
        else:
            logger.error(f"Failed to track game progress for user {username}, game {game_type}, level {level}")

        return success

    except ValueError as e:
        logger.error(f"Validation error tracking game progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error tracking game progress for user {username}, game {game_type}, level {level}: {e}")
        return False


def reset_user_progress(username: str, activity_type: Optional[str] = None) -> bool:
    """
    Reset progress for a user, optionally for a specific activity type.

    Args:
        username: The username to reset progress for
        activity_type: Optional activity type to reset (lesson, exercise, vocabulary, game)

    Returns:
        True if progress was reset successfully, False otherwise

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Resetting progress for user {username}" + (f", activity type {activity_type}" if activity_type else ""))

        if activity_type:
            # Reset specific activity type
            success = delete_rows(
                f"{activity_type}_progress",
                "WHERE username = ?",
                (username,)
            )
        else:
            # Reset all progress types
            tables = ["lesson_progress", "activity_progress", "vocabulary_progress", "game_progress"]
            success = True

            for table in tables:
                table_success = delete_rows(table, "WHERE username = ?", (username,))
                if not table_success:
                    success = False
                    logger.error(f"Failed to reset progress for table {table}")

        if success:
            logger.info(f"Successfully reset progress for user {username}")
        else:
            logger.error(f"Failed to reset progress for user {username}")

        return success

    except ValueError as e:
        logger.error(f"Validation error resetting user progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error resetting progress for user {username}: {e}")
        return False
