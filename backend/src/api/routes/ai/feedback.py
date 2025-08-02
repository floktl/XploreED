"""
AI Feedback Routes

This module contains API routes for AI-powered feedback generation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging
from typing import Dict, Any

from flask import request, jsonify # type: ignore
from api.middleware.auth import require_user
from config.blueprint import ai_bp
from features.ai.feedback import (
    generate_feedback_with_progress,
    get_feedback_progress,
    get_feedback_result,
    generate_ai_feedback_simple,
    get_cached_feedback_list,
    get_cached_feedback_item,
)


logger = logging.getLogger(__name__)


@ai_bp.route("/ai-feedback/progress/<session_id>", methods=["GET"])
def get_feedback_progress_route(session_id):
    """
    Get the current progress of AI feedback generation.

    This endpoint allows the frontend to poll for progress updates
    during AI feedback generation.

    Path Parameters:
        - session_id (str, required): The feedback session ID

    JSON Response Structure:
        {
            "session_id": str,                   # Feedback session identifier
            "status": str,                       # Generation status (processing, completed, failed)
            "progress": int,                     # Progress percentage (0-100)
            "current_step": str,                 # Current processing step
            "estimated_time": int,               # Estimated time remaining in seconds
            "error": str                         # Error message (if failed)
        }

    Status Codes:
        - 200: Success
        - 400: Invalid session ID
        - 401: Unauthorized
        - 404: Session not found
        - 500: Internal server error
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

    Request Body:
        - answers (object, required): User's exercise answers
        - exercise_block (object, optional): Exercise block metadata
        - feedback_type (str, optional): Type of feedback to generate

    JSON Response Structure:
        {
            "session_id": str,                   # Feedback session identifier
            "message": str,                      # Status message
            "estimated_duration": int            # Estimated generation time in seconds
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
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

    This endpoint retrieves the completed AI feedback results
    once the generation process is finished.

    Path Parameters:
        - session_id (str, required): The feedback session ID

    JSON Response Structure:
        {
            "session_id": str,                   # Feedback session identifier
            "completed": bool,                   # Whether generation is complete
            "feedback": {                        # Generated feedback
                "overall_assessment": str,       # Overall performance assessment
                "strengths": [str],              # Identified strengths
                "weaknesses": [str],             # Areas for improvement
                "recommendations": [str],        # Learning recommendations
                "detailed_feedback": [           # Detailed feedback per exercise
                    {
                        "exercise_id": str,      # Exercise identifier
                        "feedback": str,         # Exercise-specific feedback
                        "score": float,          # Exercise score
                        "suggestions": [str]     # Improvement suggestions
                    }
                ]
            },
            "generated_at": str                  # Generation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Session not found or not completed
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.debug(f"Getting feedback result for user {username}, session {session_id}")

        result = get_feedback_result(session_id)

        if "error" in result:
            return jsonify(result), 404

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
    Get cached AI feedback list for the current user.

    This endpoint retrieves a list of previously generated AI feedback
    sessions for the authenticated user.

    Query Parameters:
        - limit (int, optional): Maximum number of feedback items (default: 10)
        - offset (int, optional): Pagination offset (default: 0)
        - status (str, optional): Filter by feedback status

    JSON Response Structure:
        {
            "feedback_list": [                   # Array of feedback sessions
                {
                    "session_id": str,           # Session identifier
                    "created_at": str,           # Creation timestamp
                    "status": str,               # Feedback status
                    "exercise_count": int,       # Number of exercises
                    "overall_score": float       # Overall performance score
                }
            ],
            "total": int,                        # Total number of feedback sessions
            "limit": int,                        # Requested limit
            "offset": int                        # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.debug(f"Getting AI feedback list for user {username}")

        # Get query parameters
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        status = request.args.get("status")

        feedback_list = get_cached_feedback_list(username, limit, offset, status)

        return jsonify(feedback_list)

    except ValueError as e:
        logger.error(f"Validation error getting AI feedback list: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting AI feedback list: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback/<feedback_id>", methods=["GET"])
def get_ai_feedback_item_route(feedback_id):
    """
    Get a specific AI feedback item by ID.

    This endpoint retrieves detailed information about a specific
    AI feedback session including the complete feedback content.

    Path Parameters:
        - feedback_id (str, required): The feedback session ID

    JSON Response Structure:
        {
            "feedback_id": str,                  # Feedback session identifier
            "user": str,                         # User identifier
            "created_at": str,                   # Creation timestamp
            "completed_at": str,                 # Completion timestamp
            "status": str,                       # Feedback status
            "exercise_data": {                   # Exercise information
                "exercise_count": int,           # Number of exercises
                "exercise_types": [str],         # Types of exercises
                "difficulty_level": str          # Overall difficulty level
            },
            "feedback_content": {                # Generated feedback content
                "overall_assessment": str,       # Overall performance assessment
                "strengths": [str],              # Identified strengths
                "weaknesses": [str],             # Areas for improvement
                "recommendations": [str],        # Learning recommendations
                "detailed_feedback": [           # Detailed feedback per exercise
                    {
                        "exercise_id": str,      # Exercise identifier
                        "question": str,         # Exercise question
                        "user_answer": str,      # User's answer
                        "correct_answer": str,   # Correct answer
                        "feedback": str,         # Exercise-specific feedback
                        "score": float,          # Exercise score
                        "suggestions": [str]     # Improvement suggestions
                    }
                ]
            },
            "performance_metrics": {             # Performance metrics
                "overall_score": float,          # Overall score
                "accuracy_rate": float,          # Accuracy percentage
                "completion_time": int,          # Time taken in seconds
                "difficulty_rating": float       # Perceived difficulty
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Feedback not found
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.debug(f"Getting AI feedback item {feedback_id} for user {username}")

        feedback_item = get_cached_feedback_item(feedback_id, username)

        if "error" in feedback_item:
            return jsonify(feedback_item), 404

        return jsonify(feedback_item)

    except ValueError as e:
        logger.error(f"Validation error getting AI feedback item: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting AI feedback item: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-feedback", methods=["POST"])
def generate_ai_feedback_route():
    """
    Generate AI feedback for exercise answers.

    This endpoint generates immediate AI feedback for user exercise answers
    without progress tracking. Suitable for quick feedback generation.

    Request Body:
        - answers (object, required): User's exercise answers
        - exercise_block (object, optional): Exercise block metadata
        - feedback_type (str, optional): Type of feedback to generate

    JSON Response Structure:
        {
            "feedback": {                        # Generated feedback
                "overall_assessment": str,       # Overall performance assessment
                "strengths": [str],              # Identified strengths
                "weaknesses": [str],             # Areas for improvement
                "recommendations": [str],        # Learning recommendations
                "detailed_feedback": [           # Detailed feedback per exercise
                    {
                        "exercise_id": str,      # Exercise identifier
                        "feedback": str,         # Exercise-specific feedback
                        "score": float,          # Exercise score
                        "suggestions": [str]     # Improvement suggestions
                    }
                ]
            },
            "performance_summary": {             # Performance summary
                "total_exercises": int,          # Total number of exercises
                "correct_answers": int,          # Number of correct answers
                "accuracy_percentage": float,    # Accuracy percentage
                "overall_score": float           # Overall performance score
            },
            "generated_at": str                  # Generation timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting immediate AI feedback generation")

        data = request.get_json() or {}
        answers = data.get("answers", {})
        exercise_block = data.get("exercise_block")
        feedback_type = data.get("feedback_type", "comprehensive")

        if not answers:
            return jsonify({"error": "No answers provided"}), 400

        feedback = generate_ai_feedback_simple(username, answers, exercise_block, feedback_type)

        if "error" in feedback:
            return jsonify(feedback), 500

        return jsonify(feedback)

    except ValueError as e:
        logger.error(f"Validation error generating AI feedback: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating AI feedback: {e}")
        return jsonify({"error": "Server error"}), 500
