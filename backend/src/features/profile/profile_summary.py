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
from typing import Dict, Any, List, Optional

from core.services.import_service import *
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection

logger = logging.getLogger(__name__)


def get_user_profile_summary(username: str) -> Dict[str, Any]:
    """
    Get comprehensive profile summary for a user.

    Args:
        username: The username to get profile for

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

        # Get various statistics
        game_stats = _get_game_statistics(username)
        vocabulary_count = _get_vocabulary_count(username)
        lessons_completed = _get_lessons_completed(username)

        # Calculate skill level based on performance
        skill_level = _calculate_skill_level(game_stats, vocabulary_count, lessons_completed)

        # Get learning streak
        learning_streak = _calculate_learning_streak(username)

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

        logger.info(f"Retrieved profile summary for user {username}: skill level {skill_level}")
        return profile_summary

    except ValueError as e:
        logger.error(f"Validation error getting profile summary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting profile summary for user {username}: {e}")
        return {
            "username": username,
            "exists": False,
            "error": str(e),
        }


def get_user_game_results(username: str) -> List[Dict[str, Any]]:
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


def _get_game_statistics(username: str) -> Dict[str, Any]:
    """
    Get game statistics for a user.

    Args:
        username: The username to get statistics for

    Returns:
        Dictionary containing game statistics
    """
    try:
        # Get total games played
        total_games_result = select_one(
            "results",
            columns="COUNT(*) as count",
            where="username = ?",
            params=(username,),
        )
        total_games = total_games_result.get("count", 0) if total_games_result else 0

        # Get correct answers
        correct_answers_result = select_one(
            "results",
            columns="COUNT(*) as count",
            where="username = ? AND correct = 1",
            params=(username,),
        )
        correct_answers = correct_answers_result.get("count", 0) if correct_answers_result else 0

        # Calculate average score
        average_score = (correct_answers / total_games * 100) if total_games > 0 else 0.0

        # Get best score (highest level achieved)
        best_score_result = select_one(
            "results",
            columns="MAX(level) as max_level",
            where="username = ?",
            params=(username,),
        )
        best_score = best_score_result.get("max_level", 0) if best_score_result else 0

        # Get last activity
        last_activity_result = select_one(
            "results",
            columns="MAX(timestamp) as last_timestamp",
            where="username = ?",
            params=(username,),
        )
        last_activity = last_activity_result.get("last_timestamp") if last_activity_result else None

        # Calculate completion rate (games with correct answers)
        completion_rate = (correct_answers / total_games * 100) if total_games > 0 else 0.0

        # Estimate total play time (rough calculation)
        total_play_time = total_games * 2  # Assuming 2 minutes per game

        return {
            "total_games": total_games,
            "correct_answers": correct_answers,
            "average_score": round(average_score, 2),
            "best_score": best_score,
            "last_activity": last_activity,
            "completion_rate": round(completion_rate, 2),
            "total_play_time": total_play_time,
        }

    except Exception as e:
        logger.error(f"Error getting game statistics for user {username}: {e}")
        return {
            "total_games": 0,
            "correct_answers": 0,
            "average_score": 0.0,
            "best_score": 0,
            "last_activity": None,
            "completion_rate": 0.0,
            "total_play_time": 0,
        }


def _get_vocabulary_count(username: str) -> int:
    """
    Get vocabulary count for a user.

    Args:
        username: The username to get vocabulary count for

    Returns:
        Number of vocabulary words
    """
    try:
        vocab_result = select_one(
            "vocab_log",
            columns="COUNT(*) as count",
            where="username = ?",
            params=(username,),
        )
        return vocab_result.get("count", 0) if vocab_result else 0

    except Exception as e:
        logger.error(f"Error getting vocabulary count for user {username}: {e}")
        return 0


def _get_lessons_completed(username: str) -> int:
    """
    Get lessons completed count for a user.

    Args:
        username: The username to get lessons count for

    Returns:
        Number of completed lessons
    """
    try:
        lessons_result = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="user_id = ? AND completed_blocks >= total_blocks",
            params=(username,),
        )
        return lessons_result.get("count", 0) if lessons_result else 0

    except Exception as e:
        logger.error(f"Error getting lessons completed for user {username}: {e}")
        return 0


def _calculate_skill_level(game_stats: Dict[str, Any], vocabulary_count: int, lessons_completed: int) -> int:
    """
    Calculate skill level based on user performance.

    Args:
        game_stats: Game statistics dictionary
        vocabulary_count: Number of vocabulary words
        lessons_completed: Number of completed lessons

    Returns:
        Skill level (1-10)
    """
    try:
        total_games = game_stats.get("total_games", 0)
        average_score = game_stats.get("average_score", 0.0)
        best_score = game_stats.get("best_score", 0)

        # Base score from games
        game_score = min(10, (total_games * 0.1) + (average_score * 0.05) + (best_score * 0.2))

        # Vocabulary bonus
        vocab_bonus = min(3, vocabulary_count * 0.01)

        # Lessons bonus
        lessons_bonus = min(2, lessons_completed * 0.5)

        # Calculate total skill level
        skill_level = int(game_score + vocab_bonus + lessons_bonus)
        return max(1, min(10, skill_level))

    except Exception as e:
        logger.error(f"Error calculating skill level: {e}")
        return 1


def _calculate_learning_streak(username: str) -> int:
    """
    Calculate learning streak for a user.

    Args:
        username: The username to calculate streak for

    Returns:
        Number of consecutive days with activity
    """
    try:
        # Get recent activity (last 30 days)
        recent_activity = select_rows(
            "results",
            columns="DISTINCT DATE(timestamp) as activity_date",
            where="username = ? AND timestamp >= date('now', '-30 days')",
            params=(username,),
            order_by="activity_date DESC",
        )

        if not recent_activity:
            return 0

        # Calculate streak
        streak = 0
        current_date = None

        for row in recent_activity:
            activity_date = row.get("activity_date")
            if current_date is None:
                current_date = activity_date
                streak = 1
            else:
                # Check if consecutive day
                from datetime import datetime, timedelta
                try:
                    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
                    activity_dt = datetime.strptime(activity_date, "%Y-%m-%d")
                    if (current_dt - activity_dt).days == 1:
                        streak += 1
                        current_date = activity_date
                    else:
                        break
                except:
                    break

        return streak

    except Exception as e:
        logger.error(f"Error calculating learning streak for user {username}: {e}")
        return 0
