"""
User Analytics Module

This module provides comprehensive analytics functionality for user behavior tracking,
performance metrics, and learning progress analysis in the German learning platform.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from core.services.import_service import *
from core.database.connection import select_rows, select_one, insert_row
from features.ai.memory.vocabulary_memory import get_user_vocab_stats


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

            # Fetch user exercise data
            exercise_data = self._get_exercise_statistics()

            # Calculate vocabulary mastery
            vocab_stats = get_user_vocab_stats(self.user_id)

            # Get learning streak
            streak_days = self._calculate_learning_streak()

            # Fetch user profile
            user_profile = self._get_user_profile()

            analytics_data = UserAnalyticsData(
                user_id=self.user_id,
                total_exercises_completed=exercise_data['total_exercises'],
                average_score=exercise_data['average_score'],
                vocabulary_mastered=vocab_stats.get('mastered_count', 0),
                learning_streak_days=streak_days,
                last_activity_date=exercise_data['last_activity'],
                skill_level=user_profile.get('skill_level', 0)
            )

            self.logger.info(f"Successfully calculated analytics for user {self.user_id}")
            return analytics_data

        except ValueError as e:
            self.logger.error(f"Validation error for user {self.user_id}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate learning progress for user {self.user_id}: {e}")
            raise

    def _get_exercise_statistics(self) -> Dict[str, any]:
        """
        Retrieve exercise statistics from the database.

        Returns:
            Dict containing exercise statistics
        """
        try:
            # Get total exercises completed
            exercises_result = select_rows(
                "results",
                columns=["COUNT(*) as total", "AVG(correct) as avg_score", "MAX(timestamp) as last_activity"],
                where="username = ?",
                params=(self.user_id,)
            )

            if not exercises_result:
                return {
                    'total_exercises': 0,
                    'average_score': 0.0,
                    'last_activity': datetime.now()
                }

            result = exercises_result[0]
            return {
                'total_exercises': result.get('total', 0),
                'average_score': float(result.get('avg_score', 0.0)),
                'last_activity': datetime.fromisoformat(result.get('last_activity', datetime.now().isoformat()))
            }

        except Exception as e:
            self.logger.error(f"Database error fetching exercise statistics: {e}")
            return {
                'total_exercises': 0,
                'average_score': 0.0,
                'last_activity': datetime.now()
            }

    def _calculate_learning_streak(self) -> int:
        """
        Calculate the user's current learning streak in days.

        Returns:
            Number of consecutive days the user has been active
        """
        try:
            # Get user activity dates
            activity_dates = select_rows(
                "results",
                columns=["DISTINCT DATE(timestamp) as activity_date"],
                where="username = ?",
                params=(self.user_id,),
                order_by="activity_date DESC"
            )

            if not activity_dates:
                return 0

            # Convert to datetime objects
            dates = [datetime.fromisoformat(row['activity_date']) for row in activity_dates]
            dates.sort(reverse=True)

            # Calculate streak
            streak = 0
            current_date = datetime.now().date()

            for date in dates:
                date_obj = date.date()
                if current_date - date_obj == timedelta(days=streak):
                    streak += 1
                else:
                    break

            return streak

        except Exception as e:
            self.logger.error(f"Error calculating learning streak: {e}")
            return 0

    def _get_user_profile(self) -> Dict[str, any]:
        """
        Retrieve user profile information.

        Returns:
            Dict containing user profile data
        """
        try:
            profile = select_one(
                "users",
                columns=["skill_level", "created_at"],
                where="username = ?",
                params=(self.user_id,)
            )

            return profile or {}

        except Exception as e:
            self.logger.error(f"Error fetching user profile: {e}")
            return {}

    def generate_learning_insights(self) -> Dict[str, str]:
        """
        Generate personalized learning insights based on analytics.

        Returns:
            Dict containing personalized insights and recommendations
        """
        try:
            analytics = self.calculate_learning_progress()

            insights = {
                'strength': self._identify_strengths(analytics),
                'weakness': self._identify_weaknesses(analytics),
                'recommendation': self._generate_recommendations(analytics),
                'motivation': self._generate_motivational_message(analytics)
            }

            return insights

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return {
                'strength': 'Consistent learning effort',
                'weakness': 'Need more practice',
                'recommendation': 'Continue with daily exercises',
                'motivation': 'Keep up the great work!'
            }

    def _identify_strengths(self, analytics: UserAnalyticsData) -> str:
        """Identify user's learning strengths."""
        if analytics.learning_streak_days >= 7:
            return f"Excellent consistency! {analytics.learning_streak_days} day streak"
        elif analytics.average_score >= 0.8:
            return f"Strong performance with {analytics.average_score:.1%} average score"
        elif analytics.vocabulary_mastered >= 100:
            return f"Impressive vocabulary mastery: {analytics.vocabulary_mastered} words"
        else:
            return "Dedicated learning approach"

    def _identify_weaknesses(self, analytics: UserAnalyticsData) -> str:
        """Identify areas for improvement."""
        if analytics.average_score < 0.6:
            return "Focus on accuracy - consider reviewing previous lessons"
        elif analytics.learning_streak_days < 3:
            return "Build consistency with daily practice"
        elif analytics.vocabulary_mastered < 50:
            return "Expand vocabulary through reading and exercises"
        else:
            return "Continue building on current progress"

    def _generate_recommendations(self, analytics: UserAnalyticsData) -> str:
        """Generate personalized learning recommendations."""
        recommendations = []

        if analytics.average_score < 0.7:
            recommendations.append("Review previous exercises to improve accuracy")

        if analytics.learning_streak_days < 5:
            recommendations.append("Try to practice daily to build consistency")

        if analytics.vocabulary_mastered < 100:
            recommendations.append("Focus on vocabulary building exercises")

        if not recommendations:
            recommendations.append("Continue with current learning path")

        return "; ".join(recommendations)

    def _generate_motivational_message(self, analytics: UserAnalyticsData) -> str:
        """Generate motivational message based on progress."""
        if analytics.learning_streak_days >= 10:
            return f"Amazing dedication! {analytics.learning_streak_days} days strong!"
        elif analytics.total_exercises_completed >= 100:
            return f"Fantastic progress! {analytics.total_exercises_completed} exercises completed!"
        elif analytics.average_score >= 0.8:
            return "Outstanding performance! Keep up the excellent work!"
        else:
            return "Every step forward is progress. You're doing great!"


