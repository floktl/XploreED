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
from typing import Optional, List
from datetime import datetime

from flask import request, jsonify # type: ignore
from infrastructure.imports import Imports
from api.middleware.auth import get_current_user, require_user
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
from shared.exceptions import DatabaseError, AIEvaluationError


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
        - skill_level (str, optional): Filter by skill level
        - game_type (str, optional): Filter by game type
        - limit (int, optional): Maximum number of games to return (default: 20)

    Valid Game Types:
        - vocabulary: Vocabulary building games
        - grammar: Grammar practice games
        - comprehension: Reading comprehension games
        - pronunciation: Pronunciation practice games
        - listening: Listening comprehension games

    JSON Response Structure:
        {
            "games": [                             # Array of available games
                {
                    "id": int,                     # Game identifier
                    "title": str,                  # Game title
                    "description": str,            # Game description
                    "game_type": str,              # Type of game
                    "skill_level": str,            # Required skill level
                    "duration": int,               # Estimated duration in minutes
                    "difficulty": str,             # Game difficulty
                    "prerequisites": [str],        # Required prerequisites
                    "learning_objectives": [str]   # Learning objectives
                }
            ],
            "total": int,                          # Total number of games
            "user_level": str,                     # User's current skill level
            "recommended_games": [int]             # Recommended game IDs
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
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

        # Get user's current level
        user_level = get_user_game_level(user)

        # Get recommended games based on user level
        recommended_games = select_rows(
            "educational_games",
            columns="id",
            where="skill_level = ?",
            params=(user_level,),
            limit=5
        )

        return jsonify({
            "games": games,
            "total": len(games),
            "user_level": user_level,
            "recommended_games": [g["id"] for g in recommended_games]
        })

    except Exception as e:
        logger.error(f"Error getting available games: {e}")
        return jsonify({"error": "Failed to retrieve games"}), 500


@game_bp.route("/games/<int:game_id>", methods=["GET"])
def get_game_details_route(game_id: int):
    """
    Get detailed information about a specific game.

    This endpoint retrieves comprehensive information about a game
    including rules, objectives, and user progress.

    Path Parameters:
        - game_id (int, required): Unique identifier of the game

    JSON Response Structure:
        {
            "game": {                              # Game information
                "id": int,                         # Game identifier
                "title": str,                      # Game title
                "description": str,                # Detailed description
                "game_type": str,                  # Type of game
                "skill_level": str,                # Required skill level
                "duration": int,                   # Estimated duration in minutes
                "difficulty": str,                 # Game difficulty
                "rules": [str],                    # Game rules
                "objectives": [str],               # Learning objectives
                "prerequisites": [str],            # Required prerequisites
                "features": [str]                  # Game features
            },
            "user_progress": {                     # User's progress in this game
                "best_score": float,               # Best score achieved
                "total_plays": int,                # Total number of plays
                "average_score": float,            # Average score
                "last_played": str,                # Last play timestamp
                "completion_rate": float           # Completion rate percentage
            },
            "leaderboard": [                       # Top players for this game
                {
                    "username": str,               # Player username
                    "score": float,                # Player score
                    "rank": int,                   # Player rank
                    "played_at": str               # Play timestamp
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Game not found
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get game details
        game = select_one(
            "educational_games",
            columns="*",
            where="id = ?",
            params=(game_id,)
        )

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Get user's progress for this game
        user_progress = select_one(
            "game_results",
            columns="MAX(score) as best_score, COUNT(*) as total_plays, AVG(score) as average_score, MAX(created_at) as last_played",
            where="game_id = ? AND username = ?",
            params=(game_id, user)
        )

        # Get leaderboard for this game
        leaderboard = select_rows(
            "game_results",
            columns="username, score, created_at",
            where="game_id = ?",
            params=(game_id,),
            order_by="score DESC",
            limit=10
        )

        # Add ranks to leaderboard
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1

        return jsonify({
            "game": game,
            "user_progress": user_progress or {},
            "leaderboard": leaderboard
        })

    except Exception as e:
        logger.error(f"Error getting game details for game {game_id}: {e}")
        return jsonify({"error": "Failed to retrieve game details"}), 500


@game_bp.route("/games/<int:game_id>/start", methods=["POST"])
def start_game_session_route(game_id: int):
    """
    Start a new game session.

    This endpoint creates a new game session and initializes
    the game state for the user.

    Path Parameters:
        - game_id (int, required): Unique identifier of the game

    Request Body:
        - difficulty (str, optional): Game difficulty level
        - settings (object, optional): Game-specific settings

    JSON Response Structure:
        {
            "session_id": str,                     # Game session identifier
            "game": {                              # Game information
                "id": int,                         # Game identifier
                "title": str,                      # Game title
                "game_type": str,                  # Type of game
                "difficulty": str                  # Selected difficulty
            },
            "initial_state": {                     # Initial game state
                "level": int,                      # Current level
                "score": int,                      # Current score
                "lives": int,                      # Remaining lives
                "time_limit": int,                 # Time limit in seconds
                "rounds": int                      # Total rounds
            },
            "first_round": {                       # First round data
                "question": str,                   # Question or prompt
                "options": [str],                  # Answer options (if applicable)
                "hint": str                        # Hint for the question
            },
            "started_at": str                      # Session start timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid game or settings
        - 401: Unauthorized
        - 404: Game not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json() or {}

        # Check if game exists
        game = select_one(
            "educational_games",
            columns="*",
            where="id = ?",
            params=(game_id,)
        )

        if not game:
            return jsonify({"error": "Game not found"}), 404

        # Get game settings
        difficulty = data.get("difficulty", "medium")
        settings = data.get("settings", {})

        # Create game session
        session_data = {
            "username": user,
            "game_id": game_id,
            "difficulty": difficulty,
            "settings": str(settings),
            "started_at": datetime.now().isoformat(),
            "status": "active"
        }

        session_id = create_game_session(session_data)

        if not session_id:
            return jsonify({"error": "Failed to create game session"}), 500

        # Generate first round
        first_round = create_game_round(session_id, game_id, difficulty)

        return jsonify({
            "session_id": session_id,
            "game": {
                "id": game_id,
                "title": game["title"],
                "game_type": game["game_type"],
                "difficulty": difficulty
            },
            "initial_state": {
                "level": 1,
                "score": 0,
                "lives": 3,
                "time_limit": game.get("duration", 300) * 60,
                "rounds": 10
            },
            "first_round": first_round,
            "started_at": session_data["started_at"]
        })

    except Exception as e:
        logger.error(f"Error starting game session for game {game_id}: {e}")
        return jsonify({"error": "Failed to start game session"}), 500


@game_bp.route("/sessions/<session_id>/progress", methods=["POST"])
def update_game_progress_route(session_id: str):
    """
    Update game session progress.

    This endpoint processes user answers and updates the game
    session progress with new rounds and scores.

    Path Parameters:
        - session_id (str, required): Game session identifier

    Request Body:
        - answer (str, required): User's answer
        - round_number (int, required): Current round number
        - time_spent (int, optional): Time spent on this round

    JSON Response Structure:
        {
            "session_id": str,                     # Game session identifier
            "round_result": {                      # Round result
                "correct": bool,                   # Whether answer is correct
                "score": int,                      # Points earned
                "feedback": str,                   # Feedback message
                "explanation": str                 # Answer explanation
            },
            "game_state": {                        # Updated game state
                "level": int,                      # Current level
                "score": int,                      # Total score
                "lives": int,                      # Remaining lives
                "rounds_completed": int,           # Rounds completed
                "accuracy": float                  # Current accuracy percentage
            },
            "next_round": {                        # Next round data
                "question": str,                   # Question or prompt
                "options": [str],                  # Answer options (if applicable)
                "hint": str,                       # Hint for the question
                "time_limit": int                  # Time limit for this round
            },
            "session_complete": bool               # Whether session is complete
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or session
        - 401: Unauthorized
        - 404: Session not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        answer = data.get("answer", "").strip()
        round_number = data.get("round_number")
        time_spent = data.get("time_spent", 0)

        if not answer:
            return jsonify({"error": "Answer is required"}), 400

        if round_number is None:
            return jsonify({"error": "Round number is required"}), 400

        # Check if session exists and belongs to user
        session = select_one(
            "game_sessions",
            columns="*",
            where="session_id = ? AND username = ?",
            params=(session_id, user)
        )

        if not session:
            return jsonify({"error": "Game session not found"}), 404

        # Evaluate the answer
        round_result = evaluate_game_answer(session_id, answer, round_number, time_spent)

        # Update game progress
        game_state = update_game_progress(session_id, round_result)

        # Check if session is complete
        session_complete = game_state.get("lives", 0) <= 0 or game_state.get("rounds_completed", 0) >= 10

        # Generate next round if session is not complete
        next_round = None
        if not session_complete:
            next_round = create_game_round(session_id, session["game_id"], session["difficulty"])

        return jsonify({
            "session_id": session_id,
            "round_result": round_result,
            "game_state": game_state,
            "next_round": next_round,
            "session_complete": session_complete
        })

    except Exception as e:
        logger.error(f"Error updating game progress for session {session_id}: {e}")
        return jsonify({"error": "Failed to update game progress"}), 500


@game_bp.route("/sessions/<session_id>/end", methods=["POST"])
def end_game_session_route(session_id: str):
    """
    End a game session and save results.

    This endpoint finalizes a game session, calculates final scores,
    and saves the results to the user's profile.

    Path Parameters:
        - session_id (str, required): Game session identifier

    Request Body:
        - reason (str, optional): Reason for ending session (completed, abandoned, error)

    JSON Response Structure:
        {
            "session_id": str,                     # Game session identifier
            "final_results": {                     # Final session results
                "total_score": int,                # Final total score
                "rounds_completed": int,           # Total rounds completed
                "accuracy": float,                 # Overall accuracy percentage
                "time_spent": int,                 # Total time spent in seconds
                "lives_remaining": int,            # Lives remaining at end
                "performance_rating": str          # Performance rating (excellent, good, fair, poor)
            },
            "achievements": [                      # Achievements earned
                {
                    "id": str,                     # Achievement identifier
                    "title": str,                  # Achievement title
                    "description": str,            # Achievement description
                    "earned_at": str               # Achievement timestamp
                }
            ],
            "improvements": [str],                 # Areas for improvement
            "next_recommendations": [              # Recommended next steps
                {
                    "game_id": int,                # Recommended game ID
                    "reason": str                  # Reason for recommendation
                }
            ],
            "completed_at": str                    # Session completion timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Session not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json() or {}

        reason = data.get("reason", "completed")

        # Check if session exists and belongs to user
        session = select_one(
            "game_sessions",
            columns="*",
            where="session_id = ? AND username = ?",
            params=(session_id, user)
        )

        if not session:
            return jsonify({"error": "Game session not found"}), 404

        # Calculate final results
        final_results = calculate_game_score(session_id)

        # Update session status
        update_row(
            "game_sessions",
            {
                "status": "completed",
                "ended_at": datetime.now().isoformat(),
                "final_score": final_results["total_score"],
                "completion_reason": reason
            },
            "WHERE session_id = ?",
            (session_id,)
        )

        # Save results to user's profile
        result_data = {
            "username": user,
            "game_id": session["game_id"],
            "session_id": session_id,
            "score": final_results["total_score"],
            "accuracy": final_results["accuracy"],
            "time_spent": final_results["time_spent"],
            "completed_at": datetime.now().isoformat()
        }

        insert_row("game_results", result_data)

        # Get achievements and recommendations
        achievements = get_game_achievements(user, session["game_id"], final_results)
        recommendations = get_game_recommendations(user, final_results)

        return jsonify({
            "session_id": session_id,
            "final_results": final_results,
            "achievements": achievements,
            "improvements": get_improvement_areas(final_results),
            "next_recommendations": recommendations,
            "completed_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error ending game session {session_id}: {e}")
        return jsonify({"error": "Failed to end game session"}), 500


@game_bp.route("/results", methods=["GET"])
def get_game_results_route():
    """
    Get user's game results and history.

    This endpoint retrieves the user's game playing history
    including scores, achievements, and performance trends.

    Query Parameters:
        - game_type (str, optional): Filter by game type
        - limit (int, optional): Maximum number of results (default: 20)
        - offset (int, optional): Pagination offset (default: 0)
        - sort_by (str, optional): Sort field (score, date, accuracy)

    JSON Response Structure:
        {
            "results": [                           # Array of game results
                {
                    "id": int,                     # Result identifier
                    "game_id": int,                # Game identifier
                    "game_title": str,             # Game title
                    "game_type": str,              # Game type
                    "score": int,                  # Achieved score
                    "accuracy": float,             # Accuracy percentage
                    "time_spent": int,             # Time spent in seconds
                    "completed_at": str,           # Completion timestamp
                    "performance_rating": str      # Performance rating
                }
            ],
            "summary": {                           # Results summary
                "total_games": int,                # Total games played
                "average_score": float,            # Average score
                "best_score": int,                 # Best score achieved
                "total_time": int,                 # Total time spent
                "favorite_game": str               # Most played game
            },
            "achievements": [                      # User achievements
                {
                    "id": str,                     # Achievement identifier
                    "title": str,                  # Achievement title
                    "description": str,            # Achievement description
                    "earned_at": str,              # Achievement timestamp
                    "icon": str                    # Achievement icon
                }
            ],
            "total": int,                          # Total number of results
            "limit": int,                          # Requested limit
            "offset": int                          # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        game_type = request.args.get("game_type")
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        sort_by = request.args.get("sort_by", "date")

        # Build query conditions
        where_conditions = ["username = ?"]
        params = [user]

        if game_type:
            where_conditions.append("game_type = ?")
            params.append(game_type)

        where_clause = " AND ".join(where_conditions)

        # Get user's game results
        results = select_rows(
            "game_results",
            columns="*",
            where=where_clause,
            params=tuple(params),
            order_by=f"{sort_by} DESC",
            limit=limit,
            offset=offset
        )

        # Get results summary
        summary = get_game_statistics(user)

        # Get user achievements
        achievements = select_rows(
            "user_achievements",
            columns="*",
            where="username = ?",
            params=(user,),
            order_by="earned_at DESC"
        )

        return jsonify({
            "results": results,
            "summary": summary,
            "achievements": achievements,
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
    game session including round-by-round performance.

    Path Parameters:
        - result_id (int, required): Game result identifier

    JSON Response Structure:
        {
            "result": {                            # Game result information
                "id": int,                         # Result identifier
                "game_id": int,                    # Game identifier
                "game_title": str,                 # Game title
                "game_type": str,                  # Game type
                "score": int,                      # Final score
                "accuracy": float,                 # Overall accuracy
                "time_spent": int,                 # Total time spent
                "completed_at": str,               # Completion timestamp
                "difficulty": str,                 # Game difficulty
                "session_duration": int            # Session duration in seconds
            },
            "rounds": [                            # Round-by-round details
                {
                    "round_number": int,           # Round number
                    "question": str,               # Question asked
                    "user_answer": str,            # User's answer
                    "correct_answer": str,         # Correct answer
                    "correct": bool,               # Whether answer was correct
                    "score": int,                  # Points earned
                    "time_spent": int,             # Time spent on round
                    "feedback": str                # Round feedback
                }
            ],
            "performance_analysis": {              # Performance analysis
                "strengths": [str],                # Identified strengths
                "weaknesses": [str],               # Areas for improvement
                "recommendations": [str],          # Learning recommendations
                "skill_progress": {                # Skill progress
                    "vocabulary": float,           # Vocabulary improvement
                    "grammar": float,              # Grammar improvement
                    "comprehension": float         # Comprehension improvement
                }
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Result not found
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get game result
        result = select_one(
            "game_results",
            columns="*",
            where="id = ? AND username = ?",
            params=(result_id, user)
        )

        if not result:
            return jsonify({"error": "Game result not found"}), 404

        # Get round-by-round details
        rounds = select_rows(
            "game_rounds",
            columns="*",
            where="session_id = ?",
            params=(result["session_id"],),
            order_by="round_number ASC"
        )

        # Get performance analysis
        performance_analysis = analyze_game_performance(result, rounds)

        return jsonify({
            "result": result,
            "rounds": rounds,
            "performance_analysis": performance_analysis
        })

    except Exception as e:
        logger.error(f"Error getting game result details for result {result_id}: {e}")
        return jsonify({"error": "Failed to retrieve game result details"}), 500


@game_bp.route("/analytics", methods=["GET"])
def get_game_analytics_route():
    """
    Get comprehensive game analytics for the user.

    This endpoint provides detailed analytics about the user's
    game playing patterns, performance trends, and learning progress.

    Query Parameters:
        - timeframe (str, optional): Analytics timeframe (week, month, year)
        - game_type (str, optional): Filter by game type

    JSON Response Structure:
        {
            "overview": {                          # Overview statistics
                "total_games_played": int,         # Total games played
                "total_time_spent": int,           # Total time spent in minutes
                "average_score": float,            # Average score
                "improvement_rate": float,         # Score improvement rate
                "favorite_game_type": str          # Most played game type
            },
            "performance_trends": {                # Performance trends
                "daily_scores": [                  # Daily score progression
                    {
                        "date": str,               # Date
                        "average_score": float,    # Average score for day
                        "games_played": int        # Number of games played
                    }
                ],
                "weekly_progress": [               # Weekly progress
                    {
                        "week": str,               # Week identifier
                        "total_score": int,        # Total score for week
                        "accuracy": float          # Weekly accuracy
                    }
                ]
            },
            "game_type_breakdown": [               # Performance by game type
                {
                    "game_type": str,              # Game type
                    "games_played": int,           # Number of games played
                    "average_score": float,        # Average score
                    "best_score": int,             # Best score
                    "total_time": int              # Total time spent
                }
            ],
            "learning_insights": {                 # Learning insights
                "strengths": [str],                # User strengths
                "weaknesses": [str],               # Areas for improvement
                "recommendations": [str],          # Learning recommendations
                "next_goals": [str]                # Suggested next goals
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        timeframe = request.args.get("timeframe", "month")
        game_type = request.args.get("game_type")

        # Get analytics data
        analytics = get_game_analytics(user, timeframe, game_type)

        return jsonify(analytics)

    except Exception as e:
        logger.error(f"Error getting game analytics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve game analytics"}), 500


@game_bp.route("/analytics/performance", methods=["GET"])
def get_performance_analytics_route():
    """
    Get detailed performance analytics and insights.

    This endpoint provides in-depth performance analysis including
    skill development, learning patterns, and personalized insights.

    Query Parameters:
        - skill_area (str, optional): Focus on specific skill area
        - comparison_period (str, optional): Period for comparison

    JSON Response Structure:
        {
            "skill_development": {                 # Skill development tracking
                "vocabulary": {                    # Vocabulary skills
                    "current_level": str,          # Current level
                    "progress_percentage": float,  # Progress percentage
                    "words_learned": int,          # Words learned
                    "retention_rate": float        # Retention rate
                },
                "grammar": {                       # Grammar skills
                    "current_level": str,          # Current level
                    "progress_percentage": float,  # Progress percentage
                    "concepts_mastered": int,      # Concepts mastered
                    "accuracy_rate": float         # Accuracy rate
                },
                "comprehension": {                 # Comprehension skills
                    "current_level": str,          # Current level
                    "progress_percentage": float,  # Progress percentage
                    "texts_completed": int,        # Texts completed
                    "understanding_rate": float    # Understanding rate
                }
            },
            "learning_patterns": {                 # Learning pattern analysis
                "preferred_times": [str],          # Preferred learning times
                "session_duration": {              # Session duration patterns
                    "average": int,                # Average session length
                    "optimal": int,                # Optimal session length
                    "distribution": [int]          # Duration distribution
                },
                "difficulty_preference": str,      # Preferred difficulty level
                "game_type_preference": str        # Preferred game type
            },
            "improvement_areas": [                 # Areas needing improvement
                {
                    "skill": str,                  # Skill area
                    "current_performance": float,  # Current performance
                    "target_performance": float,   # Target performance
                    "recommended_actions": [str]   # Recommended actions
                }
            ],
            "achievement_progress": {              # Achievement progress
                "total_achievements": int,         # Total achievements
                "recent_achievements": [str],      # Recently earned achievements
                "next_achievements": [             # Upcoming achievements
                    {
                        "title": str,              # Achievement title
                        "progress": float,         # Progress percentage
                        "remaining": str           # What's remaining
                    }
                ]
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        skill_area = request.args.get("skill_area")
        comparison_period = request.args.get("comparison_period", "month")

        # Get performance analytics
        performance_analytics = get_performance_analytics(user, skill_area, comparison_period)

        return jsonify(performance_analytics)

    except Exception as e:
        logger.error(f"Error getting performance analytics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve performance analytics"}), 500
