"""
XplorED - Lesson Service

This module provides core lesson business logic services,
following clean architecture principles as outlined in the documentation.

Lesson Service Components:
- Lesson retrieval and content management
- Lesson progress tracking
- Lesson access validation
- Lesson analytics and statistics

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional
from core.database.connection import select_rows, select_one, update_row, insert_row
from core.authentication import user_exists
from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


class LessonService:
    """Core lesson business logic service."""

    @staticmethod
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
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

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
                lesson_summary = LessonService._build_lesson_summary(username, lesson_id, lesson)
                results.append(lesson_summary)

            logger.info(f"Retrieved {len(results)} lesson summaries for user {username}")
            return results

        except ValidationError as e:
            logger.error(f"Validation error getting lesson summary: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting lesson summary for user {username}: {e}")
            return []

    @staticmethod
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
                raise ValidationError("Username is required")

            if not lesson_id or lesson_id <= 0:
                raise ValidationError("Valid lesson ID is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

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

            lesson_data = rows[0]
            lesson_content = {
                "lesson_id": lesson_id,
                "title": lesson_data["title"],
                "content": lesson_data["content"],
                "created_at": lesson_data["created_at"],
                "num_blocks": lesson_data["num_blocks"],
                "ai_enabled": bool(lesson_data["ai_enabled"]),
            }

            logger.info(f"Retrieved lesson content for user {username}, lesson {lesson_id}")
            return lesson_content

        except ValidationError as e:
            logger.error(f"Validation error getting lesson content: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting lesson content for user {username}, lesson {lesson_id}: {e}")
            return None

    @staticmethod
    def get_lesson_progress(username: str, lesson_id: int) -> Dict[str, Any]:
        """
        Get lesson progress for a user.

        Args:
            username: The username to get progress for
            lesson_id: The lesson ID to get progress for

        Returns:
            Dictionary containing lesson progress information

        Raises:
            ValueError: If username or lesson_id is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not lesson_id or lesson_id <= 0:
                raise ValidationError("Valid lesson ID is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            logger.info(f"Getting lesson progress for user {username}, lesson {lesson_id}")

            # Get lesson progress
            progress_rows = select_rows(
                "lesson_progress",
                columns=["block_id", "completed", "updated_at"],
                where="user_id = ? AND lesson_id = ?",
                params=(username, lesson_id),
            )

            # Get lesson blocks
            blocks = LessonService.get_lesson_blocks(lesson_id)

            # Calculate progress statistics
            total_blocks = len(blocks)
            completed_blocks = len([p for p in progress_rows if p.get("completed")])
            completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0

            progress = {
                "lesson_id": lesson_id,
                "username": username,
                "total_blocks": total_blocks,
                "completed_blocks": completed_blocks,
                "completion_percentage": round(completion_percentage, 2),
                "blocks": blocks,
                "user_progress": progress_rows,
                "is_completed": completed_blocks >= total_blocks if total_blocks > 0 else False
            }

            logger.info(f"Retrieved lesson progress for user {username}, lesson {lesson_id}: {completed_blocks}/{total_blocks} blocks completed")
            return progress

        except ValueError as e:
            logger.error(f"Validation error getting lesson progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting lesson progress for user {username}, lesson {lesson_id}: {e}")
            return {
                "lesson_id": lesson_id,
                "username": username,
                "total_blocks": 0,
                "completed_blocks": 0,
                "completion_percentage": 0.0,
                "blocks": [],
                "user_progress": [],
                "is_completed": False
            }

    @staticmethod
    def update_lesson_progress(username: str, lesson_id: int, block_id: str, completed: bool) -> bool:
        """
        Update lesson progress for a user.

        Args:
            username: The username to update progress for
            lesson_id: The lesson ID to update progress for
            block_id: The block ID to update progress for
            completed: Whether the block is completed

        Returns:
            True if update was successful

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not username:
                raise ValueError("Username is required")

            if not lesson_id or lesson_id <= 0:
                raise ValueError("Valid lesson ID is required")

            if not block_id:
                raise ValueError("Block ID is required")

            if not user_exists(username):
                raise ValueError(f"User {username} does not exist")

            logger.info(f"Updating lesson progress for user {username}, lesson {lesson_id}, block {block_id}: completed={completed}")

            # Check if progress entry exists
            existing_progress = select_one(
                "lesson_progress",
                columns="*",
                where="user_id = ? AND lesson_id = ? AND block_id = ?",
                params=(username, lesson_id, block_id),
            )

            if existing_progress:
                # Update existing progress
                success = update_row(
                    "lesson_progress",
                    {"completed": completed, "updated_at": "datetime('now')"},
                    "WHERE user_id = ? AND lesson_id = ? AND block_id = ?",
                    (username, lesson_id, block_id),
                )
            else:
                # Create new progress entry
                progress_data = {
                    "user_id": username,
                    "lesson_id": lesson_id,
                    "block_id": block_id,
                    "completed": completed,
                    "created_at": "datetime('now')",
                    "updated_at": "datetime('now')",
                }
                success = insert_row("lesson_progress", progress_data)

            if success:
                logger.info(f"Successfully updated lesson progress for user {username}, lesson {lesson_id}, block {block_id}")
            else:
                logger.error(f"Failed to update lesson progress for user {username}, lesson {lesson_id}, block {block_id}")

            return success

        except ValueError as e:
            logger.error(f"Validation error updating lesson progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating lesson progress for user {username}, lesson {lesson_id}, block {block_id}: {e}")
            return False

    @staticmethod
    def get_lesson_statistics(username: str) -> Dict[str, Any]:
        """
        Get comprehensive lesson statistics for a user.

        Args:
            username: The username to get statistics for

        Returns:
            Dictionary containing lesson statistics

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValueError("Username is required")

            if not user_exists(username):
                raise ValueError(f"User {username} does not exist")

            logger.info(f"Getting lesson statistics for user {username}")

            # Get total lessons available
            total_lessons_result = select_one(
                "lesson_content",
                columns="COUNT(*) as count",
                where="(target_user IS NULL OR target_user = ?) AND published = 1",
                params=(username,),
            )
            total_lessons = total_lessons_result.get("count", 0) if total_lessons_result else 0

            # Get completed lessons
            completed_lessons_result = select_one(
                "lesson_progress",
                columns="COUNT(DISTINCT lesson_id) as count",
                where="user_id = ? AND completed = 1",
                params=(username,),
            )
            completed_lessons = completed_lessons_result.get("count", 0) if completed_lessons_result else 0

            # Get total blocks completed
            total_blocks_result = select_one(
                "lesson_progress",
                columns="COUNT(*) as count",
                where="user_id = ? AND completed = 1",
                params=(username,),
            )
            total_blocks_completed = total_blocks_result.get("count", 0) if total_blocks_result else 0

            # Calculate completion rate
            completion_rate = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0

            # Get recent activity
            recent_activity = select_rows(
                "lesson_progress",
                columns="lesson_id, block_id, updated_at",
                where="user_id = ?",
                params=(username,),
                order_by="updated_at DESC",
                limit=5,
            )

            statistics = {
                "total_lessons": total_lessons,
                "completed_lessons": completed_lessons,
                "total_blocks_completed": total_blocks_completed,
                "completion_rate": round(completion_rate, 2),
                "recent_activity": recent_activity,
                "lessons_in_progress": total_lessons - completed_lessons
            }

            logger.info(f"Retrieved lesson statistics for user {username}: {completed_lessons}/{total_lessons} lessons completed ({completion_rate:.1f}%)")
            return statistics

        except ValueError as e:
            logger.error(f"Validation error getting lesson statistics: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting lesson statistics for user {username}: {e}")
            return {
                "total_lessons": 0,
                "completed_lessons": 0,
                "total_blocks_completed": 0,
                "completion_rate": 0.0,
                "recent_activity": [],
                "lessons_in_progress": 0
            }

    @staticmethod
    def validate_lesson_access(username: str, lesson_id: int) -> bool:
        """
        Validate if a user has access to a lesson.

        Args:
            username: The username to validate access for
            lesson_id: The lesson ID to validate access for

        Returns:
            True if user has access, False otherwise

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not username:
                raise ValueError("Username is required")

            if not lesson_id or lesson_id <= 0:
                raise ValueError("Valid lesson ID is required")

            if not user_exists(username):
                return False

            logger.debug(f"Validating lesson access for user {username}, lesson {lesson_id}")

            # Check if lesson exists and user has access
            lesson = select_one(
                "lesson_content",
                columns="lesson_id",
                where="lesson_id = ? AND (target_user IS NULL OR target_user = ?) AND published = 1",
                params=(lesson_id, username),
            )

            has_access = lesson is not None
            logger.debug(f"Lesson access validation for user {username}, lesson {lesson_id}: {has_access}")
            return has_access

        except ValueError as e:
            logger.error(f"Validation error checking lesson access: {e}")
            raise
        except Exception as e:
            logger.error(f"Error validating lesson access for user {username}, lesson {lesson_id}: {e}")
            return False

    @staticmethod
    def get_lesson_blocks(lesson_id: int) -> List[Dict[str, Any]]:
        """
        Get lesson blocks for a lesson.

        Args:
            lesson_id: The lesson ID to get blocks for

        Returns:
            List of lesson blocks

        Raises:
            ValueError: If lesson_id is invalid
        """
        try:
            if not lesson_id or lesson_id <= 0:
                raise ValueError("Valid lesson ID is required")

            logger.debug(f"Getting lesson blocks for lesson {lesson_id}")

            # Get lesson blocks
            blocks = select_rows(
                "lesson_blocks",
                columns=["block_id", "block_type", "content", "order_index"],
                where="lesson_id = ?",
                params=(lesson_id,),
                order_by="order_index ASC",
            )

            result = [dict(block) for block in blocks] if blocks else []
            logger.debug(f"Retrieved {len(result)} blocks for lesson {lesson_id}")
            return result

        except ValueError as e:
            logger.error(f"Validation error getting lesson blocks: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting lesson blocks for lesson {lesson_id}: {e}")
            return []

    @staticmethod
    def _build_lesson_summary(username: str, lesson_id: int, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a lesson summary with progress information."""
        try:
            # Get user progress for this lesson
            progress = LessonService.get_lesson_progress(username, lesson_id)

            summary = {
                "lesson_id": lesson_id,
                "title": lesson_data["title"],
                "created_at": lesson_data["created_at"],
                "target_user": lesson_data["target_user"],
                "num_blocks": lesson_data["num_blocks"],
                "ai_enabled": bool(lesson_data["ai_enabled"]),
                "progress": {
                    "completed_blocks": progress["completed_blocks"],
                    "total_blocks": progress["total_blocks"],
                    "completion_percentage": progress["completion_percentage"],
                    "is_completed": progress["is_completed"]
                }
            }

            return summary

        except Exception as e:
            logger.error(f"Error building lesson summary for user {username}, lesson {lesson_id}: {e}")
            return {
                "lesson_id": lesson_id,
                "title": lesson_data.get("title", "Unknown"),
                "created_at": lesson_data.get("created_at"),
                "target_user": lesson_data.get("target_user"),
                "num_blocks": lesson_data.get("num_blocks", 0),
                "ai_enabled": bool(lesson_data.get("ai_enabled", False)),
                "progress": {
                    "completed_blocks": 0,
                    "total_blocks": 0,
                    "completion_percentage": 0.0,
                    "is_completed": False
                }
            }