def create_user_analytics_report(user_id: str) -> Dict[str, any]:
    """
    Create a comprehensive analytics report for a user.

    This function provides a high-level interface for generating
    complete user analytics reports.

    Args:
        user_id: The user identifier

    Returns:
        Dict containing complete analytics report

    Raises:
        ValueError: If user_id is invalid
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")

        analytics_manager = UserAnalyticsManager(user_id)
        analytics_data = analytics_manager.calculate_learning_progress()
        insights = analytics_manager.generate_learning_insights()

        report = {
            'user_id': user_id,
            'generated_at': datetime.now().isoformat(),
            'analytics': {
                'total_exercises': analytics_data.total_exercises_completed,
                'average_score': analytics_data.average_score,
                'vocabulary_mastered': analytics_data.vocabulary_mastered,
                'learning_streak': analytics_data.learning_streak_days,
                'skill_level': analytics_data.skill_level,
                'last_activity': analytics_data.last_activity_date.isoformat()
            },
            'insights': insights,
            'recommendations': insights['recommendation']
        }

        logger.info(f"Generated analytics report for user: {user_id}")
        return report

    except ValueError as e:
        logger.error(f"Invalid input for analytics report: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate analytics report: {e}")
        raise


# Constants for analytics thresholds
MIN_ACTIVITY_DAYS = 3
TARGET_AVERAGE_SCORE = 0.8
MIN_VOCABULARY_MASTERED = 50
EXCELLENT_STREAK_DAYS = 7
