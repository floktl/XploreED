"""
XplorED - Admin Lesson Management Module

This module provides lesson management functions for admin operations,
following clean architecture principles as outlined in the documentation.

Lesson Management Components:
- Lesson Content: Creation, updating, and deletion of lesson content
- Lesson Progress: Tracking and analysis of lesson completion
- Block Management: HTML block processing and metadata management
- Progress Analytics: Lesson completion statistics and user progress

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup  # type: ignore

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows
from core.processing import strip_ai_data, inject_block_ids
from features.lessons import update_lesson_blocks_from_html
from shared.exceptions import DatabaseError
from shared.types import LessonData, LessonList, ValidationResult, AnalyticsData

logger = logging.getLogger(__name__)


def create_lesson_content(lesson_data: LessonData) -> ValidationResult:
    """
    Create a new lesson with content and block management.

    Args:
        lesson_data: Dictionary containing lesson information

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If lesson data is invalid
    """
    try:
        lesson_id = lesson_data.get("lesson_id")
        title = lesson_data.get("title", "")
        content = lesson_data.get("content", "")
        target_user = lesson_data.get("target_user")
        published = bool(lesson_data.get("published", 0))
        ai_enabled = bool(lesson_data.get("ai_enabled", 0))

        if not lesson_id:
            raise ValueError("Lesson ID is required")

        if not content:
            raise ValueError("Lesson content is required")

        logger.info(f"Creating lesson content for lesson ID {lesson_id}")

        # Strip AI data from content
        content = strip_ai_data(content)

        # Extract block IDs from HTML
        soup = BeautifulSoup(content, "html.parser")
        block_ids = set()
        for el in soup.select('[data-block-id]'):
            if el.has_attr("data-block-id"):
                block_id = el.get("data-block-id")
                if isinstance(block_id, str) and block_id:
                    block_ids.add(block_id)
        num_blocks = len(block_ids)

        # Insert lesson row
        insert_success = insert_row("lesson_content", {
            "lesson_id": lesson_id,
            "title": title,
            "content": content,
            "target_user": target_user,
            "published": published,
            "num_blocks": num_blocks,
            "ai_enabled": ai_enabled
        })

        if not insert_success:
            logger.error(f"Failed to insert lesson content for lesson ID {lesson_id}")
            return False, "Failed to insert lesson"

        # Insert individual blocks
        for block_id in block_ids:
            block_inserted = insert_row("lesson_blocks", {
                "lesson_id": lesson_id,
                "block_id": block_id
            })

            if not block_inserted:
                logger.warning(f"Failed to insert block {block_id} for lesson {lesson_id}")

        logger.info(f"Successfully created lesson content for lesson ID {lesson_id} with {num_blocks} blocks")
        return True, None

    except ValueError as e:
        logger.error(f"Validation error creating lesson content: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error creating lesson content: {e}")
        raise DatabaseError(f"Error creating lesson content: {str(e)}")


def get_all_lessons() -> LessonList:
    """
    Retrieve all lesson content for admin editing.

    Returns:
        List of all lessons with their metadata

    Raises:
        Exception: If database operations fail
    """
    try:
        logger.info("Retrieving all lesson content for admin editing")

        lessons = select_rows(
            "lesson_content",
            columns=[
                "lesson_id",
                "title",
                "content",
                "target_user",
                "published",
                "ai_enabled",
                "num_blocks",
            ],
            order_by="lesson_id ASC",
        )

        logger.info(f"Retrieved {len(lessons)} lessons")
        return lessons

    except Exception as e:
        logger.error(f"Error getting all lessons: {e}")
        raise DatabaseError(f"Error getting all lessons: {str(e)}")


def get_lesson_by_id(lesson_id: int) -> Optional[LessonData]:
    """
    Get a specific lesson by ID.

    Args:
        lesson_id: The lesson ID to retrieve

    Returns:
        Lesson data or None if not found

    Raises:
        ValueError: If lesson_id is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Retrieving lesson with ID {lesson_id}")

        lesson = select_one(
            "lesson_content",
            where="lesson_id = ?",
            params=(lesson_id,),
        )

        if not lesson:
            logger.warning(f"Lesson with ID {lesson_id} not found")
            return None

        logger.info(f"Retrieved lesson with ID {lesson_id}")
        return lesson

    except ValueError as e:
        logger.error(f"Validation error getting lesson by ID: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting lesson by ID {lesson_id}: {e}")
        raise DatabaseError(f"Error getting lesson by ID {lesson_id}: {str(e)}")


