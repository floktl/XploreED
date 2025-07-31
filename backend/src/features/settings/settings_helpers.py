"""
Settings Helper Functions

This module contains helper functions for user settings operations that are used
by the settings routes but should not be in the route files themselves.

Author: XplorED Team
Date: 2025
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


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
            raise ValueError("Username is required")

        if not current_password:
            raise ValueError("Current password is required")

        if not new_password:
            raise ValueError("New password is required")

        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long")

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

    except ValueError as e:
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
            raise ValueError("Username is required")

        logger.info(f"Deactivating account for user {username}")

        # Verify user exists
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for deactivation")
            return False, "User not found", {}

        deletion_stats = {}

        with get_connection() as conn:
            cursor = conn.cursor()

            # Delete AI user data
            cursor.execute("DELETE FROM ai_user_data WHERE username = ?", (username,))
            deletion_stats['ai_user_data'] = cursor.rowcount

            # Delete vocabulary log
            cursor.execute("DELETE FROM vocab_log WHERE username = ?", (username,))
            deletion_stats['vocab_log'] = cursor.rowcount

            # Delete topic memory
            cursor.execute("DELETE FROM topic_memory WHERE username = ?", (username,))
            deletion_stats['topic_memory'] = cursor.rowcount

            # Delete game results
            cursor.execute("DELETE FROM results WHERE username = ?", (username,))
            deletion_stats['results'] = cursor.rowcount

            # Delete exercise submissions
            cursor.execute("DELETE FROM exercise_submissions WHERE username = ?", (username,))
            deletion_stats['exercise_submissions'] = cursor.rowcount

            # Delete lesson progress
            cursor.execute("DELETE FROM lesson_progress WHERE user_id = ?", (username,))
            deletion_stats['lesson_progress'] = cursor.rowcount

            # Delete user account
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            deletion_stats['users'] = cursor.rowcount

            conn.commit()

        # Destroy all user sessions
        from api.middleware.session import session_manager
        session_manager.destroy_user_sessions(username)

        total_deleted = sum(deletion_stats.values())
        logger.info(f"Successfully deactivated account for user {username}. Deleted {total_deleted} records across {len(deletion_stats)} tables")

        return True, None, deletion_stats

    except ValueError as e:
        logger.error(f"Validation error deactivating account: {e}")
        return False, str(e), {}
    except Exception as e:
        logger.error(f"Error deactivating account for user {username}: {e}")
        return False, "Database error", {}


def debug_delete_user_data(username: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Debug function to delete all user data except core account information.

    Args:
        username: The username to delete data for

    Returns:
        Tuple of (success, error_message, affected_tables)

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Debug deleting user data for user {username}")

        # Verify user exists
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for debug data deletion")
            return False, "User not found", []

        affected_tables = []

        with get_connection() as conn:
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Delete data from tables with username or user_id columns
            for table in tables:
                # Skip protected tables
                if table in ('users', 'sessions', 'sqlite_sequence'):
                    continue

                # Check table structure
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]

                # Delete from tables with username column
                if 'username' in columns:
                    cursor.execute(f"DELETE FROM {table} WHERE username = ?", (username,))
                    if cursor.rowcount > 0:
                        affected_tables.append(f"{table} (username)")

                # Delete from tables with user_id column
                elif 'user_id' in columns:
                    cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (username,))
                    if cursor.rowcount > 0:
                        affected_tables.append(f"{table} (user_id)")

            conn.commit()

        logger.info(f"Debug deleted user data for user {username} from {len(affected_tables)} tables")
        return True, None, affected_tables

    except ValueError as e:
        logger.error(f"Validation error debug deleting user data: {e}")
        return False, str(e), []
    except Exception as e:
        logger.error(f"Error debug deleting user data for user {username}: {e}")
        return False, str(e), []


def get_user_settings(username: str) -> Dict[str, Any]:
    """
    Get user settings and preferences.

    Args:
        username: The username to get settings for

    Returns:
        Dictionary containing user settings

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting settings for user {username}")

        # Get user information
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            return {
                "username": username,
                "exists": False,
                "created_at": None,
                "skill_level": 0,
                "preferences": {}
            }

        # Get user preferences (if any preference table exists)
        preferences = _get_user_preferences(username)

        settings = {
            "username": username,
            "exists": True,
            "created_at": user_row.get("created_at"),
            "skill_level": user_row.get("skill_level", 0),
            "preferences": preferences
        }

        logger.info(f"Retrieved settings for user {username}")
        return settings

    except ValueError as e:
        logger.error(f"Validation error getting user settings: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting settings for user {username}: {e}")
        raise


