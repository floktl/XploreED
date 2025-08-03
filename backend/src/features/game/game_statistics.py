"""
XplorED - Game Statistics Module

This module provides game statistics and analysis functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Game Statistics Components:
- Performance Analysis: Analyze user game performance and statistics
- Progress Tracking: Track user progress across different game levels
- Achievement Metrics: Calculate achievement and improvement metrics

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import List, Optional

from core.database.connection import select_rows, fetch_one, fetch_all
from shared.exceptions import DatabaseError, ValidationError
from shared.types import AnalyticsData

logger = logging.getLogger(__name__)


def get_game_statistics(username: str) -> AnalyticsData:
    """
    Get comprehensive game statistics for a user.

    Args:
        username: The username to get statistics for

    Returns:
        Dictionary containing game statistics

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting game statistics for user '{username}'")

        stats = {
            "username": username,
            "total_games": 0,
            "total_rounds": 0,
            "correct_answers": 0,
            "total_answers": 0,
            "accuracy_rate": 0.0,
            "average_score": 0.0,
            "highest_level": 0,
            "current_streak": 0,
            "best_streak": 0,
            "total_play_time": 0,
            "favorite_level": None,
            "improvement_rate": 0.0,
            "last_played": None,
            "level_progress": {},
            "recent_performance": []
        }

        # Get game results
        results = select_rows(
            "results",
            columns=["level", "correct", "answer", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC"
        )

        if results:
            stats["total_rounds"] = len(results)
            stats["correct_answers"] = sum(1 for r in results if r.get("correct", 0) == 1)
            stats["total_answers"] = len(results)

            # Calculate accuracy
            if stats["total_answers"] > 0:
                stats["accuracy_rate"] = round((stats["correct_answers"] / stats["total_answers"]) * 100, 2)

            # Get highest level achieved
            levels = [r.get("level", 0) for r in results if r.get("level")]
            if levels:
                stats["highest_level"] = max(levels)

            # Calculate streaks
            current_streak = 0
            best_streak = 0
            max_streak = 0

            for result in results:
                if result.get("correct", 0) == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0

            stats["current_streak"] = current_streak
            stats["best_streak"] = max_streak

            # Get last played date
            if results:
                last_result = results[0]
                stats["last_played"] = last_result.get("timestamp")

            # Calculate level progress
            level_counts = {}
            level_correct = {}
            for result in results:
                level = result.get("level", 0)
                level_counts[level] = level_counts.get(level, 0) + 1
                if result.get("correct", 0) == 1:
                    level_correct[level] = level_correct.get(level, 0) + 1

            for level in level_counts:
                total = level_counts[level]
                correct = level_correct.get(level, 0)
                accuracy = (correct / total) * 100 if total > 0 else 0
                stats["level_progress"][level] = {
                    "total_rounds": total,
                    "correct_answers": correct,
                    "accuracy": round(accuracy, 2)
                }

            # Find favorite level (most played)
            if level_counts:
                stats["favorite_level"] = max(level_counts, key=level_counts.get)

            # Calculate recent performance (last 10 games)
            recent_results = results[:10]
            recent_correct = sum(1 for r in recent_results if r.get("correct", 0) == 1)
            if recent_results:
                stats["recent_performance"] = {
                    "games": len(recent_results),
                    "correct": recent_correct,
                    "accuracy": round((recent_correct / len(recent_results)) * 100, 2)
                }

        # Get game sessions for additional stats
        sessions = select_rows(
            "game_sessions",
            columns=["session_id", "level", "status", "created_at"],
            where="username = ?",
            params=(username,)
        )

        if sessions:
            stats["total_games"] = len(sessions)

            # Calculate average score from game scores
            scores = select_rows(
                "game_scores",
                columns=["final_score"],
                where="session_id IN (SELECT session_id FROM game_sessions WHERE username = ?)",
                params=(username,)
            )

            if scores:
                total_score = sum(s.get("final_score", 0) for s in scores)
                stats["average_score"] = round(total_score / len(scores), 2)

        # Calculate improvement rate (comparing recent vs older performance)
        if len(results) >= 20:
            recent_20 = results[:20]
            older_20 = results[-20:] if len(results) >= 40 else results[20:40]

            recent_accuracy = sum(1 for r in recent_20 if r.get("correct", 0) == 1) / len(recent_20)
            older_accuracy = sum(1 for r in older_20 if r.get("correct", 0) == 1) / len(older_20)

            if older_accuracy > 0:
                improvement = ((recent_accuracy - older_accuracy) / older_accuracy) * 100
                stats["improvement_rate"] = round(improvement, 2)

        logger.info(f"Retrieved game statistics for user '{username}': {stats['total_rounds']} rounds, {stats['accuracy_rate']}% accuracy")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting game statistics: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting game statistics for user '{username}': {e}")
        raise DatabaseError(f"Error getting game statistics for user '{username}': {str(e)}")


def get_user_game_level_progress(username: str) -> AnalyticsData:
    """
    Get detailed level progress for a user.

    Args:
        username: The username to get level progress for

    Returns:
        Dictionary containing level progress data

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting level progress for user '{username}'")

        # Get all results grouped by level
        results = select_rows(
            "results",
            columns=["level", "correct", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="level ASC, timestamp ASC"
        )

        level_progress = {}
        current_level = 0

        for result in results:
            level = result.get("level", 0)
            is_correct = result.get("correct", 0) == 1

            if level not in level_progress:
                level_progress[level] = {
                    "level": level,
                    "total_attempts": 0,
                    "correct_attempts": 0,
                    "accuracy": 0.0,
                    "first_attempt": None,
                    "last_attempt": None,
                    "consecutive_correct": 0,
                    "best_consecutive": 0,
                    "current_streak": 0
                }

            level_data = level_progress[level]
            level_data["total_attempts"] += 1
            level_data["last_attempt"] = result.get("timestamp")

            if not level_data["first_attempt"]:
                level_data["first_attempt"] = result.get("timestamp")

            if is_correct:
                level_data["correct_attempts"] += 1
                level_data["consecutive_correct"] += 1
                level_data["current_streak"] += 1
                level_data["best_consecutive"] = max(level_data["best_consecutive"], level_data["consecutive_correct"])
            else:
                level_data["consecutive_correct"] = 0
                level_data["current_streak"] = 0

            # Calculate accuracy
            if level_data["total_attempts"] > 0:
                level_data["accuracy"] = round((level_data["correct_attempts"] / level_data["total_attempts"]) * 100, 2)

        # Determine current level (highest level with good performance)
        current_level = 0
        for level in sorted(level_progress.keys()):
            level_data = level_progress[level]
            if level_data["accuracy"] >= 70 and level_data["total_attempts"] >= 5:
                current_level = level

        return {
            "username": username,
            "current_level": current_level,
            "total_levels_attempted": len(level_progress),
            "level_progress": level_progress
        }

    except ValueError as e:
        logger.error(f"Validation error getting level progress: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting level progress for user '{username}': {e}")
        raise DatabaseError(f"Error getting level progress for user '{username}': {str(e)}")


def get_game_achievements(username: str) -> AnalyticsData:
    """
    Get game achievements and milestones for a user.

    Args:
        username: The username to get achievements for

    Returns:
        Dictionary containing achievements data

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting game achievements for user '{username}'")

        # Get user statistics
        stats = get_game_statistics(username)

        achievements = {
            "username": username,
            "total_achievements": 0,
            "achievements": [],
            "milestones": [],
            "next_milestones": []
        }

        # Define achievement criteria
        achievement_criteria = [
            {"name": "First Steps", "description": "Complete your first game", "condition": lambda s: s["total_games"] >= 1},
            {"name": "Getting Started", "description": "Complete 5 games", "condition": lambda s: s["total_games"] >= 5},
            {"name": "Regular Player", "description": "Complete 25 games", "condition": lambda s: s["total_games"] >= 25},
            {"name": "Dedicated Learner", "description": "Complete 100 games", "condition": lambda s: s["total_games"] >= 100},
            {"name": "Perfect Score", "description": "Get 100% accuracy in a game", "condition": lambda s: s["accuracy_rate"] >= 100},
            {"name": "High Achiever", "description": "Maintain 90%+ accuracy", "condition": lambda s: s["accuracy_rate"] >= 90},
            {"name": "Streak Master", "description": "Get a 10-game winning streak", "condition": lambda s: s["best_streak"] >= 10},
            {"name": "Level Up", "description": "Reach level 5", "condition": lambda s: s["highest_level"] >= 5},
            {"name": "Advanced Player", "description": "Reach level 10", "condition": lambda s: s["highest_level"] >= 10},
            {"name": "Consistent Learner", "description": "Play for 7 consecutive days", "condition": lambda s: s.get("consecutive_days", 0) >= 7}
        ]

        # Check achievements
        for achievement in achievement_criteria:
            if achievement["condition"](stats):
                achievements["achievements"].append({
                    "name": achievement["name"],
                    "description": achievement["description"],
                    "earned": True,
                    "earned_date": datetime.datetime.now().isoformat()
                })
            else:
                achievements["next_milestones"].append({
                    "name": achievement["name"],
                    "description": achievement["description"],
                    "progress": 0  # Could calculate progress here
                })

        achievements["total_achievements"] = len(achievements["achievements"])

        # Add milestones based on current stats
        milestones = [
            {"name": "50 Games", "target": 50, "current": stats["total_games"]},
            {"name": "200 Games", "target": 200, "current": stats["total_games"]},
            {"name": "500 Games", "target": 500, "current": stats["total_games"]},
            {"name": "95% Accuracy", "target": 95, "current": stats["accuracy_rate"]},
            {"name": "Level 15", "target": 15, "current": stats["highest_level"]},
            {"name": "20-Game Streak", "target": 20, "current": stats["best_streak"]}
        ]

        for milestone in milestones:
            if milestone["current"] >= milestone["target"]:
                achievements["milestones"].append({
                    "name": milestone["name"],
                    "achieved": True,
                    "achieved_date": datetime.datetime.now().isoformat()
                })
            else:
                achievements["next_milestones"].append({
                    "name": milestone["name"],
                    "progress": (milestone["current"] / milestone["target"]) * 100,
                    "current": milestone["current"],
                    "target": milestone["target"]
                })

        logger.info(f"Retrieved {achievements['total_achievements']} achievements for user '{username}'")
        return achievements

    except ValueError as e:
        logger.error(f"Validation error getting game achievements: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting game achievements for user '{username}': {e}")
        raise DatabaseError(f"Error getting game achievements for user '{username}': {str(e)}")
