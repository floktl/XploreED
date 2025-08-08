"""
AI Exercise Routes

This module contains API routes for AI-powered exercise evaluation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import json
import logging
from typing import Any
from datetime import datetime

from flask import request, jsonify # type: ignore
from api.middleware.auth import require_user
from core.database.connection import select_one, insert_row, select_rows
from config.blueprint import ai_bp
from config.extensions import limiter
from features.exercise import (
    check_gap_fill_correctness,
    parse_submission_data,
    evaluate_first_exercise,
    create_immediate_results,
    evaluate_remaining_exercises_async,
)
from features.ai.evaluation import process_ai_answers
from shared.exceptions import DatabaseError, AIEvaluationError


logger = logging.getLogger(__name__)


@ai_bp.route("/ai-exercises", methods=["POST"])
def get_ai_exercises_route():
    """
    Get AI-generated exercises for the current user.

    This endpoint retrieves or generates AI exercises for the user.
    If no current exercises exist, new ones are generated automatically.

    Request Body:
        - payload (object, optional): Additional parameters for exercise generation

    JSON Response Structure:
        {
            "id": str,                           # Exercise block ID
            "username": str,                     # Username
            "title": str,                        # Exercise block title
            "level": str,                        # Difficulty level
            "topic": str,                        # Topic covered
            "exercises": [                       # Array of exercises
                {
                    "id": str,                   # Exercise identifier
                    "type": str,                 # Exercise type
                    "question": str,             # Exercise question
                    "options": [str],            # Answer options (if applicable)
                    "correct_answer": str        # Correct answer
                }
            ],
            "instructions": str,                 # Exercise instructions
            "vocabHelp": [str],                  # Vocabulary help
            "created_at": str                    # Creation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting AI exercises")

        from features.ai.generation.exercise_processing import get_ai_exercises

        # Get payload from request
        payload = request.get_json() or {}
        logger.info(f"Payload received: {payload}")
        exercise_block = get_ai_exercises(payload)
        logger.info(f"Exercise block returned: {exercise_block}")

        if not exercise_block:
            return jsonify({"error": "Failed to generate exercises"}), 500

        # Parse exercises JSON string back to list if it's a string
        exercises_field = exercise_block.get("exercises")
        if exercises_field is None:
            logger.error(f"No exercises field found for block {exercise_block.get('id')}")
            return jsonify({"error": "No exercise data found"}), 500

        if isinstance(exercises_field, str):
            try:
                exercises_data = json.loads(exercises_field)
                exercise_block["exercises"] = exercises_data
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Error parsing exercises JSON for block {exercise_block.get('id')}: {e}")
                return jsonify({"error": "Invalid exercise data"}), 500
        elif isinstance(exercises_field, list):
            # Already parsed
            exercises_data = exercises_field
        else:
            logger.error(f"Unexpected exercises field type for block {exercise_block.get('id')}: {type(exercises_field)}")
            return jsonify({"error": "Invalid exercise data format"}), 500

        logger.info(f"Returning {len(exercises_data)} exercises for user {username}")
        return jsonify(exercise_block)

    except Exception as e:
        logger.error(f"Error getting AI exercises: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id, data=None):
    """
    Evaluate a submitted exercise block and save results.

    This endpoint processes exercise submissions with immediate feedback for the first
    exercise and background processing for the remaining exercises. It supports
    streaming results and topic memory integration.

    Path Parameters:
        - block_id (str, required): The exercise block ID to submit

    Request Body:
        - exercises (array, required): Array of exercise data
        - answers (array, required): Array of user answers
        - exercise_block (object, optional): Exercise block metadata

    Exercise Structure:
        [
            {
                "id": str,                       # Exercise identifier
                "type": str,                     # Exercise type
                "question": str,                 # Exercise question
                "options": [str],                # Answer options (if applicable)
                "correct_answer": str            # Correct answer
            }
        ]

    JSON Response Structure:
        {
            "pass": bool,                        # Overall pass status (updated in background)
            "summary": {                         # Exercise summary (updated in background)
                "correct": int,                  # Number of correct answers
                "total": int,                    # Total number of exercises
                "mistakes": [str]                # List of mistakes
            },
            "results": [                         # Immediate results for first exercise
                {
                    "exercise_id": str,          # Exercise identifier
                    "correct": bool,             # Whether answer is correct
                    "feedback": str,             # Immediate feedback
                    "score": float               # Exercise score
                }
            ],
            "streaming": bool                    # Flag indicating streaming response
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or validation error
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.info(f"User {username} submitting exercise block {block_id}")

        if data is None:
            data = request.get_json() or {}

        logger.info(f"Raw submission data: {data}")
        logger.info(f"Data keys: {list(data.keys()) if data else 'None'}")

        exercises, answers, parsed_block_id = parse_submission_data(data)

        if not exercises:
            logger.error(f"No exercises found in submission data for user {username}")
            return jsonify({"error": "No exercises found"}), 400

        if not answers:
            logger.error(f"No answers found in submission data for user {username}")
            return jsonify({"error": "No answers found"}), 400

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
            try:
                with app.app_context():
                    exercise_block = data.get("exercise_block")
                    logger.info(f"Exercise block from data: topic='{exercise_block.get('topic') if exercise_block else 'None'}'")
                    if username:  # Ensure username is not None
                        logger.info(f"Calling evaluate_remaining_exercises_async for user {username}, block {block_id}")
                        evaluate_remaining_exercises_async(username, block_id, exercises, answers, first_result_with_details, exercise_block)
                    else:
                        logger.error("Username is None in background task")
            except Exception as e:
                logger.error(f"Error in background task: {e}")
                import traceback
                logger.error(f"Background task traceback: {traceback.format_exc()}")

        logger.info("Starting background thread")
        Thread(target=background_task, daemon=True).start()
        logger.info("Background thread started")

        # Create immediate results
        immediate_results = create_immediate_results(exercises, first_result_with_details)

        logger.info("Returning immediate response, background processing started")
        return jsonify({
            "block_id": block_id,  # Include the block_id for frontend polling
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
    Get results for a completed AI exercise block.

    This endpoint retrieves the final results and evaluation details
    for a completed exercise block, including AI-generated feedback.

    Path Parameters:
        - block_id (str, required): The exercise block ID

    JSON Response Structure:
        {
            "block_id": str,                     # Exercise block identifier
            "completed": bool,                   # Whether evaluation is complete
            "results": [                         # Exercise results
                {
                    "exercise_id": str,          # Exercise identifier
                    "correct": bool,             # Whether answer is correct
                    "user_answer": str,          # User's submitted answer
                    "correct_answer": str,       # Correct answer
                    "feedback": str,             # AI-generated feedback
                    "score": float,              # Exercise score
                    "explanation": str           # Detailed explanation
                }
            ],
            "summary": {                         # Overall summary
                "correct": int,                  # Number of correct answers
                "total": int,                    # Total number of exercises
                "percentage": float,             # Success percentage
                "mistakes": [str]                # List of mistakes
            },
            "ai_feedback": {                     # AI-generated overall feedback
                "general_feedback": str,         # General feedback
                "improvement_areas": [str],      # Areas for improvement
                "strengths": [str]               # User strengths
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Results not found
        - 500: Internal server error
    """
    try:
        username = require_user()

        # First try to get results from Redis
        from external.redis import redis_client
        result_key = f"exercise_result:{username}:{block_id}"
        redis_results = redis_client.get_json(result_key)

        if redis_results:
            logger.info(f"Found results in Redis for block {block_id}")

            # Convert the evaluation results to the expected format
            if isinstance(redis_results, tuple) and len(redis_results) == 2:
                evaluation_results, summary = redis_results
            else:
                evaluation_results = redis_results
                summary = {"total": 0, "correct": 0, "incorrect": 0, "accuracy": 0}

            # Ensure summary is a dictionary
            if not isinstance(summary, dict):
                summary = {"total": 0, "correct": 0, "incorrect": 0, "accuracy": 0}

            # Convert evaluation results to the expected format
            formatted_results = []

            # Handle both dictionary and list formats
            if isinstance(evaluation_results, dict):
                for exercise_id, result in evaluation_results.items():
                    formatted_results.append({
                        "id": exercise_id,
                        "is_correct": result.get("correct", False),
                        "correct_answer": result.get("correct_answer", ""),
                        "alternatives": result.get("alternatives", []),
                        "explanation": result.get("explanation", ""),
                        "user_answer": result.get("user_answer", ""),
                        "feedback": result.get("feedback", "")
                    })
            elif isinstance(evaluation_results, list):
                # If it's a list, check if it contains the evaluation results
                if len(evaluation_results) == 2 and isinstance(evaluation_results[0], dict):
                    # This is likely the format [evaluation_dict, summary_dict]
                    evaluation_dict = evaluation_results[0]
                    for exercise_id, result in evaluation_dict.items():
                        formatted_results.append({
                            "id": exercise_id,
                            "is_correct": result.get("correct", False),
                            "correct_answer": result.get("correct_answer", ""),
                            "alternatives": result.get("alternatives", []),
                            "explanation": result.get("explanation", ""),
                            "user_answer": result.get("user_answer", ""),
                            "feedback": result.get("feedback", "")
                        })
                else:
                    # If it's already a list of formatted results, use it directly
                    formatted_results = evaluation_results
            else:
                logger.warning(f"Unexpected evaluation_results format: {type(evaluation_results)}")
                formatted_results = []

            # Determine processing vs complete based on presence of AI content
            has_enrichment = any(
                (r.get("alternatives") or r.get("explanation")) for r in formatted_results
            ) if isinstance(formatted_results, list) else False

            return jsonify({
                "status": "complete" if has_enrichment else "processing",
                "block_id": block_id,
                "results": formatted_results,
                "summary": summary,
                "pass": summary.get("correct", 0) >= len(formatted_results) * 0.7 if formatted_results else False,
                "source": "redis"
            })

        # Fallback to database
        results = select_one(
            "ai_exercise_results",
            columns="*",
            where="block_id = ? AND username = ?",
            params=(block_id, username)
        )

        if not results:
            return jsonify({"error": "Exercise results not found"}), 404

        # Parse the stored results from database
        try:
            stored_results = json.loads(results.get("results", "{}"))
            stored_summary = json.loads(results.get("summary", "{}"))

            # Convert to the expected format
            formatted_results = []
            for exercise_id, result in stored_results.items():
                formatted_results.append({
                    "id": exercise_id,
                    "is_correct": result.get("correct", False),
                    "correct_answer": result.get("correct_answer", ""),
                    "alternatives": result.get("alternatives", []),
                    "explanation": result.get("explanation", ""),
                    "user_answer": result.get("user_answer", ""),
                    "feedback": result.get("feedback", "")
                })

            return jsonify({
                "status": "complete",
                "block_id": block_id,
                "results": formatted_results,
                "summary": stored_summary,
                "pass": stored_summary.get("correct", 0) >= len(formatted_results) * 0.7 if formatted_results else False,
                "source": "database"
            })
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing stored results: {e}")
            return jsonify({"error": "Invalid stored results format"}), 500

    except Exception as e:
        logger.error(f"Error getting AI exercise results: {e}")
        return jsonify({"error": "Failed to retrieve exercise results"}), 500


@ai_bp.route("/ai-exercise/<block_id>/argue", methods=["POST"])
def argue_ai_exercise(block_id):
    """
    Submit an argument against AI evaluation results.

    This endpoint allows users to challenge AI evaluation results
    and request a re-evaluation of their answers.

    Path Parameters:
        - block_id (str, required): The exercise block ID

    Request Body:
        - exercise_id (str, required): Specific exercise to argue
        - argument (str, required): User's argument against the evaluation
        - evidence (str, optional): Supporting evidence or reasoning

    JSON Response Structure:
        {
            "message": str,                      # Success message
            "argument_id": str,                  # Argument identifier
            "status": str,                       # Argument status (submitted, under_review)
            "submitted_at": str,                 # Submission timestamp
            "estimated_review_time": str         # Estimated review time
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 404: Exercise not found
        - 500: Internal server error
    """
    try:
        username = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        exercise_id = data.get("exercise_id")
        argument = data.get("argument", "").strip()
        evidence = data.get("evidence", "").strip()

        if not exercise_id:
            return jsonify({"error": "Exercise ID is required"}), 400

        if not argument:
            return jsonify({"error": "Argument is required"}), 400

        # Submit argument for review
        argument_data = {
            "username": username,
            "block_id": block_id,
            "exercise_id": exercise_id,
            "argument": argument,
            "evidence": evidence,
            "submitted_at": datetime.now().isoformat(),
            "status": "submitted"
        }

        argument_id = insert_row("ai_exercise_arguments", argument_data)

        if argument_id:
            return jsonify({
                "message": "Argument submitted successfully",
                "argument_id": argument_id,
                "status": "submitted",
                "submitted_at": argument_data["submitted_at"],
                "estimated_review_time": "24-48 hours"
            })
        else:
            return jsonify({"error": "Failed to submit argument"}), 500

    except Exception as e:
        logger.error(f"Error submitting argument: {e}")
        return jsonify({"error": "Failed to submit argument"}), 500


@ai_bp.route("/ai-exercise/debug/topic-memory", methods=["GET"])
def debug_topic_memory_route():
    """
    Debug endpoint to check topic memory functionality.
    """
    try:
        username = require_user()

        # Check if topic_memory table exists and has data
        topic_memory_count = select_rows(
            "topic_memory",
            columns="COUNT(*) as count",
            where="username = ?",
            params=(username,)
        )

        # Check if vocab_log table exists and has data
        vocab_count = select_rows(
            "vocab_log",
            columns="COUNT(*) as count",
            where="username = ?",
            params=(username,)
        )

        return jsonify({
            "username": username,
            "topic_memory_count": topic_memory_count[0].get("count", 0) if topic_memory_count else 0,
            "vocab_count": vocab_count[0].get("count", 0) if vocab_count else 0,
            "status": "ok"
        })

    except Exception as e:
        logger.error(f"Error in debug topic memory endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@ai_bp.route("/ai-exercise/<block_id>/topic-memory-status", methods=["GET"])
@limiter.limit("100/minute") # Apply rate limit to this specific endpoint
def get_topic_memory_status_route(block_id):
    """
    Get topic memory status for an exercise block.

    This endpoint provides information about the topic memory
    integration status and any updates made during exercise evaluation.

    Path Parameters:
        - block_id (str, required): The exercise block ID

    JSON Response Structure:
        {
            "block_id": str,                     # Exercise block identifier
            "topic_memory_updated": bool,        # Whether topic memory was updated
            "update_status": str,                # Update status (pending, completed, failed)
            "last_update": str,                  # Last update timestamp
            "memory_impact": {                   # Memory impact details
                "strengthened_concepts": [str],  # Concepts that were strengthened
                "weak_areas": [str],             # Identified weak areas
                "recommendations": [str]         # Learning recommendations
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Block not found
        - 500: Internal server error
    """
    try:
        username = require_user()

        # Check if the exercise block exists and has been processed
        block = select_one("ai_exercise_results", columns="*", where="block_id = ? AND username = ?", params=(block_id, username))

        if not block:
            return jsonify({
                "block_id": block_id,
                "topic_memory_updated": False,
                "update_status": "not_started",
                "last_update": None,
                "memory_impact": {
                    "strengthened_concepts": [],
                    "weak_areas": [],
                    "recommendations": []
                }
            })

        # Check if topic memory has recent entries for this user
        from datetime import datetime, timedelta
        recent_time = (datetime.now() - timedelta(minutes=5)).isoformat()

        recent_topic_memory = select_rows(
            "topic_memory",
            columns="COUNT(*) as count",
            where="username = ? AND last_review >= ?",
            params=(username, recent_time)
        )

        topic_memory_updated = recent_topic_memory and recent_topic_memory[0].get("count", 0) > 0

        # Get recent vocabulary entries
        recent_vocab = select_rows(
            "vocab_log",
            columns="COUNT(*) as count",
            where="username = ? AND created_at >= ?",
            params=(username, recent_time)
        )

        vocab_updated = recent_vocab and recent_vocab[0].get("count", 0) > 0

        # Determine overall status
        if topic_memory_updated or vocab_updated:
            update_status = "completed"
            topic_memory_updated = True
        else:
            update_status = "pending"
            topic_memory_updated = False

        return jsonify({
            "block_id": block_id,
            "topic_memory_updated": topic_memory_updated,
            "update_status": update_status,
            "last_update": block.get("created_at") if block else None,
            "memory_impact": {
                "strengthened_concepts": [],
                "weak_areas": [],
                "recommendations": []
            }
        })

    except Exception as e:
        logger.error(f"Error getting topic memory status: {e}")
        return jsonify({"error": "Failed to retrieve topic memory status"}), 500
