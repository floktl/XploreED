"""
XplorED - Educational Games API Routes

This module contains API routes for educational games and interactive learning activities,
following clean architecture principles as outlined in the documentation.

Route Categories:
- Game Management: Game creation, retrieval, and configuration
- Game Sessions: Active game session management and state tracking
- Game Results: Score tracking and performance analytics
- Game Types: Different game modes and learning activities
- Game Analytics: Usage statistics and learning effectiveness

Game Features:
- Multiple educational game types (vocabulary, grammar, comprehension)
- Real-time scoring and performance tracking
- Adaptive difficulty based on user performance
- Session management and progress persistence
- Learning analytics and effectiveness measurement

Business Logic:
All game logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import get_current_user, require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import game_bp
from features.game import (
    get_user_game_level,
    generate_game_sentence,
    create_game_round,
    evaluate_game_answer,
    get_game_statistics,
    create_game_session,
    update_game_progress,
    calculate_game_score,
)


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Game Management Routes ===
@game_bp.route("/games", methods=["GET"])
def get_available_games_route():
    """
    Get available educational games for the current user.

    This endpoint retrieves a list of available games based on the user's
    skill level and learning preferences.

    Query Parameters:
        - skill_level: Filter by skill level
        - game_type: Filter by game type
        - limit: Maximum number of games to return

    Returns:
        JSON response with available games or unauthorized error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Get query parameters
        skill_level = request.args.get("skill_level")
        game_type = request.args.get("game_type")
        limit = int(request.args.get("limit", 20))

        # Build query conditions
        where_conditions = []
        params = []

        if skill_level:
            where_conditions.append("skill_level = ?")
            params.append(skill_level)

        if game_type:
            where_conditions.append("game_type = ?")
            params.append(game_type)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get available games
        games = select_rows(
            "educational_games",
            columns="id, title, description, game_type, skill_level, duration, difficulty",
            where=where_clause,
            params=tuple(params),
            order_by="skill_level ASC, title ASC",
            limit=limit
        )

        return jsonify({
            "games": games,
            "total": len(games),
            "limit": limit
        })

    except Exception as e:
        logger.error(f"Error getting available games: {e}")
        return jsonify({"error": "Failed to retrieve available games"}), 500


