"""
XplorED - Data Management Module

This module provides data export and import functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Data Management Components:
- Data Export: Export user data in various formats
- Data Import: Import user data from external sources
- Data Validation: Validate imported data integrity
- Data Migration: Handle data format conversions

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
from typing import List, Optional, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from datetime import datetime
from shared.exceptions import ValidationError, DatabaseError
from shared.types import UserData, ValidationResult

logger = logging.getLogger(__name__)


def export_user_data(username: str) -> Optional[UserData]:
    """
    Export all user data in a structured format.

    Args:
        username: The username to export data for

    Returns:
        Dictionary containing all user data or None if export fails

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValidationError("Username is required")

        logger.info(f"Exporting data for user {username}")

        # Verify user exists
        user_info = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_info:
            logger.warning(f"User {username} not found for data export")
            return None

        export_data = {
            "export_info": {
                "username": username,
                "export_date": datetime.utcnow().isoformat(),
                "export_version": "1.0",
                "platform": "XplorED"
            },
            "user_profile": {
                "username": user_info.get("username"),
                "created_at": user_info.get("created_at"),
                "last_login": user_info.get("last_login"),
                "is_active": user_info.get("is_active", True)
            },
            "preferences": {},
            "progress_data": {},
            "activity_data": {},
            "support_data": {}
        }

        # Export user preferences
        preferences = fetch_one('user_preferences', 'WHERE username = ?', (username,))
        if preferences:
            export_data["preferences"] = {
                "language": preferences.get("language", "en"),
                "difficulty_level": preferences.get("difficulty_level", "beginner"),
                "daily_goal": preferences.get("daily_goal", 30),
                "notifications_enabled": bool(preferences.get("notifications_enabled", True)),
                "sound_enabled": bool(preferences.get("sound_enabled", True)),
                "auto_play_audio": bool(preferences.get("auto_play_audio", False)),
                "theme": preferences.get("theme", "light"),
                "study_reminders": bool(preferences.get("study_reminders", True)),
                "email_notifications": bool(preferences.get("email_notifications", False))
            }

        # Export lesson progress
        lesson_progress = fetch_all(
            "SELECT * FROM lesson_progress WHERE user_id = ?",
            (username,)
        )
        if lesson_progress:
            export_data["progress_data"]["lesson_progress"] = [
                {
                    "lesson_id": row.get("lesson_id"),
                    "block_id": row.get("block_id"),
                    "completed": bool(row.get("completed", 0)),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at")
                }
                for row in lesson_progress
            ]

        # Export exercise progress
        exercise_progress = fetch_all(
            "SELECT * FROM activity_progress WHERE username = ? AND activity_type = 'exercise'",
            (username,)
        )
        if exercise_progress:
            export_data["progress_data"]["exercise_progress"] = [
                {
                    "block_id": row.get("block_id"),
                    "score": row.get("score"),
                    "total_questions": row.get("total_questions"),
                    "completion_percentage": row.get("completion_percentage"),
                    "completed_at": row.get("completed_at")
                }
                for row in exercise_progress
            ]

        # Export vocabulary progress
        vocab_progress = fetch_all(
            "SELECT * FROM vocabulary_progress WHERE username = ?",
            (username,)
        )
        if vocab_progress:
            export_data["progress_data"]["vocabulary_progress"] = [
                {
                    "word": row.get("word"),
                    "correct": bool(row.get("correct", 0)),
                    "repetitions": row.get("repetitions"),
                    "reviewed_at": row.get("reviewed_at")
                }
                for row in vocab_progress
            ]

        # Export game progress
        game_progress = fetch_all(
            "SELECT * FROM game_progress WHERE username = ?",
            (username,)
        )
        if game_progress:
            export_data["progress_data"]["game_progress"] = [
                {
                    "game_type": row.get("game_type"),
                    "score": row.get("score"),
                    "level": row.get("level"),
                    "completed_at": row.get("completed_at")
                }
                for row in game_progress
            ]

        # Export support feedback
        support_feedback = fetch_all(
            "SELECT * FROM support_feedback WHERE username = ?",
            (username,)
        )
        if support_feedback:
            export_data["support_data"]["feedback"] = [
                {
                    "message": row.get("message"),
                    "created_at": row.get("created_at")
                }
                for row in support_feedback
            ]

        # Export support requests
        support_requests = fetch_all(
            "SELECT * FROM support_requests WHERE username = ?",
            (username,)
        )
        if support_requests:
            export_data["support_data"]["requests"] = [
                {
                    "subject": row.get("subject"),
                    "description": row.get("description"),
                    "urgency": row.get("urgency"),
                    "status": row.get("status"),
                    "created_at": row.get("created_at")
                }
                for row in support_requests
            ]

        # Add summary statistics
        export_data["summary"] = {
            "total_lessons": len(export_data["progress_data"].get("lesson_progress", [])),
            "total_exercises": len(export_data["progress_data"].get("exercise_progress", [])),
            "total_vocabulary_reviews": len(export_data["progress_data"].get("vocabulary_progress", [])),
            "total_games": len(export_data["progress_data"].get("game_progress", [])),
            "total_feedback": len(export_data["support_data"].get("feedback", [])),
            "total_support_requests": len(export_data["support_data"].get("requests", []))
        }

        logger.info(f"Successfully exported data for user {username}")
        return export_data

    except ValueError as e:
        logger.error(f"Validation error exporting user data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error exporting user data for {username}: {e}")
        raise DatabaseError(f"Error exporting user data for {username}: {str(e)}")