def update_admin_lesson_content(lesson_id: int, lesson_data: LessonData) -> ValidationResult:
    """
    Update an existing lesson with new content and metadata.

    Args:
        lesson_id: The lesson ID to update
        lesson_data: Dictionary containing updated lesson information

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If lesson_id or lesson_data is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        if not lesson_data:
            raise ValueError("Lesson data is required")

        logger.info(f"Updating lesson content for lesson ID {lesson_id}")

        content = lesson_data.get("content", "")
        if not content:
            raise ValueError("Lesson content is required")

        # Inject or reassign block IDs and strip AI data
        content = inject_block_ids(content)
        content = strip_ai_data(content)

        # Count block IDs
        soup = BeautifulSoup(content, "html.parser")
        block_ids = set()
        for el in soup.select('[data-block-id]'):
            if el.has_attr("data-block-id"):
                block_id = el.get("data-block-id")
                if isinstance(block_id, str) and block_id:
                    block_ids.add(block_id)
        num_blocks = len(block_ids)

        # Update the lesson row
        update_row(
            "lesson_content",
            {
                "title": lesson_data.get("title"),
                "content": content,
                "target_user": lesson_data.get("target_user"),
                "published": bool(lesson_data.get("published", 0)),
                "num_blocks": num_blocks,
                "ai_enabled": bool(lesson_data.get("ai_enabled", 0)),
            },
            "WHERE lesson_id = ?",
            (lesson_id,),
        )

        # Sync lesson_blocks table
        update_lesson_blocks_from_html(lesson_id, content)

        logger.info(f"Successfully updated lesson content for lesson ID {lesson_id}")
        return True, None

    except ValueError as e:
        logger.error(f"Validation error updating lesson content: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error updating lesson content for lesson ID {lesson_id}: {e}")
        raise DatabaseError(f"Error updating lesson content for lesson ID {lesson_id}: {str(e)}")


def delete_lesson_content(lesson_id: int) -> Tuple[bool, Optional[str]]:
    """
    Delete a lesson and all related data.

    Args:
        lesson_id: The lesson ID to delete

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If lesson_id is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Deleting lesson content for lesson ID {lesson_id}")

        # Delete related records first
        delete_rows("lesson_progress", "WHERE lesson_id = ?", (lesson_id,))
        delete_rows("lesson_blocks", "WHERE lesson_id = ?", (lesson_id,))
        delete_rows("lesson_content", "WHERE lesson_id = ?", (lesson_id,))

        logger.info(f"Successfully deleted lesson content for lesson ID {lesson_id}")
        return True, None

    except ValueError as e:
        logger.error(f"Validation error deleting lesson content: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error deleting lesson content for lesson ID {lesson_id}: {e}")
        raise DatabaseError(f"Error deleting lesson content for lesson ID {lesson_id}: {str(e)}")


def get_lesson_progress_summary() -> AnalyticsData:
    """
    Get percentage completion summary for all lessons.

    Returns:
        Dictionary mapping lesson IDs to completion statistics

    Raises:
        Exception: If database operations fail
    """
    try:
        logger.info("Retrieving lesson progress summary")

        lesson_ids = [
            row["lesson_id"] for row in select_rows(
                "lesson_content",
                columns="DISTINCT lesson_id",
            )
        ]

        summary = {}
        for lesson_id in lesson_ids:
            row = select_one(
                "lesson_content",
                columns="num_blocks",
                where="lesson_id = ?",
                params=(lesson_id,),
            )
            total_blocks = row.get("num_blocks") if row else 0

            if total_blocks == 0:
                summary[lesson_id] = {"percent": 0, "num_blocks": 0}
                continue

            user_rows = select_rows(
                "lesson_progress",
                columns="DISTINCT user_id",
                where="lesson_id = ?",
                params=(lesson_id,),
            )
            users = [row["user_id"] for row in user_rows]

            if not users:
                summary[lesson_id] = {"percent": 0, "num_blocks": total_blocks}
                continue

            total_percent = 0.0
            for user_id in users:
                completed_row = select_one(
                    "lesson_progress",
                    columns="COUNT(*) as count",
                    where="lesson_id = ? AND user_id = ? AND completed = 1",
                    params=(lesson_id, user_id),
                )
                completed = completed_row.get("count") if completed_row else 0
                total_percent += (completed / total_blocks) * 100 if total_blocks and total_blocks > 0 else 0

            summary[lesson_id] = {
                "percent": round(total_percent / len(users)),
                "num_blocks": total_blocks,
            }

        logger.info(f"Retrieved progress summary for {len(summary)} lessons")
        return summary

    except Exception as e:
        logger.error(f"Error getting lesson statistics: {e}")
        raise DatabaseError(f"Error getting lesson statistics: {str(e)}")


def get_individual_lesson_progress(lesson_id: int) -> LessonList:
    """
    Get per-user completion stats for a specific lesson.

    Args:
        lesson_id: The lesson ID to get progress for

    Returns:
        List of user progress data for the lesson

    Raises:
        ValueError: If lesson_id is invalid
    """
    try:
        if not lesson_id or lesson_id <= 0:
            raise ValueError("Valid lesson ID is required")

        logger.info(f"Retrieving individual lesson progress for lesson ID {lesson_id}")

        num_blocks_row = select_one(
            "lesson_content",
            columns="num_blocks",
            where="lesson_id = ?",
            params=(lesson_id,),
        )
        total_blocks = num_blocks_row.get("num_blocks") if num_blocks_row else 0

        if total_blocks == 0:
            logger.warning(f"No blocks found for lesson ID {lesson_id}")
            return []

        rows = select_rows(
            "lesson_progress",
            columns=["user_id", "COUNT(*) AS completed_blocks"],
            where="lesson_id = ? AND completed = 1",
            params=(lesson_id,),
            group_by="user_id",
        )

        result = [
            {
                "user": row["user_id"],
                "completed": row["completed_blocks"],
                "total": total_blocks,
                "percent": round((row["completed_blocks"] / total_blocks) * 100),
            }
            for row in rows
        ]

        logger.info(f"Retrieved progress for {len(result)} users in lesson {lesson_id}")
        return result

    except ValueError as e:
        logger.error(f"Validation error getting individual lesson progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting individual lesson progress for lesson ID {lesson_id}: {e}")
        raise DatabaseError(f"Error getting individual lesson progress for lesson ID {lesson_id}: {str(e)}")
