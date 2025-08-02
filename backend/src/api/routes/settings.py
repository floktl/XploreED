"""
XplorED - User Settings API Routes

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
from infrastructure.imports import Imports
from api.middleware.auth import require_user
from core.database.connection import insert_row, select_one
from config.blueprint import settings_bp
from features.settings import (
    update_user_password,
    deactivate_user_account,
    debug_delete_user_data,
    get_user_settings,
    update_user_settings,
    get_account_statistics,
    export_user_data,
    import_user_data,
    validate_import_data,
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

    JSON Response Structure:
        {
            "preferences": {                       # User preferences
                "username": str,                   # Username
                "language": str,                   # Interface language
                "difficulty": str,                 # Learning difficulty level
                "notifications": bool,             # Notification preferences
                "theme": str,                      # UI theme preference
                "sound_enabled": bool,             # Sound effects setting
                "auto_save": bool,                 # Auto-save preference
                "timezone": str,                   # User timezone
                "date_format": str,                # Date format preference
                "time_format": str,                # Time format preference
                "accessibility": {                 # Accessibility settings
                    "high_contrast": bool,         # High contrast mode
                    "font_size": str,              # Font size preference
                    "screen_reader": bool          # Screen reader support
                },
                "created_at": str,                 # Settings creation timestamp
                "updated_at": str                  # Last update timestamp
            },
            "last_updated": str                    # Last update timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
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

    This endpoint allows users to update their personal preferences
    including language, theme, notifications, and accessibility settings.

    Request Body:
        - language (str, optional): Interface language code
        - theme (str, optional): UI theme (light, dark, auto)
        - sound_enabled (bool, optional): Enable/disable sound effects
        - auto_save (bool, optional): Enable/disable auto-save
        - timezone (str, optional): User timezone
        - date_format (str, optional): Date format preference
        - time_format (str, optional): Time format preference
        - accessibility (object, optional): Accessibility settings

    Accessibility Settings:
        {
            "high_contrast": bool,                 # High contrast mode
            "font_size": str,                      # Font size (small, medium, large)
            "screen_reader": bool                  # Screen reader support
        }

    JSON Response Structure:
        {
            "message": str,                        # Success message
            "preferences": {                       # Updated preferences
                "username": str,                   # Username
                "language": str,                   # Updated language
                "theme": str,                      # Updated theme
                "sound_enabled": bool,             # Updated sound setting
                "auto_save": bool,                 # Updated auto-save setting
                "timezone": str,                   # Updated timezone
                "date_format": str,                # Updated date format
                "time_format": str,                # Updated time format
                "accessibility": object,           # Updated accessibility settings
                "updated_at": str                  # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate theme
        if "theme" in data:
            valid_themes = ["light", "dark", "auto"]
            if data["theme"] not in valid_themes:
                return jsonify({"error": f"Invalid theme: {data['theme']}"}), 400

        # Validate language
        if "language" in data:
            valid_languages = ["en", "de", "es", "fr", "it", "pt", "ru", "ja", "ko", "zh"]
            if data["language"] not in valid_languages:
                return jsonify({"error": f"Invalid language: {data['language']}"}), 400

        # Update user settings
        updated_settings = update_user_settings(user, data)

        return jsonify({
            "message": "Preferences updated successfully",
            "preferences": updated_settings
        })

    except Exception as e:
        logger.error(f"Error updating preferences for user {user}: {e}")
        return jsonify({"error": "Failed to update preferences"}), 500


@settings_bp.route("/learning", methods=["GET"])
def get_learning_settings_route():
    """
    Get user learning settings and preferences.

    This endpoint retrieves educational preferences including
    difficulty levels, learning goals, and study preferences.

    JSON Response Structure:
        {
            "learning_settings": {                 # Learning preferences
                "difficulty": str,                 # Learning difficulty level
                "learning_goals": [str],           # User's learning goals
                "study_preferences": {             # Study preferences
                    "session_duration": int,       # Preferred session duration (minutes)
                    "sessions_per_day": int,       # Preferred sessions per day
                    "break_duration": int,         # Break duration between sessions
                    "preferred_times": [str]       # Preferred study times
                },
                "content_preferences": {           # Content preferences
                    "vocabulary_focus": bool,      # Focus on vocabulary
                    "grammar_focus": bool,         # Focus on grammar
                    "conversation_focus": bool,    # Focus on conversation
                    "reading_focus": bool,         # Focus on reading
                    "writing_focus": bool          # Focus on writing
                },
                "adaptive_learning": {             # Adaptive learning settings
                    "enabled": bool,               # Enable adaptive learning
                    "difficulty_adjustment": str,  # Difficulty adjustment speed
                    "review_frequency": str        # Review frequency preference
                },
                "practice_settings": {             # Practice settings
                    "spaced_repetition": bool,     # Enable spaced repetition
                    "mistake_review": bool,        # Review mistakes
                    "progress_tracking": bool      # Track progress
                }
            },
            "current_level": str,                  # Current skill level
            "target_level": str,                   # Target skill level
            "progress_percentage": float           # Progress toward target
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get learning settings
        learning_settings = get_user_settings(user, "learning")

        if not learning_settings:
            # Create default learning settings
            default_learning_settings = {
                "username": user,
                "difficulty": "medium",
                "learning_goals": ["improve_vocabulary", "master_grammar"],
                "study_preferences": {
                    "session_duration": 30,
                    "sessions_per_day": 2,
                    "break_duration": 5,
                    "preferred_times": ["morning", "evening"]
                },
                "content_preferences": {
                    "vocabulary_focus": True,
                    "grammar_focus": True,
                    "conversation_focus": False,
                    "reading_focus": True,
                    "writing_focus": False
                },
                "adaptive_learning": {
                    "enabled": True,
                    "difficulty_adjustment": "moderate",
                    "review_frequency": "daily"
                },
                "practice_settings": {
                    "spaced_repetition": True,
                    "mistake_review": True,
                    "progress_tracking": True
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            insert_row("user_learning_settings", default_learning_settings)
            learning_settings = default_learning_settings

        # Get current and target levels
        user_progress = select_one(
            "user_progress",
            columns="current_level, target_level, progress_percentage",
            where="username = ?",
            params=(user,)
        )

        return jsonify({
            "learning_settings": learning_settings,
            "current_level": user_progress.get("current_level", "beginner") if user_progress else "beginner",
            "target_level": user_progress.get("target_level", "intermediate") if user_progress else "intermediate",
            "progress_percentage": user_progress.get("progress_percentage", 0.0) if user_progress else 0.0
        })

    except Exception as e:
        logger.error(f"Error getting learning settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve learning settings"}), 500


@settings_bp.route("/learning", methods=["PUT"])
def update_learning_settings_route():
    """
    Update user learning settings and preferences.

    This endpoint allows users to update their educational preferences
    including difficulty levels, learning goals, and study preferences.

    Request Body:
        - difficulty (str, optional): Learning difficulty level
        - learning_goals (array, optional): User's learning goals
        - study_preferences (object, optional): Study preferences
        - content_preferences (object, optional): Content preferences
        - adaptive_learning (object, optional): Adaptive learning settings
        - practice_settings (object, optional): Practice settings

    Valid Difficulty Levels:
        - beginner: Beginner level
        - elementary: Elementary level
        - intermediate: Intermediate level
        - advanced: Advanced level
        - expert: Expert level

    Valid Learning Goals:
        - improve_vocabulary: Improve vocabulary
        - master_grammar: Master grammar
        - improve_pronunciation: Improve pronunciation
        - enhance_conversation: Enhance conversation skills
        - improve_reading: Improve reading comprehension
        - improve_writing: Improve writing skills

    JSON Response Structure:
        {
            "message": str,                        # Success message
            "learning_settings": {                 # Updated learning settings
                "difficulty": str,                 # Updated difficulty level
                "learning_goals": [str],           # Updated learning goals
                "study_preferences": object,       # Updated study preferences
                "content_preferences": object,     # Updated content preferences
                "adaptive_learning": object,       # Updated adaptive learning settings
                "practice_settings": object,       # Updated practice settings
                "updated_at": str                  # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate difficulty level
        if "difficulty" in data:
            valid_difficulties = ["beginner", "elementary", "intermediate", "advanced", "expert"]
            if data["difficulty"] not in valid_difficulties:
                return jsonify({"error": f"Invalid difficulty: {data['difficulty']}"}), 400

        # Validate learning goals
        if "learning_goals" in data:
            valid_goals = [
                "improve_vocabulary", "master_grammar", "improve_pronunciation",
                "enhance_conversation", "improve_reading", "improve_writing"
            ]
            for goal in data["learning_goals"]:
                if goal not in valid_goals:
                    return jsonify({"error": f"Invalid learning goal: {goal}"}), 400

        # Update learning settings
        updated_settings = update_user_settings(user, data, "learning")

        return jsonify({
            "message": "Learning settings updated successfully",
            "learning_settings": updated_settings
        })

    except Exception as e:
        logger.error(f"Error updating learning settings for user {user}: {e}")
        return jsonify({"error": "Failed to update learning settings"}), 500


@settings_bp.route("/notifications", methods=["GET"])
def get_notification_settings_route():
    """
    Get user notification settings and preferences.

    This endpoint retrieves notification preferences including
    email notifications, push notifications, and communication settings.

    JSON Response Structure:
        {
            "notification_settings": {             # Notification preferences
                "email_notifications": {           # Email notification settings
                    "enabled": bool,               # Enable email notifications
                    "daily_summary": bool,         # Daily summary emails
                    "weekly_progress": bool,       # Weekly progress reports
                    "achievement_alerts": bool,    # Achievement notifications
                    "reminder_emails": bool        # Reminder emails
                },
                "push_notifications": {            # Push notification settings
                    "enabled": bool,               # Enable push notifications
                    "lesson_reminders": bool,      # Lesson reminders
                    "achievement_alerts": bool,    # Achievement alerts
                    "streak_reminders": bool,      # Streak reminders
                    "new_content": bool            # New content notifications
                },
                "in_app_notifications": {          # In-app notification settings
                    "enabled": bool,               # Enable in-app notifications
                    "sound_enabled": bool,         # Sound for notifications
                    "vibration_enabled": bool,     # Vibration for notifications
                    "show_badges": bool            # Show notification badges
                },
                "communication_preferences": {     # Communication preferences
                    "marketing_emails": bool,      # Marketing emails
                    "newsletter": bool,            # Newsletter subscription
                    "product_updates": bool,       # Product update notifications
                    "community_updates": bool      # Community update notifications
                }
            },
            "quiet_hours": {                       # Quiet hours settings
                "enabled": bool,                   # Enable quiet hours
                "start_time": str,                 # Quiet hours start time
                "end_time": str,                   # Quiet hours end time
                "timezone": str                    # Timezone for quiet hours
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get notification settings
        notification_settings = get_user_settings(user, "notifications")

        if not notification_settings:
            # Create default notification settings
            default_notification_settings = {
                "username": user,
                "email_notifications": {
                    "enabled": True,
                    "daily_summary": True,
                    "weekly_progress": True,
                    "achievement_alerts": True,
                    "reminder_emails": True
                },
                "push_notifications": {
                    "enabled": True,
                    "lesson_reminders": True,
                    "achievement_alerts": True,
                    "streak_reminders": True,
                    "new_content": True
                },
                "in_app_notifications": {
                    "enabled": True,
                    "sound_enabled": True,
                    "vibration_enabled": False,
                    "show_badges": True
                },
                "communication_preferences": {
                    "marketing_emails": False,
                    "newsletter": True,
                    "product_updates": True,
                    "community_updates": True
                },
                "quiet_hours": {
                    "enabled": False,
                    "start_time": "22:00",
                    "end_time": "08:00",
                    "timezone": "UTC"
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            insert_row("user_notification_settings", default_notification_settings)
            notification_settings = default_notification_settings

        return jsonify({
            "notification_settings": notification_settings
        })

    except Exception as e:
        logger.error(f"Error getting notification settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve notification settings"}), 500


@settings_bp.route("/notifications", methods=["PUT"])
def update_notification_settings_route():
    """
    Update user notification settings and preferences.

    This endpoint allows users to update their notification preferences
    including email, push, and in-app notification settings.

    Request Body:
        - email_notifications (object, optional): Email notification settings
        - push_notifications (object, optional): Push notification settings
        - in_app_notifications (object, optional): In-app notification settings
        - communication_preferences (object, optional): Communication preferences
        - quiet_hours (object, optional): Quiet hours settings

    JSON Response Structure:
        {
            "message": str,                        # Success message
            "notification_settings": {             # Updated notification settings
                "email_notifications": object,     # Updated email settings
                "push_notifications": object,      # Updated push settings
                "in_app_notifications": object,    # Updated in-app settings
                "communication_preferences": object, # Updated communication preferences
                "quiet_hours": object,             # Updated quiet hours
                "updated_at": str                  # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update notification settings
        updated_settings = update_user_settings(user, data, "notifications")

        return jsonify({
            "message": "Notification settings updated successfully",
            "notification_settings": updated_settings
        })

    except Exception as e:
        logger.error(f"Error updating notification settings for user {user}: {e}")
        return jsonify({"error": "Failed to update notification settings"}), 500


@settings_bp.route("/privacy", methods=["GET"])
def get_privacy_settings_route():
    """
    Get user privacy settings and data handling preferences.

    This endpoint retrieves privacy preferences including
    data sharing, analytics, and personal information handling.

    JSON Response Structure:
        {
            "privacy_settings": {                  # Privacy preferences
                "data_sharing": {                  # Data sharing settings
                    "analytics": bool,             # Share analytics data
                    "improvement": bool,           # Share data for improvement
                    "research": bool,              # Share data for research
                    "third_party": bool            # Share with third parties
                },
                "profile_visibility": {            # Profile visibility settings
                    "public_profile": bool,        # Public profile visibility
                    "show_progress": bool,         # Show learning progress
                    "show_achievements": bool,     # Show achievements
                    "show_username": bool          # Show username publicly
                },
                "data_retention": {                # Data retention settings
                    "keep_history": bool,          # Keep learning history
                    "retention_period": str,       # Data retention period
                    "auto_delete": bool,           # Auto-delete old data
                    "export_on_delete": bool       # Export data on account deletion
                },
                "communication_privacy": {         # Communication privacy
                    "allow_messages": bool,        # Allow direct messages
                    "show_online_status": bool,    # Show online status
                    "allow_friend_requests": bool  # Allow friend requests
                }
            },
            "data_usage": {                        # Data usage information
                "data_stored": int,                # Amount of data stored (MB)
                "last_backup": str,                # Last backup timestamp
                "backup_frequency": str            # Backup frequency
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get privacy settings
        privacy_settings = get_user_settings(user, "privacy")

        if not privacy_settings:
            # Create default privacy settings
            default_privacy_settings = {
                "username": user,
                "data_sharing": {
                    "analytics": True,
                    "improvement": True,
                    "research": False,
                    "third_party": False
                },
                "profile_visibility": {
                    "public_profile": False,
                    "show_progress": True,
                    "show_achievements": True,
                    "show_username": False
                },
                "data_retention": {
                    "keep_history": True,
                    "retention_period": "2_years",
                    "auto_delete": False,
                    "export_on_delete": True
                },
                "communication_privacy": {
                    "allow_messages": False,
                    "show_online_status": False,
                    "allow_friend_requests": False
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            insert_row("user_privacy_settings", default_privacy_settings)
            privacy_settings = default_privacy_settings

        # Get data usage information
        data_usage = get_account_statistics(user, "data_usage")

        return jsonify({
            "privacy_settings": privacy_settings,
            "data_usage": data_usage
        })

    except Exception as e:
        logger.error(f"Error getting privacy settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve privacy settings"}), 500


@settings_bp.route("/privacy", methods=["PUT"])
def update_privacy_settings_route():
    """
    Update user privacy settings and data handling preferences.

    This endpoint allows users to update their privacy preferences
    including data sharing, profile visibility, and data retention.

    Request Body:
        - data_sharing (object, optional): Data sharing settings
        - profile_visibility (object, optional): Profile visibility settings
        - data_retention (object, optional): Data retention settings
        - communication_privacy (object, optional): Communication privacy settings

    JSON Response Structure:
        {
            "message": str,                        # Success message
            "privacy_settings": {                  # Updated privacy settings
                "data_sharing": object,            # Updated data sharing settings
                "profile_visibility": object,      # Updated profile visibility
                "data_retention": object,          # Updated data retention
                "communication_privacy": object,   # Updated communication privacy
                "updated_at": str                  # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Update privacy settings
        updated_settings = update_user_settings(user, data, "privacy")

        return jsonify({
            "message": "Privacy settings updated successfully",
            "privacy_settings": updated_settings
        })

    except Exception as e:
        logger.error(f"Error updating privacy settings for user {user}: {e}")
        return jsonify({"error": "Failed to update privacy settings"}), 500


@settings_bp.route("/account", methods=["GET"])
def get_account_settings_route():
    """
    Get user account settings and security preferences.

    This endpoint retrieves account management settings including
    security preferences, account information, and access controls.

    JSON Response Structure:
        {
            "account_settings": {                  # Account settings
                "account_info": {                  # Account information
                    "username": str,               # Username
                    "email": str,                  # Email address
                    "account_created": str,        # Account creation date
                    "last_login": str,             # Last login timestamp
                    "account_status": str          # Account status
                },
                "security_settings": {             # Security settings
                    "two_factor_auth": bool,       # 2FA enabled
                    "password_last_changed": str,  # Password last changed
                    "login_notifications": bool,   # Login notifications
                    "session_timeout": int,        # Session timeout (minutes)
                    "max_sessions": int            # Maximum concurrent sessions
                },
                "access_controls": {               # Access controls
                    "ip_whitelist": [str],         # Allowed IP addresses
                    "device_management": bool,     # Device management enabled
                    "trusted_devices": [str],      # Trusted device list
                    "login_history": [             # Login history
                        {
                            "timestamp": str,      # Login timestamp
                            "ip_address": str,     # IP address
                            "device": str,         # Device information
                            "location": str        # Location information
                        }
                    ]
                }
            },
            "subscription_info": {                 # Subscription information
                "plan": str,                       # Current plan
                "status": str,                     # Subscription status
                "billing_cycle": str,              # Billing cycle
                "next_billing": str,               # Next billing date
                "features": [str]                  # Available features
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get account settings
        account_settings = get_user_settings(user, "account")

        # Get user account information
        user_info = select_one(
            "users",
            columns="username, email, created_at, last_login, status",
            where="username = ?",
            params=(user,)
        )

        # Get security settings
        security_settings = select_one(
            "user_security",
            columns="*",
            where="username = ?",
            params=(user,)
        )

        # Get subscription information
        subscription_info = select_one(
            "user_subscriptions",
            columns="*",
            where="username = ?",
            params=(user,)
        )

        return jsonify({
            "account_settings": {
                "account_info": user_info,
                "security_settings": security_settings or {},
                "access_controls": account_settings.get("access_controls", {})
            },
            "subscription_info": subscription_info or {}
        })

    except Exception as e:
        logger.error(f"Error getting account settings for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve account settings"}), 500


@settings_bp.route("/account", methods=["PUT"])
def update_account_settings_route():
    """
    Update user account settings and security preferences.

    This endpoint allows users to update their account settings
    including security preferences, access controls, and account information.

    Request Body:
        - email (str, optional): New email address
        - security_settings (object, optional): Security settings
        - access_controls (object, optional): Access control settings
        - session_timeout (int, optional): Session timeout in minutes
        - max_sessions (int, optional): Maximum concurrent sessions

    JSON Response Structure:
        {
            "message": str,                        # Success message
            "account_settings": {                  # Updated account settings
                "account_info": object,            # Updated account information
                "security_settings": object,       # Updated security settings
                "access_controls": object,         # Updated access controls
                "updated_at": str                  # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 409: Email already exists
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if email is being updated and if it already exists
        if "email" in data:
            existing_user = select_one(
                "users",
                columns="username",
                where="email = ? AND username != ?",
                params=(data["email"], user)
            )
            if existing_user:
                return jsonify({"error": "Email address already in use"}), 409

        # Update account settings
        updated_settings = update_user_settings(user, data, "account")

        return jsonify({
            "message": "Account settings updated successfully",
            "account_settings": updated_settings
        })

    except Exception as e:
        logger.error(f"Error updating account settings for user {user}: {e}")
        return jsonify({"error": "Failed to update account settings"}), 500


@settings_bp.route("/export", methods=["GET"])
def export_user_data_route():
    """
    Export user data and learning history.

    This endpoint allows users to export their personal data
    including learning progress, settings, and account information.

    Query Parameters:
        - format (str, optional): Export format (json, csv, pdf)
        - include_history (bool, optional): Include learning history
        - include_settings (bool, optional): Include user settings

    JSON Response Structure:
        {
            "export_id": str,                      # Export identifier
            "status": str,                         # Export status
            "download_url": str,                   # Download URL (when ready)
            "estimated_time": int,                 # Estimated completion time (seconds)
            "data_summary": {                      # Data summary
                "total_records": int,              # Total records exported
                "file_size": int,                  # File size in bytes
                "exported_at": str                 # Export timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        export_format = request.args.get("format", "json")
        include_history = request.args.get("include_history", "true").lower() == "true"
        include_settings = request.args.get("include_settings", "true").lower() == "true"

        # Validate export format
        valid_formats = ["json", "csv", "pdf"]
        if export_format not in valid_formats:
            return jsonify({"error": f"Invalid export format: {export_format}"}), 400

        # Export user data
        export_result = export_user_data(
            user,
            format=export_format,
            include_history=include_history,
            include_settings=include_settings
        )

        return jsonify(export_result)

    except Exception as e:
        logger.error(f"Error exporting data for user {user}: {e}")
        return jsonify({"error": "Failed to export user data"}), 500


@settings_bp.route("/import", methods=["POST"])
def import_user_data_route():
    """
    Import user data from external source.

    This endpoint allows users to import their data from
    external sources or previous exports.

    Request Body:
        - file (file, required): Data file to import
        - format (str, required): Import format (json, csv)
        - overwrite_existing (bool, optional): Overwrite existing data

    JSON Response Structure:
        {
            "import_id": str,                      # Import identifier
            "status": str,                         # Import status
            "progress": int,                       # Import progress percentage
            "summary": {                           # Import summary
                "total_records": int,              # Total records imported
                "successful_imports": int,         # Successfully imported records
                "failed_imports": int,             # Failed imports
                "imported_at": str                 # Import timestamp
            },
            "errors": [                            # Import errors
                {
                    "record_id": str,              # Record identifier
                    "error": str,                  # Error message
                    "field": str                   # Field causing error
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 400: Invalid file or format
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Check if file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Get import parameters
        import_format = request.form.get("format", "json")
        overwrite_existing = request.form.get("overwrite_existing", "false").lower() == "true"

        # Validate import format
        valid_formats = ["json", "csv"]
        if import_format not in valid_formats:
            return jsonify({"error": f"Invalid import format: {import_format}"}), 400

        # Validate file content
        validation_result = validate_import_data(file, import_format)
        if not validation_result["valid"]:
            return jsonify({"error": "Invalid file format", "details": validation_result["errors"]}), 400

        # Import user data
        import_result = import_user_data(
            user,
            file,
            format=import_format,
            overwrite_existing=overwrite_existing
        )

        return jsonify(import_result)

    except Exception as e:
        logger.error(f"Error importing data for user {user}: {e}")
        return jsonify({"error": "Failed to import user data"}), 500