def import_user_data(username: str, data: UserData) -> bool:
    """
    Import user data from an exported format.

    Args:
        username: The username to import data for
        data: Dictionary containing user data to import

    Returns:
        True if import was successful, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not username:
            raise ValidationError("Username is required")

        if not data:
            raise ValidationError("Import data is required")

        logger.info(f"Importing data for user {username}")

        # Verify user exists
        user_info = fetch_one('users', 'WHERE username = ?', (username,))
        if not user_info:
            logger.warning(f"User {username} not found for data import")
            return False

        # Validate export data structure
        if not isinstance(data, dict) or "export_info" not in data:
            logger.error(f"Invalid export data format for user {username}")
            return False

        success_count = 0
        error_count = 0

        # Import preferences
        if "preferences" in data and isinstance(data["preferences"], dict):
            try:
                preferences_data = {"username": username, **data["preferences"]}
                success = insert_row('user_preferences', preferences_data)
                if success:
                    success_count += 1
                    logger.debug(f"Imported preferences for user {username}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to import preferences for user {username}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error importing preferences for user {username}: {e}")

        # Import progress data
        if "progress_data" in data and isinstance(data["progress_data"], dict):
            progress_data = data["progress_data"]

            # Import lesson progress
            if "lesson_progress" in progress_data and isinstance(progress_data["lesson_progress"], list):
                for lesson_progress in progress_data["lesson_progress"]:
                    try:
                        lesson_data = {
                            "user_id": username,
                            "lesson_id": lesson_progress.get("lesson_id"),
                            "block_id": lesson_progress.get("block_id"),
                            "completed": int(lesson_progress.get("completed", False)),
                            "created_at": lesson_progress.get("created_at", datetime.utcnow().isoformat()),
                            "updated_at": lesson_progress.get("updated_at", datetime.utcnow().isoformat())
                        }
                        success = insert_row('lesson_progress', lesson_data)
                        if success:
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing lesson progress for user {username}: {e}")

            # Import exercise progress
            if "exercise_progress" in progress_data and isinstance(progress_data["exercise_progress"], list):
                for exercise_progress in progress_data["exercise_progress"]:
                    try:
                        exercise_data = {
                            "username": username,
                            "block_id": exercise_progress.get("block_id"),
                            "score": exercise_progress.get("score"),
                            "total_questions": exercise_progress.get("total_questions"),
                            "completion_percentage": exercise_progress.get("completion_percentage"),
                            "completed_at": exercise_progress.get("completed_at", datetime.utcnow().isoformat()),
                            "activity_type": "exercise"
                        }
                        success = insert_row('activity_progress', exercise_data)
                        if success:
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing exercise progress for user {username}: {e}")

            # Import vocabulary progress
            if "vocabulary_progress" in progress_data and isinstance(progress_data["vocabulary_progress"], list):
                for vocab_progress in progress_data["vocabulary_progress"]:
                    try:
                        vocab_data = {
                            "username": username,
                            "word": vocab_progress.get("word"),
                            "correct": int(vocab_progress.get("correct", False)),
                            "repetitions": vocab_progress.get("repetitions", 1),
                            "reviewed_at": vocab_progress.get("reviewed_at", datetime.utcnow().isoformat())
                        }
                        success = insert_row('vocabulary_progress', vocab_data)
                        if success:
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing vocabulary progress for user {username}: {e}")

            # Import game progress
            if "game_progress" in progress_data and isinstance(progress_data["game_progress"], list):
                for game_progress in progress_data["game_progress"]:
                    try:
                        game_data = {
                            "username": username,
                            "game_type": game_progress.get("game_type"),
                            "score": game_progress.get("score"),
                            "level": game_progress.get("level"),
                            "completed_at": game_progress.get("completed_at", datetime.utcnow().isoformat())
                        }
                        success = insert_row('game_progress', game_data)
                        if success:
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing game progress for user {username}: {e}")

        # Import support data
        if "support_data" in data and isinstance(data["support_data"], dict):
            support_data = data["support_data"]

            # Import feedback
            if "feedback" in support_data and isinstance(support_data["feedback"], list):
                for feedback in support_data["feedback"]:
                    try:
                        feedback_data = {
                            "username": username,
                            "message": feedback.get("message"),
                            "created_at": feedback.get("created_at", datetime.utcnow().isoformat())
                        }
                        success = insert_row('support_feedback', feedback_data)
                        if success:
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing feedback for user {username}: {e}")

            # Import support requests
            if "requests" in support_data and isinstance(support_data["requests"], list):
                for request in support_data["requests"]:
                    try:
                        request_data = {
                            "username": username,
                            "subject": request.get("subject"),
                            "description": request.get("description"),
                            "urgency": request.get("urgency", "medium"),
                            "status": request.get("status", "pending"),
                            "created_at": request.get("created_at", datetime.utcnow().isoformat()),
                            "updated_at": request.get("created_at", datetime.utcnow().isoformat())
                        }
                        success = insert_row('support_requests', request_data)
                        if success:
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing support request for user {username}: {e}")

        if success_count > 0:
            logger.info(f"Successfully imported {success_count} data records for user {username}")
            if error_count > 0:
                logger.warning(f"Failed to import {error_count} data records for user {username}")
            return True
        else:
            logger.error(f"Failed to import any data for user {username}")
            return False

    except ValidationError as e:
        logger.error(f"Validation error importing user data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error importing user data for {username}: {e}")
        raise DatabaseError(f"Error importing user data for {username}: {str(e)}")


def validate_import_data(data: UserData) -> ValidationResult:
    """
    Validate the structure and content of import data.

    Args:
        data: Dictionary containing data to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Raises:
        ValueError: If data is invalid
    """
    try:
        if not data:
            raise ValidationError("Data is required")

        errors = []

        # Check required top-level keys
        required_keys = ["export_info"]
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")

        # Validate export info
        if "export_info" in data:
            export_info = data["export_info"]
            if not isinstance(export_info, dict):
                errors.append("export_info must be a dictionary")
            else:
                if "username" not in export_info:
                    errors.append("export_info missing username")
                if "export_date" not in export_info:
                    errors.append("export_info missing export_date")

        # Validate progress data structure
        if "progress_data" in data:
            progress_data = data["progress_data"]
            if not isinstance(progress_data, dict):
                errors.append("progress_data must be a dictionary")
            else:
                valid_progress_types = ["lesson_progress", "exercise_progress", "vocabulary_progress", "game_progress"]
                for progress_type in progress_data:
                    if progress_type not in valid_progress_types:
                        errors.append(f"Invalid progress type: {progress_type}")
                    elif not isinstance(progress_data[progress_type], list):
                        errors.append(f"{progress_type} must be a list")

        # Validate support data structure
        if "support_data" in data:
            support_data = data["support_data"]
            if not isinstance(support_data, dict):
                errors.append("support_data must be a dictionary")
            else:
                valid_support_types = ["feedback", "requests"]
                for support_type in support_data:
                    if support_type not in valid_support_types:
                        errors.append(f"Invalid support type: {support_type}")
                    elif not isinstance(support_data[support_type], list):
                        errors.append(f"{support_type} must be a list")

        is_valid = len(errors) == 0
        return is_valid, errors

    except Exception as e:
        return False, [f"Validation error: {str(e)}"]
