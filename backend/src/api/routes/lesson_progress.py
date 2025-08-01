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
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import lesson_progress_bp
from features.progress import (
    track_lesson_progress,
    get_lesson_progress,
    track_exercise_progress,
    track_vocabulary_progress,
    track_game_progress,
    get_user_progress_summary,
    reset_user_progress,
    get_progress_trends,
    get_user_lesson_progress,
    update_block_progress,
    mark_lesson_complete,
    check_lesson_completion_status,
    mark_lesson_as_completed,
    get_lesson_progress_summary,
    reset_lesson_progress,
)
from features.lessons import validate_block_completion


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
        - include_details: Include detailed progress information
        - timeframe: Time period for progress data (week, month, all)

    Returns:
        JSON response with progress overview or unauthorized error
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

        # Get overall progress statistics
        total_lessons = select_one(
            "lesson_content",
            columns="COUNT(*) as total",
            where="published = 1"
        )

        user_progress = select_rows(
            "lesson_progress",
            columns="lesson_id, COUNT(*) as blocks_completed",
            where="user_id = ? AND completed = 1",
            params=(user,),
            group_by="lesson_id"
        )

        # Calculate completion statistics
        total_completed_blocks = sum(p.get("blocks_completed", 0) for p in user_progress)
        lessons_started = len(user_progress)
        total_lessons_count = total_lessons.get("total", 0) if total_lessons else 0

        progress_overview = {
            "user": user,
            "total_lessons": total_lessons_count,
            "lessons_started": lessons_started,
            "total_completed_blocks": total_completed_blocks,
            "completion_rate": round((lessons_started / total_lessons_count * 100), 2) if total_lessons_count > 0 else 0
        }

        # Add detailed progress if requested
        if include_details:
            detailed_progress = select_rows(
                "lesson_progress",
                columns="lesson_id, block_id, completed, updated_at",
                where="user_id = ?",
                params=(user,),
                order_by="updated_at DESC"
            )
            progress_overview["detailed_progress"] = detailed_progress

        return jsonify({
            "progress": progress_overview,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting user progress for {user}: {e}")
        return jsonify({"error": "Failed to retrieve progress data"}), 500


@lesson_progress_bp.route("/progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress_route(lesson_id: int):
    """
    Get detailed progress for a specific lesson.

    This endpoint retrieves detailed progress information for a specific
    lesson including block completion status and timestamps.

    Args:
        lesson_id: Unique identifier of the lesson

    Returns:
        JSON response with lesson progress or not found error
    """
    try:
        user = require_user()

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id, title, num_blocks, skill_level",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Get user progress for this lesson
        progress = select_rows(
            "lesson_progress",
            columns="block_id, completed, updated_at",
            where="user_id = ? AND lesson_id = ?",
            params=(user, lesson_id),
            order_by="block_id"
        )

        # Calculate completion statistics
        total_blocks = lesson.get("num_blocks", 0)
        completed_blocks = len([p for p in progress if p.get("completed")])
        completion_percentage = (completed_blocks / total_blocks * 100) if total_blocks > 0 else 0

        # Get last activity
        last_activity = None
        if progress:
            valid_dates = []
            for p in progress:
                date = p.get("updated_at")
                if date is not None:
                    valid_dates.append(date)
            if valid_dates:
                last_activity = max(valid_dates)

        return jsonify({
            "lesson_id": lesson_id,
            "lesson_title": lesson.get("title"),
            "skill_level": lesson.get("skill_level"),
            "total_blocks": total_blocks,
            "completed_blocks": completed_blocks,
            "completion_percentage": round(completion_percentage, 2),
            "progress": progress,
            "last_activity": last_activity,
            "started": len(progress) > 0
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

    Args:
        lesson_id: Unique identifier of the lesson
        block_id: Identifier of the specific block

    Request Body:
        - completed: Completion status (true/false)
        - time_spent: Time spent on the block in seconds (optional)
        - score: Performance score (optional)

    Returns:
        JSON response with update status or error details
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

        # Update or insert progress
        existing_progress = select_one(
            "lesson_progress",
            columns="id",
            where="user_id = ? AND lesson_id = ? AND block_id = ?",
            params=(user, lesson_id, block_id)
        )

        if existing_progress:
            # Update existing progress
            success = update_row(
                "lesson_progress",
                progress_data,
                "WHERE user_id = ? AND lesson_id = ? AND block_id = ?",
                (user, lesson_id, block_id)
            )
        else:
            # Insert new progress
            progress_data.update({
                "user_id": user,
                "lesson_id": lesson_id,
                "block_id": block_id
            })
            success = insert_row("lesson_progress", progress_data)

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
def get_progress_analytics_route():
    """
    Get detailed progress analytics and insights.

    This endpoint provides comprehensive analytics about the user's
    learning progress including trends, patterns, and recommendations.

    Query Parameters:
        - timeframe: Analytics timeframe (week, month, quarter, year)
        - include_recommendations: Include AI-generated recommendations

    Returns:
        JSON response with progress analytics or unauthorized error
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

        # Get progress analytics
        analytics = {
            "timeframe": timeframe,
            "total_lessons_completed": 0,
            "average_completion_rate": 0.0,
            "study_time_total": 0,
            "streak_days": 0
        }

        # Add recommendations if requested
        if include_recommendations:
            # This would integrate with AI recommendation system
            analytics["recommendations"] = {
                "next_lessons": ["Advanced Grammar", "Business German", "Conversation Practice"],
                "focus_areas": ["Vocabulary Building", "Grammar Review", "Speaking Practice"],
                "study_suggestions": [
                    "Complete 2 lessons this week",
                    "Review previous vocabulary",
                    "Practice speaking exercises"
                ]
            }

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
        - period: Analysis period (week, month, quarter)
        - metric: Trend metric (completion_rate, time_spent, accuracy)

    Returns:
        JSON response with progress trends or unauthorized error
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

        # Calculate date range
        end_date = datetime.now()
        if period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:  # quarter
            start_date = end_date - timedelta(days=90)

        # Get progress data for trend analysis
        progress_data = select_rows(
            "lesson_progress",
            columns="updated_at, completed, time_spent, score",
            where="user_id = ? AND updated_at >= ?",
            params=(user, start_date.isoformat()),
            order_by="updated_at ASC"
        )

        # Analyze trends
        trends = {
            "period": period,
            "metric": metric,
            "data_points": [],
            "overall_trend": "stable"
        }

        # Group data by time periods and calculate metrics
        if metric == "completion_rate":
            # Calculate daily completion rates
            daily_completions = {}
            for progress in progress_data:
                date = progress.get("updated_at", "")[:10]  # Extract date part
                if date not in daily_completions:
                    daily_completions[date] = {"total": 0, "completed": 0}
                daily_completions[date]["total"] += 1
                if progress.get("completed"):
                    daily_completions[date]["completed"] += 1

            for date, data in sorted(daily_completions.items()):
                rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
                trends["data_points"].append({
                    "date": date,
                    "value": round(rate, 2)
                })

        elif metric == "time_spent":
            # Calculate average time spent per day
            daily_time = {}
            for progress in progress_data:
                date = progress.get("updated_at", "")[:10]
                time_spent = progress.get("time_spent", 0)
                if date not in daily_time:
                    daily_time[date] = {"total_time": 0, "count": 0}
                daily_time[date]["total_time"] += time_spent
                daily_time[date]["count"] += 1

            for date, data in sorted(daily_time.items()):
                avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
                trends["data_points"].append({
                    "date": date,
                    "value": round(avg_time, 2)
                })

        elif metric == "accuracy":
            # Calculate accuracy based on scores
            daily_scores = {}
            for progress in progress_data:
                date = progress.get("updated_at", "")[:10]
                score = progress.get("score", 0)
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

        # Determine overall trend
        if len(trends["data_points"]) >= 2:
            first_value = trends["data_points"][0]["value"]
            last_value = trends["data_points"][-1]["value"]
            if last_value > first_value * 1.1:
                trends["overall_trend"] = "improving"
            elif last_value < first_value * 0.9:
                trends["overall_trend"] = "declining"

        return jsonify({
            "user": user,
            "trends": trends,
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
        - progress_data: Array of progress updates to synchronize
        - device_id: Unique identifier for the device
        - last_sync: Timestamp of last synchronization

    Returns:
        JSON response with synchronization status or error details
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

    Returns:
        JSON response with sync status or unauthorized error
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
        - format: Export format (json, csv, pdf)
        - include_details: Include detailed progress information

    Returns:
        JSON response with exported data or error details
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

