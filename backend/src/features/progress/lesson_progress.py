"""
XplorED - Lesson Progress Module

This module provides lesson-specific progress functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Lesson Progress Components:
- Lesson Completion: Mark lessons as complete and check completion status
- Block Progress: Update and manage individual lesson block progress
- Progress Summary: Get detailed lesson progress summaries
- Progress Reset: Reset lesson progress for users

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import Dict, Optional, Any, List, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query

logger = logging.getLogger(__name__)


def get_user_lesson_progress(username: str, lesson_id: int) -> Dict[str, bool]:
    """
    Get detailed lesson progress for a specific user and lesson.

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

        logger.info(f"Getting user lesson progress for user {username}, lesson {lesson_id}")

        rows = select_rows(
            "lesson_progress",
            columns=["block_id", "completed", "updated_at"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
            order_by="block_id ASC"
        )

        progress = {}
        for row in rows:
            block_id = row.get("block_id")
            completed = bool(row.get("completed", 0))
            updated_at = row.get("updated_at")
            if block_id:
                progress[block_id] = {
                    "completed": completed,
                    "updated_at": updated_at
                }

        logger.info(f"Retrieved progress for {len(progress)} blocks for user {username}, lesson {lesson_id}")
        return progress

    except ValueError as e:
        logger.error(f"Validation error getting user lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting user lesson progress for user {username}, lesson {lesson_id}: {e}")
        return {}


def update_block_progress(username: str, lesson_id: int, block_id: str, completed: bool) -> bool:
    """
    Update progress for a specific lesson block.

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

        # Check if progress record exists
        existing = select_one(
            "lesson_progress",
            where="user_id = ? AND lesson_id = ? AND block_id = ?",
            params=(username, lesson_id, block_id)
        )

        if existing:
            # Update existing record
            success = update_row(
                "lesson_progress",
                {
                    "completed": int(completed),
                    "updated_at": datetime.datetime.utcnow()
                },
                "WHERE user_id = ? AND lesson_id = ? AND block_id = ?",
                (username, lesson_id, block_id)
            )
        else:
            # Create new record
            progress_data = {
                "user_id": username,
                "lesson_id": lesson_id,
                "block_id": block_id,
                "completed": int(completed),
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }
            success = insert_row("lesson_progress", progress_data)

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
        return False


def mark_lesson_complete(username: str, lesson_id: int) -> Tuple[bool, Optional[str]]:
    """
    Mark a lesson as complete for a user.

    Args:
        username: The username to mark lesson complete for
        lesson_id: The lesson ID to mark complete

    Returns:
        Tuple of (success, message)

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Marking lesson complete for user {username}, lesson {lesson_id}")

        # Get all blocks for the lesson
        blocks = select_rows(
            "lesson_blocks",
            columns=["block_id"],
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not blocks:
            return False, "No blocks found for this lesson"

        # Mark all blocks as completed
        success_count = 0
        for block in blocks:
            block_id = block.get("block_id")
            if block_id:
                success = update_block_progress(username, lesson_id, block_id, True)
                if success:
                    success_count += 1

        if success_count == len(blocks):
            # Create lesson completion record
            completion_data = {
                "username": username,
                "lesson_id": lesson_id,
                "completed_at": datetime.datetime.utcnow().isoformat(),
                "completion_method": "manual"
            }

            insert_success = insert_row("lesson_completions", completion_data)

            if insert_success:
                logger.info(f"Successfully marked lesson {lesson_id} complete for user {username}")
                return True, f"Lesson marked complete. {success_count} blocks updated."
            else:
                logger.warning(f"Lesson blocks updated but completion record failed for user {username}, lesson {lesson_id}")
                return True, f"Lesson blocks updated but completion record failed. {success_count} blocks updated."
        else:
            logger.error(f"Failed to mark all blocks complete for user {username}, lesson {lesson_id}")
            return False, f"Failed to mark all blocks complete. {success_count}/{len(blocks)} blocks updated."

    except ValueError as e:
        logger.error(f"Validation error marking lesson complete: {e}")
        raise
    except Exception as e:
        logger.error(f"Error marking lesson complete for user {username}, lesson {lesson_id}: {e}")
        return False, f"Error marking lesson complete: {str(e)}"


def check_lesson_completion_status(username: str, lesson_id: int) -> Dict[str, Any]:
    """
    Check the completion status of a lesson for a user.

    Args:
        username: The username to check status for
        lesson_id: The lesson ID to check

    Returns:
        Dictionary containing completion status information

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Checking lesson completion status for user {username}, lesson {lesson_id}")

        # Get all blocks for the lesson
        blocks = select_rows(
            "lesson_blocks",
            columns=["block_id"],
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not blocks:
            return {
                "lesson_id": lesson_id,
                "username": username,
                "total_blocks": 0,
                "completed_blocks": 0,
                "completion_percentage": 0.0,
                "is_complete": False,
                "message": "No blocks found for this lesson"
            }

        total_blocks = len(blocks)
        block_ids = [block.get("block_id") for block in blocks if block.get("block_id")]

        # Get completion status for each block
        progress = get_user_lesson_progress(username, lesson_id)

        completed_blocks = sum(1 for block_data in progress.values() if isinstance(block_data, dict) and block_data.get("completed", False))
        completion_percentage = (completed_blocks / total_blocks) * 100 if total_blocks > 0 else 0
        is_complete = completed_blocks == total_blocks

        # Check if lesson completion record exists
        completion_record = select_one(
            "lesson_completions",
            where="username = ? AND lesson_id = ?",
            params=(username, lesson_id)
        )

        status = {
            "lesson_id": lesson_id,
            "username": username,
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "completion_percentage": round(completion_percentage, 2),
            "is_complete": is_complete,
            "has_completion_record": bool(completion_record),
            "completion_date": completion_record.get("completed_at") if completion_record else None,
            "block_progress": progress
        }

        logger.info(f"Lesson completion status for user {username}, lesson {lesson_id}: {completed_blocks}/{total_blocks} blocks complete ({completion_percentage:.1f}%)")
        return status

    except ValueError as e:
        logger.error(f"Validation error checking lesson completion status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error checking lesson completion status for user {username}, lesson {lesson_id}: {e}")
        return {
            "lesson_id": lesson_id,
            "username": username,
            "error": str(e),
            "total_blocks": 0,
            "completed_blocks": 0,
            "completion_percentage": 0.0,
            "is_complete": False
        }


def mark_lesson_as_completed(username: str, lesson_id: int) -> Tuple[bool, Optional[str]]:
    """
    Mark a lesson as completed with validation.

    Args:
        username: The username to mark lesson complete for
        lesson_id: The lesson ID to mark complete

    Returns:
        Tuple of (success, message)

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Marking lesson as completed for user {username}, lesson {lesson_id}")

        # Check current completion status
        status = check_lesson_completion_status(username, lesson_id)

        if status.get("error"):
            return False, f"Error checking lesson status: {status['error']}"

        if status.get("is_complete"):
            return True, "Lesson is already complete"

        # Mark lesson complete
        success, message = mark_lesson_complete(username, lesson_id)

        if success:
            # Verify completion
            new_status = check_lesson_completion_status(username, lesson_id)
            if new_status.get("is_complete"):
                logger.info(f"Successfully marked lesson {lesson_id} as completed for user {username}")
                return True, f"Lesson marked as completed. {message}"
            else:
                logger.warning(f"Lesson completion verification failed for user {username}, lesson {lesson_id}")
                return False, "Lesson completion verification failed"
        else:
            return False, message

    except ValueError as e:
        logger.error(f"Validation error marking lesson as completed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error marking lesson as completed for user {username}, lesson {lesson_id}: {e}")
        return False, f"Error marking lesson as completed: {str(e)}"


def reset_lesson_progress(username: str, lesson_id: int) -> bool:
    """
    Reset progress for a specific lesson.

    Args:
        username: The username to reset progress for
        lesson_id: The lesson ID to reset

    Returns:
        True if progress was reset successfully, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Resetting lesson progress for user {username}, lesson {lesson_id}")

        # Delete lesson progress records
        progress_success = delete_rows(
            "lesson_progress",
            "WHERE user_id = ? AND lesson_id = ?",
            (username, lesson_id)
        )

        # Delete lesson completion record
        completion_success = delete_rows(
            "lesson_completions",
            "WHERE username = ? AND lesson_id = ?",
            (username, lesson_id)
        )

        if progress_success and completion_success:
            logger.info(f"Successfully reset lesson progress for user {username}, lesson {lesson_id}")
            return True
        else:
            logger.error(f"Failed to reset lesson progress for user {username}, lesson {lesson_id}")
            return False

    except ValueError as e:
        logger.error(f"Validation error resetting lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error resetting lesson progress for user {username}, lesson {lesson_id}: {e}")
        return Falsegit
