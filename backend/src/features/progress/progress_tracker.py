"""
Progress Tracker

This module contains core progress tracking functions for monitoring user
learning progress across different activities.

Author: XplorED Team
Date: 2025
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


def get_lesson_progress(username: str, lesson_id: int) -> Dict[str, bool]:
    """
    Get completion status for each block in a lesson.

    Args:
        username: The username to get progress for
        lesson_id: The lesson ID to get progress for

    Returns:
        Dictionary mapping block IDs to completion status

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Getting lesson progress for user {username}, lesson {lesson_id}")

        rows = select_rows(
            "lesson_progress",
            columns=["block_id", "completed"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        progress = {row["block_id"]: bool(row["completed"]) for row in rows}

        logger.info(f"Retrieved progress for {len(progress)} blocks for user {username}, lesson {lesson_id}")
        return progress

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson progress for user {username}, lesson {lesson_id}: {e}")
        raise


def track_exercise_progress(username: str, block_id: str, score: float, total_questions: int) -> bool:
    """
    Track progress for an exercise block.

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
            raise ValueError("Invalid score or total questions")

        logger.info(f"Tracking exercise progress for user {username}, block {block_id}")

        # Calculate percentage
        percentage = (score / total_questions) * 100

        # Create progress data
        progress_data = {
            "username": username,
            "activity_type": "exercise",
            "activity_id": block_id,
            "score": score,
            "total_questions": total_questions,
            "percentage": percentage,
            "completed_at": datetime.datetime.now().isoformat()
        }

        # Insert progress record
        success = insert_row("user_progress", progress_data)

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

        logger.info(f"Tracking vocabulary progress for user {username}, word {word}")

        # Create progress data
        progress_data = {
            "username": username,
            "activity_type": "vocabulary",
            "activity_id": word,
            "correct": int(correct),
            "repetitions": repetitions,
            "completed_at": datetime.datetime.now().isoformat()
        }

        # Insert progress record
        success = insert_row("user_progress", progress_data)

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
    Track progress for game activities.

    Args:
        username: The username to track progress for
        game_type: Type of game (sentence_order, etc.)
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

        if score < 0:
            raise ValueError("Invalid score")

        logger.info(f"Tracking game progress for user {username}, game {game_type}, level {level}")

        # Create progress data
        progress_data = {
            "username": username,
            "activity_type": "game",
            "activity_id": game_type,
            "score": score,
            "level": level,
            "completed_at": datetime.datetime.now().isoformat()
        }

        # Insert progress record
        success = insert_row("user_progress", progress_data)

        if success:
            logger.info(f"Successfully tracked game progress for user {username}, game {game_type}")
        else:
            logger.error(f"Failed to track game progress for user {username}, game {game_type}")

        return success

    except ValueError as e:
        logger.error(f"Validation error tracking game progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error tracking game progress for user {username}, game {game_type}: {e}")
        return False


def get_user_progress_summary(username: str, days: int = 30) -> Dict[str, Any]:
    """
    Get a comprehensive progress summary for a user.

    Args:
        username: The username to get summary for
        days: Number of days to look back

    Returns:
        Dictionary containing progress summary

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if days <= 0:
            days = 30

        logger.info(f"Getting progress summary for user {username} over {days} days")

        # Get lesson progress
        lesson_progress = fetch_custom("""
            SELECT
                lesson_id,
                COUNT(*) as total_blocks,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_blocks
            FROM lesson_progress
            WHERE user_id = ?
                AND updated_at >= date('now', '-{} days')
            GROUP BY lesson_id
        """.format(days), (username,))

        # Get exercise progress
        exercise_progress = fetch_custom("""
            SELECT
                activity_id,
                AVG(percentage) as avg_score,
                COUNT(*) as attempts
            FROM user_progress
            WHERE username = ?
                AND activity_type = 'exercise'
                AND completed_at >= date('now', '-{} days')
            GROUP BY activity_id
        """.format(days), (username,))

        # Get vocabulary progress
        vocabulary_progress = fetch_custom("""
            SELECT
                COUNT(*) as total_words,
                AVG(correct) as accuracy_rate,
                SUM(repetitions) as total_repetitions
            FROM user_progress
            WHERE username = ?
                AND activity_type = 'vocabulary'
                AND completed_at >= date('now', '-{} days')
        """.format(days), (username,))

        # Get game progress
        game_progress = fetch_custom("""
            SELECT
                activity_id,
                MAX(level) as highest_level,
                AVG(score) as avg_score
            FROM user_progress
            WHERE username = ?
                AND activity_type = 'game'
                AND completed_at >= date('now', '-{} days')
            GROUP BY activity_id
        """.format(days), (username,))

        # Calculate overall statistics
        total_activities = fetch_custom("""
            SELECT COUNT(*) as count
            FROM user_progress
            WHERE username = ?
                AND completed_at >= date('now', '-{} days')
        """.format(days), (username,))

        summary = {
            "period_days": days,
            "total_activities": total_activities[0]["count"] if total_activities else 0,
            "lesson_progress": [
                {
                    "lesson_id": row["lesson_id"],
                    "total_blocks": row["total_blocks"],
                    "completed_blocks": row["completed_blocks"],
                    "completion_rate": round((row["completed_blocks"] / row["total_blocks"] * 100) if row["total_blocks"] > 0 else 0, 2)
                }
                for row in lesson_progress
            ],
            "exercise_progress": [
                {
                    "exercise_id": row["activity_id"],
                    "avg_score": round(row["avg_score"], 2),
                    "attempts": row["attempts"]
                }
                for row in exercise_progress
            ],
            "vocabulary_progress": {
                "total_words": vocabulary_progress[0]["total_words"] if vocabulary_progress else 0,
                "accuracy_rate": round(vocabulary_progress[0]["accuracy_rate"] * 100, 2) if vocabulary_progress else 0,
                "total_repetitions": vocabulary_progress[0]["total_repetitions"] if vocabulary_progress else 0
            },
            "game_progress": [
                {
                    "game_type": row["activity_id"],
                    "highest_level": row["highest_level"],
                    "avg_score": round(row["avg_score"], 2)
                }
                for row in game_progress
            ]
        }

        logger.info(f"Retrieved progress summary for user {username}: {summary['total_activities']} activities")
        return summary

    except ValueError as e:
        logger.error(f"Validation error getting progress summary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting progress summary for user {username}: {e}")
        return {"period_days": days, "total_activities": 0, "lesson_progress": [], "exercise_progress": [], "vocabulary_progress": {"total_words": 0, "accuracy_rate": 0, "total_repetitions": 0}, "game_progress": []}


def reset_user_progress(username: str, activity_type: Optional[str] = None) -> bool:
    """
    Reset progress for a user.

    Args:
        username: The username to reset progress for
        activity_type: Specific activity type to reset (optional, resets all if None)

    Returns:
        True if reset was successful, False otherwise

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Resetting progress for user {username}" + (f", activity type {activity_type}" if activity_type else ""))

        if activity_type:
            # Reset specific activity type
            success = delete_rows("user_progress", "WHERE username = ? AND activity_type = ?", (username, activity_type))
        else:
            # Reset all progress
            success = delete_rows("user_progress", "WHERE username = ?", (username,))
            # Also reset lesson progress
            lesson_success = delete_rows("lesson_progress", "WHERE user_id = ?", (username,))
            success = success and lesson_success

        if success:
            logger.info(f"Successfully reset progress for user {username}")
        else:
            logger.error(f"Failed to reset progress for user {username}")

        return success

    except ValueError as e:
        logger.error(f"Validation error resetting progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error resetting progress for user {username}: {e}")
        return False


def get_progress_trends(username: str, days: int = 7) -> Dict[str, Any]:
    """
    Get progress trends over time.

    Args:
        username: The username to get trends for
        days: Number of days to analyze

    Returns:
        Dictionary containing progress trends

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if days <= 0:
            days = 7

        logger.info(f"Getting progress trends for user {username} over {days} days")

        # Get daily activity counts
        daily_activity = fetch_custom("""
            SELECT
                DATE(completed_at) as date,
                activity_type,
                COUNT(*) as count
            FROM user_progress
            WHERE username = ?
                AND completed_at >= date('now', '-{} days')
            GROUP BY DATE(completed_at), activity_type
            ORDER BY date
        """.format(days), (username,))

        # Get daily scores for exercises
        daily_scores = fetch_custom("""
            SELECT
                DATE(completed_at) as date,
                AVG(percentage) as avg_score
            FROM user_progress
            WHERE username = ?
                AND activity_type = 'exercise'
                AND completed_at >= date('now', '-{} days')
            GROUP BY DATE(completed_at)
            ORDER BY date
        """.format(days), (username,))

        # Get vocabulary accuracy trends
        vocab_accuracy = fetch_custom("""
            SELECT
                DATE(completed_at) as date,
                AVG(correct) as accuracy_rate
            FROM user_progress
            WHERE username = ?
                AND activity_type = 'vocabulary'
                AND completed_at >= date('now', '-{} days')
            GROUP BY DATE(completed_at)
            ORDER BY date
        """.format(days), (username,))

        trends = {
            "period_days": days,
            "daily_activity": {},
            "daily_scores": {row["date"]: round(row["avg_score"], 2) for row in daily_scores},
            "vocabulary_accuracy": {row["date"]: round(row["accuracy_rate"] * 100, 2) for row in vocab_accuracy}
        }

        # Organize daily activity by date and type
        for row in daily_activity:
            date = row["date"]
            activity_type = row["activity_type"]
            count = row["count"]

            if date not in trends["daily_activity"]:
                trends["daily_activity"][date] = {}

            trends["daily_activity"][date][activity_type] = count

        logger.info(f"Retrieved progress trends for user {username}")
        return trends

    except ValueError as e:
        logger.error(f"Validation error getting progress trends: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting progress trends for user {username}: {e}")
        return {"period_days": days, "daily_activity": {}, "daily_scores": {}, "vocabulary_accuracy": {}}


# === Lesson Progress Functions (Moved from lessons module) ===

def get_user_lesson_progress(username: str, lesson_id: int) -> Dict[str, bool]:
    """
    Get completion status for each block in a lesson.

    Args:
        username: The username to get progress for
        lesson_id: The lesson ID to get progress for

    Returns:
        Dictionary mapping block IDs to completion status

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Getting lesson progress for user {username}, lesson {lesson_id}")

        rows = select_rows(
            "lesson_progress",
            columns=["block_id", "completed"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        progress = {row["block_id"]: bool(row["completed"]) for row in rows}

        logger.info(f"Retrieved progress for {len(progress)} blocks for user {username}, lesson {lesson_id}")
        return progress

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson progress for user {username}, lesson {lesson_id}: {e}")
        raise


def update_block_progress(username: str, lesson_id: int, block_id: str, completed: bool) -> bool:
    """
    Mark a single lesson block as completed or not.

    Args:
        username: The username to update progress for
        lesson_id: The lesson ID
        block_id: The block ID to update
        completed: Whether the block is completed

    Returns:
        True if progress was updated successfully, False otherwise

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

        logger.info(f"Updating block progress for user {username}, lesson {lesson_id}, block {block_id}")

        # Use UPSERT to handle both insert and update cases
        success = execute_query("""
            INSERT INTO lesson_progress (user_id, lesson_id, block_id, completed, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, lesson_id, block_id)
            DO UPDATE SET completed = excluded.completed, updated_at = excluded.updated_at
        """, (username, lesson_id, block_id, int(completed), datetime.datetime.utcnow()))

        if success:
            logger.info(f"Successfully updated block progress for user {username}, lesson {lesson_id}, block {block_id}")
        else:
            logger.error(f"Failed to update block progress for user {username}, lesson {lesson_id}, block {block_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error updating block progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating block progress for user {username}, lesson {lesson_id}, block {block_id}: {e}")
        raise


def mark_lesson_complete(username: str, lesson_id: int) -> Tuple[bool, Optional[str]]:
    """
    Confirm that a lesson is fully completed.

    Args:
        username: The username to mark lesson complete for
        lesson_id: The lesson ID to mark complete

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Marking lesson complete for user {username}, lesson {lesson_id}")

        # Get total blocks for the lesson
        num_blocks_row = select_one(
            "lesson_content",
            columns="num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,),
        )
        total_blocks = num_blocks_row.get("num_blocks") if num_blocks_row else 0

        # Get completed blocks count
        completed_blocks_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="user_id = ? AND lesson_id = ? AND completed = 1",
            params=(username, lesson_id),
        )
        completed_blocks = completed_blocks_row.get("count") if completed_blocks_row else 0

        # Verify all blocks are completed
        if completed_blocks < total_blocks and total_blocks > 0:
            logger.warning(f"Lesson {lesson_id} not fully completed for user {username}")
            return False, "Lesson not fully completed"

        # Mark all blocks as completed
        success = update_row(
            "lesson_progress",
            {"completed": 1},
            "user_id = ? AND lesson_id = ?",
            (username, lesson_id),
        )

        if success:
            logger.info(f"Successfully marked lesson {lesson_id} complete for user {username}")
            return True, None
        else:
            logger.error(f"Failed to mark lesson {lesson_id} complete for user {username}")
            return False, "Failed to update lesson progress"

    except ValueError as e:
        logger.error(f"Validation error marking lesson complete: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error marking lesson complete for user {username}, lesson {lesson_id}: {e}")
        return False, "Database error"


def check_lesson_completion_status(username: str, lesson_id: int) -> Dict[str, Any]:
    """
    Check if a lesson is marked as completed for the user.

    Args:
        username: The username to check completion for
        lesson_id: The lesson ID to check

    Returns:
        Dictionary containing completion status and details

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Checking lesson completion status for user {username}, lesson {lesson_id}")

        # Get total blocks for the lesson
        total_blocks_row = select_one(
            "lesson_blocks",
            columns="COUNT(*) as count",
            where="lesson_id = ?",
            params=(lesson_id,),
        )
        total_blocks = total_blocks_row.get("count") if total_blocks_row else 0

        # Get completed blocks count
        completed_blocks_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="user_id = ? AND lesson_id = ? AND completed = 1",
            params=(username, lesson_id),
        )
        completed_blocks = completed_blocks_row.get("count") if completed_blocks_row else 0

        # Determine completion status
        completed = total_blocks > 0 and completed_blocks == total_blocks
        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks > 0 else 0

        status = {
            "completed": completed,
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "percent_complete": percent_complete,
            "lesson_id": lesson_id,
            "username": username
        }

        logger.info(f"Lesson {lesson_id} completion status for user {username}: {completed}")
        return status

    except ValueError as e:
        logger.error(f"Validation error checking lesson completion: {e}")
        raise
    except Exception as e:
        logger.error(f"Error checking lesson completion for user {username}, lesson {lesson_id}: {e}")
        raise


def mark_lesson_as_completed(username: str, lesson_id: int) -> Tuple[bool, Optional[str]]:
    """
    Mark an entire lesson as completed and record results.

    Args:
        username: The username to mark lesson complete for
        lesson_id: The lesson ID to mark complete

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Marking lesson as completed for user {username}, lesson {lesson_id}")

        # Get total blocks for the lesson
        num_blocks_row = select_one(
            "lesson_content",
            columns="num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,),
        )
        total_blocks = num_blocks_row.get("num_blocks") if num_blocks_row else 0

        # If no blocks, mark as completed immediately
        if total_blocks == 0:
            success = insert_row("results", {
                "username": username,
                "level": lesson_id,
                "correct": 1
            })

            if success:
                logger.info(f"Marked lesson {lesson_id} as completed (no blocks) for user {username}")
                return True, None
            else:
                logger.error(f"Failed to mark lesson {lesson_id} as completed for user {username}")
                return False, "Failed to record completion"

        # Check if all blocks are completed
        completed_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="lesson_id = ? AND user_id = ? AND completed = 1",
            params=(lesson_id, username),
        )
        completed = completed_row.get("count") if completed_row else 0

        if completed < total_blocks:
            logger.warning(f"Lesson {lesson_id} not fully completed for user {username}")
            return False, "Lesson is not fully completed"

        # Record completion in results table
        success = insert_row("results", {
            "username": username,
            "level": lesson_id,
            "correct": 1
        })

        if success:
            logger.info(f"Successfully marked lesson {lesson_id} as completed for user {username}")
            return True, None
        else:
            logger.error(f"Failed to mark lesson {lesson_id} as completed for user {username}")
            return False, "Failed to record completion"

    except ValueError as e:
        logger.error(f"Validation error marking lesson as completed: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error marking lesson as completed for user {username}, lesson {lesson_id}: {e}")
        return False, "Database error"


def get_lesson_progress_summary(username: str, lesson_id: int) -> Dict[str, Any]:
    """
    Get comprehensive progress summary for a lesson.

    Args:
        username: The username to get summary for
        lesson_id: The lesson ID to get summary for

    Returns:
        Dictionary containing progress summary

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Getting lesson progress summary for user {username}, lesson {lesson_id}")

        # Get lesson information
        lesson_info = select_one(
            "lesson_content",
            columns=["title", "num_blocks"],
            where="lesson_id = ?",
            params=(lesson_id,),
        )

        if not lesson_info:
            return {
                "lesson_id": lesson_id,
                "title": "Unknown Lesson",
                "total_blocks": 0,
                "completed_blocks": 0,
                "percent_complete": 0,
                "is_completed": False,
                "last_activity": None
            }

        total_blocks = lesson_info.get("num_blocks") or 0

        # Get completed blocks count
        completed_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="lesson_id = ? AND user_id = ? AND completed = 1",
            params=(lesson_id, username),
        )
        completed_blocks = completed_row.get("count") if completed_row else 0

        # Get last activity
        last_activity_row = select_one(
            "lesson_progress",
            columns="MAX(updated_at) as last_activity",
            where="lesson_id = ? AND user_id = ?",
            params=(lesson_id, username),
        )
        last_activity = last_activity_row.get("last_activity") if last_activity_row else None

        # Calculate completion percentage
        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks > 0 else 0
        is_completed = total_blocks > 0 and completed_blocks == total_blocks

        summary = {
            "lesson_id": lesson_id,
            "title": lesson_info.get("title") or f"Lesson {lesson_id}",
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "percent_complete": percent_complete,
            "is_completed": is_completed,
            "last_activity": last_activity
        }

        logger.info(f"Retrieved progress summary for user {username}, lesson {lesson_id}")
        return summary

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress summary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson progress summary for user {username}, lesson {lesson_id}: {e}")
        raise


def reset_lesson_progress(username: str, lesson_id: int) -> bool:
    """
    Reset all progress for a specific lesson.

    Args:
        username: The username to reset progress for
        lesson_id: The lesson ID to reset progress for

    Returns:
        True if progress was reset successfully, False otherwise

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Resetting lesson progress for user {username}, lesson {lesson_id}")

        # Delete all progress records for this lesson
        success = delete_rows(
            "lesson_progress",
            "WHERE user_id = ? AND lesson_id = ?",
            (username, lesson_id)
        )

        if success:
            logger.info(f"Successfully reset lesson progress for user {username}, lesson {lesson_id}")
        else:
            logger.error(f"Failed to reset lesson progress for user {username}, lesson {lesson_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error resetting lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error resetting lesson progress for user {username}, lesson {lesson_id}: {e}")
        raise
