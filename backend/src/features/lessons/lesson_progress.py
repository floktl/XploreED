"""
XplorED - Lesson Progress Module

This module provides lesson progress tracking and validation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Lesson Progress Components:
- Progress Tracking: Track lesson progress and block completion
- Progress Updates: Update lesson progress and completion status
- Progress Statistics: Get lesson progress statistics and metrics
- Block Validation: Validate block completion and access

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional

from core.services.import_service import *
from core.database.connection import select_rows, select_one, update_row, insert_row

logger = logging.getLogger(__name__)


def get_lesson_progress(username: str, lesson_id: int) -> Dict[str, bool]:
    """
    Get progress information for a specific lesson.

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

        # Get progress data
        progress_data = select_one(
            "lesson_progress",
            columns=["progress_data"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        if progress_data and progress_data.get("progress_data"):
            import json
            try:
                progress = json.loads(progress_data["progress_data"])
                logger.info(f"Retrieved lesson progress for user {username}, lesson {lesson_id}")
                return progress
            except json.JSONDecodeError:
                logger.warning(f"Invalid progress data format for user {username}, lesson {lesson_id}")
                return {}
        else:
            logger.info(f"No progress data found for user {username}, lesson {lesson_id}")
            return {}

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson progress for user {username}, lesson {lesson_id}: {e}")
        return {}


def update_lesson_progress(username: str, lesson_id: int, block_id: str, completed: bool) -> bool:
    """
    Update progress for a specific lesson block.

    Args:
        username: The username to update progress for
        lesson_id: The lesson ID to update progress for
        block_id: The block ID to update progress for
        completed: Whether the block is completed

    Returns:
        True if update was successful, False otherwise

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

        logger.info(f"Updating lesson progress for user {username}, lesson {lesson_id}, block {block_id}, completed: {completed}")

        # Get current progress
        progress_data = select_one(
            "lesson_progress",
            columns=["progress_data", "completed_blocks", "total_blocks"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        import json
        from datetime import datetime

        if progress_data:
            # Update existing progress
            try:
                progress = json.loads(progress_data["progress_data"]) if progress_data["progress_data"] else {}
            except json.JSONDecodeError:
                progress = {}

            progress[block_id] = completed

            # Calculate new completion stats
            completed_blocks = sum(1 for is_completed in progress.values() if is_completed)
            total_blocks = progress_data.get("total_blocks", len(progress))

            # Update progress record
            success = update_row(
                "lesson_progress",
                {
                    "progress_data": json.dumps(progress),
                    "completed_blocks": completed_blocks,
                    "last_accessed": datetime.utcnow().isoformat(),
                },
                "user_id = ? AND lesson_id = ?",
                (username, lesson_id),
            )

        else:
            # Create new progress record
            progress = {block_id: completed}
            completed_blocks = 1 if completed else 0

            # Get total blocks for this lesson
            lesson_data = select_one(
                "lesson_content",
                columns=["num_blocks"],
                where="lesson_id = ?",
                params=(lesson_id,),
            )
            total_blocks = lesson_data.get("num_blocks", 1) if lesson_data else 1

            success = insert_row(
                "lesson_progress",
                {
                    "user_id": username,
                    "lesson_id": lesson_id,
                    "progress_data": json.dumps(progress),
                    "completed_blocks": completed_blocks,
                    "total_blocks": total_blocks,
                    "last_accessed": datetime.utcnow().isoformat(),
                },
            )

        if success:
            logger.info(f"Successfully updated lesson progress for user {username}, lesson {lesson_id}, block {block_id}")
            return True
        else:
            logger.error(f"Failed to update lesson progress for user {username}, lesson {lesson_id}, block {block_id}")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating lesson progress for user {username}, lesson {lesson_id}, block {block_id}: {e}")
        return False


def get_lesson_statistics(username: str, lesson_id: int) -> Dict[str, Any]:
    """
    Get detailed statistics for a specific lesson.

    Args:
        username: The username to get statistics for
        lesson_id: The lesson ID to get statistics for

    Returns:
        Dictionary containing lesson statistics

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Getting lesson statistics for user {username}, lesson {lesson_id}")

        # Get lesson progress data
        progress_data = select_one(
            "lesson_progress",
            columns=["progress_data", "completed_blocks", "total_blocks", "last_accessed"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        # Get lesson content data
        lesson_data = select_one(
            "lesson_content",
            columns=["title", "num_blocks", "created_at"],
            where="lesson_id = ?",
            params=(lesson_id,),
        )

        if not lesson_data:
            logger.warning(f"Lesson {lesson_id} not found")
            return {}

        # Calculate statistics
        total_blocks = lesson_data.get("num_blocks", 0)
        completed_blocks = progress_data.get("completed_blocks", 0) if progress_data else 0
        completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0

        # Get detailed progress by block
        block_progress = {}
        if progress_data and progress_data.get("progress_data"):
            import json
            try:
                block_progress = json.loads(progress_data["progress_data"])
            except json.JSONDecodeError:
                block_progress = {}

        statistics = {
            "lesson_id": lesson_id,
            "title": lesson_data.get("title", ""),
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "completion_percentage": round(completion_percentage, 2),
            "is_completed": completion_percentage >= 100,
            "last_accessed": progress_data.get("last_accessed") if progress_data else None,
            "block_progress": block_progress,
            "remaining_blocks": total_blocks - completed_blocks,
            "started": completed_blocks > 0,
        }

        logger.info(f"Retrieved lesson statistics for user {username}, lesson {lesson_id}: {completion_percentage:.1f}% complete")
        return statistics

    except ValueError as e:
        logger.error(f"Validation error getting lesson statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson statistics for user {username}, lesson {lesson_id}: {e}")
        return {}


def validate_block_completion(user: str, lesson_id: int, block_id: str) -> Dict[str, Any]:
    """
    Validate if a user can complete a specific block.

    Args:
        user: The username to validate for
        lesson_id: The lesson ID to validate for
        block_id: The block ID to validate for

    Returns:
        Dictionary containing validation result and block information

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        if not block_id:
            raise ValueError("Block ID is required")

        logger.info(f"Validating block completion for user {user}, lesson {lesson_id}, block {block_id}")

        # Check if lesson exists and user has access
        lesson = select_one(
            "lesson_content",
            columns=["lesson_id", "published"],
            where="lesson_id = ? AND (target_user IS NULL OR target_user = ?)",
            params=(lesson_id, user),
        )

        if not lesson:
            return {
                "valid": False,
                "error": "Lesson not found or access denied",
                "block_id": block_id,
            }

        if not lesson.get("published"):
            return {
                "valid": False,
                "error": "Lesson is not published",
                "block_id": block_id,
            }

        # Check if block exists
        block = select_one(
            "lesson_blocks",
            columns=["block_id", "block_type", "order_index"],
            where="lesson_id = ? AND block_id = ?",
            params=(lesson_id, block_id),
        )

        if not block:
            return {
                "valid": False,
                "error": "Block not found",
                "block_id": block_id,
            }

        # Check current progress
        progress_data = select_one(
            "lesson_progress",
            columns=["progress_data"],
            where="user_id = ? AND lesson_id = ?",
            params=(user, lesson_id),
        )

        is_already_completed = False
        if progress_data and progress_data.get("progress_data"):
            import json
            try:
                progress = json.loads(progress_data["progress_data"])
                is_already_completed = progress.get(block_id, False)
            except json.JSONDecodeError:
                pass

        validation_result = {
            "valid": True,
            "block_id": block_id,
            "block_type": block.get("block_type"),
            "order_index": block.get("order_index"),
            "is_already_completed": is_already_completed,
            "lesson_id": lesson_id,
        }

        logger.info(f"Block completion validation for user {user}, lesson {lesson_id}, block {block_id}: valid")
        return validation_result

    except ValueError as e:
        logger.error(f"Validation error checking block completion: {e}")
        raise
    except Exception as e:
        logger.error(f"Error validating block completion for user {user}, lesson {lesson_id}, block {block_id}: {e}")
        return {
            "valid": False,
            "error": "Validation error",
            "block_id": block_id,
        }
