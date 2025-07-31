"""
XplorED - User Profile API Routes

This module contains API routes for user profile management and statistics,
following clean architecture principles as outlined in the documentation.

Route Categories:
- Profile Information: User profile data and personal information
- Learning Statistics: Educational progress and performance metrics
- Achievement Tracking: User achievements and milestones
- Progress Analytics: Detailed learning analytics and insights
- Profile Management: Profile updates and customization

Profile Features:
- Comprehensive user statistics and progress tracking
- Achievement system and milestone recognition
- Detailed learning analytics and performance insights
- Profile customization and personal information management

Business Logic:
All profile logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import profile_bp
from features.profile.profile_helpers import (
    get_user_game_results,
    get_user_profile_summary,
    get_user_achievements,
    get_user_activity_timeline
)
from features.debug.debug_helpers import get_user_statistics


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Profile Information Routes ===
@profile_bp.route("/info", methods=["GET"])
def get_profile_info_route():
    """
    Get user profile information and basic statistics.

    This endpoint retrieves the user's profile information including
    personal details, account statistics, and basic learning metrics.

    Returns:
        JSON response with profile information or unauthorized error
    """
    try:
        user = require_user()

        # Get user profile data
        profile_data = select_one(
            "users",
            columns="username, created_at, skill_level, last_login",
            where="username = ?",
            params=(user,)
        )

        if not profile_data:
            return jsonify({"error": "User profile not found"}), 404

        # Get basic statistics
        stats = get_user_statistics(user)

        return jsonify({
            "profile": profile_data,
            "statistics": stats,
            "last_updated": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting profile info for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve profile information"}), 500


@profile_bp.route("/info", methods=["PUT"])
def update_profile_info_route():
    """
    Update user profile information.

    This endpoint allows users to update their profile information
    including personal details and preferences.

    Request Body:
        - display_name: User's display name
        - bio: User biography or description
        - location: User's location
        - interests: User's learning interests
        - avatar_url: Profile picture URL

    Returns:
        JSON response with update status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate and prepare profile updates
        valid_updates = {}

        if "display_name" in data:
            display_name = data["display_name"].strip()
            if display_name and len(display_name) <= 50:
                valid_updates["display_name"] = display_name
            else:
                return jsonify({"error": "Display name must be 1-50 characters"}), 400

        if "bio" in data:
            bio = data["bio"].strip()
            if len(bio) <= 500:
                valid_updates["bio"] = bio
            else:
                return jsonify({"error": "Bio must be 500 characters or less"}), 400

        if "location" in data:
            location = data["location"].strip()
            if len(location) <= 100:
                valid_updates["location"] = location
            else:
                return jsonify({"error": "Location must be 100 characters or less"}), 400

        if "interests" in data:
            interests = data["interests"]
            if isinstance(interests, list) and len(interests) <= 10:
                valid_updates["interests"] = ",".join(interests)
            else:
                return jsonify({"error": "Interests must be a list of 10 or fewer items"}), 400

        if "avatar_url" in data:
            avatar_url = data["avatar_url"].strip()
            if avatar_url and len(avatar_url) <= 255:
                valid_updates["avatar_url"] = avatar_url
            else:
                return jsonify({"error": "Avatar URL must be 255 characters or less"}), 400

        if not valid_updates:
            return jsonify({"error": "No valid profile updates provided"}), 400

        # Update profile information
        success = update_profile_info(user, valid_updates)

        if success:
            return jsonify({
                "message": "Profile updated successfully",
                "updated_fields": list(valid_updates.keys())
            })
        else:
            return jsonify({"error": "Failed to update profile"}), 500

    except Exception as e:
        logger.error(f"Error updating profile for user {user}: {e}")
        return jsonify({"error": "Failed to update profile"}), 500


