"""
XplorED - Account Management Module

This module provides account management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Account Management Components:
- Password Management: Update and validate user passwords
- Account Deactivation: Deactivate user accounts and clean up data
- Account Deletion: Debug functions for account deletion
- Security: Password hashing and validation

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


def update_user_password(username: str, current_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Update a user's password with validation.

    Args:
        username: The username to update password for
        current_password: The current password for verification
        new_password: The new password to set

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValidationError("Username is required")

        if not current_password:
            raise ValidationError("Current password is required")

        if not new_password:
            raise ValidationError("New password is required")

        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters long")

        logger.info(f"Updating password for user {username}")

        # Verify current password
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for password update")
            return False, "User not found"

        if not check_password_hash(user_row['password'], current_password):
            logger.warning(f"Invalid current password for user {username}")
            return False, "Incorrect current password"

        # Hash and update new password
        hashed_password = generate_password_hash(new_password)
        success = update_row('users', {'password': hashed_password}, 'username = ?', (username,))

        if success:
            logger.info(f"Successfully updated password for user {username}")
            return True, None
        else:
            logger.error(f"Failed to update password for user {username}")
            return False, "Failed to update password"

    except ValidationError as e:
        logger.error(f"Validation error updating password: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error updating password for user {username}: {e}")
        return False, "Database error"


def deactivate_user_account(username: str) -> Tuple[bool, Optional[str], Dict[str, int]]:
    """
    Deactivate a user account by deleting all associated data.

    Args:
        username: The username to deactivate

    Returns:
        Tuple of (success, error_message, deletion_stats)

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValidationError("Username is required")

        logger.info(f"Deactivating account for user {username}")

        # Verify user exists
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for deactivation")
            return False, "User not found", {}

        deletion_stats = {
            "lesson_progress": 0,
            "exercise_progress": 0,
            "vocabulary_progress": 0,
            "game_progress": 0,
            "support_feedback": 0,
            "support_requests": 0,
            "user_sessions": 0,
            "user_preferences": 0
        }

        # Delete lesson progress
        lesson_deleted = delete_rows("lesson_progress", "WHERE user_id = ?", (username,))
        if lesson_deleted:
            deletion_stats["lesson_progress"] = fetch_one(
                "SELECT COUNT(*) as count FROM lesson_progress WHERE user_id = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM lesson_progress WHERE user_id = ?", (username,)) else 0

        # Delete exercise progress
        exercise_deleted = delete_rows("activity_progress", "WHERE username = ?", (username,))
        if exercise_deleted:
            deletion_stats["exercise_progress"] = fetch_one(
                "SELECT COUNT(*) as count FROM activity_progress WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM activity_progress WHERE username = ?", (username,)) else 0

        # Delete vocabulary progress
        vocab_deleted = delete_rows("vocabulary_progress", "WHERE username = ?", (username,))
        if vocab_deleted:
            deletion_stats["vocabulary_progress"] = fetch_one(
                "SELECT COUNT(*) as count FROM vocabulary_progress WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM vocabulary_progress WHERE username = ?", (username,)) else 0

        # Delete game progress
        game_deleted = delete_rows("game_progress", "WHERE username = ?", (username,))
        if game_deleted:
            deletion_stats["game_progress"] = fetch_one(
                "SELECT COUNT(*) as count FROM game_progress WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM game_progress WHERE username = ?", (username,)) else 0

        # Delete support feedback
        feedback_deleted = delete_rows("support_feedback", "WHERE username = ?", (username,))
        if feedback_deleted:
            deletion_stats["support_feedback"] = fetch_one(
                "SELECT COUNT(*) as count FROM support_feedback WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM support_feedback WHERE username = ?", (username,)) else 0

        # Delete support requests
        requests_deleted = delete_rows("support_requests", "WHERE username = ?", (username,))
        if requests_deleted:
            deletion_stats["support_requests"] = fetch_one(
                "SELECT COUNT(*) as count FROM support_requests WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM support_requests WHERE username = ?", (username,)) else 0

        # Delete user sessions
        sessions_deleted = delete_rows("user_sessions", "WHERE username = ?", (username,))
        if sessions_deleted:
            deletion_stats["user_sessions"] = fetch_one(
                "SELECT COUNT(*) as count FROM user_sessions WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM user_sessions WHERE username = ?", (username,)) else 0

        # Delete user preferences
        preferences_deleted = delete_rows("user_preferences", "WHERE username = ?", (username,))
        if preferences_deleted:
            deletion_stats["user_preferences"] = fetch_one(
                "SELECT COUNT(*) as count FROM user_preferences WHERE username = ?",
                (username,)
            ).get("count", 0) if fetch_one("SELECT COUNT(*) as count FROM user_preferences WHERE username = ?", (username,)) else 0

        # Finally, delete the user account
        user_deleted = delete_rows("users", "WHERE username = ?", (username,))

        if user_deleted:
            total_deleted = sum(deletion_stats.values())
            logger.info(f"Successfully deactivated account for user {username}. Deleted {total_deleted} records.")
            return True, f"Account deactivated. Deleted {total_deleted} records.", deletion_stats
        else:
            logger.error(f"Failed to delete user account for {username}")
            return False, "Failed to delete user account", deletion_stats

    except ValueError as e:
        logger.error(f"Validation error deactivating account: {e}")
        return False, str(e), {}
    except Exception as e:
        logger.error(f"Error deactivating account for user {username}: {e}")
        return False, "Database error", {}


def debug_delete_user_data(username: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Debug function to delete all user data for testing purposes.

    Args:
        username: The username to delete data for

    Returns:
        Tuple of (success, error_message, deleted_tables)

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.warning(f"DEBUG: Deleting all data for user {username}")

        deleted_tables = []
        tables_to_delete = [
            "lesson_progress",
            "activity_progress",
            "vocabulary_progress",
            "game_progress",
            "support_feedback",
            "support_requests",
            "user_sessions",
            "user_preferences",
            "users"
        ]

        for table in tables_to_delete:
            try:
                if table == "users":
                    success = delete_rows(table, "WHERE username = ?", (username,))
                else:
                    success = delete_rows(table, "WHERE username = ?", (username,))

                if success:
                    deleted_tables.append(table)
                    logger.debug(f"DEBUG: Deleted data from {table} for user {username}")
                else:
                    logger.debug(f"DEBUG: No data found in {table} for user {username}")
            except Exception as e:
                logger.error(f"DEBUG: Error deleting from {table} for user {username}: {e}")

        if deleted_tables:
            logger.warning(f"DEBUG: Successfully deleted data from {len(deleted_tables)} tables for user {username}")
            return True, f"Deleted data from {len(deleted_tables)} tables", deleted_tables
        else:
            logger.warning(f"DEBUG: No data found to delete for user {username}")
            return True, "No data found to delete", []

    except ValueError as e:
        logger.error(f"Validation error in debug delete: {e}")
        return False, str(e), []
    except Exception as e:
        logger.error(f"Error in debug delete for user {username}: {e}")
        return False, "Database error", []
