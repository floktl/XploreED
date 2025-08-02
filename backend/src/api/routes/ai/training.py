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
from api.middleware.auth import require_user
from config.blueprint import ai_bp
from core.database.connection import select_one
from core.processing import run_in_background
from features.ai.generation.exercise_creation import (
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
    Generate or retrieve AI-powered training exercises for the user.

    This endpoint provides personalized training exercises based on the user's
    learning progress and identified weaknesses. It supports intelligent caching
    and background prefetching for optimal performance.

    Request Body:
        - answers (object, optional): Previous exercise answers for context
        - force_new (bool, optional): Force generation of new exercises (default: false)
        - difficulty (str, optional): Target difficulty level (easy, medium, hard)
        - topic (str, optional): Specific topic to focus on

    Exercise Types:
        - grammar: Grammar practice exercises
        - vocabulary: Vocabulary building exercises
        - comprehension: Reading comprehension exercises
        - translation: Translation exercises
        - conversation: Dialogue and speaking exercises
        - mixed: Mixed skill exercises

    JSON Response Structure:
        {
            "block_id": str,                          # Exercise block identifier
            "topic": str,                             # Exercise topic
            "difficulty": str,                        # Exercise difficulty level
            "exercises": [                            # Array of exercises
                {
                    "id": str,                        # Exercise identifier
                    "type": str,                      # Exercise type
                    "question": str,                  # Exercise question
                    "options": [str],                 # Answer options (if applicable)
                    "correct_answer": str,            # Correct answer
                    "explanation": str,               # Answer explanation
                    "hint": str,                      # Exercise hint
                    "points": int                     # Points for correct answer
                }
            ],
            "metadata": {                             # Exercise metadata
                "total_exercises": int,               # Total number of exercises
                "estimated_time": int,                # Estimated completion time (minutes)
                "skill_focus": [str],                 # Skills being tested
                "learning_objectives": [str]          # Learning objectives
            },
            "generated_at": str,                      # Generation timestamp
            "cache_status": str                       # Cache status (cached, generated, prefetched)
        }

    Error Codes:
        - NO_EXERCISES_AVAILABLE: No exercises available for user
        - GENERATION_FAILED: Exercise generation failed
        - CACHE_ERROR: Error accessing cached exercises
        - INVALID_PARAMETERS: Invalid request parameters

    Status Codes:
        - 200: Success
        - 400: Bad request (invalid parameters)
        - 401: Unauthorized
        - 500: Internal server error (generation failed)

    Caching Behavior:
        - Exercises are cached to improve performance
        - Cached exercises are returned if available
        - Background prefetching ensures smooth experience
        - Cache is invalidated when user completes exercises

    Performance Features:
        - Intelligent caching system
        - Background prefetching of next exercises
        - Adaptive difficulty based on user performance
        - Personalized content based on learning history

    Usage Examples:
        Get new exercises:
        {
            "force_new": true,
            "difficulty": "medium"
        }

        Continue with context:
        {
            "answers": {
                "exercise_1": "correct_answer",
                "exercise_2": "incorrect_answer"
            }
        }

        Focus on specific topic:
        {
            "topic": "Modalverben",
            "difficulty": "hard"
        }
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
                    else:
                        logger.error(f"Generated ai_block is empty or invalid for user {username}")
                        return jsonify({"error": "Failed to generate exercises"}), 500
                else:
                    logger.error(f"Username is None for training exercises request")
                    return jsonify({"error": "Invalid user"}), 400
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
                    else:
                        logger.error(f"Generated ai_block is empty or invalid for user {username}")
                        return jsonify({"error": "Failed to generate exercises"}), 500
                else:
                    logger.error(f"Username is None for training exercises request")
                    return jsonify({"error": "Invalid user"}), 400
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
    Submit training exercise answers for AI-powered evaluation.

    This endpoint processes training exercise submissions and provides
    detailed feedback and evaluation results. It integrates with the main
    exercise evaluation system for consistent assessment.

    Request Body:
        - answers (object, required): User's answers to exercises
        - exercise_ids (array, optional): Array of exercise identifiers
        - time_spent (int, optional): Total time spent on exercises (seconds)
        - confidence_level (str, optional): User's confidence level (low, medium, high)

    Answer Format:
        {
            "exercise_id": "user_answer",             # Exercise ID and user's answer
            "exercise_1": "correct_answer",
            "exercise_2": "incorrect_answer"
        }

    JSON Response Structure:
        {
            "block_id": str,                          # Exercise block identifier
            "overall_score": float,                   # Overall score (0-100)
            "pass_status": bool,                      # Whether user passed the exercises
            "results": [                              # Individual exercise results
                {
                    "exercise_id": str,               # Exercise identifier
                    "user_answer": str,               # User's submitted answer
                    "correct_answer": str,            # Correct answer
                    "is_correct": bool,               # Whether answer is correct
                    "score": float,                   # Individual exercise score
                    "feedback": str,                  # Detailed feedback
                    "explanation": str,               # Answer explanation
                    "improvement_tips": [str]         # Tips for improvement
                }
            ],
            "performance_analysis": {                 # Performance analysis
                "strengths": [str],                   # Identified strengths
                "weaknesses": [str],                  # Areas for improvement
                "recommendations": [str],             # Learning recommendations
                "next_topics": [str]                  # Suggested next topics
            },
            "learning_progress": {                    # Learning progress update
                "topics_improved": [str],             # Topics that improved
                "topics_needing_work": [str],         # Topics needing more work
                "skill_level_changes": object         # Skill level adjustments
            },
            "completion_time": int,                   # Total completion time (seconds)
            "submitted_at": str                       # Submission timestamp
        }

    Error Codes:
        - NO_EXERCISES_FOUND: No current exercises found for user
        - INVALID_EXERCISE_DATA: Exercise data is corrupted or invalid
        - EVALUATION_FAILED: Exercise evaluation failed
        - MISSING_ANSWERS: No answers provided in request

    Status Codes:
        - 200: Success
        - 400: Bad request (missing answers, invalid data)
        - 401: Unauthorized
        - 500: Internal server error (evaluation failed)

    Evaluation Features:
        - AI-powered answer evaluation
        - Detailed feedback and explanations
        - Performance analysis and recommendations
        - Learning progress tracking
        - Adaptive difficulty adjustment
        - Topic memory integration

    Learning Integration:
        - Updates user's topic memory
        - Adjusts learning recommendations
        - Tracks skill progression
        - Identifies learning patterns
        - Suggests next learning steps

    Usage Examples:
        Submit exercise answers:
        {
            "answers": {
                "exercise_1": "Ich habe das Buch gelesen",
                "exercise_2": "Modalverben"
            },
            "time_spent": 300,
            "confidence_level": "medium"
        }

        Submit with exercise IDs:
        {
            "answers": {
                "exercise_1": "correct_answer"
            },
            "exercise_ids": ["exercise_1"],
            "time_spent": 120
        }
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


