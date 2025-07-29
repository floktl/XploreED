"""
AI Feedback Routes

This module contains API routes for AI-powered feedback generation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.ai.feedback_helpers import (
    get_feedback_progress,
    generate_feedback_with_progress,
    get_feedback_result,
    get_cached_feedback_list,
    get_cached_feedback_item,
    generate_ai_feedback_simple
)


logger = logging.getLogger(__name__)


@ai_bp.route("/ai-feedback/progress/<session_id>", methods=["GET"])
def get_feedback_progress_route(session_id):
    """
    Get the current progress of AI feedback generation.

    This endpoint allows the frontend to poll for progress updates
    during AI feedback generation.

    Args:
        session_id: The feedback session ID

    Returns:
        JSON response with progress information or error details
    """
    try:
        username = require_user()
        logger.debug(f"Getting feedback progress for user {username}, session {session_id}")

        progress = get_feedback_progress(session_id)

        if "error" in progress:
            return jsonify(progress), 404

        return jsonify(progress)

    except ValueError as e:
        logger.error(f"Validation error getting feedback progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting feedback progress: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback/generate-with-progress", methods=["POST"])
def generate_ai_feedback_with_progress_route():
    """
    Generate AI feedback with progress tracking.

    This endpoint initiates AI feedback generation with real-time progress
    tracking and returns a session ID for progress monitoring.

    Returns:
        JSON response with session ID for progress tracking
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting AI feedback generation with progress")

        data = request.get_json() or {}
        answers = data.get("answers", {})
        exercise_block = data.get("exercise_block")

        if not answers:
            return jsonify({"error": "No answers provided"}), 400

        session_id = generate_feedback_with_progress(str(username), answers, exercise_block)

        logger.info(f"Started feedback generation for user {username}, session {session_id}")
        return jsonify({"session_id": session_id})

    except ValueError as e:
        logger.error(f"Validation error generating feedback with progress: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating feedback with progress: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback/result/<session_id>", methods=["GET"])
def get_feedback_result_route(session_id):
    """
    Get the final result of AI feedback generation.

    This endpoint retrieves the completed feedback result for a given session.

    Args:
        session_id: The feedback session ID

    Returns:
        JSON response with feedback result or error details
    """
    try:
        username = require_user()
        logger.debug(f"Getting feedback result for user {username}, session {session_id}")

        result = get_feedback_result(session_id)

        if "error" in result:
            if result["error"] == "Session not found or not ready":
                return jsonify(result), 404
            elif result["error"] == "Generation not complete":
                return jsonify(result), 400
            else:
                return jsonify(result), 500

        return jsonify(result)

    except ValueError as e:
        logger.error(f"Validation error getting feedback result: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting feedback result: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback", methods=["GET"])
def get_ai_feedback_route():
    """
    Get the list of cached AI feedback entries.

    This endpoint retrieves all cached feedback entries for the user.

    Returns:
        JSON response with list of cached feedback entries
    """
    try:
        username = require_user()
        logger.debug(f"Getting cached feedback list for user {username}")

        feedback_data = get_cached_feedback_list()
        return jsonify(feedback_data)

    except ValueError as e:
        logger.error(f"Validation error getting cached feedback: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting cached feedback: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback/<feedback_id>", methods=["GET"])
def get_ai_feedback_item_route(feedback_id):
    """
    Get a single cached feedback item by ID.

    This endpoint retrieves a specific cached feedback entry by its ID.

    Args:
        feedback_id: The feedback item ID

    Returns:
        JSON response with feedback item or error details
    """
    try:
        username = require_user()
        logger.debug(f"Getting cached feedback item {feedback_id} for user {username}")

        if not feedback_id:
            return jsonify({"error": "Feedback ID is required"}), 400

        item = get_cached_feedback_item(feedback_id)

        if not item:
            return jsonify({"error": "Feedback not found"}), 404

        return jsonify(item)

    except ValueError as e:
        logger.error(f"Validation error getting cached feedback item: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting cached feedback item: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback", methods=["POST"])
def generate_ai_feedback_route():
    """
    Generate AI feedback from submitted exercise results.

    This endpoint generates AI feedback without progress tracking,
    suitable for immediate feedback generation.

    Returns:
        JSON response with generated feedback or error details
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting AI feedback generation")

        data = request.get_json() or {}
        answers = data.get("answers", {})
        exercise_block = data.get("exercise_block")

        if not answers:
            return jsonify({"error": "No answers provided"}), 400

        feedback = generate_ai_feedback_simple(str(username), answers, exercise_block)

        if "error" in feedback:
            return jsonify(feedback), 500

        logger.info(f"Generated feedback for user {username}")
        return jsonify(feedback)

    except ValueError as e:
        logger.error(f"Validation error generating AI feedback: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating AI feedback: {e}")
        return jsonify({"error": "Server error"}), 500
