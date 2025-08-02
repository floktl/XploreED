"""
XplorED - User Settings Module

This module provides user settings and preferences management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

User Settings Components:
- Settings Retrieval: Get user settings and preferences
- Settings Updates: Update user settings and preferences
- Account Statistics: Get comprehensive account statistics
- Preferences Management: Manage user learning preferences

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from datetime import datetime
from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


def get_user_settings(username: str) -> Dict[str, Any]:
    """
    Get all settings and preferences for a user.

    Args:
        username: The username to get settings for

    Returns:
        Dictionary containing user settings and preferences

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValidationError("Username is required")

        logger.info(f"Getting settings for user {username}")

        # Get user preferences
        preferences = _get_user_preferences(username)

        # Get user account information
        user_info = fetch_one('users', 'WHERE username = ?', (username,))

        if not user_info:
            logger.warning(f"User {username} not found for settings retrieval")
            return {
                "error": "User not found",
                "preferences": {},
                "account_info": {},
                "statistics": {}
            }

        # Get account statistics
        statistics = get_account_statistics(username)

        settings = {
            "username": username,
            "preferences": preferences,
            "account_info": {
                "created_at": user_info.get("created_at"),
                "last_login": user_info.get("last_login"),
                "is_active": user_info.get("is_active", True)
            },
            "statistics": statistics,
            "retrieved_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Retrieved settings for user {username}")
        return settings

    except ValidationError as e:
        logger.error(f"Validation error getting user settings: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting user settings for {username}: {e}")
        return {
            "username": username,
            "error": str(e),
            "preferences": {},
            "account_info": {},
            "statistics": {}
        }


