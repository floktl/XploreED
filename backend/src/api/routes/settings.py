"""
German Class Tool - User Settings API Routes

This module contains API routes for user settings management and preferences,
following clean architecture principles as outlined in the documentation.

Route Categories:
- User Preferences: Personal settings and customization
- Learning Settings: Educational preferences and difficulty levels
- Notification Settings: Communication preferences
- Privacy Settings: Data handling and privacy controls
- Account Settings: Account management and security

Settings Features:
- Personalized learning experience configuration
- Notification and communication preferences
- Privacy and data handling controls
- Account security and management options

Business Logic:
All settings logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from flask import request, jsonify # type: ignore
from datetime import datetime
from core.services.import_service import *
from core.utils.helpers import require_user
from core.database.connection import insert_row, select_one
from config.blueprint import settings_bp
from features.settings.settings_helpers import (
    get_user_settings,
    update_user_settings,
    update_user_password,
    deactivate_user_account,
    get_account_statistics,
    export_user_data,
    import_user_data
)


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === User Preferences Routes ===
@settings_bp.route("/preferences", methods=["GET"])
def get_user_preferences_route():
    """
    Get user preferences and settings.

    This endpoint retrieves all user preferences including learning
    settings, notification preferences, and personal customization options.

    Returns:
        JSON response with user preferences or unauthorized error
    """
    try:
        user = require_user()

        # Get user settings
        settings = get_user_settings(user)

        if not settings:
            # Create default settings if none exist
            default_settings = {
                "username": user,
                "language": "en",
                "difficulty": "medium",
                "notifications": True,
                "theme": "light",
                "sound_enabled": True,
                "auto_save": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            insert_row("user_settings", default_settings)
            settings = default_settings

        return jsonify({
            "preferences": settings,
            "last_updated": settings.get("updated_at")
        })

    except Exception as e:
        logger.error(f"Error getting preferences for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve preferences"}), 500


@settings_bp.route("/preferences", methods=["PUT"])
def update_user_preferences_route():
    """
    Update user preferences and settings.

    This endpoint allows users to modify their preferences including
    learning settings, notification preferences, and personal customization.

    Request Body:
        - language: Interface language preference
        - difficulty: Learning difficulty level
        - notifications: Notification preferences
        - theme: UI theme preference
        - sound_enabled: Sound effects toggle
        - auto_save: Auto-save functionality toggle

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate and prepare settings update
        valid_settings = {}

        # Language preference
        if "language" in data:
            language = data["language"]
            valid_languages = ["en", "de", "es", "fr", "it"]
            if language in valid_languages:
                valid_settings["language"] = language
            else:
                return jsonify({"error": f"Invalid language: {language}"}), 400

        # Difficulty level
        if "difficulty" in data:
            difficulty = data["difficulty"]
            valid_difficulties = ["beginner", "medium", "advanced", "expert"]
            if difficulty in valid_difficulties:
                valid_settings["difficulty"] = difficulty
            else:
                return jsonify({"error": f"Invalid difficulty: {difficulty}"}), 400

        # Notification settings
        if "notifications" in data:
            valid_settings["notifications"] = bool(data["notifications"])

        # Theme preference
        if "theme" in data:
            theme = data["theme"]
            valid_themes = ["light", "dark", "auto"]
            if theme in valid_themes:
                valid_settings["theme"] = theme
            else:
                return jsonify({"error": f"Invalid theme: {theme}"}), 400

        # Sound settings
        if "sound_enabled" in data:
            valid_settings["sound_enabled"] = bool(data["sound_enabled"])

        # Auto-save setting
        if "auto_save" in data:
            valid_settings["auto_save"] = bool(data["auto_save"])

        if not valid_settings:
            return jsonify({"error": "No valid settings provided"}), 400

        # Add timestamp
        valid_settings["updated_at"] = datetime.now().isoformat()

        # Update settings
        success = update_user_settings(user, valid_settings)

        if success:
            return jsonify({
                "message": "Preferences updated successfully",
                "updated_settings": valid_settings
            })
        else:
            return jsonify({"error": "Failed to update preferences"}), 500

    except Exception as e:
        logger.error(f"Error updating preferences for user {user}: {e}")
        return jsonify({"error": "Failed to update preferences"}), 500


