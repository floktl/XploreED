"""
XplorED - Profile Summary Module

This module provides profile summary and basic profile functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Profile Summary Components:
- Profile Summaries: Get comprehensive profile summaries for users
- Game Results: Retrieve user game results and performance
- Basic Profile Info: Get user basic information and statistics
- Profile Validation: Validate user profile data and access

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import List, Optional

from infrastructure.imports import Imports
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from core.services import UserService
from shared.exceptions import DatabaseError
from shared.types import AnalyticsData, GameList

logger = logging.getLogger(__name__)


def get_user_profile_summary(
    username: str,
    timeframe: str = "all",
    include_details: bool = False
) -> AnalyticsData:
    """
    Get comprehensive profile summary for a user.

    Args:
        username: The username to get profile for
        timeframe: Statistics timeframe (week, month, year, all)
        include_details: Include detailed breakdown

    Returns:
        Dictionary containing profile summary

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting profile summary for user {username}")

        # Get user basic info
        user_info = fetch_one("users", "WHERE username = ?", (username,))
        if not user_info:
            return {
                "username": username,
                "exists": False,
                "created_at": None,
                "skill_level": 0,
                "total_games": 0,
                "total_vocabulary": 0,
                "lessons_completed": 0,
                "achievements": [],
                "recent_activity": [],
                "learning_streak": 0,
                "average_score": 0.0,
                "best_score": 0,
                "total_play_time": 0,
            }

        # Get comprehensive user statistics using core service
        user_stats = UserService.get_user_statistics(username)

        # Extract values from user statistics
        skill_level = user_stats.get("skill_level", 1)
        game_stats = user_stats.get("game_statistics", {})
        vocabulary_count = user_stats.get("total_vocabulary", 0)
        lessons_completed = user_stats.get("lessons_completed", 0)
        learning_streak = user_stats.get("learning_streak", 0)

        # Base profile summary
        profile_summary = {
            "username": username,
            "exists": True,
            "created_at": user_info.get("created_at"),
            "skill_level": skill_level,
            "total_games": game_stats.get("total_games", 0),
            "total_vocabulary": vocabulary_count,
            "lessons_completed": lessons_completed,
            "achievements": [],  # Will be populated by achievements module
            "recent_activity": [],  # Will be populated by achievements module
            "learning_streak": learning_streak,
            "average_score": game_stats.get("average_score", 0.0),
            "best_score": game_stats.get("best_score", 0),
            "total_play_time": game_stats.get("total_play_time", 0),
            "last_activity": game_stats.get("last_activity"),
            "completion_rate": game_stats.get("completion_rate", 0.0),
        }

        # Add timeframe-specific data if requested
        if timeframe != "all":
            # Calculate date range based on timeframe
            from datetime import datetime, timedelta
            now = datetime.now()

            if timeframe == "week":
                start_date = now - timedelta(days=7)
            elif timeframe == "month":
                start_date = now - timedelta(days=30)
            elif timeframe == "year":
                start_date = now - timedelta(days=365)
            else:
                start_date = now - timedelta(days=30)  # Default to month

            # Add timeframe-specific statistics
            profile_summary["timeframe"] = timeframe
            profile_summary["period_start"] = start_date.isoformat()
            profile_summary["period_end"] = now.isoformat()

        # Add detailed breakdown if requested
        if include_details:
            profile_summary["detailed_breakdown"] = {
                "vocabulary_progress": {
                    "words_learned": vocabulary_count,
                    "words_reviewed": 0,  # Placeholder
                    "mastery_rate": 0.0,  # Placeholder
                },
                "lesson_progress": {
                    "lessons_started": lessons_completed,
                    "lessons_completed": lessons_completed,
                    "completion_rate": 1.0 if lessons_completed > 0 else 0.0,
                },
                "game_performance": {
                    "games_played": game_stats.get("total_games", 0),
                    "average_score": game_stats.get("average_score", 0.0),
                    "best_score": game_stats.get("best_score", 0),
                    "total_play_time": game_stats.get("total_play_time", 0),
                }
            }

        logger.info(f"Retrieved profile summary for user {username}: skill level {skill_level}")
        return profile_summary

    except ValueError as e:
        logger.error(f"Validation error getting profile summary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting profile summary for {username}: {e}")
        raise DatabaseError(f"Error getting profile summary for {username}: {str(e)}")


def get_user_game_results(username: str) -> GameList:
    """
    Get the current user's past game results.

    Args:
        username: The username to get results for

    Returns:
        List of game results with details

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting game results for user {username}")

        rows = select_rows(
            "results",
            columns=["level", "answer", "correct", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
        )

        if rows is None:
            logger.error(f"Failed to fetch results for user {username}")
            return []

        results = [
            {
                "level": row["level"],
                "answer": row["answer"],
                "correct": row["correct"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

        logger.info(f"Retrieved {len(results)} game results for user {username}")
        return results

    except ValueError as e:
        logger.error(f"Validation error getting user game results: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting game results for user {username}: {e}")
        raise


# Note: Game statistics, vocabulary count, lessons completed, skill level calculation,
# and learning streak calculation are now handled by the UserService in core/services/user_service.py
