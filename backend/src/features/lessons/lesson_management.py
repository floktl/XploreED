"""
XplorED - Lesson Management Module

This module provides lesson content management and analytics functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Lesson Management Components:
- Content Management: Update and manage lesson content
- Lesson Publishing: Publish and unpublish lessons
- Lesson Analytics: Get lesson usage analytics and insights
- Content Validation: Validate lesson content and structure

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional

from core.services.import_service import *
from core.database.connection import select_rows, select_one, update_row, insert_row

logger = logging.getLogger(__name__)


def update_lesson_content(lesson_id: int, updates: Dict[str, Any]) -> bool:
    """
    Update lesson content and metadata.

    Args:
        lesson_id: The lesson ID to update
        updates: Dictionary containing fields to update

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If lesson_id is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        if not updates or not isinstance(updates, dict):
            raise ValueError("Updates dictionary is required")

        logger.info(f"Updating lesson content for lesson {lesson_id}")

        # Verify lesson exists
        existing = select_one("lesson_content", columns=["lesson_id"], where="lesson_id = ?", params=(lesson_id,))
        if not existing:
            logger.warning(f"Lesson {lesson_id} not found for update")
            return False

        # Filter out invalid fields
        valid_fields = {
            "title", "content", "num_blocks", "ai_enabled", "target_user", "published"
        }

        filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not filtered_updates:
            logger.warning(f"No valid fields to update for lesson {lesson_id}")
            return False

        # Update the lesson
        success = update_row("lesson_content", filtered_updates, "lesson_id = ?", (lesson_id,))

        if success:
            logger.info(f"Successfully updated lesson content for lesson {lesson_id}")
            return True
        else:
            logger.error(f"Failed to update lesson content for lesson {lesson_id}")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating lesson content: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating lesson content for lesson {lesson_id}: {e}")
        return False


def publish_lesson(lesson_id: int, published: bool) -> bool:
    """
    Publish or unpublish a lesson.

    Args:
        lesson_id: The lesson ID to publish/unpublish
        published: True to publish, False to unpublish

    Returns:
        True if operation was successful, False otherwise

    Raises:
        ValueError: If lesson_id is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"{'Publishing' if published else 'Unpublishing'} lesson {lesson_id}")

        # Verify lesson exists
        existing = select_one("lesson_content", columns=["lesson_id"], where="lesson_id = ?", params=(lesson_id,))
        if not existing:
            logger.warning(f"Lesson {lesson_id} not found for publish/unpublish")
            return False

        # Update published status
        success = update_row("lesson_content", {"published": int(published)}, "lesson_id = ?", (lesson_id,))

        if success:
            status = "published" if published else "unpublished"
            logger.info(f"Successfully {status} lesson {lesson_id}")
            return True
        else:
            logger.error(f"Failed to {'publish' if published else 'unpublish'} lesson {lesson_id}")
            return False

    except ValueError as e:
        logger.error(f"Validation error publishing lesson: {e}")
        raise
    except Exception as e:
        logger.error(f"Error publishing lesson {lesson_id}: {e}")
        return False


def get_lesson_analytics(lesson_id: int, timeframe: str = "all") -> Dict[str, Any]:
    """
    Get analytics data for a specific lesson.

    Args:
        lesson_id: The lesson ID to get analytics for
        timeframe: Timeframe for analytics ("all", "week", "month", "year")

    Returns:
        Dictionary containing lesson analytics

    Raises:
        ValueError: If lesson_id is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Getting lesson analytics for lesson {lesson_id}, timeframe: {timeframe}")

        # Verify lesson exists
        lesson_data = select_one(
            "lesson_content",
            columns=["title", "created_at", "num_blocks"],
            where="lesson_id = ?",
            params=(lesson_id,),
        )

        if not lesson_data:
            logger.warning(f"Lesson {lesson_id} not found for analytics")
            return {}

        # Build timeframe filter
        timeframe_filter = ""
        if timeframe == "week":
            timeframe_filter = "AND last_accessed >= date('now', '-7 days')"
        elif timeframe == "month":
            timeframe_filter = "AND last_accessed >= date('now', '-30 days')"
        elif timeframe == "year":
            timeframe_filter = "AND last_accessed >= date('now', '-365 days')"

        # Get user progress data
        progress_data = select_rows(
            "lesson_progress",
            columns=["user_id", "completed_blocks", "total_blocks", "last_accessed"],
            where=f"lesson_id = ? {timeframe_filter}",
            params=(lesson_id,),
        )

        # Calculate analytics
        total_users = len(progress_data) if progress_data else 0
        completed_users = sum(1 for row in progress_data if row.get("completed_blocks", 0) >= row.get("total_blocks", 0)) if progress_data else 0
        completion_rate = (completed_users / total_users * 100) if total_users > 0 else 0

        # Calculate average completion percentage
        avg_completion = 0
        if progress_data:
            total_completion = 0
            for row in progress_data:
                completed = row.get("completed_blocks", 0)
                total = row.get("total_blocks", 1)
                if total > 0:
                    total_completion += (completed / total * 100)
            avg_completion = total_completion / len(progress_data)

        # Get recent activity
        recent_activity = select_rows(
            "lesson_progress",
            columns=["user_id", "last_accessed"],
            where=f"lesson_id = ? AND last_accessed >= date('now', '-7 days')",
            params=(lesson_id,),
            order_by="last_accessed DESC",
            limit=10,
        )

        analytics = {
            "lesson_id": lesson_id,
            "title": lesson_data.get("title", ""),
            "timeframe": timeframe,
            "total_users": total_users,
            "completed_users": completed_users,
            "completion_rate": round(completion_rate, 2),
            "average_completion_percentage": round(avg_completion, 2),
            "total_blocks": lesson_data.get("num_blocks", 0),
            "created_at": lesson_data.get("created_at"),
            "recent_activity": [
                {
                    "user_id": row.get("user_id"),
                    "last_accessed": row.get("last_accessed")
                }
                for row in recent_activity
            ] if recent_activity else [],
        }

        logger.info(f"Retrieved lesson analytics for lesson {lesson_id}: {total_users} users, {completion_rate:.1f}% completion rate")
        return analytics

    except ValueError as e:
        logger.error(f"Validation error getting lesson analytics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson analytics for lesson {lesson_id}: {e}")
        return {}