# === Learning Settings Routes ===
@settings_bp.route("/learning", methods=["GET"])
def get_learning_settings_route():
    """
    Get user learning preferences and educational settings.

    This endpoint retrieves learning-specific settings including
    difficulty levels, study preferences, and educational goals.

    Returns:
        JSON response with learning settings or unauthorized error
    """
    try:
        user = require_user()

        # Get learning-specific settings
        learning_settings = select_one(
            "user_settings",
            columns="difficulty, study_duration, daily_goal, review_frequency, grammar_focus, vocab_focus",
            where="username = ?",
            params=(user,)
        )

        if not learning_settings:
            # Return default learning settings
            return jsonify({
                "difficulty": "medium",
                "study_duration": 30,
                "daily_goal": 10,
                "review_frequency": "daily",
                "grammar_focus": True,
                "vocab_focus": True
            })

        return jsonify(learning_settings)

    except Exception as e:
        logger.error(f"Error getting learning settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve learning settings"}), 500


@settings_bp.route("/learning", methods=["PUT"])
def update_learning_settings_route():
    """
    Update user learning preferences and educational settings.

    This endpoint allows users to modify their learning preferences
    including study duration, daily goals, and focus areas.

    Request Body:
        - study_duration: Daily study duration in minutes
        - daily_goal: Daily learning goal (exercises/words)
        - review_frequency: How often to review learned content
        - grammar_focus: Focus on grammar exercises
        - vocab_focus: Focus on vocabulary learning

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate learning settings
        updates = {}

        if "study_duration" in data:
            duration = int(data["study_duration"])
            if 5 <= duration <= 180:
                updates["study_duration"] = duration
            else:
                return jsonify({"error": "Study duration must be between 5 and 180 minutes"}), 400

        if "daily_goal" in data:
            goal = int(data["daily_goal"])
            if 1 <= goal <= 100:
                updates["daily_goal"] = goal
            else:
                return jsonify({"error": "Daily goal must be between 1 and 100"}), 400

        if "review_frequency" in data:
            frequency = data["review_frequency"]
            valid_frequencies = ["daily", "weekly", "biweekly", "monthly"]
            if frequency in valid_frequencies:
                updates["review_frequency"] = frequency
            else:
                return jsonify({"error": f"Invalid review frequency: {frequency}"}), 400

        if "grammar_focus" in data:
            updates["grammar_focus"] = bool(data["grammar_focus"])

        if "vocab_focus" in data:
            updates["vocab_focus"] = bool(data["vocab_focus"])

        if not updates:
            return jsonify({"error": "No valid learning settings provided"}), 400

        # Update learning settings
        success = update_user_settings(user, updates)

        if success:
            return jsonify({
                "message": "Learning settings updated successfully",
                "updated_settings": updates
            })
        else:
            return jsonify({"error": "Failed to update learning settings"}), 500

    except Exception as e:
        logger.error(f"Error updating learning settings for user {user}: {e}")
        return jsonify({"error": "Failed to update learning settings"}), 500


# === Notification Settings Routes ===
@settings_bp.route("/notifications", methods=["GET"])
def get_notification_settings_route():
    """
    Get user notification preferences.

    This endpoint retrieves notification settings including
    email preferences, push notifications, and communication frequency.

    Returns:
        JSON response with notification settings or unauthorized error
    """
    try:
        user = require_user()

        # Get notification settings
        notification_settings = select_one(
            "user_settings",
            columns="notifications, email_notifications, push_notifications, reminder_frequency, study_reminders",
            where="username = ?",
            params=(user,)
        )

        if not notification_settings:
            # Return default notification settings
            return jsonify({
                "notifications": True,
                "email_notifications": False,
                "push_notifications": True,
                "reminder_frequency": "daily",
                "study_reminders": True
            })

        return jsonify(notification_settings)

    except Exception as e:
        logger.error(f"Error getting notification settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve notification settings"}), 500


@settings_bp.route("/notifications", methods=["PUT"])
def update_notification_settings_route():
    """
    Update user notification preferences.

    This endpoint allows users to modify their notification settings
    including email preferences and reminder frequencies.

    Request Body:
        - email_notifications: Enable email notifications
        - push_notifications: Enable push notifications
        - reminder_frequency: How often to send reminders
        - study_reminders: Enable study reminders

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate notification settings
        updates = {}

        if "email_notifications" in data:
            updates["email_notifications"] = bool(data["email_notifications"])

        if "push_notifications" in data:
            updates["push_notifications"] = bool(data["push_notifications"])

        if "reminder_frequency" in data:
            frequency = data["reminder_frequency"]
            valid_frequencies = ["never", "daily", "weekly", "monthly"]
            if frequency in valid_frequencies:
                updates["reminder_frequency"] = frequency
            else:
                return jsonify({"error": f"Invalid reminder frequency: {frequency}"}), 400

        if "study_reminders" in data:
            updates["study_reminders"] = bool(data["study_reminders"])

        if not updates:
            return jsonify({"error": "No valid notification settings provided"}), 400

        # Update notification settings
        success = update_user_settings(user, updates)

        if success:
            return jsonify({
                "message": "Notification settings updated successfully",
                "updated_settings": updates
            })
        else:
            return jsonify({"error": "Failed to update notification settings"}), 500

    except Exception as e:
        logger.error(f"Error updating notification settings for user {user}: {e}")
        return jsonify({"error": "Failed to update notification settings"}), 500


