"""
Lesson Helper Functions

This module contains helper functions for lesson operations that are used
by the lesson routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any, List, Optional

from core.services.import_service import *
from core.database.connection import select_rows, select_one


logger = logging.getLogger(__name__)


def get_user_lessons_summary(username: str) -> List[Dict[str, Any]]:
    """
    Get summary information for all published lessons for a user.

    Args:
        username: The username to get lessons for

    Returns:
        List of lesson summaries with progress information

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting lesson summary for user {username}")

        # Get all published lessons for the user
        lessons = select_rows(
            "lesson_content",
            columns=[
                "lesson_id",
                "title",
                "created_at",
                "target_user",
                "num_blocks",
                "ai_enabled",
            ],
            where="(target_user IS NULL OR target_user = ?) AND published = 1",
            params=(username,),
            order_by="created_at DESC",
        )

        results = []

        for lesson in lessons:
            lesson_id = lesson["lesson_id"]
            lesson_summary = _build_lesson_summary(username, lesson_id, lesson)
            results.append(lesson_summary)

        logger.info(f"Retrieved {len(results)} lesson summaries for user {username}")
        return results

    except ValueError as e:
        logger.error(f"Validation error getting lesson summary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson summary for user {username}: {e}")
        raise


def get_lesson_content(username: str, lesson_id: int) -> Optional[Dict[str, Any]]:
    """
    Get HTML content and metadata for a specific lesson.

    Args:
        username: The username requesting the lesson
        lesson_id: The lesson ID to retrieve

    Returns:
        Lesson content and metadata or None if not found

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Getting lesson content for user {username}, lesson {lesson_id}")

        # Get lesson content with user access control
        rows = select_rows(
            "lesson_content",
            columns=["title", "content", "created_at", "num_blocks", "ai_enabled"],
            where="lesson_id = ? AND (target_user IS NULL OR target_user = ?) AND published = 1",
            params=(lesson_id, username),
        )

        if not rows:
            logger.warning(f"Lesson {lesson_id} not found or not accessible for user {username}")
            return None

        lesson_data = {
            "title": rows[0]["title"],
            "content": rows[0]["content"],
            "created_at": rows[0]["created_at"],
            "num_blocks": rows[0]["num_blocks"],
            "ai_enabled": bool(rows[0].get("ai_enabled", 0)),
        }

        logger.info(f"Retrieved lesson content for user {username}, lesson {lesson_id}")
        return lesson_data

    except ValueError as e:
        logger.error(f"Validation error getting lesson content: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson content for user {username}, lesson {lesson_id}: {e}")
        raise


def get_lesson_progress(username: str, lesson_id: int) -> Dict[str, bool]:
    """
    Get completion status of each block in a lesson.

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

        # Get progress for all blocks in the lesson
        rows = select_rows(
            "lesson_progress",
            columns=["block_id", "completed"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        progress = {row[0]: bool(row[1]) for row in rows}

        logger.info(f"Retrieved progress for {len(progress)} blocks for user {username}, lesson {lesson_id}")
        return progress

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson progress for user {username}, lesson {lesson_id}: {e}")
        raise


def update_lesson_progress(username: str, lesson_id: int, block_id: str, completed: bool) -> bool:
    """
    Update the completion status of a specific block in a lesson.

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

        logger.info(f"Updating lesson progress for user {username}, lesson {lesson_id}, block {block_id}")

        # Check if progress record exists
        existing = select_one(
            "lesson_progress",
            columns="1",
            where="user_id = ? AND lesson_id = ? AND block_id = ?",
            params=(username, lesson_id, block_id),
        )

        if existing:
            # Update existing record
            success = update_row(
                "lesson_progress",
                {"completed": completed},
                "user_id = ? AND lesson_id = ? AND block_id = ?",
                (username, lesson_id, block_id),
            )
        else:
            # Insert new record
            success = insert_row("lesson_progress", {
                "user_id": username,
                "lesson_id": lesson_id,
                "block_id": block_id,
                "completed": completed,
            })

        if success:
            logger.info(f"Successfully updated progress for user {username}, lesson {lesson_id}, block {block_id}")
        else:
            logger.error(f"Failed to update progress for user {username}, lesson {lesson_id}, block {block_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error updating lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating lesson progress for user {username}, lesson {lesson_id}, block {block_id}: {e}")
        raise


def get_lesson_statistics(username: str, lesson_id: int) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a specific lesson.

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

        # Get lesson information
        lesson_info = select_one(
            "lesson_content",
            columns=["title", "num_blocks", "ai_enabled"],
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
                "ai_enabled": False,
                "last_activity": None,
                "completion_date": None
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
            columns="MAX(timestamp) as last_activity",
            where="lesson_id = ? AND user_id = ?",
            params=(lesson_id, username),
        )
        last_activity = last_activity_row.get("last_activity") if last_activity_row else None

        # Calculate completion date (when all blocks were completed)
        completion_date = None
        if completed_blocks == total_blocks and total_blocks > 0:
            completion_row = select_one(
                "lesson_progress",
                columns="MAX(timestamp) as completion_date",
                where="lesson_id = ? AND user_id = ? AND completed = 1",
                params=(lesson_id, username),
            )
            completion_date = completion_row.get("completion_date") if completion_row else None

        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks > 0 else 0

        stats = {
            "lesson_id": lesson_id,
            "title": lesson_info.get("title") or f"Lesson {lesson_id}",
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "percent_complete": percent_complete,
            "ai_enabled": bool(lesson_info.get("ai_enabled", 0)),
            "last_activity": last_activity,
            "completion_date": completion_date
        }

        logger.info(f"Retrieved lesson statistics for user {username}, lesson {lesson_id}")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting lesson statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson statistics for user {username}, lesson {lesson_id}: {e}")
        raise


def _build_lesson_summary(username: str, lesson_id: int, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a lesson summary with progress information.

    Args:
        username: The username
        lesson_id: The lesson ID
        lesson_data: Raw lesson data from database

    Returns:
        Dictionary containing lesson summary
    """
    try:
        total_blocks = lesson_data.get("num_blocks") or 0

        # Get completed blocks count
        completed_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="lesson_id = ? AND user_id = ? AND completed = 1",
            params=(lesson_id, username),
        )
        completed_blocks = completed_row.get("count") if completed_row else 0

        # Check if lesson is fully completed
        completed = bool(
            select_one(
                "results",
                columns="1",
                where="username = ? AND level = ? AND correct = 1",
                params=(username, lesson_id),
            )
        )

        # Calculate completion percentage
        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks > 0 else 100
        if completed:
            percent_complete = 100

        # Get last attempt timestamp
        latest_row = select_one(
            "results",
            columns="MAX(timestamp) as ts",
            where="username = ? AND level = ?",
            params=(username, lesson_id),
        )
        latest = latest_row.get("ts") if latest_row else None

        return {
            "id": lesson_id,
            "title": lesson_data["title"] or f"Lesson {lesson_id + 1}",
            "completed": completed,
            "last_attempt": latest,
            "percent_complete": percent_complete,
            "ai_enabled": bool(lesson_data.get("ai_enabled", 0)),
        }

    except Exception as e:
        logger.error(f"Error building lesson summary for user {username}, lesson {lesson_id}: {e}")
        return {
            "id": lesson_id,
            "title": lesson_data.get("title") or f"Lesson {lesson_id + 1}",
            "completed": False,
            "last_attempt": None,
            "percent_complete": 0,
            "ai_enabled": False,
        }


def validate_lesson_access(username: str, lesson_id: int) -> bool:
    """
    Validate if a user has access to a specific lesson.

    Args:
        username: The username to check access for
        lesson_id: The lesson ID to check access for

    Returns:
        True if user has access, False otherwise
    """
    try:
        if not username or not lesson_id:
            return False

        # Check if lesson exists and user has access
        lesson = select_one(
            "lesson_content",
            columns="1",
            where="lesson_id = ? AND (target_user IS NULL OR target_user = ?) AND published = 1",
            params=(lesson_id, username),
        )

        return lesson is not None

    except Exception as e:
        logger.error(f"Error validating lesson access for user {username}, lesson {lesson_id}: {e}")
        return False
