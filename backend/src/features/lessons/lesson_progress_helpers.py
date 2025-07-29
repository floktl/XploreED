"""
Lesson Progress Helper Functions

This module contains helper functions for lesson progress operations that are used
by the lesson progress routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
import datetime
from typing import Dict, Any, Optional, Tuple

from core.services.import_service import *


logger = logging.getLogger(__name__)


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
