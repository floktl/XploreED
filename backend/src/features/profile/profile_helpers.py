"""
Profile Helper Functions

This module contains helper functions for user profile operations that are used
by the profile routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any, List, Optional

from core.services.import_service import *


logger = logging.getLogger(__name__)


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
                "correct_games": 0,
                "accuracy": 0.0,
                "vocabulary_count": 0,
                "lessons_completed": 0
            }

        # Get game statistics
        game_stats = _get_game_statistics(username)

        # Get vocabulary count
        vocab_count = _get_vocabulary_count(username)

        # Get lessons completed
        lessons_completed = _get_lessons_completed(username)

        profile_summary = {
            "username": username,
            "exists": True,
            "created_at": user_info.get("created_at"),
            "skill_level": user_info.get("skill_level", 0),
            "total_games": game_stats["total_games"],
            "correct_games": game_stats["correct_games"],
            "accuracy": game_stats["accuracy"],
            "vocabulary_count": vocab_count,
            "lessons_completed": lessons_completed
        }

        logger.info(f"Retrieved profile summary for user {username}")
        return profile_summary

    except ValueError as e:
        logger.error(f"Validation error getting profile summary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting profile summary for user {username}: {e}")
        raise


def get_user_achievements(username: str) -> List[Dict[str, Any]]:
    """
    Get user achievements and milestones.

    Args:
        username: The username to get achievements for

    Returns:
        List of achievements with details

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting achievements for user {username}")

        achievements = []

        # Get game statistics for achievement calculation
        game_stats = _get_game_statistics(username)
        vocab_count = _get_vocabulary_count(username)
        lessons_completed = _get_lessons_completed(username)

        # First game achievement
        if game_stats["total_games"] >= 1:
            achievements.append({
                "id": "first_game",
                "title": "First Steps",
                "description": "Completed your first game",
                "unlocked_at": _get_first_game_timestamp(username),
                "icon": "🎮"
            })

        # 10 games achievement
        if game_stats["total_games"] >= 10:
            achievements.append({
                "id": "ten_games",
                "title": "Getting Started",
                "description": "Completed 10 games",
                "unlocked_at": _get_nth_game_timestamp(username, 10),
                "icon": "🎯"
            })

        # 50 games achievement
        if game_stats["total_games"] >= 50:
            achievements.append({
                "id": "fifty_games",
                "title": "Dedicated Learner",
                "description": "Completed 50 games",
                "unlocked_at": _get_nth_game_timestamp(username, 50),
                "icon": "🏆"
            })

        # 100 games achievement
        if game_stats["total_games"] >= 100:
            achievements.append({
                "id": "hundred_games",
                "title": "Century Club",
                "description": "Completed 100 games",
                "unlocked_at": _get_nth_game_timestamp(username, 100),
                "icon": "💎"
            })

        # Perfect score achievement
        if game_stats["accuracy"] >= 100.0 and game_stats["total_games"] >= 5:
            achievements.append({
                "id": "perfect_score",
                "title": "Perfect Score",
                "description": "Achieved 100% accuracy in 5+ games",
                "unlocked_at": _get_perfect_score_timestamp(username),
                "icon": "⭐"
            })

        # Vocabulary achievements
        if vocab_count >= 10:
            achievements.append({
                "id": "vocab_beginner",
                "title": "Vocabulary Builder",
                "description": "Learned 10 vocabulary words",
                "unlocked_at": _get_vocab_achievement_timestamp(username, 10),
                "icon": "📚"
            })

        if vocab_count >= 50:
            achievements.append({
                "id": "vocab_intermediate",
                "title": "Word Master",
                "description": "Learned 50 vocabulary words",
                "unlocked_at": _get_vocab_achievement_timestamp(username, 50),
                "icon": "📖"
            })

        # Lesson completion achievements
        if lessons_completed >= 1:
            achievements.append({
                "id": "first_lesson",
                "title": "Lesson Learner",
                "description": "Completed your first lesson",
                "unlocked_at": _get_first_lesson_timestamp(username),
                "icon": "📝"
            })

        if lessons_completed >= 5:
            achievements.append({
                "id": "five_lessons",
                "title": "Lesson Explorer",
                "description": "Completed 5 lessons",
                "unlocked_at": _get_nth_lesson_timestamp(username, 5),
                "icon": "🎓"
            })

        logger.info(f"Retrieved {len(achievements)} achievements for user {username}")
        return achievements

    except ValueError as e:
        logger.error(f"Validation error getting user achievements: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting achievements for user {username}: {e}")
        raise


