"""
Profile Routes

This module contains API routes for user profile management and data retrieval.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.profile.profile_helpers import (
    get_user_game_results,
    get_user_profile_summary,
    get_user_achievements,
    get_user_activity_timeline
)


logger = logging.getLogger(__name__)


@profile_bp.route("/profile", methods=["GET"])
def get_profile():
    """
    Get the current user's past game results.

    This endpoint retrieves all game results for the authenticated user,
    including level, answer, correctness, and timestamp information.

    Returns:
        JSON response with game results or error details
    """
    try:
        username = require_user()

        results = get_user_game_results(str(username))
        return jsonify(results)

    except ValueError as e:
        logger.error(f"Validation error getting profile: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({"error": "Server error"}), 500


@profile_bp.route("/profile/summary", methods=["GET"])
def get_profile_summary():
    """
    Get comprehensive profile summary for the current user.

    This endpoint provides a complete overview of the user's profile
    including statistics, achievements, and progress information.

    Returns:
        JSON response with profile summary or error details
    """
    try:
        username = require_user()

        summary = get_user_profile_summary(str(username))
        return jsonify(summary)

    except ValueError as e:
        logger.error(f"Validation error getting profile summary: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting profile summary: {e}")
        return jsonify({"error": "Server error"}), 500


@profile_bp.route("/profile/achievements", methods=["GET"])
def get_achievements():
    """
    Get user achievements and milestones.

    This endpoint retrieves all achievements earned by the user
    including game milestones, vocabulary achievements, and lesson completions.

    Returns:
        JSON response with achievements list or error details
    """
    try:
        username = require_user()

        achievements = get_user_achievements(str(username))
        return jsonify(achievements)

    except ValueError as e:
        logger.error(f"Validation error getting achievements: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting achievements: {e}")
        return jsonify({"error": "Server error"}), 500


@profile_bp.route("/profile/timeline", methods=["GET"])
def get_activity_timeline():
    """
    Get user activity timeline with recent actions.

    This endpoint provides a chronological list of user activities
    including games, vocabulary learning, and lesson completions.

    Returns:
        JSON response with activity timeline or error details
    """
    try:
        username = require_user()

        # Get limit from query parameters
        limit = request.args.get("limit", 20, type=int)
        if limit <= 0 or limit > 100:
            limit = 20

        timeline = get_user_activity_timeline(str(username), limit)
        return jsonify(timeline)

    except ValueError as e:
        logger.error(f"Validation error getting activity timeline: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting activity timeline: {e}")
        return jsonify({"error": "Server error"}), 500


@profile_bp.route("/profile/stats", methods=["GET"])
def get_profile_stats():
    """
    Get detailed statistics for the current user.

    This endpoint provides comprehensive statistics about the user's
    learning progress, performance metrics, and activity patterns.

    Returns:
        JSON response with detailed statistics or error details
    """
    try:
        username = require_user()

        # Get profile summary which includes basic stats
        summary = get_user_profile_summary(str(username))

        # Add additional statistics
        stats = {
            "basic_stats": summary,
            "recent_activity": {
                "last_game": _get_last_activity_timestamp(str(username), "game"),
                "last_vocabulary": _get_last_activity_timestamp(str(username), "vocabulary"),
                "last_lesson": _get_last_activity_timestamp(str(username), "lesson")
            },
            "performance_trends": {
                "weekly_games": _get_weekly_game_count(str(username)),
                "monthly_games": _get_monthly_game_count(str(username)),
                "accuracy_trend": _get_accuracy_trend(str(username))
            }
        }

        return jsonify(stats)

    except ValueError as e:
        logger.error(f"Validation error getting profile stats: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting profile stats: {e}")
        return jsonify({"error": "Server error"}), 500


def _get_last_activity_timestamp(username: str, activity_type: str) -> str | None:
    """
    Get the timestamp of the last activity of a specific type.

    Args:
        username: The username to check
        activity_type: Type of activity (game, vocabulary, lesson)

    Returns:
        Timestamp string or None
    """
    try:
        if activity_type == "game":
            row = select_one(
                "results",
                columns="timestamp",
                where="username = ?",
                params=(username,),
                order_by="timestamp DESC"
            )
        elif activity_type == "vocabulary":
            row = select_one(
                "vocab_log",
                columns="timestamp",
                where="username = ?",
                params=(username,),
                order_by="timestamp DESC"
            )
        elif activity_type == "lesson":
            row = select_one(
                "results",
                columns="timestamp",
                where="username = ? AND level > 100",
                params=(username,),
                order_by="timestamp DESC"
            )
        else:
            return None

        return row.get("timestamp") if row else None

    except Exception as e:
        logger.error(f"Error getting last {activity_type} timestamp for user {username}: {e}")
        return None


def _get_weekly_game_count(username: str) -> int:
    """Get the number of games played in the last week."""
    try:
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)

        row = select_one(
            "results",
            columns="COUNT(*) as count",
            where="username = ? AND timestamp >= ?",
            params=(username, week_ago.isoformat())
        )

        return row.get("count", 0) if row else 0

    except Exception as e:
        logger.error(f"Error getting weekly game count for user {username}: {e}")
        return 0


def _get_monthly_game_count(username: str) -> int:
    """Get the number of games played in the last month."""
    try:
        from datetime import datetime, timedelta
        month_ago = datetime.now() - timedelta(days=30)

        row = select_one(
            "results",
            columns="COUNT(*) as count",
            where="username = ? AND timestamp >= ?",
            params=(username, month_ago.isoformat())
        )

        return row.get("count", 0) if row else 0

    except Exception as e:
        logger.error(f"Error getting monthly game count for user {username}: {e}")
        return 0


def _get_accuracy_trend(username: str) -> Dict[str, float]:
    """Get accuracy trend over time."""
    try:
        # Get accuracy for last 4 weeks
        from datetime import datetime, timedelta

        trend = {}
        for i in range(4):
            week_start = datetime.now() - timedelta(weeks=i+1)
            week_end = datetime.now() - timedelta(weeks=i)

            row = select_one(
                "results",
                columns="COUNT(*) as total, SUM(correct) as correct",
                where="username = ? AND timestamp >= ? AND timestamp < ?",
                params=(username, week_start.isoformat(), week_end.isoformat())
            )

            if row and row.get("total", 0) > 0:
                accuracy = (row.get("correct", 0) / row.get("total", 1)) * 100
                trend[f"week_{i+1}"] = round(accuracy, 1)
            else:
                trend[f"week_{i+1}"] = 0.0

        return trend

    except Exception as e:
        logger.error(f"Error getting accuracy trend for user {username}: {e}")
        return {"week_1": 0.0, "week_2": 0.0, "week_3": 0.0, "week_4": 0.0}
