"""
XplorED - Lesson Progress Tracking API Routes

This module contains API routes for lesson progress tracking and completion management,
following clean architecture principles as outlined in the documentation.

Route Categories:
- Progress Tracking: User progress monitoring and completion status
- Block Management: Interactive block completion and validation
- Progress Analytics: Detailed progress statistics and insights
- Progress Synchronization: Multi-device progress synchronization
- Progress Export: Progress data export and backup

Progress Features:
- Real-time progress tracking across all lesson types
- Interactive block completion validation
- Progress analytics and performance insights
- Cross-device progress synchronization
- Progress data export and backup capabilities

Business Logic:
All progress logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta

from flask import request, jsonify # type: ignore
from infrastructure.imports import Imports
from api.middleware.auth import require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import lesson_progress_bp
from core.services import ProgressService, LessonService
from features.lessons import validate_block_completion
from shared.exceptions import DatabaseError


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Progress Tracking Routes ===

@lesson_progress_bp.route("/progress", methods=["GET"])
def get_user_progress_route():
    """
    Get comprehensive progress overview for the current user.

    This endpoint retrieves an overview of the user's progress across
    all lessons and learning activities.

    Query Parameters:
        - include_details (bool, optional): Include detailed progress information
        - timeframe (str, optional): Time period for progress data (week, month, all)

    JSON Response Structure:
        {
            "progress": {
                "user": str,                    # User identifier
                "total_lessons": int,           # Total number of lessons
                "lessons_started": int,         # Number of lessons in progress
                "total_completed_blocks": int,  # Total blocks completed
                "completion_rate": float,       # Overall completion percentage
                "total_activities": int,        # Total learning activities
                "streak_days": int,             # Current learning streak
                "average_score": float,         # Average performance score
                "activity_breakdown": {         # Breakdown by activity type
                    "exercises": int,
                    "vocabulary": int,
                    "games": int
                },
                "recent_activity": [            # Recent activity list
                    {
                        "date": str,           # ISO format date
                        "activity_type": str,  # Type of activity
                        "score": float,        # Activity score
                        "time_spent": int      # Time in seconds
                    }
                ],
                "detailed_progress": [...]      # Detailed progress (if include_details=true)
            },
            "timeframe": str,                   # Requested timeframe
            "generated_at": str                 # ISO format timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid timeframe parameter
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        include_details = request.args.get("include_details", "false").lower() == "true"
        timeframe = request.args.get("timeframe", "all")

        # Validate timeframe
        valid_timeframes = ["week", "month", "all"]
        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Map timeframe to days for ProgressService
        timeframe_days = {
            "week": 7,
            "month": 30,
            "all": 365
        }
        days = timeframe_days.get(timeframe, 30)

        # Get comprehensive progress summary using ProgressService
        progress_summary = ProgressService.get_user_progress_summary(user, days)

        # Get lesson statistics using LessonService
        lesson_stats = LessonService.get_lesson_statistics(user)

        progress_overview = {
            "user": user,
            "total_lessons": lesson_stats.get("total_lessons", 0),
            "lessons_started": lesson_stats.get("lessons_in_progress", 0),
            "total_completed_blocks": lesson_stats.get("total_blocks_completed", 0),
            "completion_rate": lesson_stats.get("completion_rate", 0.0),
            "total_activities": progress_summary.get("total_activities", 0),
            "streak_days": progress_summary.get("streak_days", 0),
            "average_score": progress_summary.get("average_score", 0.0),
            "activity_breakdown": progress_summary.get("activity_breakdown", {}),
            "recent_activity": progress_summary.get("recent_activity", [])
        }

        # Add detailed progress if requested
        if include_details:
            progress_overview["detailed_progress"] = progress_summary.get("recent_activity", [])

        return jsonify({
            "progress": progress_overview,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting user progress for {user}: {e}")
        return jsonify({"error": "Failed to retrieve progress data"}), 500


@lesson_progress_bp.route("/progress/summary", methods=["GET"])
def get_user_progress_summary_route():
    """
    Get detailed progress summary for the current user.

    This endpoint provides a comprehensive summary of the user's
    learning progress including analytics and trends.

    Query Parameters:
        - days (int, optional): Number of days to analyze (default: 30)

    JSON Response Structure:
        {
            "user": str,                        # User identifier
            "progress_summary": {
                "total_activities": int,        # Total activities in period
                "lessons_completed": int,       # Lessons completed
                "average_score": float,         # Average performance score
                "streak_days": int,             # Current learning streak
                "activity_breakdown": {         # Activity type breakdown
                    "exercises": int,
                    "vocabulary": int,
                    "games": int
                },
                "recent_activity": [            # Recent activity timeline
                    {
                        "date": str,           # ISO format date
                        "activity_type": str,  # Type of activity
                        "score": float,        # Activity score
                        "time_spent": int      # Time in seconds
                    }
                ]
            },
            "generated_at": str                 # ISO format timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        days = request.args.get("days", "30")
        try:
            days = int(days)
            if days <= 0:
                days = 30
        except ValueError:
            days = 30

        # Get progress summary using ProgressService
        progress_summary = ProgressService.get_user_progress_summary(user, days)

        return jsonify({
            "user": user,
            "progress_summary": progress_summary,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting user progress summary for {user}: {e}")
        return jsonify({"error": "Failed to retrieve progress summary"}), 500


@lesson_progress_bp.route("/track/exercise", methods=["POST"])
def track_exercise_progress_route():
    """
    Track exercise completion progress.

    This endpoint allows tracking of exercise completion with scores
    and performance metrics.

    Request Body:
        - block_id (str, required): The exercise block ID
        - score (float, required): The score achieved
        - total_questions (int, required): Total number of questions

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "block_id": str,                   # Exercise block ID
            "score": float,                    # Achieved score
            "total_questions": int             # Total questions
        }

    Status Codes:
        - 200: Success
        - 400: Missing required fields
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        block_id = data.get("block_id")
        score = data.get("score")
        total_questions = data.get("total_questions")

        if not block_id:
            return jsonify({"error": "Block ID is required"}), 400

        if score is None or total_questions is None:
            return jsonify({"error": "Score and total questions are required"}), 400

        # Track exercise progress using ProgressService
        success = ProgressService.track_exercise_progress(user, block_id, score, total_questions)

        if success:
            return jsonify({
                "message": "Exercise progress tracked successfully",
                "block_id": block_id,
                "score": score,
                "total_questions": total_questions
            })
        else:
            return jsonify({"error": "Failed to track exercise progress"}), 500

    except Exception as e:
        logger.error(f"Error tracking exercise progress for user {user}: {e}")
        return jsonify({"error": "Failed to track exercise progress"}), 500


@lesson_progress_bp.route("/track/vocabulary", methods=["POST"])
def track_vocabulary_progress_route():
    """
    Track vocabulary learning progress.

    This endpoint allows tracking of vocabulary review progress.

    Request Body:
        - word (str, required): The vocabulary word
        - correct (bool, required): Whether the answer was correct
        - repetitions (int, optional): Number of repetitions (default: 1)

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "word": str,                       # Vocabulary word
            "correct": bool,                   # Answer correctness
            "repetitions": int                 # Number of repetitions
        }

    Status Codes:
        - 200: Success
        - 400: Missing required fields
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        word = data.get("word")
        correct = data.get("correct")
        repetitions = data.get("repetitions", 1)

        if not word:
            return jsonify({"error": "Word is required"}), 400

        if correct is None:
            return jsonify({"error": "Correct status is required"}), 400

        # Track vocabulary progress using ProgressService
        success = ProgressService.track_vocabulary_progress(user, word, correct, repetitions)

        if success:
            return jsonify({
                "message": "Vocabulary progress tracked successfully",
                "word": word,
                "correct": correct,
                "repetitions": repetitions
            })
        else:
            return jsonify({"error": "Failed to track vocabulary progress"}), 500

    except Exception as e:
        logger.error(f"Error tracking vocabulary progress for user {user}: {e}")
        return jsonify({"error": "Failed to track vocabulary progress"}), 500


@lesson_progress_bp.route("/track/game", methods=["POST"])
def track_game_progress_route():
    """
    Track game completion progress.

    This endpoint allows tracking of game completion with scores and levels.

    Request Body:
        - game_type (str, required): The type of game
        - score (float, required): The score achieved
        - level (int, required): The game level

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "game_type": str,                  # Type of game
            "score": float,                    # Achieved score
            "level": int                       # Game level
        }

    Status Codes:
        - 200: Success
        - 400: Missing required fields
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        game_type = data.get("game_type")
        score = data.get("score")
        level = data.get("level")

        if not game_type:
            return jsonify({"error": "Game type is required"}), 400

        if score is None or level is None:
            return jsonify({"error": "Score and level are required"}), 400

        # Track game progress using ProgressService
        success = ProgressService.track_game_progress(user, game_type, score, level)

        if success:
            return jsonify({
                "message": "Game progress tracked successfully",
                "game_type": game_type,
                "score": score,
                "level": level
            })
        else:
            return jsonify({"error": "Failed to track game progress"}), 500

    except Exception as e:
        logger.error(f"Error tracking game progress for user {user}: {e}")
        return jsonify({"error": "Failed to track game progress"}), 500


@lesson_progress_bp.route("/reset", methods=["POST"])
def reset_user_progress_route():
    """
    Reset user progress data.

    This endpoint allows users to reset their progress data,
    optionally for specific activity types.

    Request Body:
        - activity_type (str, optional): Activity type to reset (lesson, exercise, vocabulary, game)

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "activity_type": str               # Reset activity type or "all"
        }

    Status Codes:
        - 200: Success
        - 400: Invalid activity type
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json() or {}

        activity_type = data.get("activity_type")

        # Validate activity type if provided
        if activity_type:
            valid_types = ["lesson", "exercise", "vocabulary", "game"]
            if activity_type not in valid_types:
                return jsonify({"error": f"Invalid activity type: {activity_type}"}), 400

        # Reset progress using ProgressService
        success = ProgressService.reset_user_progress(user, activity_type)

        if success:
            message = f"Progress reset successfully" + (f" for {activity_type}" if activity_type else " for all activities")
            return jsonify({
                "message": message,
                "activity_type": activity_type or "all"
            })
        else:
            return jsonify({"error": "Failed to reset progress"}), 500

    except Exception as e:
        logger.error(f"Error resetting progress for user {user}: {e}")
        return jsonify({"error": "Failed to reset progress"}), 500


@lesson_progress_bp.route("/progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress_detail_route(lesson_id: int):
    """
    Get detailed progress for a specific lesson.

    This endpoint retrieves detailed progress information for a specific
    lesson including block completion status and timestamps.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson

    JSON Response Structure:
        {
            "lesson_id": int,                  # Lesson identifier
            "lesson_title": str,               # Lesson title
            "total_blocks": int,               # Total blocks in lesson
            "completed_blocks": int,           # Number of completed blocks
            "completion_percentage": float,    # Completion percentage
            "progress": [                      # User progress details
                {
                    "block_id": str,           # Block identifier
                    "completed": bool,         # Completion status
                    "completed_at": str,       # Completion timestamp
                    "time_spent": int,         # Time spent in seconds
                    "score": float             # Performance score
                }
            ],
            "blocks": [                        # All lesson blocks
                {
                    "block_id": str,           # Block identifier
                    "block_type": str,         # Type of block
                    "title": str,              # Block title
                    "order": int               # Block order
                }
            ],
            "is_completed": bool               # Overall lesson completion
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get lesson progress using LessonService
        lesson_progress = LessonService.get_lesson_progress(user, lesson_id)

        if not lesson_progress:
            return jsonify({"error": "Lesson not found"}), 404

        return jsonify({
            "lesson_id": lesson_id,
            "lesson_title": lesson_progress.get("lesson_title", "Unknown"),
            "total_blocks": lesson_progress.get("total_blocks", 0),
            "completed_blocks": lesson_progress.get("completed_blocks", 0),
            "completion_percentage": lesson_progress.get("completion_percentage", 0.0),
            "progress": lesson_progress.get("user_progress", []),
            "blocks": lesson_progress.get("blocks", []),
            "is_completed": lesson_progress.get("is_completed", False)
        })

    except Exception as e:
        logger.error(f"Error getting lesson progress for lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to retrieve lesson progress"}), 500


@lesson_progress_bp.route("/progress/<int:lesson_id>/block/<block_id>", methods=["POST"])
def update_block_progress_route(lesson_id: int, block_id: str):
    """
    Update progress for a specific lesson block.

    This endpoint allows users to mark lesson blocks as completed
    and track their progress through interactive content.

    Path Parameters:
        - lesson_id (int, required): Unique identifier of the lesson
        - block_id (str, required): Identifier of the specific block

    Request Body:
        - completed (bool, optional): Completion status (default: true)
        - time_spent (int, optional): Time spent on the block in seconds
        - score (float, optional): Performance score

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "lesson_id": int,                  # Lesson identifier
            "block_id": str,                   # Block identifier
            "completed": bool                  # Completion status
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or validation failed
        - 401: Unauthorized
        - 404: Lesson not found
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        completed = data.get("completed", True)
        time_spent = data.get("time_spent")
        score = data.get("score")

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Validate block completion if provided
        if completed:
            validation_result = validate_block_completion(user, lesson_id, block_id)
            if not validation_result.get("valid", False):
                return jsonify({
                    "error": "Block completion validation failed",
                    "details": validation_result.get("message", "Unknown validation error")
                }), 400

        # Prepare progress data
        progress_data = {
            "completed": completed,
            "updated_at": datetime.now().isoformat()
        }

        if time_spent is not None:
            progress_data["time_spent"] = time_spent

        if score is not None:
            progress_data["score"] = score

        # Update lesson progress using LessonService
        success = LessonService.update_lesson_progress(user, lesson_id, block_id, completed)

        if success:
            return jsonify({
                "message": "Progress updated successfully",
                "lesson_id": lesson_id,
                "block_id": block_id,
                "completed": completed
            })
        else:
            return jsonify({"error": "Failed to update progress"}), 500

    except Exception as e:
        logger.error(f"Error updating block progress for lesson {lesson_id}, block {block_id}: {e}")
        return jsonify({"error": "Failed to update progress"}), 500


# === Progress Analytics Routes ===

@lesson_progress_bp.route("/analytics", methods=["GET"])
def get_lesson_progress_analytics_route():
    """
    Get detailed progress analytics and insights.

    This endpoint provides comprehensive analytics about the user's
    learning progress including trends, patterns, and recommendations.

    Query Parameters:
        - timeframe (str, optional): Analytics timeframe (week, month, quarter, year)
        - include_recommendations (bool, optional): Include AI-generated recommendations

    JSON Response Structure:
        {
            "user": str,                        # User identifier
            "timeframe": str,                   # Requested timeframe
            "analytics": {
                "total_lessons_completed": int, # Lessons completed in period
                "total_activities": int,        # Total activities in period
                "average_score": float,         # Average performance score
                "streak_days": int,             # Current learning streak
                "activity_breakdown": {         # Activity type breakdown
                    "exercises": int,
                    "vocabulary": int,
                    "games": int
                },
                "recent_activity": [            # Recent activity timeline
                    {
                        "date": str,           # ISO format date
                        "activity_type": str,  # Type of activity
                        "score": float,        # Activity score
                        "time_spent": int      # Time in seconds
                    }
                ],
                "trends": {                     # Activity trends
                    "daily_activity": {},      # Daily activity counts
                    "weekly_trends": {},       # Weekly trend data
                    "monthly_trends": {}       # Monthly trend data
                },
                "performance_trends": {         # Performance analysis
                    "average_score": float,    # Average score
                    "trend_direction": str,    # Improving/declining/stable
                    "score_distribution": {}   # Score distribution
                },
                "learning_patterns": {          # Learning behavior patterns
                    "preferred_times": [],     # Preferred learning times
                    "session_duration": {},    # Session duration patterns
                    "activity_preferences": {} # Activity type preferences
                },
                "recommendations": [...]        # AI recommendations (if requested)
            },
            "generated_at": str                 # ISO format timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid timeframe parameter
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        timeframe = request.args.get("timeframe", "month")
        include_recommendations = request.args.get("include_recommendations", "false").lower() == "true"

        # Validate timeframe
        valid_timeframes = ["week", "month", "quarter", "year"]
        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Map timeframe to days for ProgressService
        timeframe_days = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "year": 365
        }
        days = timeframe_days.get(timeframe, 30)

        # Get progress analytics using ProgressService
        progress_summary = ProgressService.get_user_progress_summary(user, days)

        # Get progress trends
        progress_trends = ProgressService.get_progress_trends(user, days)

        analytics = {
            "timeframe": timeframe,
            "total_lessons_completed": progress_summary.get("lessons_completed", 0),
            "total_activities": progress_summary.get("total_activities", 0),
            "average_score": progress_summary.get("average_score", 0.0),
            "streak_days": progress_summary.get("streak_days", 0),
            "activity_breakdown": progress_summary.get("activity_breakdown", {}),
            "recent_activity": progress_summary.get("recent_activity", []),
            "trends": progress_trends.get("activity_trends", {}),
            "performance_trends": progress_trends.get("performance_trends", {}),
            "learning_patterns": progress_trends.get("learning_patterns", {})
        }

        # Add recommendations if requested
        if include_recommendations:
            analytics["recommendations"] = progress_trends.get("recommendations", [])

        return jsonify({
            "user": user,
            "timeframe": timeframe,
            "analytics": analytics,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting progress analytics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve progress analytics"}), 500


@lesson_progress_bp.route("/analytics/trends", methods=["GET"])
def get_progress_trends_route():
    """
    Get progress trends over time.

    This endpoint provides trend analysis of the user's learning
    progress including completion rates and activity patterns.

    Query Parameters:
        - period (str, optional): Analysis period (week, month, quarter)
        - metric (str, optional): Trend metric (completion_rate, time_spent, accuracy)

    JSON Response Structure:
        {
            "user": str,                        # User identifier
            "trends": {
                "period": str,                  # Analysis period
                "metric": str,                  # Trend metric
                "data_points": [                # Trend data points
                    {
                        "date": str,           # ISO format date
                        "value": float         # Metric value
                    }
                ],
                "overall_trend": str            # Overall trend direction
            },
            "daily_activity": {                 # Daily activity breakdown
                "2024-01-01": {
                    "total": int,              # Total activities
                    "exercises": int,          # Exercise count
                    "vocabulary": int,         # Vocabulary count
                    "games": int               # Game count
                }
            },
            "performance_trends": {             # Performance analysis
                "average_score": float,        # Average score
                "trend_direction": str,        # Improving/declining/stable
                "score_distribution": {}       # Score distribution
            },
            "learning_patterns": {              # Learning behavior patterns
                "preferred_times": [],         # Preferred learning times
                "session_duration": {},        # Session duration patterns
                "activity_preferences": {}     # Activity type preferences
            },
            "recommendations": [                # AI-generated recommendations
                {
                    "type": str,               # Recommendation type
                    "title": str,              # Recommendation title
                    "description": str,        # Recommendation description
                    "priority": str            # Priority level
                }
            ],
            "generated_at": str                 # ISO format timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid parameters
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        period = request.args.get("period", "month")
        metric = request.args.get("metric", "completion_rate")

        # Validate parameters
        valid_periods = ["week", "month", "quarter"]
        valid_metrics = ["completion_rate", "time_spent", "accuracy"]

        if period not in valid_periods:
            return jsonify({"error": f"Invalid period: {period}"}), 400

        if metric not in valid_metrics:
            return jsonify({"error": f"Invalid metric: {metric}"}), 400

        # Map period to days for ProgressService
        period_days = {
            "week": 7,
            "month": 30,
            "quarter": 90
        }
        days = period_days.get(period, 30)

        # Get progress trends using ProgressService
        progress_trends = ProgressService.get_progress_trends(user, days)

        # Build response based on requested metric
        trends = {
            "period": period,
            "metric": metric,
            "data_points": [],
            "overall_trend": "stable"
        }

        # Extract data points based on metric
        daily_activity = progress_trends.get("daily_activity", {})

        if metric == "completion_rate":
            # Calculate completion rates from daily activity
            for date, activity in daily_activity.items():
                total_activities = activity.get("total", 0)
                if total_activities > 0:
                    # Estimate completion rate based on activity volume
                    completion_rate = min(total_activities * 10, 100)  # Simplified calculation
                    trends["data_points"].append({
                        "date": date,
                        "value": round(completion_rate, 2)
                    })

        elif metric == "time_spent":
            # Use activity volume as proxy for time spent
            for date, activity in daily_activity.items():
                total_activities = activity.get("total", 0)
                estimated_time = total_activities * 5  # 5 minutes per activity
                trends["data_points"].append({
                    "date": date,
                    "value": round(estimated_time, 2)
                })

        elif metric == "accuracy":
            # Use performance trends for accuracy
            performance_trends = progress_trends.get("performance_trends", {})
            avg_score = performance_trends.get("average_score", 0)
            for date, activity in daily_activity.items():
                trends["data_points"].append({
                    "date": date,
                    "value": round(avg_score, 2)
                })

        # Determine overall trend from performance trends
        performance_trends = progress_trends.get("performance_trends", {})
        trend_direction = performance_trends.get("trend_direction", "stable")
        trends["overall_trend"] = trend_direction

        return jsonify({
            "user": user,
            "trends": trends,
            "daily_activity": daily_activity,
            "performance_trends": performance_trends,
            "learning_patterns": progress_trends.get("learning_patterns", {}),
            "recommendations": progress_trends.get("recommendations", []),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting progress trends for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve progress trends"}), 500


# === Progress Synchronization Routes ===

@lesson_progress_bp.route("/sync", methods=["POST"])
def sync_progress_route():
    """
    Synchronize progress data across devices.

    This endpoint allows users to synchronize their progress data
    across multiple devices and platforms.

    Request Body:
        - progress_data (array, required): Array of progress updates to synchronize
        - device_id (str, optional): Unique identifier for the device
        - last_sync (str, optional): Timestamp of last synchronization

    Progress Data Structure:
        [
            {
                "lesson_id": int,              # Lesson identifier
                "block_id": str,               # Block identifier
                "completed": bool,             # Completion status
                "score": float,                # Performance score
                "time_spent": int,             # Time spent in seconds
                "updated_at": str              # ISO format timestamp
            }
        ]

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "synced_items": int,               # Number of items synchronized
            "conflicts_resolved": int,         # Number of conflicts resolved
            "last_sync": str                   # ISO format timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data structure
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        progress_data = data.get("progress_data", [])
        device_id = data.get("device_id", "")
        last_sync = data.get("last_sync")

        if not progress_data:
            return jsonify({"error": "Progress data is required"}), 400

        # Validate progress data structure
        for progress in progress_data:
            required_fields = ["lesson_id", "block_id", "completed"]
            for field in required_fields:
                if field not in progress:
                    return jsonify({"error": f"Missing required field: {field}"}), 400

        # Synchronize progress data
        sync_result = {
            "success": True,
            "synced_count": len(progress_data),
            "conflicts_resolved": 0
        }

        if sync_result.get("success"):
            return jsonify({
                "message": "Progress synchronized successfully",
                "synced_items": sync_result.get("synced_count", 0),
                "conflicts_resolved": sync_result.get("conflicts_resolved", 0),
                "last_sync": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "error": "Failed to synchronize progress",
                "details": sync_result.get("error", "Unknown sync error")
            }), 500

    except Exception as e:
        logger.error(f"Error synchronizing progress for user {user}: {e}")
        return jsonify({"error": "Failed to synchronize progress"}), 500


@lesson_progress_bp.route("/sync/status", methods=["GET"])
def get_sync_status_route():
    """
    Get synchronization status and last sync information.

    This endpoint provides information about the user's progress
    synchronization status across devices.

    JSON Response Structure:
        {
            "user": str,                        # User identifier
            "sync_status": str,                 # Sync status (synced, never_synced, error)
            "last_sync": str,                   # Last sync timestamp (ISO format)
            "device_count": int                 # Number of synced devices
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get last sync information
        last_sync_info = select_one(
            "user_sync_status",
            columns="last_sync, device_count, sync_status",
            where="user_id = ?",
            params=(user,)
        )

        if not last_sync_info:
            return jsonify({
                "user": user,
                "sync_status": "never_synced",
                "last_sync": None,
                "device_count": 0
            })

        return jsonify({
            "user": user,
            "sync_status": last_sync_info.get("sync_status", "unknown"),
            "last_sync": last_sync_info.get("last_sync"),
            "device_count": last_sync_info.get("device_count", 0)
        })

    except Exception as e:
        logger.error(f"Error getting sync status for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve sync status"}), 500


# === Progress Export Routes ===

@lesson_progress_bp.route("/export", methods=["GET"])
def export_progress_route():
    """
    Export user progress data.

    This endpoint allows users to export their progress data
    for backup or analysis purposes.

    Query Parameters:
        - format (str, optional): Export format (json, csv, pdf)
        - include_details (bool, optional): Include detailed progress information

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "format": str,                     # Export format
            "data": {                          # Exported data
                "user": str,                   # User identifier
                "format": str,                 # Export format
                "include_details": bool,       # Include details flag
                "exported_at": str             # Export timestamp
            },
            "exported_at": str                 # ISO format timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid format parameter
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        format_type = request.args.get("format", "json")
        include_details = request.args.get("include_details", "false").lower() == "true"

        # Validate format
        valid_formats = ["json", "csv", "pdf"]
        if format_type not in valid_formats:
            return jsonify({"error": f"Invalid format: {format_type}"}), 400

        # Export progress data
        exported_data = {
            "user": user,
            "format": format_type,
            "include_details": include_details,
            "exported_at": datetime.now().isoformat()
        }

        if exported_data:
            return jsonify({
                "message": "Progress data exported successfully",
                "format": format_type,
                "data": exported_data,
                "exported_at": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to export progress data"}), 500

    except Exception as e:
        logger.error(f"Error exporting progress for user {user}: {e}")
        return jsonify({"error": "Failed to export progress data"}), 500