def get_user_activity_timeline(username: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get user activity timeline with recent actions.

    Args:
        username: The username to get timeline for
        limit: Maximum number of activities to return

    Returns:
        List of activities with timestamps

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if limit <= 0:
            limit = 20

        logger.info(f"Getting activity timeline for user {username}")

        timeline = []

        # Get recent game results
        game_results = select_rows(
            "results",
            columns=["level", "correct", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
            limit=limit
        )

        for result in game_results:
            timeline.append({
                "type": "game",
                "action": "Completed game",
                "details": f"Level {result['level']} - {'Correct' if result['correct'] else 'Incorrect'}",
                "timestamp": result["timestamp"],
                "icon": "🎮"
            })

        # Get recent vocabulary additions
        vocab_results = select_rows(
            "vocab_log",
            columns=["word", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
            limit=limit
        )

        for vocab in vocab_results:
            timeline.append({
                "type": "vocabulary",
                "action": "Learned new word",
                "details": f"Added '{vocab['word']}' to vocabulary",
                "timestamp": vocab["timestamp"],
                "icon": "📚"
            })

        # Get recent lesson completions
        lesson_results = select_rows(
            "results",
            columns=["level", "timestamp"],
            where="username = ? AND level > 100",  # Assuming lessons have higher level numbers
            params=(username,),
            order_by="timestamp DESC",
            limit=limit
        )

        for lesson in lesson_results:
            timeline.append({
                "type": "lesson",
                "action": "Completed lesson",
                "details": f"Finished lesson {lesson['level']}",
                "timestamp": lesson["timestamp"],
                "icon": "📝"
            })

        # Sort by timestamp and limit results
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        timeline = timeline[:limit]

        logger.info(f"Retrieved {len(timeline)} activities for user {username}")
        return timeline

    except ValueError as e:
        logger.error(f"Validation error getting activity timeline: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting activity timeline for user {username}: {e}")
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
        # Get total games and correct games
        stats_row = select_one(
            "results",
            columns="COUNT(*) as total_games, SUM(correct) as correct_games",
            where="username = ?",
            params=(username,)
        )

        total_games = stats_row.get("total_games", 0) if stats_row else 0
        correct_games = stats_row.get("correct_games", 0) if stats_row else 0

        # Calculate accuracy
        accuracy = (correct_games / total_games * 100) if total_games > 0 else 0.0

        return {
            "total_games": total_games,
            "correct_games": correct_games,
            "accuracy": round(accuracy, 1)
        }

    except Exception as e:
        logger.error(f"Error getting game statistics for user {username}: {e}")
        return {
            "total_games": 0,
            "correct_games": 0,
            "accuracy": 0.0
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
        vocab_row = select_one(
            "vocab_log",
            columns="COUNT(*) as count",
            where="username = ?",
            params=(username,)
        )

        return vocab_row.get("count", 0) if vocab_row else 0

    except Exception as e:
        logger.error(f"Error getting vocabulary count for user {username}: {e}")
        return 0


def _get_lessons_completed(username: str) -> int:
    """
    Get number of lessons completed by a user.

    Args:
        username: The username to get lesson count for

    Returns:
        Number of completed lessons
    """
    try:
        lesson_row = select_one(
            "results",
            columns="COUNT(*) as count",
            where="username = ? AND level > 100",  # Assuming lessons have higher level numbers
            params=(username,)
        )

        return lesson_row.get("count", 0) if lesson_row else 0

    except Exception as e:
        logger.error(f"Error getting lessons completed for user {username}: {e}")
        return 0


def _get_first_game_timestamp(username: str) -> Optional[str]:
    """Get timestamp of first game."""
    try:
        row = select_one(
            "results",
            columns="timestamp",
            where="username = ?",
            params=(username,),
            order_by="timestamp ASC"
        )
        return row.get("timestamp") if row else None
    except Exception:
        return None


def _get_nth_game_timestamp(username: str, n: int) -> Optional[str]:
    """Get timestamp of nth game."""
    try:
        row = select_one(
            "results",
            columns="timestamp",
            where="username = ?",
            params=(username,),
            order_by="timestamp ASC",
            limit=n
        )
        return row.get("timestamp") if row else None
    except Exception:
        return None


def _get_perfect_score_timestamp(username: str) -> Optional[str]:
    """Get timestamp when perfect score was achieved."""
    try:
        # This is a simplified implementation
        return _get_first_game_timestamp(username)
    except Exception:
        return None


def _get_vocab_achievement_timestamp(username: str, count: int) -> Optional[str]:
    """Get timestamp when vocabulary achievement was unlocked."""
    try:
        row = select_one(
            "vocab_log",
            columns="timestamp",
            where="username = ?",
            params=(username,),
            order_by="timestamp ASC",
            limit=count
        )
        return row.get("timestamp") if row else None
    except Exception:
        return None


def _get_first_lesson_timestamp(username: str) -> Optional[str]:
    """Get timestamp of first lesson completion."""
    try:
        row = select_one(
            "results",
            columns="timestamp",
            where="username = ? AND level > 100",
            params=(username,),
            order_by="timestamp ASC"
        )
        return row.get("timestamp") if row else None
    except Exception:
        return None


def _get_nth_lesson_timestamp(username: str, n: int) -> Optional[str]:
    """Get timestamp of nth lesson completion."""
    try:
        row = select_one(
            "results",
            columns="timestamp",
            where="username = ? AND level > 100",
            params=(username,),
            order_by="timestamp ASC",
            limit=n
        )
        return row.get("timestamp") if row else None
    except Exception:
        return None