# === Learning Statistics Routes ===
@profile_bp.route("/statistics", methods=["GET"])
def get_learning_statistics_route():
    """
    Get comprehensive learning statistics for the user.

    This endpoint provides detailed statistics about the user's learning
    progress including exercise completion, vocabulary mastery, and time spent.

    Query Parameters:
        - period: Time period for statistics (week, month, year, all)
        - category: Statistics category (exercises, vocabulary, time)

    Returns:
        JSON response with learning statistics or unauthorized error
    """
    try:
        user = require_user()

        # Get query parameters
        period = request.args.get("period", "all")
        category = request.args.get("category", "all")

        # Validate period
        valid_periods = ["week", "month", "year", "all"]
        if period not in valid_periods:
            return jsonify({"error": f"Invalid period: {period}"}), 400

        # Get learning statistics
        statistics = get_learning_progress(user, period, category)

        return jsonify({
            "user": user,
            "period": period,
            "category": category,
            "statistics": statistics,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting learning statistics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve learning statistics"}), 500


@profile_bp.route("/statistics/detailed", methods=["GET"])
def get_detailed_statistics_route():
    """
    Get detailed breakdown of user learning statistics.

    This endpoint provides a comprehensive breakdown of the user's
    learning statistics with detailed metrics and trends.

    Query Parameters:
        - start_date: Start date for statistics (YYYY-MM-DD)
        - end_date: End date for statistics (YYYY-MM-DD)
        - group_by: Grouping method (day, week, month)

    Returns:
        JSON response with detailed statistics or unauthorized error
    """
    try:
        user = require_user()

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

        # Get detailed statistics
        detailed_stats = get_user_statistics(user, start_date, end_date, group_by)

        return jsonify({
            "user": user,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "group_by": group_by,
            "statistics": detailed_stats,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting detailed statistics for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve detailed statistics"}), 500


# === Achievement Tracking Routes ===
@profile_bp.route("/achievements", methods=["GET"])
def get_user_achievements_route():
    """
    Get user achievements and milestones.

    This endpoint retrieves the user's earned achievements and
    tracks progress toward upcoming milestones.

    Returns:
        JSON response with achievements or unauthorized error
    """
    try:
        user = require_user()

        # Get user achievements
        achievements = get_achievements(user)

        return jsonify({
            "user": user,
            "achievements": achievements.get("earned", []),
            "upcoming": achievements.get("upcoming", []),
            "total_earned": len(achievements.get("earned", [])),
            "total_available": len(achievements.get("earned", [])) + len(achievements.get("upcoming", []))
        })

    except Exception as e:
        logger.error(f"Error getting achievements for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve achievements"}), 500


@profile_bp.route("/achievements/<achievement_id>", methods=["GET"])
def get_achievement_details_route(achievement_id: str):
    """
    Get detailed information about a specific achievement.

    This endpoint provides detailed information about a specific
    achievement including requirements and progress.

    Args:
        achievement_id: Unique identifier of the achievement

    Returns:
        JSON response with achievement details or not found error
    """
    try:
        user = require_user()

        # Get achievement details
        achievement = select_one(
            "achievements",
            columns="*",
            where="id = ?",
            params=(achievement_id,)
        )

        if not achievement:
            return jsonify({"error": "Achievement not found"}), 404

        # Get user progress for this achievement
        progress = select_one(
            "user_achievements",
            columns="progress, earned_at",
            where="username = ? AND achievement_id = ?",
            params=(user, achievement_id)
        )

        return jsonify({
            "achievement": achievement,
            "user_progress": progress,
            "is_earned": progress is not None and progress.get("earned_at") is not None
        })

    except Exception as e:
        logger.error(f"Error getting achievement details for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve achievement details"}), 500


# === Progress Analytics Routes ===
@profile_bp.route("/analytics", methods=["GET"])
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
        analytics = get_learning_progress(user, timeframe, "analytics")

        # Add recommendations if requested
        if include_recommendations:
            # This would integrate with AI recommendation system
            analytics["recommendations"] = {
                "strengths": ["Grammar fundamentals", "Vocabulary retention"],
                "areas_for_improvement": ["Speaking practice", "Complex sentence structures"],
                "suggested_actions": [
                    "Complete 3 speaking exercises this week",
                    "Review advanced grammar concepts",
                    "Practice with native speaker content"
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


@profile_bp.route("/analytics/strengths", methods=["GET"])
def get_learning_strengths_route():
    """
    Get user's learning strengths and areas of excellence.

    This endpoint analyzes the user's performance to identify
    their strongest areas and learning patterns.

    Returns:
        JSON response with learning strengths or unauthorized error
    """
    try:
        user = require_user()

        # Get user's performance data
        performance_data = select_rows(
            "results",
            columns="level, correct, answer, timestamp",
            where="username = ? AND correct = 1",
            params=(user,),
            order_by="timestamp DESC",
            limit=100
        )

        # Analyze strengths (simplified analysis)
        strengths = {
            "grammar": {"score": 0, "exercises": 0},
            "vocabulary": {"score": 0, "exercises": 0},
            "comprehension": {"score": 0, "exercises": 0},
            "speaking": {"score": 0, "exercises": 0}
        }

        for result in performance_data:
            level = result.get("level", "").lower()
            if "grammar" in level:
                strengths["grammar"]["score"] += 1
                strengths["grammar"]["exercises"] += 1
            elif "vocab" in level:
                strengths["vocabulary"]["score"] += 1
                strengths["vocabulary"]["exercises"] += 1
            elif "reading" in level or "comprehension" in level:
                strengths["comprehension"]["score"] += 1
                strengths["comprehension"]["exercises"] += 1
            elif "speaking" in level or "pronunciation" in level:
                strengths["speaking"]["score"] += 1
                strengths["speaking"]["exercises"] += 1

        # Calculate percentages
        for category in strengths:
            if strengths[category]["exercises"] > 0:
                strengths[category]["percentage"] = (
                    strengths[category]["score"] / strengths[category]["exercises"]
                ) * 100
            else:
                strengths[category]["percentage"] = 0

        return jsonify({
            "user": user,
            "strengths": strengths,
            "top_strength": max(strengths.keys(), key=lambda k: strengths[k]["percentage"]),
            "analysis_date": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting learning strengths for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve learning strengths"}), 500


@profile_bp.route("/analytics/weaknesses", methods=["GET"])
def get_learning_weaknesses_route():
    """
    Get user's learning weaknesses and areas for improvement.

    This endpoint analyzes the user's performance to identify
    areas that need more attention and practice.

    Returns:
        JSON response with learning weaknesses or unauthorized error
    """
    try:
        user = require_user()

        # Get user's performance data (incorrect answers)
        performance_data = select_rows(
            "results",
            columns="level, correct, answer, timestamp",
            where="username = ? AND correct = 0",
            params=(user,),
            order_by="timestamp DESC",
            limit=100
        )

        # Analyze weaknesses (simplified analysis)
        weaknesses = {
            "grammar": {"mistakes": 0, "total": 0},
            "vocabulary": {"mistakes": 0, "total": 0},
            "comprehension": {"mistakes": 0, "total": 0},
            "speaking": {"mistakes": 0, "total": 0}
        }

        for result in performance_data:
            level = result.get("level", "").lower()
            if "grammar" in level:
                weaknesses["grammar"]["mistakes"] += 1
                weaknesses["grammar"]["total"] += 1
            elif "vocab" in level:
                weaknesses["vocabulary"]["mistakes"] += 1
                weaknesses["vocabulary"]["total"] += 1
            elif "reading" in level or "comprehension" in level:
                weaknesses["comprehension"]["mistakes"] += 1
                weaknesses["comprehension"]["total"] += 1
            elif "speaking" in level or "pronunciation" in level:
                weaknesses["speaking"]["mistakes"] += 1
                weaknesses["speaking"]["total"] += 1

        # Get total exercises for each category
        total_exercises = select_rows(
            "results",
            columns="level, COUNT(*) as total",
            where="username = ?",
            params=(user,),
            group_by="level"
        )

        for exercise in total_exercises:
            level = exercise.get("level", "").lower()
            total = exercise.get("total", 0)

            if "grammar" in level:
                weaknesses["grammar"]["total"] = total
            elif "vocab" in level:
                weaknesses["vocabulary"]["total"] = total
            elif "reading" in level or "comprehension" in level:
                weaknesses["comprehension"]["total"] = total
            elif "speaking" in level or "pronunciation" in level:
                weaknesses["speaking"]["total"] = total

        # Calculate error rates
        for category in weaknesses:
            if weaknesses[category]["total"] > 0:
                weaknesses[category]["error_rate"] = (
                    weaknesses[category]["mistakes"] / weaknesses[category]["total"]
                ) * 100
            else:
                weaknesses[category]["error_rate"] = 0

        return jsonify({
            "user": user,
            "weaknesses": weaknesses,
            "biggest_challenge": max(weaknesses.keys(), key=lambda k: weaknesses[k]["error_rate"]),
            "analysis_date": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting learning weaknesses for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve learning weaknesses"}), 500
