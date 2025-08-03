"""
XplorED - User Insights Module

This module provides user insights and recommendations functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

User Insights Components:
- Learning Insights: Generate personalized learning insights
- Strength Analysis: Identify user learning strengths
- Weakness Analysis: Identify areas for improvement
- Recommendations: Generate personalized learning recommendations
- Motivational Messages: Create motivational content based on progress

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from datetime import datetime

from infrastructure.imports import Imports
from .user_analytics import UserAnalyticsManager, UserAnalyticsData
from shared.exceptions import DatabaseError
from shared.types import AnalyticsData

logger = logging.getLogger(__name__)


def generate_learning_insights(user_id: str) -> AnalyticsData:
    """
    Generate personalized learning insights based on user analytics.

    Args:
        user_id: The user ID to generate insights for

    Returns:
        Dictionary containing personalized insights and recommendations

    Raises:
        ValueError: If user_id is invalid
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")

        logger.info(f"Generating learning insights for user: {user_id}")

        # Create analytics manager
        analytics_manager = UserAnalyticsManager(user_id)

        # Calculate learning progress
        analytics = analytics_manager.calculate_learning_progress()

        # Generate insights
        insights = {
            'strength': _identify_strengths(analytics),
            'weakness': _identify_weaknesses(analytics),
            'recommendation': _generate_recommendations(analytics),
            'motivation': _generate_motivational_message(analytics)
        }

        logger.info(f"Successfully generated insights for user {user_id}")
        return insights

    except ValueError as e:
        logger.error(f"Validation error generating insights: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating insights for user {user_id}: {e}")
        raise DatabaseError(f"Error generating insights for user {user_id}: {str(e)}")


def _identify_strengths(analytics: UserAnalyticsData) -> str:
    """
    Identify user's learning strengths.

    Args:
        analytics: User analytics data

    Returns:
        String describing the user's strengths
    """
    try:
        if analytics.learning_streak_days >= 7:
            return f"Excellent consistency! {analytics.learning_streak_days} day streak"
        elif analytics.average_score >= 80:
            return f"Strong performance with {analytics.average_score:.1f}% average score"
        elif analytics.vocabulary_mastered >= 100:
            return f"Impressive vocabulary mastery: {analytics.vocabulary_mastered} words"
        elif analytics.total_exercises_completed >= 50:
            return f"Dedicated practice with {analytics.total_exercises_completed} exercises completed"
        else:
            return "Dedicated learning approach"

    except Exception as e:
        logger.error(f"Error identifying strengths: {e}")
        raise DatabaseError(f"Error identifying strengths: {str(e)}")


def _identify_weaknesses(analytics: UserAnalyticsData) -> str:
    """
    Identify areas for improvement.

    Args:
        analytics: User analytics data

    Returns:
        String describing areas for improvement
    """
    try:
        if analytics.average_score < 60:
            return "Focus on accuracy - consider reviewing previous lessons"
        elif analytics.learning_streak_days < 3:
            return "Build consistency with daily practice"
        elif analytics.vocabulary_mastered < 50:
            return "Expand vocabulary through reading and exercises"
        elif analytics.total_exercises_completed < 20:
            return "Increase practice frequency to improve skills"
        else:
            return "Continue building on current progress"

    except Exception as e:
        logger.error(f"Error identifying weaknesses: {e}")
        raise DatabaseError(f"Error identifying weaknesses: {str(e)}")


def _generate_recommendations(analytics: UserAnalyticsData) -> str:
    """
    Generate personalized learning recommendations.

    Args:
        analytics: User analytics data

    Returns:
        String containing personalized recommendations
    """
    try:
        recommendations = []

        if analytics.average_score < 70:
            recommendations.append("Review previous exercises to improve accuracy")

        if analytics.learning_streak_days < 5:
            recommendations.append("Try to practice daily to build consistency")

        if analytics.vocabulary_mastered < 100:
            recommendations.append("Focus on vocabulary building exercises")

        if analytics.total_exercises_completed < 30:
            recommendations.append("Complete more exercises to strengthen skills")

        if not recommendations:
            recommendations.append("Continue with current learning path")

        return "; ".join(recommendations)

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise DatabaseError(f"Error generating recommendations: {str(e)}")


def _generate_motivational_message(analytics: UserAnalyticsData) -> str:
    """
    Generate motivational message based on progress.

    Args:
        analytics: User analytics data

    Returns:
        String containing motivational message
    """
    try:
        if analytics.learning_streak_days >= 10:
            return f"Amazing dedication! {analytics.learning_streak_days} days strong!"
        elif analytics.total_exercises_completed >= 100:
            return f"Fantastic progress! {analytics.total_exercises_completed} exercises completed!"
        elif analytics.average_score >= 80:
            return "Outstanding performance! Keep up the excellent work!"
        elif analytics.vocabulary_mastered >= 50:
            return f"Great vocabulary progress! {analytics.vocabulary_mastered} words mastered!"
        else:
            return "Every step forward is progress. You're doing great!"

    except Exception as e:
        logger.error(f"Error generating motivational message: {e}")
        raise DatabaseError(f"Error generating motivational message: {str(e)}")


def create_comprehensive_user_report(user_id: str) -> AnalyticsData:
    """
    Create a comprehensive user report with analytics and insights.

    Args:
        user_id: The user ID to create report for

    Returns:
        Dictionary containing comprehensive user report

    Raises:
        ValueError: If user_id is invalid
    """
    try:
        if not user_id:
            raise ValueError("User ID is required")

        logger.info(f"Creating comprehensive report for user: {user_id}")

        # Create analytics manager
        analytics_manager = UserAnalyticsManager(user_id)

        # Calculate learning progress
        analytics_data = analytics_manager.calculate_learning_progress()

        # Generate insights
        insights = generate_learning_insights(user_id)

        # Create comprehensive report
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

        logger.info(f"Successfully created comprehensive report for user {user_id}")
        return report

    except ValueError as e:
        logger.error(f"Validation error creating comprehensive report: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating comprehensive report for user {user_id}: {e}")
        raise DatabaseError(f"Error creating comprehensive report for user {user_id}: {str(e)}")


# Constants for analytics thresholds
MIN_ACTIVITY_DAYS = 3
TARGET_AVERAGE_SCORE = 80
MIN_VOCABULARY_MASTERED = 50
EXCELLENT_STREAK_DAYS = 7
