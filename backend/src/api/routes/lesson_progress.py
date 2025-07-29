"""
Lesson Progress Routes

This module contains API routes for tracking and managing lesson progress.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.lessons.lesson_progress_helpers import (
    get_user_lesson_progress,
    update_block_progress,
    check_lesson_completion_status,
    get_lesson_progress_summary,
    reset_lesson_progress
)
from features.lessons.lesson_progress_helpers import mark_lesson_complete, mark_lesson_as_completed  # type: ignore


logger = logging.getLogger(__name__)


@lesson_progress_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    """
    Get completion status for each block in a lesson.

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

        progress = get_user_lesson_progress(str(username), lesson_id)
        return jsonify(progress), 200

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@lesson_progress_bp.route("/lesson-progress", methods=["POST"])
def update_lesson_progress():
    """
    Mark a single lesson block as completed or not.

    This endpoint allows users to update the completion status
    of individual blocks within a lesson.

    Returns:
        JSON response with update status or error details
    """
    try:
        username = require_user()
        data = request.get_json() or {}

        lesson_id = data.get("lesson_id")
        block_id = data.get("block_id")
        completed = data.get("completed", False)

        if not lesson_id or not block_id:
            return jsonify({"error": "Missing lesson_id or block_id"}), 400

        try:
            lesson_id = int(lesson_id)
            block_id = str(block_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid lesson_id or block_id format"}), 400

        if lesson_id <= 0:
            return jsonify({"error": "Lesson ID must be greater than 0"}), 400

        success = update_block_progress(str(username), lesson_id, block_id, bool(completed))

        if not success:
            return jsonify({"error": "Failed to update progress"}), 500

        return jsonify({"status": "success"}), 200

    except ValueError as e:
        logger.error(f"Validation error updating lesson progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating lesson progress: {e}")
        return jsonify({"error": "Server error"}), 500


@lesson_progress_bp.route("/lesson-progress-complete", methods=["POST"])
def mark_lesson_complete():
    """
    Confirm that a lesson is fully completed.

    This endpoint verifies that all blocks in a lesson are completed
    and marks the lesson as fully complete.

    Returns:
        JSON response with completion status or error details
    """
    try:
        username = require_user()
        data = request.get_json() or {}

        if not data or "lesson_id" not in data:
            return jsonify({"error": "Missing lesson_id in request"}), 400

        try:
            lesson_id = int(data.get("lesson_id") or 0)
        except (TypeError, ValueError) as e:
            logger.error(f"Error parsing lesson_id: {e}")
            return jsonify({"error": "Invalid lesson ID"}), 400

        if lesson_id <= 0:
            logger.warning(f"Invalid lesson_id: {lesson_id}")
            return jsonify({"error": "Lesson ID must be greater than 0"}), 400

        success, error_message = mark_lesson_complete(str(username), lesson_id)  # type: ignore

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "lesson confirmed complete"}), 200

    except Exception as e:
        logger.error(f"Error marking lesson complete: {e}")
        return jsonify({"error": "Server error"}), 500


@lesson_progress_bp.route("/lesson-completed", methods=["POST"])
def check_lesson_marked_complete():
    """
    Check if a lesson is marked as completed for the current user.

    This endpoint verifies the completion status of a lesson
    and returns detailed progress information.

    Returns:
        JSON response with completion status and details or error details
    """
    try:
        username = require_user()
        data = request.get_json() or {}

        try:
            lesson_id = int(data.get("lesson_id") or 0)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid lesson ID"}), 400

        if lesson_id <= 0:
            return jsonify({"error": "Lesson ID must be greater than 0"}), 400

        status = check_lesson_completion_status(str(username), lesson_id)
        return jsonify(status)

    except ValueError as e:
        logger.error(f"Validation error checking lesson completion: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error checking lesson completion: {e}")
        return jsonify({"error": "Server error"}), 500


@lesson_progress_bp.route("/mark-as-completed", methods=["POST"])
def mark_lesson_as_completed():
    """
    Mark an entire lesson as completed and record results.

    This endpoint marks a lesson as completed and records the result
    in the results table for tracking purposes.

    Returns:
        JSON response with completion status or error details
    """
    try:
        username = require_user()
        data = request.get_json() or {}

        lesson_id = data.get("lesson_id")

        if not lesson_id:
            return jsonify({"error": "Missing lesson_id"}), 400

        try:
            lesson_id = int(lesson_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid lesson ID format"}), 400

        if lesson_id <= 0:
            return jsonify({"error": "Lesson ID must be greater than 0"}), 400

        success, error_message = mark_lesson_as_completed(str(username), lesson_id)  # type: ignore

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "completed"}), 200

    except Exception as e:
        logger.error(f"Error marking lesson as completed: {e}")
        return jsonify({"error": "Server error"}), 500


@lesson_progress_bp.route("/progress-summary/<int:lesson_id>", methods=["GET"])
def get_progress_summary(lesson_id):
    """
    Get comprehensive progress summary for a lesson.

    This endpoint provides detailed progress information including
    completion rates, activity timestamps, and overall status.

    Args:
        lesson_id: The lesson ID to get summary for

    Returns:
        JSON response with progress summary or error details
    """
    try:
        username = require_user()

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        summary = get_lesson_progress_summary(str(username), lesson_id)
        return jsonify(summary)

    except ValueError as e:
        logger.error(f"Validation error getting progress summary: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting progress summary for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@lesson_progress_bp.route("/reset-progress/<int:lesson_id>", methods=["POST"])
def reset_progress(lesson_id):
    """
    Reset all progress for a specific lesson.

    This endpoint allows users to reset their progress for a lesson,
    clearing all completion records and starting fresh.

    Args:
        lesson_id: The lesson ID to reset progress for

    Returns:
        JSON response with reset status or error details
    """
    try:
        username = require_user()

        if not lesson_id or lesson_id <= 0:
            return jsonify({"error": "Valid lesson ID is required"}), 400

        success = reset_lesson_progress(str(username), lesson_id)

        if not success:
            return jsonify({"error": "Failed to reset progress"}), 500

        return jsonify({"status": "progress reset"}), 200

    except ValueError as e:
        logger.error(f"Validation error resetting progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error resetting progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500

