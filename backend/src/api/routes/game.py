"""
Sentence Ordering Game Routes

This module contains API routes for the sentence ordering game functionality.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.game.game_helpers import (
    create_game_round,
    evaluate_game_answer,
    get_game_statistics
)


logger = logging.getLogger(__name__)


@game_bp.route("/level", methods=["POST"])
@limiter.limit("10/minute")
def level_game():
    """
    Create a new game round with scrambled sentence.

    This endpoint generates a sentence appropriate for the user's level,
    scrambles it, and returns both the original and scrambled versions.

    Returns:
        JSON response with level, sentence, and scrambled sentence
    """
    try:
        username = require_user()
        data = request.get_json() or {}
        level = data.get("level")

        game_data = create_game_round(str(username), level)
        return jsonify(game_data)

    except ValueError as e:
        logger.error(f"Validation error in level game: {e}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating game round: {e}")
        return jsonify({"msg": "Failed to create game round"}), 500


@game_bp.route("/level/submit", methods=["POST"])
@limiter.limit("20/minute")
def submit_level():
    """
    Submit and evaluate a game answer.

    This endpoint evaluates the user's answer against the correct sentence,
    saves the result, and returns feedback with the correct answer.

    Returns:
        JSON response with evaluation results and feedback
    """
    try:
        username = require_user()
        data = request.get_json() or {}

        level = data.get("level")
        sentence = data.get("sentence")
        user_answer = data.get("answer", "").strip()

        if level is None or not sentence:
            return jsonify({"msg": "Level and sentence are required"}), 400

        if not user_answer:
            return jsonify({"msg": "Answer is required"}), 400

        result = evaluate_game_answer(str(username), level, sentence, user_answer)
        return jsonify(result)

    except ValueError as e:
        logger.error(f"Validation error in submit level: {e}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        logger.error(f"Error evaluating game answer: {e}")
        return jsonify({"msg": "Failed to evaluate answer"}), 500


@game_bp.route("/statistics", methods=["GET"])
def get_statistics():
    """
    Get game statistics for the current user.

    This endpoint returns comprehensive statistics about the user's
    game performance including accuracy, total games, and recent results.

    Returns:
        JSON response with game statistics
    """
    try:
        username = require_user()

        stats = get_game_statistics(str(username))
        return jsonify(stats)

    except ValueError as e:
        logger.error(f"Validation error getting game statistics: {e}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting game statistics: {e}")
        return jsonify({"msg": "Failed to get game statistics"}), 500
