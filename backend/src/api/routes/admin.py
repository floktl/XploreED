"""
XplorED - Admin Management API Routes

This module contains API routes for administrative functions and system management,
following clean architecture principles as outlined in the documentation.

Route Categories:
- User Management: User account administration and management
- System Administration: System-wide settings and configuration
- Content Management: Lesson and content administration
- Analytics and Reporting: System analytics and user reporting
- Security Administration: Security settings and access control

Admin Features:
- Comprehensive user account management
- System-wide configuration and settings
- Content creation and management tools
- Advanced analytics and reporting
- Security and access control management

Business Logic:
All admin logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from flask import request, jsonify # type: ignore
from infrastructure.imports import Imports
from api.middleware.auth import is_admin
from core.database.connection import select_one, select_rows, update_row, delete_rows
from config.blueprint import admin_bp
from features.admin import (
    get_all_game_results,
    get_admin_user_game_results,
    create_lesson_content,
    get_all_lessons,
    get_lesson_by_id,
    update_admin_lesson_content,
    delete_lesson_content,
    get_lesson_progress_summary,
    get_individual_lesson_progress,
    get_all_users,
    update_user_data,
    delete_user_data,
)


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === User Management Routes ===

@admin_bp.route("/users", methods=["GET"])
def get_users_route():
    """
    Get comprehensive user management data (admin only).

    This endpoint provides detailed user information for administrative
    management including account status, activity, and statistics.

    Query Parameters:
        - status (str, optional): Filter by user status (active, inactive, suspended)
        - skill_level (str, optional): Filter by skill level
        - limit (int, optional): Maximum number of users to return (default: 50)
        - offset (int, optional): Pagination offset (default: 0)
        - search (str, optional): Search by username or email

    JSON Response Structure:
        {
            "users": [                            # Array of user data
                {
                    "id": int,                    # User identifier
                    "username": str,              # Username
                    "email": str,                 # Email address
                    "skill_level": str,           # Skill level
                    "status": str,                # Account status
                    "created_at": str,            # Account creation timestamp
                    "last_login": str,            # Last login timestamp
                    "is_admin": bool              # Admin status
                }
            ],
            "total": int,                         # Total number of users
            "limit": int,                         # Requested limit
            "offset": int                         # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 403: Admin access required
        - 500: Internal server error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        status = request.args.get("status")
        skill_level = request.args.get("skill_level")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        search = request.args.get("search", "").strip()

        # Build query conditions
        where_conditions = []
        params = []

        if status:
            where_conditions.append("status = ?")
            params.append(status)

        if skill_level:
            where_conditions.append("skill_level = ?")
            params.append(skill_level)

        if search:
            where_conditions.append("(username LIKE ? OR email LIKE ?)")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get users
        users = select_rows(
            "users",
            columns="id, username, email, skill_level, status, created_at, last_login, is_admin",
            where=where_clause,
            params=tuple(params),
            order_by="created_at DESC",
            limit=limit
        )

        # Get total count for pagination
        total_count = select_one(
            "users",
            columns="COUNT(*) as count",
            where=where_clause,
            params=tuple(params)
        )

        return jsonify({
            "users": users,
            "total": total_count.get("count", 0) if total_count else 0,
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({"error": "Failed to retrieve users"}), 500


@admin_bp.route("/users/<username>", methods=["GET"])
def get_user_details_route(username: str):
    """
    Get detailed information about a specific user (admin only).

    This endpoint provides comprehensive information about a specific
    user including their activity, progress, and account details.

    Path Parameters:
        - username (str, required): Username of the user to get details for

    JSON Response Structure:
        {
            "user": {                             # User information
                "id": int,                        # User identifier
                "username": str,                  # Username
                "email": str,                     # Email address
                "skill_level": str,               # Skill level
                "status": str,                    # Account status
                "created_at": str,                # Account creation timestamp
                "last_login": str,                # Last login timestamp
                "is_admin": bool,                 # Admin status
                "profile_complete": bool          # Profile completion status
            },
            "activity": {                         # User activity data
                "total_sessions": int,            # Total login sessions
                "last_activity": str,             # Last activity timestamp
                "average_session_time": float,    # Average session duration
                "preferred_times": [str]          # Preferred activity times
            },
            "progress": {                         # Learning progress
                "lessons_completed": int,         # Completed lessons
                "exercises_completed": int,       # Completed exercises
                "total_time_spent": int,          # Total learning time in minutes
                "current_streak": int,            # Current learning streak
                "average_score": float            # Average performance score
            },
            "statistics": {                       # Performance statistics
                "vocabulary_words": int,          # Vocabulary words learned
                "grammar_exercises": int,         # Grammar exercises completed
                "reading_exercises": int,         # Reading exercises completed
                "speaking_exercises": int         # Speaking exercises completed
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 403: Admin access required
        - 404: User not found
        - 500: Internal server error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get user details
        user_data = select_one(
            "users",
            columns="*",
            where="username = ?",
            params=(username,)
        )

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        # Get user activity data
        activity_data = select_one(
            "user_activity",
            columns="*",
            where="username = ?",
            params=(username,)
        )

        # Get user progress data
        progress_data = select_one(
            "user_progress",
            columns="*",
            where="username = ?",
            params=(username,)
        )

        return jsonify({
            "user": user_data,
            "activity": activity_data or {},
            "progress": progress_data or {}
        })

    except Exception as e:
        logger.error(f"Error getting user details for {username}: {e}")
        return jsonify({"error": "Failed to retrieve user details"}), 500


@admin_bp.route("/users/<username>/status", methods=["PUT"])
def update_user_status_route(username: str):
    """
    Update user account status (admin only).

    This endpoint allows administrators to update user account status,
    including activation, suspension, and account management.

    Path Parameters:
        - username (str, required): Username of the user to update

    Request Body:
        - status (str, required): New account status
        - reason (str, optional): Reason for status change
        - notes (str, optional): Administrative notes

    Valid Status Values:
        - active: Active account
        - inactive: Inactive account
        - suspended: Suspended account
        - banned: Banned account
        - pending: Pending activation

    JSON Response Structure:
        {
            "message": str,                       # Success message
            "user": {
                "username": str,                  # Username
                "status": str,                    # Updated status
                "updated_at": str,                # Update timestamp
                "updated_by": str                 # Admin who made the change
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid status or data
        - 401: Unauthorized
        - 403: Admin access required
        - 404: User not found
        - 500: Internal server error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        status = data.get("status")
        reason = data.get("reason", "")
        notes = data.get("notes", "")

        if not status:
            return jsonify({"error": "Status is required"}), 400

        # Validate status
        valid_statuses = ["active", "inactive", "suspended", "banned", "pending"]
        if status not in valid_statuses:
            return jsonify({"error": f"Invalid status: {status}"}), 400

        # Check if user exists
        user = select_one(
            "users",
            columns="id",
            where="username = ?",
            params=(username,)
        )

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update user status
        success = update_row(
            "users",
            {
                "status": status,
                "updated_at": datetime.now().isoformat()
            },
            "WHERE username = ?",
            (username,)
        )

        if not success:
            return jsonify({"error": "Failed to update user status"}), 500

        # Log the status change
        admin_user = get_current_user()
        status_log = {
            "username": username,
            "old_status": user.get("status"),
            "new_status": status,
            "reason": reason,
            "notes": notes,
            "updated_by": admin_user,
            "updated_at": datetime.now().isoformat()
        }

        insert_row("user_status_log", status_log)

        return jsonify({
            "message": f"User status updated to {status}",
            "user": {
                "username": username,
                "status": status,
                "updated_at": datetime.now().isoformat(),
                "updated_by": admin_user
            }
        })

    except Exception as e:
        logger.error(f"Error updating user status for {username}: {e}")
        return jsonify({"error": "Failed to update user status"}), 500


@admin_bp.route("/users/<username>/delete", methods=["DELETE"])
def delete_user_route(username: str):
    """
    Delete user account and all associated data (admin only).

    This endpoint permanently deletes a user account and all
    associated data including progress, vocabulary, and activity.

    Args:
        username: Username of the user to delete

    Request Body:
        - confirm: Confirmation flag to prevent accidental deletion
        - reason: Reason for deletion (optional)

    Returns:
        JSON response with deletion status or error details
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json() or {}
        confirm = data.get("confirm", False)

        if not confirm:
            return jsonify({"error": "Deletion must be confirmed"}), 400

        # Check if user exists
        user = select_one(
            "users",
            columns="id, username",
            where="username = ?",
            params=(username,)
        )

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Delete user data from all tables
        deletion_stats = {
            "users": 0,
            "results": 0,
            "vocab_log": 0,
            "sessions": 0,
            "lesson_progress": 0
        }

        try:
            # Delete from results table
            result = delete_rows("results", "WHERE username = ?", (username,))
            deletion_stats["results"] = result

            # Delete from vocab_log table
            result = delete_rows("vocab_log", "WHERE username = ?", (username,))
            deletion_stats["vocab_log"] = result

            # Delete from sessions table
            result = delete_rows("sessions", "WHERE username = ?", (username,))
            deletion_stats["sessions"] = result

            # Delete from lesson_progress table
            result = delete_rows("lesson_progress", "WHERE user_id = ?", (username,))
            deletion_stats["lesson_progress"] = result

            # Finally, delete from users table
            result = delete_rows("users", "WHERE username = ?", (username,))
            deletion_stats["users"] = result

            return jsonify({
                "message": "User deleted successfully",
                "username": username,
                "deletion_stats": deletion_stats
            })

        except Exception as e:
            logger.error(f"Error during user deletion: {e}")
            return jsonify({"error": "Failed to delete user data"}), 500

    except Exception as e:
        logger.error(f"Error deleting user {username}: {e}")
        return jsonify({"error": "Failed to delete user"}), 500


# === System Administration Routes ===
@admin_bp.route("/system/analytics", methods=["GET"])
def get_system_analytics_route():
    """
    Get comprehensive system analytics (admin only).

    This endpoint provides detailed system analytics including
    user statistics, activity metrics, and performance data.

    Query Parameters:
        - timeframe: Analytics timeframe (day, week, month, year)
        - include_details: Include detailed analytics data

    Returns:
        JSON response with system analytics or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        timeframe = request.args.get("timeframe", "month")
        include_details = request.args.get("include_details", "false").lower() == "true"

        # Validate timeframe
        valid_timeframes = ["day", "week", "month", "year"]
        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Get system analytics
        analytics = {
            "total_users": 0,
            "active_users": 0,
            "total_exercises": 0,
            "timeframe": timeframe
        }

        return jsonify({
            "system_analytics": analytics,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        return jsonify({"error": "Failed to retrieve system analytics"}), 500


@admin_bp.route("/system/settings", methods=["GET"])
def get_system_settings_route():
    """
    Get system-wide settings and configuration (admin only).

    This endpoint retrieves current system settings and
    configuration options for administrative review.

    Returns:
        JSON response with system settings or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get system settings
        settings = select_rows(
            "system_settings",
            columns="setting_key, setting_value, description, updated_at",
            order_by="setting_key ASC"
        )

        return jsonify({
            "system_settings": settings,
            "total_settings": len(settings),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting system settings: {e}")
        return jsonify({"error": "Failed to retrieve system settings"}), 500


@admin_bp.route("/system/settings", methods=["PUT"])
def update_system_settings_route():
    """
    Update system-wide settings (admin only).

    This endpoint allows administrators to update system-wide
    settings and configuration options.

    Request Body:
        - settings: Object containing setting key-value pairs

    Returns:
        JSON response with update status or error details
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data or "settings" not in data:
            return jsonify({"error": "Settings data is required"}), 400

        settings = data["settings"]
        if not isinstance(settings, dict):
            return jsonify({"error": "Settings must be an object"}), 400

        # Update settings
        updated_count = 0
        for key, value in settings.items():
            try:
                update_row(
                    "system_settings",
                    {"setting_value": str(value), "updated_at": datetime.now().isoformat()},
                    "WHERE setting_key = ?",
                    (key,)
                )
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating setting {key}: {e}")

        return jsonify({
            "message": "System settings updated successfully",
            "updated_count": updated_count,
            "total_settings": len(settings)
        })

    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        return jsonify({"error": "Failed to update system settings"}), 500


# === Content Management Routes ===
@admin_bp.route("/content/lessons", methods=["GET"])
def get_content_lessons_route():
    """
    Get lesson content for administration (admin only).

    This endpoint provides access to lesson content for
    administrative review and management.

    Query Parameters:
        - status: Filter by lesson status (published, draft)
        - skill_level: Filter by skill level
        - limit: Maximum number of lessons to return

    Returns:
        JSON response with lesson content or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        status = request.args.get("status")
        skill_level = request.args.get("skill_level")
        limit = int(request.args.get("limit", 50))

        # Build query conditions
        where_conditions = []
        params = []

        if status:
            where_conditions.append("published = ?")
            params.append(1 if status == "published" else 0)

        if skill_level:
            where_conditions.append("skill_level = ?")
            params.append(skill_level)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get lessons
        lessons = select_rows(
            "lesson_content",
            columns="id, lesson_id, title, skill_level, num_blocks, published, created_at, updated_at",
            where=where_clause,
            params=tuple(params),
            order_by="created_at DESC",
            limit=limit
        )

        return jsonify({
            "lessons": lessons,
            "total": len(lessons),
            "limit": limit
        })

    except Exception as e:
        logger.error(f"Error getting content lessons: {e}")
        return jsonify({"error": "Failed to retrieve lesson content"}), 500


@admin_bp.route("/content/lessons/<int:lesson_id>", methods=["PUT"])
def update_content_lesson_route(lesson_id: int):
    """
    Update lesson content (admin only).

    This endpoint allows administrators to update lesson content
    including publishing status and metadata.

    Args:
        lesson_id: Unique identifier of the lesson

    Request Body:
        - title: Updated lesson title
        - content: Updated lesson content
        - skill_level: Updated skill level
        - published: Publication status
        - metadata: Additional lesson metadata

    Returns:
        JSON response with update status or error details
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if lesson exists
        lesson = select_one(
            "lesson_content",
            columns="id",
            where="lesson_id = ?",
            params=(lesson_id,)
        )

        if not lesson:
            return jsonify({"error": "Lesson not found"}), 404

        # Prepare updates
        updates = {}

        if "title" in data:
            title = data["title"].strip()
            if title:
                updates["title"] = title
            else:
                return jsonify({"error": "Title cannot be empty"}), 400

        if "content" in data:
            content = data["content"].strip()
            if content:
                updates["content"] = content
            else:
                return jsonify({"error": "Content cannot be empty"}), 400

        if "skill_level" in data:
            skill_level = data["skill_level"]
            if isinstance(skill_level, int) and 1 <= skill_level <= 10:
                updates["skill_level"] = skill_level
            else:
                return jsonify({"error": "Skill level must be between 1 and 10"}), 400

        if "published" in data:
            updates["published"] = bool(data["published"])

        if "metadata" in data:
            updates["metadata"] = data["metadata"]

        if not updates:
            return jsonify({"error": "No valid updates provided"}), 400

        # Update lesson
        success = update_row("lesson_content", updates, "WHERE lesson_id = ?", (lesson_id,))

        if success:
            return jsonify({
                "message": "Lesson updated successfully",
                "lesson_id": lesson_id,
                "updated_fields": list(updates.keys())
            })
        else:
            return jsonify({"error": "Failed to update lesson"}), 500

    except Exception as e:
        logger.error(f"Error updating lesson {lesson_id}: {e}")
        return jsonify({"error": "Failed to update lesson"}), 500


# === Analytics and Reporting Routes ===
@admin_bp.route("/reports/user-activity", methods=["GET"])
def get_user_activity_report_route():
    """
    Get user activity report (admin only).

    This endpoint provides detailed user activity reports
    including engagement metrics and usage patterns.

    Query Parameters:
        - start_date: Report start date (YYYY-MM-DD)
        - end_date: Report end date (YYYY-MM-DD)
        - group_by: Grouping method (day, week, month)

    Returns:
        JSON response with activity report or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        group_by = request.args.get("group_by", "day")

        # Validate group_by
        valid_groupings = ["day", "week", "month"]
        if group_by not in valid_groupings:
            return jsonify({"error": f"Invalid group_by: {group_by}"}), 400

        # Calculate date range if not provided
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # Default to 30 days ago
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # Get user activity data
        activity_data = select_rows(
            "results",
            columns="username, COUNT(*) as exercise_count, SUM(correct) as correct_count, DATE(timestamp) as activity_date",
            where="timestamp >= ? AND timestamp <= ?",
            params=(start_date, end_date),
            group_by="username, DATE(timestamp)",
            order_by="activity_date DESC"
        )

        # Process activity data
        processed_data = {}
        for record in activity_data:
            username = record.get("username")
            date = record.get("activity_date")
            if username not in processed_data:
                processed_data[username] = {}
            processed_data[username][date] = {
                "exercises": record.get("exercise_count", 0),
                "correct": record.get("correct_count", 0),
                "accuracy": (record.get("correct_count", 0) / record.get("exercise_count", 1)) * 100
            }

        return jsonify({
            "user_activity_report": {
                "date_range": {"start_date": start_date, "end_date": end_date},
                "group_by": group_by,
                "activity_data": processed_data,
                "total_users": len(processed_data)
            },
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting user activity report: {e}")
        return jsonify({"error": "Failed to retrieve user activity report"}), 500


@admin_bp.route("/reports/performance", methods=["GET"])
def get_performance_report_route():
    """
    Get system performance report (admin only).

    This endpoint provides system performance metrics and
    usage statistics for administrative monitoring.

    Query Parameters:
        - timeframe: Report timeframe (day, week, month)
        - include_details: Include detailed performance data

    Returns:
        JSON response with performance report or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        timeframe = request.args.get("timeframe", "week")
        include_details = request.args.get("include_details", "false").lower() == "true"

        # Validate timeframe
        valid_timeframes = ["day", "week", "month"]
        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Calculate date range
        end_date = datetime.now()
        if timeframe == "day":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "week":
            start_date = end_date - timedelta(weeks=1)
        else:  # month
            start_date = end_date - timedelta(days=30)

        # Get performance metrics
        total_users = select_one(
            "users",
            columns="COUNT(*) as count",
            where="created_at >= ?",
            params=(start_date.isoformat(),)
        )

        total_exercises = select_one(
            "results",
            columns="COUNT(*) as count",
            where="timestamp >= ?",
            params=(start_date.isoformat(),)
        )

        active_users = select_one(
            "results",
            columns="COUNT(DISTINCT username) as count",
            where="timestamp >= ?",
            params=(start_date.isoformat(),)
        )

        performance_report = {
            "timeframe": timeframe,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "total_users": total_users.get("count", 0) if total_users else 0,
                "total_exercises": total_exercises.get("count", 0) if total_exercises else 0,
                "active_users": active_users.get("count", 0) if active_users else 0,
                "average_exercises_per_user": (
                    total_exercises.get("count", 0) / max(active_users.get("count", 1), 1)
                ) if total_exercises and active_users else 0
            }
        }

        if include_details:
            # Add detailed performance data
            daily_activity = select_rows(
                "results",
                columns="DATE(timestamp) as date, COUNT(*) as exercises, COUNT(DISTINCT username) as users",
                where="timestamp >= ?",
                params=(start_date.isoformat(),),
                group_by="DATE(timestamp)",
                order_by="date DESC"
            )
            performance_report["detailed_data"] = daily_activity

        return jsonify({
            "performance_report": performance_report,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting performance report: {e}")
        return jsonify({"error": "Failed to retrieve performance report"}), 500


# === Security Administration Routes ===
@admin_bp.route("/security/reports", methods=["GET"])
def get_security_reports_route():
    """
    Get security reports and alerts (admin only).

    This endpoint provides security-related reports including
    failed login attempts, suspicious activity, and access logs.

    Query Parameters:
        - report_type: Type of security report (logins, activity, alerts)
        - timeframe: Time period for the report (day, week, month)

    Returns:
        JSON response with security reports or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        report_type = request.args.get("report_type", "logins")
        timeframe = request.args.get("timeframe", "week")

        # Validate parameters
        valid_report_types = ["logins", "activity", "alerts"]
        valid_timeframes = ["day", "week", "month"]

        if report_type not in valid_report_types:
            return jsonify({"error": f"Invalid report type: {report_type}"}), 400

        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Get security reports
        security_data = {
            "total_events": 0,
            "failed_logins": 0,
            "suspicious_activity": 0
        }

        return jsonify({
            "security_report": {
                "type": report_type,
                "timeframe": timeframe,
                "data": security_data
            },
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting security reports: {e}")
        return jsonify({"error": "Failed to retrieve security reports"}), 500


@admin_bp.route("/security/settings", methods=["GET"])
def get_security_settings_route():
    """
    Get security settings and configuration (admin only).

    This endpoint retrieves current security settings and
    configuration options for administrative review.

    Returns:
        JSON response with security settings or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get security settings
        security_settings = select_rows(
            "security_settings",
            columns="setting_key, setting_value, description, updated_at",
            where="category = 'security'",
            order_by="setting_key ASC"
        )

        return jsonify({
            "security_settings": security_settings,
            "total_settings": len(security_settings),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting security settings: {e}")
        return jsonify({"error": "Failed to retrieve security settings"}), 500


@admin_bp.route("/security/settings", methods=["PUT"])
def update_security_settings_route():
    """
    Update security settings (admin only).

    This endpoint allows administrators to update security
    settings and configuration options.

    Request Body:
        - settings: Object containing security setting key-value pairs

    Returns:
        JSON response with update status or error details
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json()

        if not data or "settings" not in data:
            return jsonify({"error": "Settings data is required"}), 400

        settings = data["settings"]
        if not isinstance(settings, dict):
            return jsonify({"error": "Settings must be an object"}), 400

        # Update security settings
        updated_count = 0
        for key, value in settings.items():
            try:
                update_row(
                    "security_settings",
                    {"setting_value": str(value), "updated_at": datetime.now().isoformat()},
                    "WHERE setting_key = ? AND category = 'security'",
                    (key,)
                )
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating security setting {key}: {e}")

        return jsonify({
            "message": "Security settings updated successfully",
            "updated_count": updated_count,
            "total_settings": len(settings)
        })

    except Exception as e:
        logger.error(f"Error updating security settings: {e}")
        return jsonify({"error": "Failed to update security settings"}), 500