# === Privacy Settings Routes ===
@settings_bp.route("/privacy", methods=["GET"])
def get_privacy_settings_route():
    """
    Get user privacy settings and data handling preferences.

    This endpoint retrieves privacy-related settings including
    data sharing preferences and account visibility options.

    Returns:
        JSON response with privacy settings or unauthorized error
    """
    try:
        user = require_user()

        # Get privacy settings
        privacy_settings = select_one(
            "user_settings",
            columns="data_sharing, profile_visibility, analytics_consent, third_party_data",
            where="username = ?",
            params=(user,)
        )

        if not privacy_settings:
            # Return default privacy settings
            return jsonify({
                "data_sharing": False,
                "profile_visibility": "private",
                "analytics_consent": True,
                "third_party_data": False
            })

        return jsonify(privacy_settings)

    except Exception as e:
        logger.error(f"Error getting privacy settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve privacy settings"}), 500


@settings_bp.route("/privacy", methods=["PUT"])
def update_privacy_settings_route():
    """
    Update user privacy settings and data handling preferences.

    This endpoint allows users to modify their privacy settings
    including data sharing and visibility preferences.

    Request Body:
        - data_sharing: Allow data sharing for research
        - profile_visibility: Profile visibility setting
        - analytics_consent: Consent for analytics tracking
        - third_party_data: Allow third-party data sharing

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate privacy settings
        updates = {}

        if "data_sharing" in data:
            updates["data_sharing"] = bool(data["data_sharing"])

        if "profile_visibility" in data:
            visibility = data["profile_visibility"]
            valid_visibilities = ["private", "friends", "public"]
            if visibility in valid_visibilities:
                updates["profile_visibility"] = visibility
            else:
                return jsonify({"error": f"Invalid profile visibility: {visibility}"}), 400

        if "analytics_consent" in data:
            updates["analytics_consent"] = bool(data["analytics_consent"])

        if "third_party_data" in data:
            updates["third_party_data"] = bool(data["third_party_data"])

        if not updates:
            return jsonify({"error": "No valid privacy settings provided"}), 400

        # Update privacy settings
        success = update_user_settings(user, updates)

        if success:
            return jsonify({
                "message": "Privacy settings updated successfully",
                "updated_settings": updates
            })
        else:
            return jsonify({"error": "Failed to update privacy settings"}), 500

    except Exception as e:
        logger.error(f"Error updating privacy settings for user {user}: {e}")
        return jsonify({"error": "Failed to update privacy settings"}), 500


# === Account Settings Routes ===
@settings_bp.route("/account", methods=["GET"])
def get_account_settings_route():
    """
    Get user account settings and security preferences.

    This endpoint retrieves account-related settings including
    security preferences and account management options.

    Returns:
        JSON response with account settings or unauthorized error
    """
    try:
        user = require_user()

        # Get account settings
        account_settings = select_one(
            "user_settings",
            columns="two_factor_enabled, session_timeout, login_notifications, password_change_required",
            where="username = ?",
            params=(user,)
        )

        if not account_settings:
            # Return default account settings
            return jsonify({
                "two_factor_enabled": False,
                "session_timeout": 24,
                "login_notifications": True,
                "password_change_required": False
            })

        return jsonify(account_settings)

    except Exception as e:
        logger.error(f"Error getting account settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve account settings"}), 500


@settings_bp.route("/account", methods=["PUT"])
def update_account_settings_route():
    """
    Update user account settings and security preferences.

    This endpoint allows users to modify their account settings
    including security features and session management.

    Request Body:
        - two_factor_enabled: Enable two-factor authentication
        - session_timeout: Session timeout in hours
        - login_notifications: Notify on new logins
        - password_change_required: Require password change

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate account settings
        updates = {}

        if "two_factor_enabled" in data:
            updates["two_factor_enabled"] = bool(data["two_factor_enabled"])

        if "session_timeout" in data:
            timeout = int(data["session_timeout"])
            if 1 <= timeout <= 168:  # 1 hour to 1 week
                updates["session_timeout"] = timeout
            else:
                return jsonify({"error": "Session timeout must be between 1 and 168 hours"}), 400

        if "login_notifications" in data:
            updates["login_notifications"] = bool(data["login_notifications"])

        if "password_change_required" in data:
            updates["password_change_required"] = bool(data["password_change_required"])

        if not updates:
            return jsonify({"error": "No valid account settings provided"}), 400

        # Update account settings
        success = update_user_settings(user, updates)

        if success:
            return jsonify({
                "message": "Account settings updated successfully",
                "updated_settings": updates
            })
        else:
            return jsonify({"error": "Failed to update account settings"}), 500

    except Exception as e:
        logger.error(f"Error updating account settings for user {user}: {e}")
        return jsonify({"error": "Failed to update account settings"}), 500