def update_user_settings(username: str, settings_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Update user settings and preferences.

    Args:
        username: The username to update settings for
        settings_data: Dictionary containing settings to update

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not settings_data:
            raise ValueError("Settings data is required")

        logger.info(f"Updating settings for user {username}")

        # Verify user exists
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for settings update")
            return False, "User not found"

        # Update user preferences
        success = _update_user_preferences(username, settings_data)

        if success:
            logger.info(f"Successfully updated settings for user {username}")
            return True, None
        else:
            logger.error(f"Failed to update settings for user {username}")
            return False, "Failed to update settings"

    except ValueError as e:
        logger.error(f"Validation error updating user settings: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error updating settings for user {username}: {e}")
        return False, "Database error"


def get_account_statistics(username: str) -> Dict[str, Any]:
    """
    Get comprehensive account statistics for a user.

    Args:
        username: The username to get statistics for

    Returns:
        Dictionary containing account statistics

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting account statistics for user {username}")

        # Get user information
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            return {
                "username": username,
                "exists": False,
                "account_age_days": 0,
                "data_tables": {},
                "total_records": 0
            }

        # Calculate account age
        created_at = user_row.get("created_at")
        account_age_days = 0
        if created_at:
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                account_age_days = (datetime.now() - created_date).days
            except Exception:
                account_age_days = 0

        # Get data statistics from various tables
        data_tables = {}
        total_records = 0

        tables_to_check = [
            ("ai_user_data", "username"),
            ("vocab_log", "username"),
            ("topic_memory", "username"),
            ("results", "username"),
            ("exercise_submissions", "username"),
            ("lesson_progress", "user_id")
        ]

        for table_name, column_name in tables_to_check:
            try:
                count_row = select_one(
                    table_name,
                    columns="COUNT(*) as count",
                    where=f"{column_name} = ?",
                    params=(username,)
                )
                count = count_row.get("count", 0) if count_row else 0
                data_tables[table_name] = count
                total_records += count
            except Exception as e:
                logger.warning(f"Could not get count for table {table_name}: {e}")
                data_tables[table_name] = 0

        statistics = {
            "username": username,
            "exists": True,
            "account_age_days": account_age_days,
            "data_tables": data_tables,
            "total_records": total_records
        }

        logger.info(f"Retrieved account statistics for user {username}")
        return statistics

    except ValueError as e:
        logger.error(f"Validation error getting account statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting account statistics for user {username}: {e}")
        raise


def _get_user_preferences(username: str) -> Dict[str, Any]:
    """
    Get user preferences from the database.

    Args:
        username: The username to get preferences for

    Returns:
        Dictionary containing user preferences
    """
    try:
        # This is a placeholder implementation
        # In a real application, you would have a preferences table
        return {
            "language": "en",
            "theme": "light",
            "notifications": True,
            "difficulty_level": "medium"
        }
    except Exception as e:
        logger.error(f"Error getting preferences for user {username}: {e}")
        return {}


def _update_user_preferences(username: str, preferences: Dict[str, Any]) -> bool:
    """
    Update user preferences in the database.

    Args:
        username: The username to update preferences for
        preferences: Dictionary containing preferences to update

    Returns:
        True if preferences were updated successfully, False otherwise
    """
    try:
        # This is a placeholder implementation
        # In a real application, you would update a preferences table
        logger.info(f"Updated preferences for user {username}: {preferences}")
        return True
    except Exception as e:
        logger.error(f"Error updating preferences for user {username}: {e}")
        return False


def export_user_data(username: str) -> Optional[Dict[str, Any]]:
    """
    Export all user data for backup or transfer purposes.

    Args:
        username: The username to export data for

    Returns:
        Dictionary containing all user data or None if failed

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Exporting data for user {username}")

        # Verify user exists
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for data export")
            return None

        exported_data = {
            "user_info": {
                "username": user_row.get("username"),
                "created_at": user_row.get("created_at"),
                "skill_level": user_row.get("skill_level", 0)
            },
            "settings": get_user_settings(username),
            "vocabulary": fetch_all('vocab_log', 'WHERE username = ?', (username,)),
            "topic_memory": fetch_all('topic_memory', 'WHERE username = ?', (username,)),
            "exercise_submissions": fetch_all('exercise_submissions', 'WHERE username = ?', (username,)),
            "lesson_progress": fetch_all('lesson_progress', 'WHERE user_id = ?', (username,)),
            "game_results": fetch_all('results', 'WHERE username = ?', (username,)),
            "ai_user_data": fetch_all('ai_user_data', 'WHERE username = ?', (username,)),
            "exported_at": datetime.now().isoformat()
        }

        logger.info(f"Successfully exported data for user {username}")
        return exported_data

    except ValueError as e:
        logger.error(f"Validation error exporting user data: {e}")
        return None
    except Exception as e:
        logger.error(f"Error exporting data for user {username}: {e}")
        return None


def import_user_data(username: str, data: Dict[str, Any]) -> bool:
    """
    Import user data from a previous export.

    Args:
        username: The username to import data for
        data: Dictionary containing exported user data

    Returns:
        True if data was imported successfully, False otherwise

    Raises:
        ValueError: If username or data is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not data:
            raise ValueError("Data is required")

        logger.info(f"Importing data for user {username}")

        # Verify user exists
        user_row = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_row:
            logger.warning(f"User {username} not found for data import")
            return False

        success_count = 0
        total_operations = 0

        # Import vocabulary data
        if "vocabulary" in data and data["vocabulary"]:
            for vocab_item in data["vocabulary"]:
                vocab_item["username"] = username  # Ensure correct username
                if insert_row("vocab_log", vocab_item):
                    success_count += 1
                total_operations += 1

        # Import topic memory data
        if "topic_memory" in data and data["topic_memory"]:
            for topic_item in data["topic_memory"]:
                topic_item["username"] = username  # Ensure correct username
                if insert_row("topic_memory", topic_item):
                    success_count += 1
                total_operations += 1

        # Import exercise submissions
        if "exercise_submissions" in data and data["exercise_submissions"]:
            for submission in data["exercise_submissions"]:
                submission["username"] = username  # Ensure correct username
                if insert_row("exercise_submissions", submission):
                    success_count += 1
                total_operations += 1

        # Import lesson progress
        if "lesson_progress" in data and data["lesson_progress"]:
            for progress in data["lesson_progress"]:
                progress["user_id"] = username  # Ensure correct user_id
                if insert_row("lesson_progress", progress):
                    success_count += 1
                total_operations += 1

        # Import game results
        if "game_results" in data and data["game_results"]:
            for result in data["game_results"]:
                result["username"] = username  # Ensure correct username
                if insert_row("results", result):
                    success_count += 1
                total_operations += 1

        # Import AI user data
        if "ai_user_data" in data and data["ai_user_data"]:
            for ai_data in data["ai_user_data"]:
                ai_data["username"] = username  # Ensure correct username
                if insert_row("ai_user_data", ai_data):
                    success_count += 1
                total_operations += 1

        # Import settings if provided
        if "settings" in data and data["settings"]:
            settings = data["settings"]
            if "preferences" in settings:
                _update_user_preferences(username, settings["preferences"])

        logger.info(f"Successfully imported data for user {username}: {success_count}/{total_operations} operations")
        return success_count > 0

    except ValueError as e:
        logger.error(f"Validation error importing user data: {e}")
        return False
    except Exception as e:
        logger.error(f"Error importing data for user {username}: {e}")
        return False
