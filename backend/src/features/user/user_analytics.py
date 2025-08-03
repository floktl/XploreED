"""
XplorED - User Analytics Module

This module provides core user analytics and data collection functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

User Analytics Components:
- Analytics Data Collection: Collect and calculate user analytics data
- Progress Tracking: Track user learning progress and performance
- Statistics Calculation: Calculate comprehensive user statistics
- Data Management: Manage user analytics data and metrics

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from infrastructure.imports import Imports
from core.database.connection import select_rows, select_one, insert_row
from features.ai.memory.vocabulary_memory import get_user_vocab_stats
from core.services import UserService
from shared.exceptions import DatabaseError
from shared.types import AnalyticsData

logger = logging.getLogger(__name__)


@dataclass
class UserAnalyticsData:
    """Data class for storing user analytics information."""

    user_id: str
    total_exercises_completed: int
    average_score: float
    vocabulary_mastered: int
    learning_streak_days: int
    last_activity_date: datetime
    skill_level: int


class UserAnalyticsManager:
    """
    Manages user analytics and learning progress tracking.

    This class provides methods for analyzing user behavior, calculating
    performance metrics, and generating insights for personalized learning.
    """

    def __init__(self, user_id: str):
        """
        Initialize the analytics manager for a specific user.

        Args:
            user_id: The unique identifier for the user
        """
        self.user_id = user_id
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def calculate_learning_progress(self) -> UserAnalyticsData:
        """
        Calculate comprehensive learning progress for the user.

        Returns:
            UserAnalyticsData: Complete analytics data for the user

        Raises:
            ValueError: If user_id is invalid
            DatabaseError: If database operations fail
        """
        try:
            if not self.user_id or not isinstance(self.user_id, str):
                raise ValueError("Invalid user_id provided")

            self.logger.info(f"Calculating learning progress for user: {self.user_id}")

            # Get comprehensive user statistics using core service
            user_stats = UserService.get_user_statistics(self.user_id)

            # Get vocabulary mastery
            vocab_stats = get_user_vocab_stats(self.user_id)

            last_activity = user_stats.get('last_activity')
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            elif last_activity is None:
                last_activity = datetime.utcnow()

            analytics_data = UserAnalyticsData(
                user_id=self.user_id,
                total_exercises_completed=user_stats.get('total_games', 0),
                average_score=user_stats.get('average_score', 0.0),
                vocabulary_mastered=vocab_stats.get('mastered_count', 0),
                learning_streak_days=user_stats.get('learning_streak', 0),
                last_activity_date=last_activity,
                skill_level=user_stats.get('skill_level', 0)
            )

            self.logger.info(f"Successfully calculated analytics for user {self.user_id}")
            return analytics_data

        except ValueError as e:
            self.logger.error(f"Validation error for user {self.user_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error calculating learning progress for user {self.user_id}: {e}")
            raise

    def _get_exercise_statistics(self) -> AnalyticsData:
        """
        Get exercise statistics for the user.

        Returns:
            Dictionary containing exercise statistics
        """
        try:
            # Get total exercises completed
            total_exercises_result = select_one(
                "results",
                columns="COUNT(*) as count",
                where="username = ?",
                params=(self.user_id,)
            )
            total_exercises = total_exercises_result.get("count", 0) if total_exercises_result else 0

            # Get correct answers
            correct_answers_result = select_one(
                "results",
                columns="COUNT(*) as count",
                where="username = ? AND correct = 1",
                params=(self.user_id,)
            )
            correct_answers = correct_answers_result.get("count", 0) if correct_answers_result else 0

            # Calculate average score
            average_score = (correct_answers / total_exercises * 100) if total_exercises > 0 else 0.0

            # Get last activity
            last_activity_result = select_one(
                "results",
                columns="MAX(timestamp) as last_timestamp",
                where="username = ?",
                params=(self.user_id,)
            )
            last_activity_str = last_activity_result.get("last_timestamp") if last_activity_result else None
            last_activity = datetime.fromisoformat(last_activity_str) if last_activity_str else datetime.now()

            return {
                "total_exercises": total_exercises,
                "correct_answers": correct_answers,
                "average_score": round(average_score, 2),
                "last_activity": last_activity
            }

        except Exception as e:
            self.logger.error(f"Error getting exercise statistics for user {self.user_id}: {e}")
            return {
                "total_exercises": 0,
                "correct_answers": 0,
                "average_score": 0.0,
                "last_activity": datetime.now()
            }

    def _calculate_learning_streak(self) -> int:
        """
        Calculate the user's current learning streak.

        Returns:
            Number of consecutive days with activity
        """
        try:
            # Get recent activity (last 30 days)
            recent_activity = select_rows(
                "results",
                columns="DISTINCT DATE(timestamp) as activity_date",
                where="username = ? AND timestamp >= date('now', '-30 days')",
                params=(self.user_id,),
                order_by="activity_date DESC"
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
                    try:
                        if current_date and activity_date:
                            current_dt = datetime.strptime(current_date, "%Y-%m-%d")
                            activity_dt = datetime.strptime(activity_date, "%Y-%m-%d")
                            if (current_dt - activity_dt).days == 1:
                                streak += 1
                                current_date = activity_date
                            else:
                                break
                        else:
                            break
                    except:
                        break

            return streak

        except Exception as e:
            self.logger.error(f"Error calculating learning streak for user {self.user_id}: {e}")
            return 0

    def _get_user_profile(self) -> AnalyticsData:
        """
        Get user profile information.

        Returns:
            Dictionary containing user profile data
        """
        try:
            user_profile = select_one(
                "users",
                columns="*",
                where="username = ?",
                params=(self.user_id,)
            )
            return user_profile or {}

        except Exception as e:
            self.logger.error(f"Error getting user profile for {self.user_id}: {e}")
            return {}


def create_user_analytics_report(user_id: str) -> AnalyticsData:
    """
    Create a comprehensive analytics report for a user.

    Args:
        user_id: The user ID to create report for

    Returns:
        Dictionary containing the analytics report

    Raises:
        ValueError: If user_id is invalid
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")

        logger.info(f"Creating analytics report for user: {user_id}")

        # Create analytics manager
        analytics_manager = UserAnalyticsManager(user_id)

        # Calculate learning progress
        analytics_data = analytics_manager.calculate_learning_progress()

        # Create report
        report = {
            "user_id": user_id,
            "report_generated_at": datetime.now().isoformat(),
            "analytics": {
                "total_exercises_completed": analytics_data.total_exercises_completed,
                "average_score": analytics_data.average_score,
                "vocabulary_mastered": analytics_data.vocabulary_mastered,
                "learning_streak_days": analytics_data.learning_streak_days,
                "last_activity_date": analytics_data.last_activity_date.isoformat(),
                "skill_level": analytics_data.skill_level
            }
        }

        logger.info(f"Successfully created analytics report for user {user_id}")
        return report

    except ValueError as e:
        logger.error(f"Validation error creating analytics report: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating analytics report for user {user_id}: {e}")
        return {
            "user_id": user_id,
            "error": str(e),
            "report_generated_at": datetime.now().isoformat()
        }
