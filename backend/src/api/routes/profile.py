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
from typing import Optional
from datetime import datetime, timedelta

from flask import request, jsonify # type: ignore
from pydantic import ValidationError
from infrastructure.imports import Imports
from api.middleware.auth import require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import profile_bp
from features.profile import (
    get_user_game_results,
    get_user_profile_summary,
    get_user_achievements,
    get_user_activity_timeline,
)
from features.debug import get_user_statistics
from api.schemas import ProfileUpdateSchema
from shared.exceptions import DatabaseError


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Profile Information Routes ===

@profile_bp.route("/info", methods=["GET"])
def get_profile_info_route():
    """
    Get user profile information and basic statistics.

    This endpoint retrieves the user's profile information including
    personal details, account statistics, and basic learning metrics.

    JSON Response Structure:
        {
            "profile": {                             # User profile information
                "username": str,                     # Username
                "created_at": str,                   # Account creation timestamp
                "skill_level": str,                  # Current skill level
                "last_login": str,                   # Last login timestamp
                "display_name": str,                 # Display name
                "bio": str,                          # User biography
                "avatar_url": str,                   # Profile picture URL
                "location": str,                     # User location
                "timezone": str                      # User timezone
            },
            "statistics": {                          # Basic statistics
                "total_lessons": int,                # Total lessons completed
                "total_exercises": int,              # Total exercises completed
                "total_time": int,                   # Total learning time (minutes)
                "current_streak": int,               # Current learning streak
                "average_score": float,              # Average performance score
                "vocabulary_words": int,             # Vocabulary words learned
                "achievements_count": int            # Number of achievements earned
            },
            "last_updated": str                      # Last update timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Profile not found
        - 500: Internal server error
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

    except DatabaseError as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/info", methods=["PUT"])
def update_profile_info_route():
    """
    Update user profile information.

    This endpoint allows users to update their profile information
    including personal details and preferences.

    Request Body:
        - display_name (str, optional): User's display name
        - bio (str, optional): User biography
        - avatar_url (str, optional): Profile picture URL
        - location (str, optional): User location
        - timezone (str, optional): User timezone
        - preferences (object, optional): Profile preferences

    JSON Response Structure:
        {
            "message": str,                          # Success message
            "profile": {                             # Updated profile information
                "username": str,                     # Username
                "display_name": str,                 # Updated display name
                "bio": str,                          # Updated biography
                "avatar_url": str,                   # Updated avatar URL
                "location": str,                     # Updated location
                "timezone": str,                     # Updated timezone
                "preferences": object,               # Updated preferences
                "updated_at": str                    # Update timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate profile data
        try:
            validated_data = ProfileUpdateSchema(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 400

        # Update profile information
        update_data = {
            "display_name": validated_data.display_name,
            "bio": validated_data.bio,
            "avatar_url": validated_data.avatar_url,
            "location": validated_data.location,
            "timezone": validated_data.timezone,
            "updated_at": datetime.now().isoformat()
        }

        success = update_row(
            "users",
            update_data,
            "WHERE username = ?",
            (user,)
        )

        if not success:
            return jsonify({"error": "Failed to update profile"}), 500

        return jsonify({
            "message": "Profile updated successfully",
            "profile": {
                "username": user,
                **update_data
            }
        })

    except DatabaseError as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/statistics", methods=["GET"])
def get_learning_statistics_route():
    """
    Get comprehensive learning statistics for the user.

    This endpoint retrieves detailed learning statistics including
    progress metrics, performance data, and learning patterns.

    Query Parameters:
        - timeframe (str, optional): Statistics timeframe (week, month, year, all)
        - include_details (bool, optional): Include detailed breakdown

    JSON Response Structure:
        {
            "overview": {                            # Overview statistics
                "total_lessons": int,                # Total lessons completed
                "total_exercises": int,              # Total exercises completed
                "total_time": int,                   # Total learning time (minutes)
                "current_streak": int,               # Current learning streak
                "longest_streak": int,               # Longest learning streak
                "average_score": float,              # Average performance score
                "completion_rate": float             # Overall completion rate
            },
            "progress_metrics": {                    # Progress metrics
                "vocabulary_words": int,             # Vocabulary words learned
                "grammar_concepts": int,             # Grammar concepts mastered
                "reading_texts": int,                # Reading texts completed
                "speaking_exercises": int,           # Speaking exercises completed
                "writing_assignments": int           # Writing assignments completed
            },
            "performance_data": {                    # Performance data
                "accuracy_rate": float,              # Overall accuracy rate
                "speed_improvement": float,          # Speed improvement percentage
                "difficulty_progression": str,       # Difficulty progression
                "skill_level_changes": [             # Skill level changes
                    {
                        "from_level": str,           # Previous level
                        "to_level": str,             # New level
                        "date": str                  # Change date
                    }
                ]
            },
            "learning_patterns": {                   # Learning patterns
                "preferred_times": [str],            # Preferred learning times
                "average_session_length": int,       # Average session length (minutes)
                "sessions_per_day": float,           # Average sessions per day
                "most_active_days": [str]            # Most active days of week
            },
            "timeframe": str,                        # Requested timeframe
            "generated_at": str                      # Statistics generation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        timeframe = request.args.get("timeframe", "all")
        include_details = request.args.get("include_details", "false").lower() == "true"

        # Get learning statistics
        statistics = get_user_profile_summary(user, timeframe, include_details)

        return jsonify({
            **statistics,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error getting user statistics: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/statistics/detailed", methods=["GET"])
def get_detailed_statistics_route():
    """
    Get detailed learning statistics with comprehensive breakdowns.

    This endpoint provides in-depth learning statistics including
    detailed breakdowns by category, time periods, and performance metrics.

    Query Parameters:
        - category (str, optional): Focus on specific category
        - period (str, optional): Analysis period (daily, weekly, monthly)
        - include_comparisons (bool, optional): Include period comparisons

    JSON Response Structure:
        {
            "detailed_stats": {                      # Detailed statistics
                "vocabulary": {                      # Vocabulary statistics
                    "words_learned": int,            # Total words learned
                    "words_reviewed": int,           # Words reviewed
                    "retention_rate": float,         # Retention rate
                    "difficulty_distribution": {     # Difficulty distribution
                        "easy": int,                 # Easy words
                        "medium": int,               # Medium words
                        "hard": int                  # Hard words
                    },
                    "learning_speed": float,         # Words per day
                    "mastery_level": str             # Mastery level
                },
                "grammar": {                         # Grammar statistics
                    "concepts_mastered": int,        # Concepts mastered
                    "exercises_completed": int,      # Exercises completed
                    "accuracy_rate": float,          # Accuracy rate
                    "weak_areas": [str],             # Weak areas
                    "strengths": [str]               # Strengths
                },
                "reading": {                         # Reading statistics
                    "texts_completed": int,          # Texts completed
                    "comprehension_rate": float,     # Comprehension rate
                    "reading_speed": float,          # Words per minute
                    "difficulty_level": str,         # Current difficulty
                    "progress_trend": [float]        # Progress trend
                },
                "speaking": {                        # Speaking statistics
                    "exercises_completed": int,      # Exercises completed
                    "pronunciation_score": float,    # Pronunciation score
                    "fluency_score": float,          # Fluency score
                    "confidence_level": str,         # Confidence level
                    "practice_time": int             # Practice time (minutes)
                },
                "writing": {                         # Writing statistics
                    "assignments_completed": int,    # Assignments completed
                    "grammar_score": float,          # Grammar score
                    "vocabulary_score": float,       # Vocabulary score
                    "creativity_score": float,       # Creativity score
                    "improvement_rate": float        # Improvement rate
                }
            },
            "time_analysis": {                       # Time-based analysis
                "daily_progress": [                  # Daily progress
                    {
                        "date": str,                 # Date
                        "lessons": int,              # Lessons completed
                        "exercises": int,            # Exercises completed
                        "time_spent": int,           # Time spent (minutes)
                        "score": float               # Daily score
                    }
                ],
                "weekly_totals": [                   # Weekly totals
                    {
                        "week": str,                 # Week identifier
                        "total_lessons": int,        # Total lessons
                        "total_exercises": int,      # Total exercises
                        "total_time": int,           # Total time
                        "average_score": float       # Average score
                    }
                ],
                "monthly_summary": [                 # Monthly summary
                    {
                        "month": str,                # Month identifier
                        "lessons_completed": int,    # Lessons completed
                        "exercises_completed": int,  # Exercises completed
                        "total_time": int,           # Total time
                        "improvement_rate": float    # Improvement rate
                    }
                ]
            },
            "performance_insights": {                # Performance insights
                "strengths": [str],                  # Identified strengths
                "weaknesses": [str],                 # Areas for improvement
                "recommendations": [str],            # Learning recommendations
                "goals_progress": {                  # Goals progress
                    "short_term": float,             # Short-term goals progress
                    "medium_term": float,            # Medium-term goals progress
                    "long_term": float               # Long-term goals progress
                }
            },
            "category": str,                         # Requested category
            "period": str,                           # Analysis period
            "generated_at": str                      # Generation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        category = request.args.get("category")
        period = request.args.get("period", "weekly")
        include_comparisons = request.args.get("include_comparisons", "false").lower() == "true"

        # Get detailed statistics
        detailed_stats = get_user_statistics(user, category, period, include_comparisons)

        return jsonify({
            **detailed_stats,
            "category": category,
            "period": period,
            "generated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error getting user statistics: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/achievements", methods=["GET"])
def get_user_achievements_route():
    """
    Get user achievements and milestones.

    This endpoint retrieves all achievements earned by the user
    including badges, milestones, and special recognitions.

    Query Parameters:
        - category (str, optional): Filter by achievement category
        - status (str, optional): Filter by status (earned, in_progress)
        - limit (int, optional): Maximum number of achievements (default: 20)
        - offset (int, optional): Pagination offset (default: 0)

    JSON Response Structure:
        {
            "achievements": [                        # Array of achievements
                {
                    "id": str,                       # Achievement identifier
                    "title": str,                    # Achievement title
                    "description": str,              # Achievement description
                    "category": str,                 # Achievement category
                    "icon": str,                     # Achievement icon URL
                    "earned_at": str,                # Earned timestamp
                    "progress": float,               # Progress percentage
                    "rarity": str,                   # Achievement rarity
                    "points": int                    # Points awarded
                }
            ],
            "summary": {                             # Achievement summary
                "total_achievements": int,           # Total achievements
                "earned_count": int,                 # Achievements earned
                "in_progress_count": int,            # Achievements in progress
                "total_points": int,                 # Total points earned
                "completion_percentage": float       # Overall completion percentage
            },
            "recent_achievements": [                 # Recently earned achievements
                {
                    "id": str,                       # Achievement identifier
                    "title": str,                    # Achievement title
                    "earned_at": str,                # Earned timestamp
                    "points": int                    # Points awarded
                }
            ],
            "next_achievements": [                   # Upcoming achievements
                {
                    "id": str,                       # Achievement identifier
                    "title": str,                    # Achievement title
                    "progress": float,               # Current progress
                    "remaining": str                 # What's remaining
                }
            ],
            "total": int,                            # Total number of achievements
            "limit": int,                            # Requested limit
            "offset": int                            # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        category = request.args.get("category")
        status = request.args.get("status")
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        # Get user achievements
        achievements_data = get_user_achievements(user, category, status, limit, offset)

        return jsonify(achievements_data)

    except DatabaseError as e:
        logger.error(f"Error getting user achievements: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/achievements/<achievement_id>", methods=["GET"])
def get_achievement_details_route(achievement_id: str):
    """
    Get detailed information about a specific achievement.

    This endpoint retrieves comprehensive information about a specific
    achievement including requirements, progress, and related statistics.

    Path Parameters:
        - achievement_id (str, required): Achievement identifier

    JSON Response Structure:
        {
            "achievement": {                         # Achievement details
                "id": str,                           # Achievement identifier
                "title": str,                        # Achievement title
                "description": str,                  # Achievement description
                "category": str,                     # Achievement category
                "icon": str,                         # Achievement icon URL
                "rarity": str,                       # Achievement rarity
                "points": int,                       # Points awarded
                "requirements": [                    # Achievement requirements
                    {
                        "type": str,                 # Requirement type
                        "description": str,          # Requirement description
                        "target": int,               # Target value
                        "current": int,              # Current value
                        "completed": bool            # Whether completed
                    }
                ],
                "rewards": [                         # Achievement rewards
                    {
                        "type": str,                 # Reward type
                        "description": str,          # Reward description
                        "value": str                 # Reward value
                    }
                ]
            },
            "user_progress": {                       # User's progress
                "earned": bool,                      # Whether achievement is earned
                "earned_at": str,                    # Earned timestamp
                "progress_percentage": float,        # Progress percentage
                "current_values": {                  # Current requirement values
                    "requirement_id": int            # Current value for each requirement
                },
                "estimated_completion": str          # Estimated completion date
            },
            "statistics": {                          # Achievement statistics
                "total_earned": int,                 # Total users who earned this
                "earned_percentage": float,          # Percentage of users who earned
                "average_completion_time": int,      # Average completion time (days)
                "user_rank": int                     # User's rank among earners
            },
            "related_achievements": [                # Related achievements
                {
                    "id": str,                       # Achievement identifier
                    "title": str,                    # Achievement title
                    "category": str,                 # Achievement category
                    "earned": bool                   # Whether user earned this
                }
            ]
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Achievement not found
        - 500: Internal server error
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

        # Get user's progress for this achievement
        user_progress = select_one(
            "user_achievements",
            columns="*",
            where="username = ? AND achievement_id = ?",
            params=(user, achievement_id)
        )

        # Get achievement statistics
        stats = select_one(
            "achievement_statistics",
            columns="*",
            where="achievement_id = ?",
            params=(achievement_id,)
        )

        return jsonify({
            "achievement": achievement,
            "user_progress": user_progress or {},
            "statistics": stats or {},
            "related_achievements": []  # TODO: Implement related achievements
        })

    except DatabaseError as e:
        logger.error(f"Error getting user statistics: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/analytics", methods=["GET"])
def get_progress_analytics_route():
    """
    Get comprehensive progress analytics and insights.

    This endpoint provides detailed analytics about the user's learning
    progress including trends, patterns, and personalized insights.

    Query Parameters:
        - timeframe (str, optional): Analytics timeframe (week, month, quarter, year)
        - include_predictions (bool, optional): Include future predictions
        - focus_area (str, optional): Focus on specific learning area

    JSON Response Structure:
        {
            "progress_overview": {                   # Progress overview
                "current_level": str,                # Current skill level
                "target_level": str,                 # Target skill level
                "progress_percentage": float,        # Progress toward target
                "estimated_completion": str,         # Estimated completion date
                "learning_velocity": float,          # Learning velocity (points/day)
                "consistency_score": float           # Learning consistency score
            },
            "trend_analysis": {                      # Trend analysis
                "score_trend": [                     # Score trend over time
                    {
                        "date": str,                 # Date
                        "score": float,              # Average score
                        "trend": str                 # Trend direction
                    }
                ],
                "time_trend": [                      # Time spent trend
                    {
                        "date": str,                 # Date
                        "time_spent": int,           # Time spent (minutes)
                        "efficiency": float          # Learning efficiency
                    }
                ],
                "difficulty_progression": [          # Difficulty progression
                    {
                        "date": str,                 # Date
                        "difficulty": str,           # Difficulty level
                        "success_rate": float        # Success rate
                    }
                ]
            },
            "learning_patterns": {                   # Learning patterns
                "optimal_times": [str],              # Optimal learning times
                "session_duration": {                # Session duration analysis
                    "optimal_length": int,           # Optimal session length
                    "average_length": int,           # Average session length
                    "efficiency_by_length": [        # Efficiency by session length
                        {
                            "duration": int,         # Session duration
                            "efficiency": float      # Learning efficiency
                        }
                    ]
                },
                "break_patterns": {                  # Break pattern analysis
                    "optimal_break_length": int,     # Optimal break length
                    "break_frequency": str,          # Break frequency
                    "recovery_time": int             # Recovery time needed
                }
            },
            "skill_development": {                   # Skill development analysis
                "vocabulary_growth": {               # Vocabulary growth
                    "words_per_day": float,          # Words learned per day
                    "retention_rate": float,         # Retention rate
                    "difficulty_distribution": object # Difficulty distribution
                },
                "grammar_mastery": {                 # Grammar mastery
                    "concepts_mastered": int,        # Concepts mastered
                    "accuracy_improvement": float,   # Accuracy improvement
                    "weak_areas": [str]              # Remaining weak areas
                },
                "comprehension_skills": {            # Comprehension skills
                    "reading_speed": float,          # Reading speed (wpm)
                    "comprehension_rate": float,     # Comprehension rate
                    "text_difficulty": str           # Current text difficulty
                }
            },
            "predictions": {                         # Future predictions (if requested)
                "estimated_completion": str,         # Estimated completion date
                "projected_level": str,              # Projected skill level
                "confidence_interval": float,        # Prediction confidence
                "recommended_actions": [str]         # Recommended actions
            },
            "insights": [                            # Personalized insights
                {
                    "type": str,                     # Insight type
                    "title": str,                    # Insight title
                    "description": str,              # Insight description
                    "impact": str,                   # Potential impact
                    "action_items": [str]            # Recommended actions
                }
            ],
            "timeframe": str,                        # Requested timeframe
            "focus_area": str,                       # Requested focus area
            "generated_at": str                      # Generation timestamp
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
        include_predictions = request.args.get("include_predictions", "false").lower() == "true"
        focus_area = request.args.get("focus_area")

        # Get progress analytics
        analytics = get_user_activity_timeline(user, timeframe, include_predictions, focus_area)

        return jsonify({
            **analytics,
            "timeframe": timeframe,
            "focus_area": focus_area,
            "generated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error getting user activity timeline: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/analytics/strengths", methods=["GET"])
def get_learning_strengths_route():
    """
    Get user's learning strengths and strong areas.

    This endpoint analyzes the user's performance to identify
    their learning strengths and areas where they excel.

    Query Parameters:
        - category (str, optional): Focus on specific category
        - timeframe (str, optional): Analysis timeframe (month, quarter, year)
        - include_comparison (bool, optional): Include peer comparison

    JSON Response Structure:
        {
            "strengths_overview": {                  # Strengths overview
                "total_strengths": int,              # Total strengths identified
                "primary_strength": str,             # Primary strength area
                "strength_score": float,             # Overall strength score
                "improvement_rate": float            # Strength improvement rate
            },
            "strength_areas": [                      # Detailed strength areas
                {
                    "category": str,                 # Strength category
                    "title": str,                    # Strength title
                    "description": str,              # Strength description
                    "performance_score": float,      # Performance score
                    "consistency_score": float,      # Consistency score
                    "improvement_trend": str,        # Improvement trend
                    "evidence": [                    # Supporting evidence
                        {
                            "metric": str,           # Performance metric
                            "value": float,          # Metric value
                            "benchmark": float,      # Benchmark value
                            "percentile": float      # Percentile rank
                        }
                    ],
                    "recommendations": [str]         # Recommendations to maintain
                }
            ],
            "skill_breakdown": {                     # Skill-specific strengths
                "vocabulary": {                      # Vocabulary strengths
                    "retention_rate": float,         # Retention rate
                    "learning_speed": float,         # Learning speed
                    "difficulty_handling": str,      # Difficulty handling
                    "strong_areas": [str]            # Strong vocabulary areas
                },
                "grammar": {                         # Grammar strengths
                    "accuracy_rate": float,          # Accuracy rate
                    "concept_mastery": [str],        # Mastered concepts
                    "error_reduction": float,        # Error reduction rate
                    "application_skills": str        # Application skills
                },
                "comprehension": {                   # Comprehension strengths
                    "reading_speed": float,          # Reading speed
                    "understanding_rate": float,     # Understanding rate
                    "inference_skills": str,         # Inference skills
                    "context_usage": str             # Context usage
                },
                "speaking": {                        # Speaking strengths
                    "pronunciation": float,          # Pronunciation score
                    "fluency": float,                # Fluency score
                    "confidence": str,               # Confidence level
                    "communication_skills": str      # Communication skills
                },
                "writing": {                         # Writing strengths
                    "grammar_accuracy": float,       # Grammar accuracy
                    "vocabulary_usage": float,       # Vocabulary usage
                    "creativity": float,             # Creativity score
                    "structure_skills": str          # Structure skills
                }
            },
            "comparative_analysis": {                # Peer comparison (if requested)
                "peer_percentile": float,            # Peer percentile
                "top_performers_comparison": {       # Comparison with top performers
                    "gap_analysis": [str],           # Gap analysis
                    "similarities": [str],           # Similarities
                    "competitive_advantages": [str]  # Competitive advantages
                },
                "improvement_potential": float       # Improvement potential
            },
            "maintenance_strategies": [              # Strategies to maintain strengths
                {
                    "strength": str,                 # Strength area
                    "strategy": str,                 # Maintenance strategy
                    "frequency": str,                # Recommended frequency
                    "expected_benefit": str          # Expected benefit
                }
            ],
            "category": str,                         # Requested category
            "timeframe": str,                        # Analysis timeframe
            "generated_at": str                      # Generation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        category = request.args.get("category")
        timeframe = request.args.get("timeframe", "month")
        include_comparison = request.args.get("include_comparison", "false").lower() == "true"

        # Get learning strengths
        strengths_data = get_user_profile_summary(user, timeframe, True, "strengths")

        return jsonify({
            **strengths_data,
            "category": category,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error getting user learning progress: {e}")
        return jsonify({"error": "Internal server error"}), 500


@profile_bp.route("/analytics/weaknesses", methods=["GET"])
def get_learning_weaknesses_route():
    """
    Get user's learning weaknesses and areas for improvement.

    This endpoint analyzes the user's performance to identify
    areas that need improvement and provides targeted recommendations.

    Query Parameters:
        - category (str, optional): Focus on specific category
        - timeframe (str, optional): Analysis timeframe (month, quarter, year)
        - include_recommendations (bool, optional): Include improvement recommendations

    JSON Response Structure:
        {
            "weaknesses_overview": {                 # Weaknesses overview
                "total_weaknesses": int,             # Total weaknesses identified
                "primary_weakness": str,             # Primary weakness area
                "impact_score": float,               # Impact on overall performance
                "improvement_priority": str          # Improvement priority level
            },
            "weakness_areas": [                      # Detailed weakness areas
                {
                    "category": str,                 # Weakness category
                    "title": str,                    # Weakness title
                    "description": str,              # Weakness description
                    "severity": str,                 # Severity level
                    "frequency": float,              # Frequency of occurrence
                    "impact_on_learning": str,       # Impact on learning
                    "evidence": [                    # Supporting evidence
                        {
                            "metric": str,           # Performance metric
                            "current_value": float,  # Current value
                            "target_value": float,   # Target value
                            "gap": float             # Performance gap
                        }
                    ],
                    "root_causes": [str],            # Root causes
                    "improvement_potential": float   # Improvement potential
                }
            ],
            "skill_breakdown": {                     # Skill-specific weaknesses
                "vocabulary": {                      # Vocabulary weaknesses
                    "retention_issues": [str],       # Retention issues
                    "difficulty_struggles": [str],   # Difficulty struggles
                    "learning_barriers": [str],      # Learning barriers
                    "weak_areas": [str]              # Weak vocabulary areas
                },
                "grammar": {                         # Grammar weaknesses
                    "error_patterns": [str],         # Error patterns
                    "difficult_concepts": [str],     # Difficult concepts
                    "application_issues": [str],     # Application issues
                    "understanding_gaps": [str]      # Understanding gaps
                },
                "comprehension": {                   # Comprehension weaknesses
                    "reading_difficulties": [str],   # Reading difficulties
                    "understanding_issues": [str],   # Understanding issues
                    "inference_problems": [str],     # Inference problems
                    "context_usage": str             # Context usage issues
                },
                "speaking": {                        # Speaking weaknesses
                    "pronunciation_issues": [str],   # Pronunciation issues
                    "fluency_problems": [str],       # Fluency problems
                    "confidence_issues": str,        # Confidence issues
                    "communication_barriers": [str]  # Communication barriers
                },
                "writing": {                         # Writing weaknesses
                    "grammar_errors": [str],         # Grammar errors
                    "vocabulary_limitations": [str], # Vocabulary limitations
                    "structure_issues": [str],       # Structure issues
                    "creativity_barriers": [str]     # Creativity barriers
                }
            },
            "improvement_recommendations": [          # Improvement recommendations
                {
                    "weakness": str,                 # Weakness area
                    "recommendation": str,           # Improvement recommendation
                    "priority": str,                 # Priority level
                    "estimated_time": str,           # Estimated improvement time
                    "resources": [str],              # Recommended resources
                    "practice_exercises": [str],     # Practice exercises
                    "expected_improvement": float    # Expected improvement
                }
            ],
            "learning_strategies": [                 # Learning strategies
                {
                    "strategy": str,                 # Learning strategy
                    "description": str,              # Strategy description
                    "applicability": [str],          # Applicable areas
                    "implementation_steps": [str],   # Implementation steps
                    "success_metrics": [str]         # Success metrics
                }
            ],
            "progress_tracking": {                   # Progress tracking plan
                "baseline_metrics": {                # Baseline metrics
                    "metric": float                  # Current metric values
                },
                "target_metrics": {                  # Target metrics
                    "metric": float                  # Target metric values
                },
                "checkpoints": [                     # Progress checkpoints
                    {
                        "date": str,                 # Checkpoint date
                        "target": float,             # Target value
                        "status": str                # Checkpoint status
                    }
                ],
                "review_schedule": str               # Review schedule
            },
            "category": str,                         # Requested category
            "timeframe": str,                        # Analysis timeframe
            "generated_at": str                      # Generation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Get query parameters
        category = request.args.get("category")
        timeframe = request.args.get("timeframe", "month")
        include_recommendations = request.args.get("include_recommendations", "true").lower() == "true"

        # Get learning weaknesses
        weaknesses_data = get_user_profile_summary(user, timeframe, True, "weaknesses")

        return jsonify({
            **weaknesses_data,
            "category": category,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except DatabaseError as e:
        logger.error(f"Error getting user learning weaknesses: {e}")
        return jsonify({"error": "Internal server error"}), 500
