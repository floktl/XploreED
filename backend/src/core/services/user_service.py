"""
XplorED - User Service

This module provides core user business logic services,
following clean architecture principles as outlined in the documentation.

User Service Components:
- User level management
- Skill level calculation
- User statistics
- User validation

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Optional
from core.database.connection import select_one, fetch_one, select_rows
from core.authentication import user_exists
from shared.exceptions import ValidationError
from shared.types import AnalyticsData

logger = logging.getLogger(__name__)


class UserService:
    """Core user business logic service."""

    @staticmethod
    def get_user_level(username: str) -> int:
        """
        Get the current level for a user.

        Args:
            username: The username to get level for

        Returns:
            int: User's current level

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            # Get user's skill level from database
            row = fetch_one("users", "WHERE username = ?", (username,))
            level = row.get("skill_level", 1) if row else 1

            logger.info(f"Retrieved level {level} for user {username}")
            return int(level)

        except ValidationError as e:
            logger.error(f"Validation error getting user level: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user level for {username}: {e}")
            return 1

    @staticmethod
    def calculate_skill_level(game_stats: AnalyticsData, vocabulary_count: int, lessons_completed: int) -> int:
        """
        Calculate user's skill level based on performance metrics.

        Args:
            game_stats: User's game performance statistics
            vocabulary_count: Number of vocabulary words learned
            lessons_completed: Number of lessons completed

        Returns:
            int: Calculated skill level (1-10)
        """
        try:
            # Base level from database
            base_level = game_stats.get("skill_level", 1)

            # Performance-based adjustments
            total_games = game_stats.get("total_games", 0)
            average_score = game_stats.get("average_score", 0.0)
            completion_rate = game_stats.get("completion_rate", 0.0)

            # Calculate performance bonus
            performance_bonus = 0

            if total_games >= 50:
                performance_bonus += 1
            if average_score >= 80.0:
                performance_bonus += 1
            if completion_rate >= 0.8:
                performance_bonus += 1
            if vocabulary_count >= 100:
                performance_bonus += 1
            if lessons_completed >= 10:
                performance_bonus += 1

            # Calculate final level (capped at 10)
            final_level = min(base_level + performance_bonus, 10)

            logger.debug(f"Calculated skill level {final_level} for user (base: {base_level}, bonus: {performance_bonus})")
            return final_level

        except Exception as e:
            logger.error(f"Error calculating skill level: {e}")
            return 1

    @staticmethod
    def get_user_statistics(username: str) -> AnalyticsData:
        """
        Get comprehensive user statistics.

        Args:
            username: The username to get statistics for

        Returns:
            AnalyticsData: User statistics

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            # Get user basic info
            user_info = fetch_one("users", "WHERE username = ?", (username,))
            if not user_info:
                return {
                    "username": username,
                    "exists": False,
                    "created_at": None,
                    "skill_level": 1,
                    "total_games": 0,
                    "total_vocabulary": 0,
                    "lessons_completed": 0,
                    "learning_streak": 0,
                    "average_score": 0.0,
                    "best_score": 0,
                    "total_play_time": 0,
                }

            # Get game statistics
            game_stats = UserService._get_game_statistics(username)

            # Get vocabulary count
            vocab_count = UserService._get_vocabulary_count(username)

            # Get lessons completed
            lessons_completed = UserService._get_lessons_completed(username)

            # Calculate skill level
            skill_level = UserService.calculate_skill_level(game_stats, vocab_count, lessons_completed)

            # Calculate learning streak
            learning_streak = UserService._calculate_learning_streak(username)

            statistics = {
                "username": username,
                "exists": True,
                "created_at": user_info.get("created_at"),
                "skill_level": skill_level,
                "total_games": game_stats.get("total_games", 0),
                "total_vocabulary": vocab_count,
                "lessons_completed": lessons_completed,
                "learning_streak": learning_streak,
                "average_score": game_stats.get("average_score", 0.0),
                "best_score": game_stats.get("best_score", 0),
                "total_play_time": game_stats.get("total_play_time", 0),
                "last_activity": game_stats.get("last_activity"),
                "completion_rate": game_stats.get("completion_rate", 0.0),
            }

            logger.info(f"Retrieved statistics for user {username}: level {skill_level}")
            return statistics

        except ValidationError as e:
            logger.error(f"Validation error getting user statistics: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user statistics for {username}: {e}")
            return {
                "username": username,
                "exists": False,
                "error": str(e)
            }

    @staticmethod
    def _get_game_statistics(username: str) -> AnalyticsData:
        """Get user's game performance statistics."""
        try:
            # Get game results
            results = select_rows(
                "results",
                where="username = ?",
                params=(username,)
            )

            if not results:
                return {
                    "total_games": 0,
                    "average_score": 0.0,
                    "best_score": 0,
                    "total_play_time": 0,
                    "completion_rate": 0.0,
                    "last_activity": None
                }

            total_games = len(results)
            total_correct = sum(1 for r in results if r.get("correct", 0) == 1)
            average_score = (total_correct / total_games * 100) if total_games > 0 else 0.0
            best_score = max((r.get("correct", 0) for r in results), default=0)

            return {
                "total_games": total_games,
                "average_score": round(average_score, 2),
                "best_score": best_score,
                "total_play_time": 0,  # TODO: Implement play time tracking
                "completion_rate": round(total_correct / total_games, 2) if total_games > 0 else 0.0,
                "last_activity": results[-1].get("timestamp") if results else None
            }

        except Exception as e:
            logger.error(f"Error getting game statistics for {username}: {e}")
            return {
                "total_games": 0,
                "average_score": 0.0,
                "best_score": 0,
                "total_play_time": 0,
                "completion_rate": 0.0,
                "last_activity": None
            }

    @staticmethod
    def _get_vocabulary_count(username: str) -> int:
        """Get user's vocabulary word count."""
        try:
            results = select_rows(
                "vocab_log",
                where="username = ?",
                params=(username,)
            )
            return len(results)
        except Exception as e:
            logger.error(f"Error getting vocabulary count for {username}: {e}")
            return 0

    @staticmethod
    def _get_lessons_completed(username: str) -> int:
        """Get user's completed lessons count."""
        try:
            # TODO: Implement lesson completion tracking
            return 0
        except Exception as e:
            logger.error(f"Error getting lessons completed for {username}: {e}")
            return 0

    @staticmethod
    def _calculate_learning_streak(username: str) -> int:
        """Calculate user's learning streak."""
        try:
            # TODO: Implement learning streak calculation
            return 0
        except Exception as e:
            logger.error(f"Error calculating learning streak for {username}: {e}")
            return 0
