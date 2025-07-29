"""
Admin Helper Functions

This module contains helper functions for admin operations that are used
by the admin routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup

from core.services.import_service import *


logger = logging.getLogger(__name__)


def get_all_game_results() -> List[Dict[str, Any]]:
    """
    Retrieve all game results for admin review.

    Returns:
        List of game results with user and performance data

    Raises:
        Exception: If database operations fail
    """
    try:
        logger.info("Retrieving all game results for admin review")

        results = select_rows(
            "results",
            columns=["username", "level", "correct", "answer", "timestamp"],
            order_by="username ASC, timestamp DESC",
        )

        logger.info(f"Retrieved {len(results)} game results")
        return results

    except Exception as e:
        logger.error(f"Error retrieving game results: {e}")
        raise


def get_user_game_results(username: str) -> List[Dict[str, Any]]:
    """
    Get game results for a specific user.

    Args:
        username: The username to get results for

    Returns:
        List of game results for the user

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        username = username.strip()
        if not username:
            raise ValueError("Username cannot be empty")

        logger.info(f"Retrieving game results for user {username}")

        rows = select_rows(
            "results",
            columns=["level", "correct", "answer", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
        )

        results = [
            {
                "level": row["level"],
                "correct": bool(row["correct"]),
                "answer": row["answer"],
                "timestamp": row["timestamp"]
            }
            for row in rows
        ]

        logger.info(f"Retrieved {len(results)} game results for user {username}")
        return results

    except ValueError as e:
        logger.error(f"Validation error getting user game results: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting game results for user {username}: {e}")
        raise


def create_lesson_content(lesson_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
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
        block_ids = {
            el["data-block-id"] for el in soup.select('[data-block-id]')
            if el.has_attr("data-block-id")
        }
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
        return False, "Database error"


def get_all_lessons() -> List[Dict[str, Any]]:
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
        logger.error(f"Error retrieving lessons: {e}")
        raise


def get_lesson_by_id(lesson_id: int) -> Optional[Dict[str, Any]]:
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
        raise


def update_lesson_content(lesson_id: int, lesson_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
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
        block_ids = {
            el["data-block-id"] for el in soup.select('[data-block-id]')
            if el.has_attr("data-block-id")
        }
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
        return False, "Database error"


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
        return False, "Deletion failed"


def get_lesson_progress_summary() -> Dict[int, Dict[str, Any]]:
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

            total_percent = 0
            for user_id in users:
                completed_row = select_one(
                    "lesson_progress",
                    columns="COUNT(*) as count",
                    where="lesson_id = ? AND user_id = ? AND completed = 1",
                    params=(lesson_id, user_id),
                )
                completed = completed_row.get("count") if completed_row else 0
                total_percent += (completed / total_blocks) * 100

            summary[lesson_id] = {
                "percent": round(total_percent / len(users)),
                "num_blocks": total_blocks,
            }

        logger.info(f"Retrieved progress summary for {len(summary)} lessons")
        return summary

    except Exception as e:
        logger.error(f"Error retrieving lesson progress summary: {e}")
        raise


def get_individual_lesson_progress(lesson_id: int) -> List[Dict[str, Any]]:
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
        raise


def get_all_users() -> List[Dict[str, Any]]:
    """
    Get a list of all registered users.

    Returns:
        List of user data with basic information

    Raises:
        Exception: If database operations fail
    """
    try:
        logger.info("Retrieving all registered users")

        rows = select_rows(
            "users",
            columns=["username", "created_at", "skill_level"],
            order_by="username",
        )

        logger.info(f"Retrieved {len(rows)} users")
        return rows

    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise


def update_user_data(username: str, user_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Update user information including username, password, and skill level.

    Args:
        username: The current username
        user_data: Dictionary containing updated user information

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If username or user_data is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not user_data:
            raise ValueError("User data is required")

        logger.info(f"Updating user data for {username}")

        new_username = user_data.get("username", username).strip()
        new_password = user_data.get("password")
        skill_level = user_data.get("skill_level")

        # Check if new username is taken
        if new_username != username and user_exists(new_username):
            logger.warning(f"Username update failed: {new_username} already exists")
            return False, "Username already taken"

        # Update username across all tables if changed
        if new_username != username:
            _update_username_across_tables(username, new_username)
            session_manager.destroy_user_sessions(username)
            username = new_username

        # Update password if provided
        if new_password:
            hashed_password = generate_password_hash(new_password)
            update_row("users", {"password": hashed_password}, "username = ?", (username,))

        # Update skill level if provided
        if skill_level is not None:
            update_row("users", {"skill_level": int(skill_level)}, "username = ?", (username,))

        logger.info(f"Successfully updated user data for {username}")
        return True, None

    except ValueError as e:
        logger.error(f"Validation error updating user data: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error updating user data for {username}: {e}")
        return False, "Database error"


def delete_user_data(username: str) -> Tuple[bool, Optional[str]]:
    """
    Delete a user account and all associated data.

    Args:
        username: The username to delete

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Deleting user data for {username}")

        # Delete all user data from all tables
        delete_rows("results", "WHERE username = ?", (username,))
        delete_rows("vocab_log", "WHERE username = ?", (username,))
        delete_rows("topic_memory", "WHERE username = ?", (username,))
        delete_rows("ai_user_data", "WHERE username = ?", (username,))
        delete_rows("exercise_submissions", "WHERE username = ?", (username,))
        delete_rows("lesson_progress", "WHERE user_id = ?", (username,))
        delete_rows("users", "WHERE username = ?", (username,))

        # Destroy user sessions
        session_manager.destroy_user_sessions(username)

        logger.info(f"Successfully deleted user data for {username}")
        return True, None

    except ValueError as e:
        logger.error(f"Validation error deleting user data: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error deleting user data for {username}: {e}")
        return False, "Database error"


def _update_username_across_tables(old_username: str, new_username: str) -> None:
    """
    Update username across all database tables.

    Args:
        old_username: The old username
        new_username: The new username
    """
    try:
        tables_and_columns = [
            ("users", "username"),
            ("results", "username"),
            ("vocab_log", "username"),
            ("lesson_progress", "user_id"),
            ("topic_memory", "username"),
            ("ai_user_data", "username"),
            ("exercise_submissions", "username"),
        ]

        for table, column in tables_and_columns:
            update_row(table, {column: new_username}, f"{column} = ?", (old_username,))

        logger.info(f"Updated username from {old_username} to {new_username} across all tables")

    except Exception as e:
        logger.error(f"Error updating username across tables: {e}")
        raise