# === Data Management Routes ===
# @settings_bp.route("/reset", methods=["POST"])
# def reset_user_settings_route():
#     """
#     Reset user settings to default values.
#     """
#     # TODO: Implement reset functionality
#     return jsonify({"error": "Not implemented"}), 501


@settings_bp.route("/export", methods=["GET"])
def export_user_data_route():
    """
    Export user data and settings.

    This endpoint allows users to export their data including
    settings, progress, and learning history.

    Returns:
        JSON response with exported data or error details
    """
    try:
        user = require_user()

        # Export user data
        exported_data = export_user_data(user)

        if exported_data:
            return jsonify({
                "message": "Data exported successfully",
                "data": exported_data,
                "exported_at": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to export data"}), 500

    except Exception as e:
        logger.error(f"Error exporting data for user {user}: {e}")
        return jsonify({"error": "Failed to export data"}), 500


@settings_bp.route("/import", methods=["POST"])
def import_user_data_route():
    """
    Import user data and settings.

    This endpoint allows users to import previously exported
    data and settings.

    Request Body:
        - data: Exported user data to import

    Returns:
        JSON response with import status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data or "data" not in data:
            return jsonify({"error": "No data provided for import"}), 400

        # Import user data
        success = import_user_data(user, data["data"])

        if success:
            return jsonify({
                "message": "Data imported successfully",
                "status": "imported"
            })
        else:
            return jsonify({"error": "Failed to import data"}), 500

    except Exception as e:
        logger.error(f"Error importing data for user {user}: {e}")
        return jsonify({"error": "Failed to import data"}), 500
