"""
AI Training Routes

This module contains API routes for AI-powered training exercise generation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging
import json
from typing import Dict, Any

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user, run_in_background
from config.blueprint import ai_bp
from core.database.connection import select_one
from features.ai.generation.exercise_generator import (
    generate_training_exercises,
    prefetch_next_exercises
)
from features.ai.generation.helpers import (
    store_user_ai_data
)


logger = logging.getLogger(__name__)


@ai_bp.route("/training-exercises", methods=["POST"])
def get_training_exercises():
    """
    Get training exercises for the user.

    This endpoint generates or retrieves cached training exercises for the user.
    It supports both immediate generation and background prefetching for better
    performance.

    Returns:
        JSON response with training exercises or error details
    """
    try:
        username = require_user()
        logger.info(f"Training exercises request from user: {username}")

        data = request.get_json()
        answers = data.get("answers", {})
        logger.info(f"Training request data for user {username}: answers_count={len(answers)}")

        if answers:
            logger.info(f"User {username} has answers, checking cached next exercises")
            # Check if we have cached next exercises
            row = select_one(
                "ai_user_data",
                columns="exercises, next_exercises",
                where="username = ?",
                params=(username,),
            )
            if row and row.get("next_exercises"):
                try:
                    cached_next = json.loads(row["next_exercises"])
                    if cached_next and cached_next.get("exercises"):
                        logger.info(f"Found cached next exercises for user {username}")
                        logger.info(f"Successfully loaded cached next exercises for user {username}")
                        logger.debug(f"Retrieved exercise block with topic: '{cached_next.get('topic')}'")
                        logger.debug(f"Retrieved exercise block keys: {list(cached_next.keys())}")
                        block_id = cached_next.get('block_id') if cached_next and isinstance(cached_next, dict) else None
                        logger.debug(f"Returning cached exercises with block_id: {block_id}")
                        return jsonify(cached_next)
                except Exception as e:
                    logger.error(f"Failed to parse cached next exercises for user {username}: {e}")

            logger.info(f"No cached next exercises for user {username}, generating new ones")
            try:
                if username:  # Ensure username is not None
                    ai_block = generate_training_exercises(username)
                    if ai_block and ai_block.get("exercises"):
                        logger.info(f"Storing exercises for user {username}")
                        logger.debug(f"Storing exercise block with topic: '{ai_block.get('topic')}'")
                        logger.debug(f"Exercise block keys: {list(ai_block.keys())}")
                        store_user_ai_data(
                            username,
                            {
                                "current_exercises": json.dumps(ai_block),
                                "next_exercises": json.dumps(ai_block),  # For now, store same as next
                            },
                        )
                        logger.info(f"Running prefetch next exercises for user {username}")
                        run_in_background(prefetch_next_exercises, username)
                        logger.info(f"Returning preloaded training exercises for user {username}")
                        block_id = ai_block.get('block_id') if ai_block and isinstance(ai_block, dict) else None
                        logger.debug(f"Returning generated exercises with block_id: {block_id}")
                        return jsonify(ai_block)
            except Exception as e:
                logger.error(f"Failed to generate training exercises for user {username}: {e}")
                return jsonify({"error": "Failed to generate exercises"}), 500
        else:
            logger.info(f"User {username} has no answers, checking cached exercises")
            # Check if we have cached current exercises
            row = select_one(
                "ai_user_data",
                columns="exercises, next_exercises",
                where="username = ?",
                params=(username,),
            )
            if row and row.get("exercises"):
                try:
                    cached_current = json.loads(row["exercises"])
                    if cached_current and cached_current.get("exercises"):
                        logger.info(f"Found cached exercises for user {username}")
                        logger.debug(f"Retrieved current exercise block with topic: '{cached_current.get('topic')}'")
                        logger.debug(f"Retrieved current exercise block keys: {list(cached_current.keys())}")
                        block_id = cached_current.get('block_id') if cached_current and isinstance(cached_current, dict) else None
                        logger.debug(f"Returning cached exercises with block_id: {block_id}")
                        return jsonify(cached_current)
                except Exception as e:
                    logger.error(f"Failed to parse cached exercises for user {username}: {e}")

            logger.info(f"No cached next exercises for user {username}, prefetching")
            try:
                if username:  # Ensure username is not None
                    ai_block = generate_training_exercises(username)
                    if ai_block and ai_block.get("exercises"):
                        logger.info(f"Returning cached exercises for user {username}")
                        return jsonify(ai_block)
            except Exception as e:
                logger.error(f"Failed to generate training exercises for user {username}: {e}")
                return jsonify({"error": "Failed to generate exercises"}), 500

    except ValueError as e:
        logger.error(f"Validation error getting training exercises: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting training exercises: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ai-exercise/training/submit", methods=["POST"])
def submit_training_exercise():
    """
    Submit training exercise answers for evaluation.

    This endpoint handles training exercise submissions and delegates to the
    main exercise submission handler.

    Returns:
        JSON response with evaluation results or error details
    """
    try:
        username = require_user()
        logger.info(f"User {username} submitting training exercise")

        data = request.get_json() or {}

        # Get the current exercise block from user data
        row = select_one(
            "ai_user_data",
            columns="exercises",
            where="username = ?",
            params=(username,),
        )

        if not row or not row.get("exercises"):
            return jsonify({"error": "No current exercises found"}), 400

        try:
            exercise_block = json.loads(row["exercises"])
            block_id = exercise_block.get("block_id", "training")
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid exercise data"}), 400

                                                        # Add the exercise block to the request data
        data["exercise_block"] = exercise_block

        # Delegate to the main exercise submission handler
        from .exercise import submit_ai_exercise

        # Simply call the function - the parse_submission_data function now handles both formats
        try:
            result = submit_ai_exercise(block_id)
            return result
        except Exception as e:
            logger.error(f"Error in submit_ai_exercise: {e}")
            return jsonify({"error": "Exercise evaluation failed"}), 500

    except ValueError as e:
        logger.error(f"Validation error submitting training exercise: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting training exercise: {e}")
        return jsonify({"error": "Server error"}), 500


