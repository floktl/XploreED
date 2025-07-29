"""
Admin Routes

This module contains API routes for administrative operations including
user management, lesson management, and system monitoring. All business
logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging

from core.services.import_service import *
from features.admin.admin_helpers import (
    get_all_game_results,
    get_user_game_results,
    create_lesson_content,
    get_all_lessons,
    get_lesson_by_id,
    update_lesson_content,
    delete_lesson_content,
    get_lesson_progress_summary,
    get_individual_lesson_progress,
    get_all_users,
    update_user_data,
    delete_user_data
)


logger = logging.getLogger(__name__)


@admin_bp.route("/check-admin", methods=["GET"])
def check_admin():
    """
    Check if the current session belongs to the admin user.

    This endpoint verifies admin privileges for the current session.

    Returns:
        JSON response indicating admin status
    """
    try:
        is_admin_user = is_admin()
        return jsonify({"is_admin": is_admin_user})

    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/results", methods=["GET"])
def admin_results():
    """
    Get all game results for admin review.

    This endpoint retrieves comprehensive game results data
    for administrative monitoring and analysis.

    Returns:
        JSON response with all game results or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        results = get_all_game_results()
        return jsonify(results)

    except Exception as e:
        logger.error(f"Error retrieving admin results: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-content", methods=["POST"])
def insert_lesson_content():
    """
    Create a new lesson with content and block management.

    This endpoint creates a new lesson entry with proper content
    processing, block ID extraction, and database management.

    Returns:
        JSON response with creation status or error details
    """
    try:
        if not is_admin():
            logger.warning("Unauthorized access attempt to insert lesson content")
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json() or {}

        success, error_message = create_lesson_content(data)

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error(f"Error inserting lesson content: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/profile-stats", methods=["POST"])
def profile_stats():
    """
    Get game results for a specific user.

    This endpoint retrieves detailed game performance data
    for a specific user for administrative review.

    Returns:
        JSON response with user game results or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json() or {}
        username = data.get("username", "").strip()

        if not username:
            return jsonify({"error": "Missing username"}), 400

        results = get_user_game_results(username)
        return jsonify(results)

    except ValueError as e:
        logger.error(f"Validation error in profile stats: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting profile stats: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-content", methods=["GET"])
def get_all_lessons():
    """
    Get all lesson content for admin editing.

    This endpoint retrieves all lesson content with metadata
    for administrative management and editing.

    Returns:
        JSON response with all lessons or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        lessons = get_all_lessons()
        return jsonify(lessons)

    except Exception as e:
        logger.error(f"Error retrieving all lessons: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/debug-lessons", methods=["GET"])
def debug_lessons():
    """
    Get raw lesson data without authorization checks.

    This endpoint provides direct access to lesson data
    for debugging purposes without admin verification.

    Returns:
        JSON response with raw lesson data
    """
    try:
        lessons = select_rows("lesson_content")
        return jsonify(lessons)

    except Exception as e:
        logger.error(f"Error in debug lessons: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    """
    Delete a lesson and all related data.

    This endpoint removes a lesson and all associated
    progress records and block data.

    Args:
        lesson_id: The lesson ID to delete

    Returns:
        JSON response with deletion status or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        success, error_message = delete_lesson_content(lesson_id)

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "deleted"}), 200

    except Exception as e:
        logger.error(f"Error deleting lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["GET"])
def get_lesson_by_id(lesson_id):
    """
    Get a specific lesson by ID.

    This endpoint retrieves detailed information about
    a specific lesson for administrative review.

    Args:
        lesson_id: The lesson ID to retrieve

    Returns:
        JSON response with lesson data or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        lesson = get_lesson_by_id(lesson_id)

        if not lesson:
            return jsonify({"error": "not found"}), 404

        return jsonify(lesson)

    except ValueError as e:
        logger.error(f"Validation error getting lesson {lesson_id}: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["PUT"])
def update_lesson_by_id(lesson_id):
    """
    Update an existing lesson with new content and metadata.

    This endpoint updates lesson content with proper block
    management and content processing.

    Args:
        lesson_id: The lesson ID to update

    Returns:
        JSON response with update status or error details
    """
    try:
        if not is_admin():
            logger.warning("Unauthorized access attempt to update lesson")
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json() or {}

        success, error_message = update_lesson_content(lesson_id, data)

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "updated"})

    except Exception as e:
        logger.error(f"Error updating lesson {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-progress-summary", methods=["GET"])
def lesson_progress_summary():
    """
    Get percentage completion summary for all lessons.

    This endpoint provides comprehensive progress statistics
    across all lessons for administrative monitoring.

    Returns:
        JSON response with progress summary or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        summary = get_lesson_progress_summary()
        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error getting lesson progress summary: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_individual_lesson_progress(lesson_id):
    """
    Get per-user completion stats for a specific lesson.

    This endpoint provides detailed user progress data
    for a specific lesson for administrative review.

    Args:
        lesson_id: The lesson ID to get progress for

    Returns:
        JSON response with user progress data or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        progress_data = get_individual_lesson_progress(lesson_id)
        return jsonify(progress_data)

    except ValueError as e:
        logger.error(f"Validation error getting lesson progress {lesson_id}: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting lesson progress {lesson_id}: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/users", methods=["GET"])
def list_users():
    """
    Get a list of all registered users.

    This endpoint retrieves basic information about all
    registered users for administrative management.

    Returns:
        JSON response with user list or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        users = get_all_users()
        return jsonify(users)

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/users/<string:username>", methods=["PUT"])
def update_user(username):
    """
    Update user information including username, password, and skill level.

    This endpoint allows administrators to modify user account
    information with proper validation and data consistency.

    Args:
        username: The current username to update

    Returns:
        JSON response with update status or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json() or {}

        success, error_message = update_user_data(username, data)

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "updated"})

    except Exception as e:
        logger.error(f"Error updating user {username}: {e}")
        return jsonify({"error": "Server error"}), 500


@admin_bp.route("/users/<string:username>", methods=["DELETE"])
def delete_user(username):
    """
    Delete a user account and all associated data.

    This endpoint removes a user account and all related
    data from the system for administrative purposes.

    Args:
        username: The username to delete

    Returns:
        JSON response with deletion status or error details
    """
    try:
        if not is_admin():
            return jsonify({"error": "unauthorized"}), 401

        success, error_message = delete_user_data(username)

        if not success:
            return jsonify({"error": error_message}), 400

        return jsonify({"status": "deleted"})

    except Exception as e:
        logger.error(f"Error deleting user {username}: {e}")
        return jsonify({"error": "Server error"}), 500