@game_bp.route("/games/<int:game_id>", methods=["GET"])
def get_game_details_route(game_id: int):
    """
    Get detailed information about a specific game.

    This endpoint retrieves comprehensive information about a game
    including rules, objectives, and configuration.

    Args:
        game_id: Unique identifier of the game

    Returns:
        JSON response with game details or not found error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401

        # Get game details
        game = select_one(
            "educational_games",
            columns="*",
            where="id = ?",
            params=(game_id,)
        )

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Get user's previous performance for this game
        previous_results = select_rows(
            "game_results",
            columns="score, completed_at, time_spent",
            where="user_id = ? AND game_id = ?",
            params=(user, game_id),
            order_by="completed_at DESC",
            limit=5
        )

        return jsonify({
            "game": game,
            "previous_performance": previous_results,
            "best_score": max([r.get("score", 0) for r in previous_results]) if previous_results else 0,
            "total_plays": len(previous_results)
        })

    except Exception as e:
        logger.error(f"Error getting game details for game {game_id}: {e}")
        return jsonify({"error": "Failed to retrieve game details"}), 500


# === Game Sessions Routes ===
@game_bp.route("/games/<int:game_id>/start", methods=["POST"])
def start_game_session_route(game_id: int):
    """
    Start a new game session.

    This endpoint creates a new game session and initializes the game state
    for the user to begin playing.

    Args:
        game_id: Unique identifier of the game to start

    Request Body:
        - difficulty: Game difficulty level (optional)
        - custom_settings: Custom game settings (optional)

    Returns:
        JSON response with session information or error details
    """
    try:
        user = require_user()
        data = request.get_json() or {}

        # Check if game exists
        game = select_one(
            "educational_games",
            columns="id, title, game_type, skill_level",
            where="id = ?",
            params=(game_id,)
        )

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Get game settings
        difficulty = data.get("difficulty", "medium")
        custom_settings = data.get("custom_settings", {})

        # Create game session
        session_data = {
            "user_id": user,
            "game_id": game_id,
            "difficulty": difficulty,
            "custom_settings": custom_settings,
            "started_at": datetime.now().isoformat(),
            "status": "active"
        }

        session_id = create_game_session(session_data)

        if session_id:
            return jsonify({
                "message": "Game session started successfully",
                "session_id": session_id,
                "game": {
                    "id": game_id,
                    "title": game.get("title"),
                    "type": game.get("game_type"),
                    "skill_level": game.get("skill_level")
                },
                "settings": {
                    "difficulty": difficulty,
                    "custom_settings": custom_settings
                }
            })
        else:
            return jsonify({"error": "Failed to start game session"}), 500

    except Exception as e:
        logger.error(f"Error starting game session for game {game_id}: {e}")
        return jsonify({"error": "Failed to start game session"}), 500


@game_bp.route("/sessions/<session_id>/progress", methods=["POST"])
def update_game_progress_route(session_id: str):
    """
    Update game session progress.

    This endpoint allows the game to update the current session progress
    including score, level, and game state.

    Args:
        session_id: Unique identifier of the game session

    Request Body:
        - score: Current game score
        - level: Current game level
        - progress: Progress percentage (0-100)
        - game_state: Current game state data

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if session exists and belongs to user
        session = select_one(
            "game_sessions",
            columns="id, game_id, status",
            where="session_id = ? AND user_id = ?",
            params=(session_id, user)
        )

        if not session:
            return jsonify({"error": "Game session not found"}), 404

        if session.get("status") != "active":
            return jsonify({"error": "Game session is not active"}), 400

        # Prepare progress update
        progress_data = {
            "score": data.get("score", 0),
            "level": data.get("level", 1),
            "progress": data.get("progress", 0),
            "game_state": data.get("game_state", {}),
            "updated_at": datetime.now().isoformat()
        }

        # Update game progress
        success = update_game_progress(session_id, progress_data)

        if success:
            return jsonify({
                "message": "Game progress updated successfully",
                "session_id": session_id,
                "current_score": progress_data["score"],
                "current_level": progress_data["level"],
                "progress": progress_data["progress"]
            })
        else:
            return jsonify({"error": "Failed to update game progress"}), 500

    except Exception as e:
        logger.error(f"Error updating game progress for session {session_id}: {e}")
        return jsonify({"error": "Failed to update game progress"}), 500


