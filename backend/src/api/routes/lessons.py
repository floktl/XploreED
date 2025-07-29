"""
Lesson Routes

This module contains API routes for lesson management and content delivery.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.lessons.lesson_helpers import (
    get_user_lessons_summary,
    validate_lesson_access
)
from features.lessons.lesson_helpers import get_lesson_content, get_lesson_progress, update_lesson_progress, get_lesson_statistics  # type: ignore


logger = logging.getLogger(__name__)


@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons():
    """
    Get summary information for all published lessons for the current user.

    This endpoint retrieves a comprehensive list of all published lessons
    available to the user, including progress information and completion status.

    Returns:
        JSON response with lesson summaries or error details
    """
    try:
        username = require_user()

        lessons = get_user_lessons_summary(str(username))
        return jsonify(lessons)

    except ValueError as e:
        logger.error(f"Validation error getting lessons: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lessons: {e}")
        return jsonify({"error": "Server error"}), 500


@lessons_bp.route("/lesson/<int:lesson_id>", methods=["GET"])
def get_lesson_content(lesson_id):
    """
    Get HTML content and metadata for a specific lesson.

    This endpoint retrieves the full content of a lesson including
    HTML content, metadata, and access control validation.

    Args:
        lesson_id: The lesson ID to retrieve

    Returns:
        JSON response with lesson content or error details
    """
    try:
        username = require_user()

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        # Validate lesson access
        if not validate_lesson_access(str(username), lesson_id):
            return jsonify({"error": "Lesson not found or access denied"}), 404

        lesson_data = get_lesson_content(str(username), lesson_id)  # type: ignore

        if not lesson_data:
            return jsonify({"error": "Lesson not found"}), 404

        return jsonify(lesson_data)

    except ValueError as e:
        logger.error(f"Validation error getting lesson content: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lesson content for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@lessons_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    """
    Get completion status of each block in a lesson.

    This endpoint retrieves the progress status for all blocks
    within a specific lesson for the current user.

    Args:
        lesson_id: The lesson ID to get progress for

    Returns:
        JSON response with block completion status or error details
    """
    try:
        username = require_user()

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        # Validate lesson access
        if not validate_lesson_access(str(username), lesson_id):
            return jsonify({"error": "Lesson not found or access denied"}), 404

        progress = get_lesson_progress(str(username), lesson_id)  # type: ignore
        return jsonify(progress)

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@lessons_bp.route("/lesson-progress/<int:lesson_id>", methods=["POST"])
def update_lesson_progress(lesson_id):
    """
    Update the completion status of a specific block in a lesson.

    This endpoint allows users to mark blocks as completed or incomplete
    within a lesson, tracking their progress through the content.

    Args:
        lesson_id: The lesson ID to update progress for

    Returns:
        JSON response with update status or error details
    """
    try:
        username = require_user()
        data = request.get_json() or {}

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        block_id = data.get("block_id")
        completed = data.get("completed")

        if not block_id:
            return jsonify({"error": "Block ID is required"}), 400

        if completed is None:
            return jsonify({"error": "Completion status is required"}), 400

        # Validate lesson access
        if not validate_lesson_access(str(username), lesson_id):
            return jsonify({"error": "Lesson not found or access denied"}), 404

        success = update_lesson_progress(str(username), lesson_id, block_id, bool(completed))  # type: ignore

        if not success:
            return jsonify({"error": "Failed to update progress"}), 500

        return jsonify({"status": "updated"})

    except ValueError as e:
        logger.error(f"Validation error updating lesson progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@lessons_bp.route("/lesson-statistics/<int:lesson_id>", methods=["GET"])
def get_lesson_statistics(lesson_id):
    """
    Get comprehensive statistics for a specific lesson.

    This endpoint provides detailed statistics about a user's progress
    through a specific lesson including completion rates and activity data.

    Args:
        lesson_id: The lesson ID to get statistics for

    Returns:
        JSON response with lesson statistics or error details
    """
    try:
        username = require_user()

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        # Validate lesson access
        if not validate_lesson_access(str(username), lesson_id):
            return jsonify({"error": "Lesson not found or access denied"}), 404

        stats = get_lesson_statistics(str(username), lesson_id)  # type: ignore
        return jsonify(stats)

    except ValueError as e:
        logger.error(f"Validation error getting lesson statistics: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lesson statistics for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@lessons_bp.route("/lesson-access/<int:lesson_id>", methods=["GET"])
def check_lesson_access(lesson_id):
    """
    Check if the current user has access to a specific lesson.

    This endpoint validates whether the current user can access
    a specific lesson based on permissions and lesson availability.

    Args:
        lesson_id: The lesson ID to check access for

    Returns:
        JSON response with access status or error details
    """
    try:
        username = require_user()

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        has_access = validate_lesson_access(str(username), lesson_id)

        return jsonify({
            "lesson_id": lesson_id,
            "has_access": has_access,
            "username": username
        })

    except Exception as e:
        logger.error(f"Error checking lesson access for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500