def update_user_settings(username: str, settings_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Update user settings and preferences.

    Args:
        username: The username to update settings for
        settings_data: Dictionary containing settings to update

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValidationError("Username is required")

        if not settings_data:
            raise ValidationError("Settings data is required")

        logger.info(f"Updating settings for user {username}")

        # Verify user exists
        user_exists = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_exists:
            logger.warning(f"User {username} not found for settings update")
            return False, "User not found"

        success_count = 0
        error_messages = []

        # Update preferences if provided
        if "preferences" in settings_data:
            preferences = settings_data["preferences"]
            if isinstance(preferences, dict):
                pref_success = _update_user_preferences(username, preferences)
                if pref_success:
                    success_count += 1
                else:
                    error_messages.append("Failed to update preferences")

        # Update account settings if provided
        if "account_settings" in settings_data:
            account_settings = settings_data["account_settings"]
            if isinstance(account_settings, dict):
                # Filter out sensitive fields that shouldn't be updated via settings
                safe_settings = {k: v for k, v in account_settings.items()
                               if k not in ["password", "username", "id"]}

                if safe_settings:
                    account_success = update_row('users', safe_settings, 'username = ?', (username,))
                    if account_success:
                        success_count += 1
                    else:
                        error_messages.append("Failed to update account settings")

        if success_count > 0:
            logger.info(f"Successfully updated {success_count} setting categories for user {username}")
            return True, None
        else:
            error_msg = "; ".join(error_messages) if error_messages else "No valid settings to update"
            logger.error(f"Failed to update settings for user {username}: {error_msg}")
            return False, error_msg

    except ValidationError as e:
        logger.error(f"Validation error updating user settings: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error updating user settings for {username}: {e}")
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
            raise ValidationError("Username is required")

        logger.info(f"Getting account statistics for user {username}")

        statistics = {
            "username": username,
            "total_lessons_completed": 0,
            "total_exercises_completed": 0,
            "total_vocabulary_reviews": 0,
            "total_games_played": 0,
            "average_exercise_score": 0.0,
            "learning_streak_days": 0,
            "total_study_time_minutes": 0,
            "favorite_activity": "none",
            "weakest_area": "none",
            "account_age_days": 0,
            "last_activity": None
        }

        # Get lesson progress statistics
        lesson_stats = fetch_one(
            "SELECT COUNT(*) as count FROM lesson_progress WHERE user_id = ? AND completed = 1",
            (username,)
        )
        if lesson_stats:
            statistics["total_lessons_completed"] = lesson_stats.get("count", 0)

        # Get exercise progress statistics
        exercise_stats = fetch_one(
            "SELECT COUNT(*) as count, AVG(completion_percentage) as avg_score FROM activity_progress WHERE username = ? AND activity_type = 'exercise'",
            (username,)
        )
        if exercise_stats:
            statistics["total_exercises_completed"] = exercise_stats.get("count", 0)
            statistics["average_exercise_score"] = round(exercise_stats.get("avg_score", 0), 2)

        # Get vocabulary progress statistics
        vocab_stats = fetch_one(
            "SELECT COUNT(*) as count FROM vocabulary_progress WHERE username = ?",
            (username,)
        )
        if vocab_stats:
            statistics["total_vocabulary_reviews"] = vocab_stats.get("count", 0)

        # Get game progress statistics
        game_stats = fetch_one(
            "SELECT COUNT(*) as count FROM game_progress WHERE username = ?",
            (username,)
        )
        if game_stats:
            statistics["total_games_played"] = game_stats.get("count", 0)

        # Get account age
        user_info = fetch_one('users', 'WHERE username = ?', (username,))
        if user_info and user_info.get("created_at"):
            try:
                created_date = datetime.fromisoformat(user_info["created_at"].replace('Z', '+00:00'))
                current_date = datetime.utcnow()
                account_age = (current_date - created_date).days
                statistics["account_age_days"] = account_age
            except:
                statistics["account_age_days"] = 0

        # Get last activity
        last_activity = fetch_one(
            """
            SELECT MAX(activity_date) as last_activity FROM (
                SELECT updated_at as activity_date FROM lesson_progress WHERE user_id = ?
                UNION ALL
                SELECT completed_at as activity_date FROM activity_progress WHERE username = ?
                UNION ALL
                SELECT reviewed_at as activity_date FROM vocabulary_progress WHERE username = ?
                UNION ALL
                SELECT completed_at as activity_date FROM game_progress WHERE username = ?
            )
            """,
            (username, username, username, username)
        )
        if last_activity and last_activity.get("last_activity"):
            statistics["last_activity"] = last_activity["last_activity"]

        # Determine favorite activity
        activities = {
            "lessons": statistics["total_lessons_completed"],
            "exercises": statistics["total_exercises_completed"],
            "vocabulary": statistics["total_vocabulary_reviews"],
            "games": statistics["total_games_played"]
        }

        if any(activities.values()):
            statistics["favorite_activity"] = max(activities, key=activities.get)

        # Calculate learning streak (simplified)
        if statistics["last_activity"]:
            try:
                last_activity_date = datetime.fromisoformat(statistics["last_activity"].replace('Z', '+00:00'))
                current_date = datetime.utcnow()
                days_since_activity = (current_date - last_activity_date).days

                if days_since_activity <= 1:
                    statistics["learning_streak_days"] = 1
                elif days_since_activity <= 7:
                    statistics["learning_streak_days"] = 3
                elif days_since_activity <= 30:
                    statistics["learning_streak_days"] = 7
                else:
                    statistics["learning_streak_days"] = 0
            except:
                statistics["learning_streak_days"] = 0

        logger.info(f"Generated account statistics for user {username}")
        return statistics

    except ValueError as e:
        logger.error(f"Validation error getting account statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting account statistics for {username}: {e}")
        return {
            "username": username,
            "error": str(e),
            "total_lessons_completed": 0,
            "total_exercises_completed": 0,
            "total_vocabulary_reviews": 0,
            "total_games_played": 0,
            "average_exercise_score": 0.0,
            "learning_streak_days": 0,
            "total_study_time_minutes": 0,
            "favorite_activity": "none",
            "weakest_area": "none",
            "account_age_days": 0,
            "last_activity": None
        }


def _get_user_preferences(username: str) -> Dict[str, Any]:
    """
    Get user preferences from the database.

    Args:
        username: The username to get preferences for

    Returns:
        Dictionary containing user preferences
    """
    try:
        preferences_row = fetch_one('user_preferences', 'WHERE username = ?', (username,))

        if preferences_row:
            return {
                "language": preferences_row.get("language", "en"),
                "difficulty_level": preferences_row.get("difficulty_level", "beginner"),
                "daily_goal": preferences_row.get("daily_goal", 30),
                "notifications_enabled": bool(preferences_row.get("notifications_enabled", True)),
                "sound_enabled": bool(preferences_row.get("sound_enabled", True)),
                "auto_play_audio": bool(preferences_row.get("auto_play_audio", False)),
                "theme": preferences_row.get("theme", "light"),
                "study_reminders": bool(preferences_row.get("study_reminders", True)),
                "email_notifications": bool(preferences_row.get("email_notifications", False))
            }
        else:
            # Return default preferences if none exist
            return {
                "language": "en",
                "difficulty_level": "beginner",
                "daily_goal": 30,
                "notifications_enabled": True,
                "sound_enabled": True,
                "auto_play_audio": False,
                "theme": "light",
                "study_reminders": True,
                "email_notifications": False
            }

    except Exception as e:
        logger.error(f"Error getting user preferences for {username}: {e}")
        return {
            "language": "en",
            "difficulty_level": "beginner",
            "daily_goal": 30,
            "notifications_enabled": True,
            "sound_enabled": True,
            "auto_play_audio": False,
            "theme": "light",
            "study_reminders": True,
            "email_notifications": False
        }


def _update_user_preferences(username: str, preferences: Dict[str, Any]) -> bool:
    """
    Update user preferences in the database.

    Args:
        username: The username to update preferences for
        preferences: Dictionary containing preferences to update

    Returns:
        True if update was successful, False otherwise
    """
    try:
        # Check if preferences record exists
        existing = fetch_one('user_preferences', 'WHERE username = ?', (username,))

        if existing:
            # Update existing preferences
            success = update_row('user_preferences', preferences, 'username = ?', (username,))
        else:
            # Create new preferences record
            preferences_data = {"username": username, **preferences}
            success = insert_row('user_preferences', preferences_data)

        return success

    except Exception as e:
        logger.error(f"Error updating user preferences for {username}: {e}")
        return False