@game_bp.route("/sessions/<session_id>/end", methods=["POST"])
def end_game_session_route(session_id: str):
    """
    End a game session and record final results.

    This endpoint finalizes a game session and records the complete
    results for analytics and progress tracking.

    Args:
        session_id: Unique identifier of the game session

    Request Body:
        - final_score: Final game score
        - time_spent: Total time spent playing (seconds)
        - completed: Whether the game was completed
        - achievements: List of achievements earned

    Returns:
        JSON response with final results or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if session exists and belongs to user
        session = select_one(
            "game_sessions",
            columns="id, game_id, started_at",
            where="session_id = ? AND user_id = ?",
            params=(session_id, user)
        )

        if not session:
            return jsonify({"error": "Game session not found"}), 404

        # Calculate final results
        final_score = data.get("final_score", 0)
        time_spent = data.get("time_spent", 0)
        completed = data.get("completed", False)
        achievements = data.get("achievements", [])

        # Calculate performance metrics
        performance_metrics = calculate_game_score(
            final_score, time_spent, completed, achievements
        )

        # Record game results
        result_data = {
            "user_id": user,
            "game_id": session.get("game_id"),
            "session_id": session_id,
            "score": final_score,
            "time_spent": time_spent,
            "completed": completed,
            "performance_rating": performance_metrics.get("rating", "average"),
            "achievements": achievements,
            "completed_at": datetime.now().isoformat()
        }

        result_id = insert_row("game_results", result_data)

        # Update session status
        update_row(
            "game_sessions",
            {"status": "completed", "ended_at": datetime.now().isoformat()},
            "WHERE session_id = ?",
            (session_id,)
        )

        if result_id:
            return jsonify({
                "message": "Game session ended successfully",
                "session_id": session_id,
                "final_score": final_score,
                "performance_rating": performance_metrics.get("rating"),
                "achievements": achievements,
                "result_id": result_id
            })
        else:
            return jsonify({"error": "Failed to record game results"}), 500

    except Exception as e:
        logger.error(f"Error ending game session {session_id}: {e}")
        return jsonify({"error": "Failed to end game session"}), 500


# === Game Results Routes ===
@game_bp.route("/results", methods=["GET"])
def get_game_results_route():
    """
    Get user's game results and performance history.

    This endpoint retrieves the user's game performance history
    including scores, completion times, and achievements.

    Query Parameters:
        - game_id: Filter by specific game
        - limit: Maximum number of results to return
        - offset: Pagination offset

    Returns:
        JSON response with game results or unauthorized error
    """
    try:
        user = require_user()

        # Get query parameters
        game_id = request.args.get("game_id")
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        # Build query conditions
        where_conditions = ["user_id = ?"]
        params = [user]

        if game_id:
            where_conditions.append("game_id = ?")
            params.append(game_id)

        where_clause = " AND ".join(where_conditions)

        # Get game results
        results = select_rows(
            "game_results",
            columns="id, game_id, score, time_spent, completed, performance_rating, achievements, completed_at",
            where=where_clause,
            params=tuple(params),
            order_by="completed_at DESC",
            limit=limit
        )

        # Get game titles for results
        game_titles = {}
        if results:
            game_ids = list(set(r.get("game_id") for r in results))
            games = select_rows(
                "educational_games",
                columns="id, title",
                where=f"id IN ({','.join(['?'] * len(game_ids))})",
                params=tuple(game_ids)
            )
            game_titles = {g.get("id"): g.get("title") for g in games}

        # Add game titles to results
        for result in results:
            result["game_title"] = game_titles.get(result.get("game_id"), "Unknown Game")

        return jsonify({
            "results": results,
            "total": len(results),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.error(f"Error getting game results for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve game results"}), 500


@game_bp.route("/results/<int:result_id>", methods=["GET"])
def get_game_result_details_route(result_id: int):
    """
    Get detailed information about a specific game result.

    This endpoint retrieves comprehensive details about a specific
    game result including performance metrics and achievements.

    Args:
        result_id: Unique identifier of the game result

    Returns:
        JSON response with result details or not found error
    """
    try:
        user = require_user()

        # Get result details
        result = select_one(
            "game_results",
            columns="*",
            where="id = ? AND user_id = ?",
            params=(result_id, user)
        )

        if not result:
            return jsonify({"error": "Game result not found"}), 404

        # Get game details
        game = select_one(
            "educational_games",
            columns="title, description, game_type, skill_level",
            where="id = ?",
            params=(result.get("game_id"),)
        )

        # Get session details
        session = select_one(
            "game_sessions",
            columns="started_at, difficulty, custom_settings",
            where="session_id = ?",
            params=(result.get("session_id"),)
        )

        return jsonify({
            "result": result,
            "game": game,
            "session": session,
            "performance_analysis": {
                "score_percentage": (result.get("score", 0) / 100) * 100,
                "time_efficiency": result.get("time_spent", 0) / max(result.get("score", 1), 1),
                "completion_rate": 100 if result.get("completed") else 0
            }
        })

    except Exception as e:
        logger.error(f"Error getting game result details for result {result_id}: {e}")
        return jsonify({"error": "Failed to retrieve game result details"}), 500


# === Game Analytics Routes ===
@game_bp.route("/analytics", methods=["GET"])
def get_game_analytics_route():
    """
    Get comprehensive game analytics for the user.

    This endpoint provides detailed analytics about the user's
    gaming performance and learning effectiveness.

    Query Parameters:
        - timeframe: Analytics timeframe (week, month, year)
        - game_type: Filter by game type

    Returns:
        JSON response with game analytics or unauthorized error
    """
    try:
        user = require_user()

        # Get query parameters
        timeframe = request.args.get("timeframe", "month")
        game_type = request.args.get("game_type")

        # Validate timeframe
        valid_timeframes = ["week", "month", "year"]
        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Get game analytics
        analytics = get_game_analytics(user, timeframe, game_type)

        return jsonify({
            "user": user,
            "timeframe": timeframe,
            "game_type": game_type,
            "analytics": analytics,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting game analytics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve game analytics"}), 500


@game_bp.route("/analytics/performance", methods=["GET"])
def get_performance_analytics_route():
    """
    Get detailed performance analytics across all games.

    This endpoint provides performance analysis including
    improvement trends, skill development, and learning patterns.

    Query Parameters:
        - period: Analysis period (week, month, quarter)
        - metric: Performance metric (score, time, accuracy)

    Returns:
        JSON response with performance analytics or unauthorized error
    """
    try:
        user = require_user()

        # Get query parameters
        period = request.args.get("period", "month")
        metric = request.args.get("metric", "score")

        # Validate parameters
        valid_periods = ["week", "month", "quarter"]
        valid_metrics = ["score", "time", "accuracy"]

        if period not in valid_periods:
            return jsonify({"error": f"Invalid period: {period}"}), 400

        if metric not in valid_metrics:
            return jsonify({"error": f"Invalid metric: {metric}"}), 400

        # Get performance data
        performance_data = select_rows(
            "game_results",
            columns="score, time_spent, completed, completed_at, game_id",
            where="user_id = ?",
            params=(user,),
            order_by="completed_at DESC"
        )

        # Analyze performance trends
        trends = {
            "period": period,
            "metric": metric,
            "data_points": [],
            "overall_trend": "stable",
            "improvement_rate": 0
        }

        # Group data by time periods and calculate metrics
        if metric == "score":
            # Calculate average scores over time
            daily_scores = {}
            for result in performance_data:
                date = result.get("completed_at", "")[:10]
                score = result.get("score", 0)
                if date not in daily_scores:
                    daily_scores[date] = {"total_score": 0, "count": 0}
                daily_scores[date]["total_score"] += score
                daily_scores[date]["count"] += 1

            for date, data in sorted(daily_scores.items()):
                avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
                trends["data_points"].append({
                    "date": date,
                    "value": round(avg_score, 2)
                })

        elif metric == "time":
            # Calculate average completion times
            daily_times = {}
            for result in performance_data:
                date = result.get("completed_at", "")[:10]
                time_spent = result.get("time_spent", 0)
                if date not in daily_times:
                    daily_times[date] = {"total_time": 0, "count": 0}
                daily_times[date]["total_time"] += time_spent
                daily_times[date]["count"] += 1

            for date, data in sorted(daily_times.items()):
                avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
                trends["data_points"].append({
                    "date": date,
                    "value": round(avg_time, 2)
                })

        elif metric == "accuracy":
            # Calculate completion rates
            daily_completions = {}
            for result in performance_data:
                date = result.get("completed_at", "")[:10]
                completed = result.get("completed", False)
                if date not in daily_completions:
                    daily_completions[date] = {"total": 0, "completed": 0}
                daily_completions[date]["total"] += 1
                if completed:
                    daily_completions[date]["completed"] += 1

            for date, data in sorted(daily_completions.items()):
                accuracy = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
                trends["data_points"].append({
                    "date": date,
                    "value": round(accuracy, 2)
                })

        # Calculate improvement rate
        if len(trends["data_points"]) >= 2:
            first_value = trends["data_points"][0]["value"]
            last_value = trends["data_points"][-1]["value"]
            if first_value > 0:
                trends["improvement_rate"] = round(((last_value - first_value) / first_value) * 100, 2)

        return jsonify({
            "user": user,
            "performance_trends": trends,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting performance analytics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve performance analytics"}), 500
