"""
AI Exercise Routes

This module contains API routes for AI-powered exercise evaluation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging
from typing import Dict, Any

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user, run_in_background
from config.blueprint import ai_bp
from features.exercise import (
    check_gap_fill_correctness,
    parse_submission_data,
    evaluate_first_exercise,
    create_immediate_results,
    evaluate_remaining_exercises_async,
)
from features.ai.evaluation.exercise_evaluator import process_ai_answers


logger = logging.getLogger(__name__)


@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id):
    """
    Evaluate a submitted exercise block and save results.

    This endpoint processes exercise submissions with immediate feedback for the first
    exercise and background processing for the remaining exercises. It supports
    streaming results and topic memory integration.

    Args:
        block_id: The exercise block ID to submit

    Returns:
        JSON response with immediate results and streaming status
    """
    try:
        username = require_user()
        logger.info(f"User {username} submitting exercise block {block_id}")

        data = request.get_json() or {}
        exercises, answers, error = parse_submission_data(data)

        if error:
            logger.error(f"Parse submission data error for user {username}: {error}")
            return jsonify({"error": error}), 400

        logger.info(f"Successfully parsed {len(exercises)} exercises with {len(answers)} answers for user: {username}")

        # Evaluate first exercise immediately for fast feedback
        first_result_with_details = evaluate_first_exercise(exercises, answers)

        # Capture the Flask app before starting background thread
        from flask import current_app # type: ignore
        app = current_app._get_current_object()

        # Start background task to evaluate remaining exercises
        from threading import Thread
        def background_task():
            logger.info("Starting background task for full evaluation and topic memory updates")
            with app.app_context():
                exercise_block = data.get("exercise_block")
                logger.debug(f"Exercise block from data: topic='{exercise_block.get('topic') if exercise_block else 'None'}'")
                if username:  # Ensure username is not None
                    evaluate_remaining_exercises_async(username, block_id, exercises, answers, first_result_with_details, exercise_block)

        Thread(target=background_task, daemon=True).start()

        # Create immediate results
        immediate_results = create_immediate_results(exercises, first_result_with_details)

        logger.info("Returning immediate response, background processing started")
        return jsonify({
            "pass": False,  # Will be updated in background
            "summary": {"correct": 0, "total": len(exercises), "mistakes": []},  # Will be updated in background
            "results": immediate_results,
            "streaming": True  # Flag to indicate this is a streaming response
        })

    except ValueError as e:
        logger.error(f"Validation error submitting AI exercise: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting AI exercise: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-exercise/<block_id>/results", methods=["GET"])
def get_ai_exercise_results(block_id):
    """
    Get the latest results for an exercise block, including alternatives and explanations.

    This endpoint retrieves exercise results from Redis cache, supporting streaming
    updates as background processing completes.

    Args:
        block_id: The exercise block ID to get results for

    Returns:
        JSON response with exercise results and processing status
    """
    try:
        username = require_user()
        logger.debug(f"Getting exercise results for user {username}, block {block_id}")

        if username:  # Ensure username is not None
            results = get_exercise_results(username, block_id)
            return jsonify(results)
        else:
            return jsonify({"error": "User not authenticated"}), 401

    except ValueError as e:
        logger.error(f"Validation error getting exercise results: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting exercise results: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-exercise/<block_id>/argue", methods=["POST"])
def argue_ai_exercise(block_id):
    """
    Reevaluate answers when the student wants to argue with the AI.

    This endpoint allows users to challenge AI evaluations and get re-evaluated
    results with updated topic memory processing.

    Args:
        block_id: The exercise block ID to argue

    Returns:
        JSON response with reevaluation results
    """
    try:
        username = require_user()
        logger.info(f"User {username} arguing exercise evaluation for block {block_id}")

        data = request.get_json() or {}
        answers = data.get("answers", {})
        exercise_block = data.get("exercise_block") or {}
        exercises = exercise_block.get("exercises", [])

        if not exercises:
            return jsonify({"error": "No exercises provided"}), 400

        if not answers:
            return jsonify({"error": "No answers provided"}), 400

        evaluation = argue_exercise_evaluation(block_id, exercises, answers, exercise_block)

        if "error" in evaluation:
            return jsonify({"error": evaluation["error"]}), 500

        # Update topic memory asynchronously with the reevaluated results
        run_in_background(
            process_ai_answers,
            username,
            str(block_id),
            answers,
            exercise_block,  # Pass the full exercise block with topic
        )

        return jsonify(evaluation)

    except ValueError as e:
        logger.error(f"Validation error arguing AI exercise: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error arguing AI exercise: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-exercise/<block_id>/topic-memory-status", methods=["GET"])
def get_topic_memory_status_route(block_id):
    """
    Check if topic memory processing is complete for a given block.

    This endpoint allows the frontend to check the status of background
    topic memory processing for exercise blocks.

    Args:
        block_id: The exercise block ID to check status for

    Returns:
        JSON response with topic memory processing status
    """
    try:
        username = require_user()
        logger.debug(f"Checking topic memory status for user {username}, block {block_id}")

        if username:  # Ensure username is not None
            status = get_topic_memory_status(username, block_id)
            return jsonify(status)
        else:
            return jsonify({"error": "User not authenticated"}), 401

    except ValueError as e:
        logger.error(f"Validation error checking topic memory status: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error checking topic memory status: {e}")
        return jsonify({"error": "Server error"}), 500
