"""
XplorED - Admin User Management Module

This module provides user management functions for admin operations,
following clean architecture principles as outlined in the documentation.

User Management Components:
- User Data: Retrieval and management of user information
- Account Operations: User account creation, updates, and deletion
- Session Management: User session handling and cleanup
- Data Synchronization: Cross-table username updates and data consistency

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from core.database.connection import select_rows, update_row, delete_rows
from core.authentication import user_exists
from werkzeug.security import generate_password_hash  # type: ignore

logger = logging.getLogger(__name__)


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
            from api.middleware.session import session_manager
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
        from api.middleware.session import session_manager
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
