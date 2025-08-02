"""
XplorED - Lesson Retrieval Module

This module provides lesson content and summary retrieval functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Lesson Retrieval Components:
- Lesson Summaries: Get lesson summaries and overview information
- Lesson Content: Retrieve lesson HTML content and metadata
- Lesson Blocks: Get lesson block information and structure
- Access Validation: Validate user access to lessons

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional

from core.database.connection import select_rows, select_one, update_row, insert_row
from core.services import LessonService

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
    return LessonService.get_user_lessons_summary(username)


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
    return LessonService.get_lesson_content(username, lesson_id)


def get_lesson_blocks(lesson_id: int) -> List[Dict[str, Any]]:
    """
    Get all blocks for a specific lesson.

    Args:
        lesson_id: The lesson ID to get blocks for

    Returns:
        List of lesson blocks with metadata

    Raises:
        ValueError: If lesson_id is invalid
    """
    return LessonService.get_lesson_blocks(lesson_id)


def validate_lesson_access(username: str, lesson_id: int) -> bool:
    """
    Validate if a user has access to a specific lesson.

    Args:
        username: The username to validate access for
        lesson_id: The lesson ID to check access for

    Returns:
        True if user has access, False otherwise

    Raises:
        ValueError: If username or lesson_id is invalid
    """
    return LessonService.validate_lesson_access(username, lesson_id)


def _build_lesson_summary(username: str, lesson_id: int, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a lesson summary with progress information.

    Args:
        username: The username
        lesson_id: The lesson ID
        lesson_data: The lesson data from database

    Returns:
        Dictionary containing lesson summary with progress
    """
    try:
        # Get lesson progress
        progress_data = select_one(
            "lesson_progress",
            columns=["completed_blocks", "total_blocks", "last_accessed"],
            where="user_id = ? AND lesson_id = ?",
            params=(username, lesson_id),
        )

        # Calculate completion percentage
        total_blocks = lesson_data.get("num_blocks", 0)
        completed_blocks = progress_data.get("completed_blocks", 0) if progress_data else 0
        completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0

        summary = {
            "lesson_id": lesson_id,
            "title": lesson_data.get("title", ""),
            "created_at": lesson_data.get("created_at"),
            "num_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "completion_percentage": round(completion_percentage, 2),
            "ai_enabled": bool(lesson_data.get("ai_enabled", False)),
            "last_accessed": progress_data.get("last_accessed") if progress_data else None,
            "is_completed": completion_percentage >= 100,
        }

        return summary

    except Exception as e:
        logger.error(f"Error building lesson summary for user {username}, lesson {lesson_id}: {e}")
        return {
            "lesson_id": lesson_id,
            "title": lesson_data.get("title", ""),
            "created_at": lesson_data.get("created_at"),
            "num_blocks": lesson_data.get("num_blocks", 0),
            "completed_blocks": 0,
            "completion_percentage": 0.0,
            "ai_enabled": bool(lesson_data.get("ai_enabled", False)),
            "last_accessed": None,
            "is_completed": False,
        }
