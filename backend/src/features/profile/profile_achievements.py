"""
XplorED - Profile Achievements Module

This module provides user achievements and activity timeline functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Profile Achievements Components:
- User Achievements: Get and track user achievements
- Activity Timeline: Generate user activity timeline
- Achievement Validation: Validate achievement criteria
- Progress Tracking: Track progress towards achievements

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import List, Optional

from infrastructure.imports import Imports
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from shared.exceptions import DatabaseError
from shared.types import AnalyticsData, AnalyticsList

logger = logging.getLogger(__name__)


def get_user_achievements(
    username: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> AnalyticsData:
    """
    Get achievements for a user with filtering and pagination.

    Args:
        username: The username to get achievements for
        category: Filter by achievement category
        status: Filter by status (earned, in_progress)
        limit: Maximum number of achievements to return
        offset: Number of achievements to skip for pagination

    Returns:
        Dictionary containing achievements data with metadata

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting achievements for user {username}")

        achievements = []

        # First Game Achievement
        first_game_timestamp = _get_first_game_timestamp(username)
        if first_game_timestamp:
            achievements.append({
                "id": "first_game",
                "title": "First Steps",
                "description": "Played your first game",
                "icon": "🎮",
                "unlocked_at": first_game_timestamp,
                "category": "gaming"
            })

        # 10th Game Achievement
        tenth_game_timestamp = _get_nth_game_timestamp(username, 10)
        if tenth_game_timestamp:
            achievements.append({
                "id": "tenth_game",
                "title": "Getting the Hang of It",
                "description": "Played 10 games",
                "icon": "🎯",
                "unlocked_at": tenth_game_timestamp,
                "category": "gaming"
            })

        # Perfect Score Achievement
        perfect_score_timestamp = _get_perfect_score_timestamp(username)
        if perfect_score_timestamp:
            achievements.append({
                "id": "perfect_score",
                "title": "Perfect Score",
                "description": "Achieved a perfect score in a game",
                "icon": "⭐",
                "unlocked_at": perfect_score_timestamp,
                "category": "performance"
            })

        # Vocabulary Achievements
        vocab_10_timestamp = _get_vocab_achievement_timestamp(username, 10)
        if vocab_10_timestamp:
            achievements.append({
                "id": "vocab_10",
                "title": "Word Collector",
                "description": "Learned 10 vocabulary words",
                "icon": "📚",
                "unlocked_at": vocab_10_timestamp,
                "category": "vocabulary"
            })

        vocab_50_timestamp = _get_vocab_achievement_timestamp(username, 50)
        if vocab_50_timestamp:
            achievements.append({
                "id": "vocab_50",
                "title": "Vocabulary Master",
                "description": "Learned 50 vocabulary words",
                "icon": "📖",
                "unlocked_at": vocab_50_timestamp,
                "category": "vocabulary"
            })

        # First Lesson Achievement
        first_lesson_timestamp = _get_first_lesson_timestamp(username)
        if first_lesson_timestamp:
            achievements.append({
                "id": "first_lesson",
                "title": "Student",
                "description": "Completed your first lesson",
                "icon": "📝",
                "unlocked_at": first_lesson_timestamp,
                "category": "learning"
            })

        # 5th Lesson Achievement
        fifth_lesson_timestamp = _get_nth_lesson_timestamp(username, 5)
        if fifth_lesson_timestamp:
            achievements.append({
                "id": "fifth_lesson",
                "title": "Dedicated Learner",
                "description": "Completed 5 lessons",
                "icon": "🎓",
                "unlocked_at": fifth_lesson_timestamp,
                "category": "learning"
            })

        # Learning Streak Achievements
        streak_7_timestamp = _get_streak_achievement_timestamp(username, 7)
        if streak_7_timestamp:
            achievements.append({
                "id": "streak_7",
                "title": "Week Warrior",
                "description": "Maintained a 7-day learning streak",
                "icon": "🔥",
                "unlocked_at": streak_7_timestamp,
                "category": "consistency"
            })

        streak_30_timestamp = _get_streak_achievement_timestamp(username, 30)
        if streak_30_timestamp:
            achievements.append({
                "id": "streak_30",
                "title": "Consistency King",
                "description": "Maintained a 30-day learning streak",
                "icon": "👑",
                "unlocked_at": streak_30_timestamp,
                "category": "consistency"
            })

        # Apply category filter if provided
        if category:
            achievements = [a for a in achievements if a.get("category") == category]

        # Apply status filter if provided
        if status:
            if status == "earned":
                achievements = [a for a in achievements if a.get("unlocked_at")]
            elif status == "in_progress":
                # For now, all achievements are considered earned if they exist
                # This could be enhanced to check progress towards achievements
                achievements = []

        # Calculate total before pagination
        total = len(achievements)

        # Sort achievements by unlock date (newest first)
        achievements.sort(key=lambda x: x.get("unlocked_at", ""), reverse=True)

        # Apply pagination
        paginated_achievements = achievements[offset:offset + limit]

        # Calculate summary statistics
        earned_count = len([a for a in achievements if a.get("unlocked_at")])
        in_progress_count = total - earned_count

        # Get recent achievements (last 5)
        recent_achievements = achievements[:5]

        # Get next achievements (achievements not yet earned)
        next_achievements = [a for a in achievements if not a.get("unlocked_at")][:5]

        result = {
            "achievements": paginated_achievements,
            "summary": {
                "total_achievements": total,
                "earned_count": earned_count,
                "in_progress_count": in_progress_count,
                "total_points": sum(a.get("points", 0) for a in achievements),
                "completion_percentage": (earned_count / total * 100) if total > 0 else 0.0
            },
            "recent_achievements": recent_achievements,
            "next_achievements": next_achievements,
            "total": total,
            "limit": limit,
            "offset": offset
        }

        logger.info(f"Retrieved {len(paginated_achievements)} achievements for user {username}")
        return result

    except ValueError as e:
        logger.error(f"Validation error getting user achievements: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting achievements for {username}: {e}")
        raise DatabaseError(f"Error getting achievements for {username}: {str(e)}")


def get_user_activity_timeline(username: str, limit: int = 20) -> AnalyticsList:
    """
    Get user activity timeline.

    Args:
        username: The username to get timeline for
        limit: Maximum number of activities to return

    Returns:
        List of activities in chronological order

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if limit <= 0:
            limit = 20

        logger.info(f"Getting activity timeline for user {username}, limit: {limit}")

        timeline = []

        # Get game activities
        game_activities = select_rows(
            "results",
            columns=["level", "correct", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
            limit=limit // 2,  # Half from games
        )

        for activity in game_activities:
            timeline.append({
                "type": "game",
                "title": f"Played Level {activity['level']}",
                "description": f"{'Correct' if activity['correct'] else 'Incorrect'} answer",
                "timestamp": activity["timestamp"],
                "icon": "🎮",
                "level": activity["level"],
                "correct": bool(activity["correct"]),
            })

        # Get lesson activities
        lesson_activities = select_rows(
            "lesson_progress",
            columns=["lesson_id", "completed_blocks", "total_blocks", "last_accessed"],
            where="user_id = ? AND last_accessed IS NOT NULL",
            params=(username,),
            order_by="last_accessed DESC",
            limit=limit // 2,  # Half from lessons
        )

        for activity in lesson_activities:
            completion_percentage = (activity["completed_blocks"] / activity["total_blocks"] * 100) if activity["total_blocks"] > 0 else 0
            timeline.append({
                "type": "lesson",
                "title": f"Lesson {activity['lesson_id']} Progress",
                "description": f"{completion_percentage:.1f}% complete",
                "timestamp": activity["last_accessed"],
                "icon": "📝",
                "lesson_id": activity["lesson_id"],
                "completion_percentage": round(completion_percentage, 1),
            })

        # Get vocabulary activities
        vocab_activities = select_rows(
            "vocab_log",
            columns=["vocab", "created_at"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=limit // 4,  # Quarter from vocabulary
        )

        for activity in vocab_activities:
            timeline.append({
                "type": "vocabulary",
                "title": f"Learned '{activity['vocab']}'",
                "description": "Added new vocabulary word",
                "timestamp": activity["created_at"],
                "icon": "📚",
                "word": activity["vocab"],
            })

        # Sort all activities by timestamp (newest first)
        timeline.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Limit the final result
        timeline = timeline[:limit]

        logger.info(f"Retrieved {len(timeline)} activities for user {username}")
        return timeline

    except ValueError as e:
        logger.error(f"Validation error getting activity timeline: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting activity timeline for user {username}: {e}")
        return []


def _get_first_game_timestamp(username: str) -> Optional[str]:
    """
    Get timestamp of user's first game.

    Args:
        username: The username

    Returns:
        Timestamp string or None if no games played
    """
    try:
        result = select_one(
            "results",
            columns="MIN(timestamp) as first_timestamp",
            where="username = ?",
            params=(username,),
        )
        return result.get("first_timestamp") if result else None

    except Exception as e:
        logger.error(f"Error getting first game timestamp for user {username}: {e}")
        return None


def _get_nth_game_timestamp(username: str, n: int) -> Optional[str]:
    """
    Get timestamp of user's nth game.

    Args:
        username: The username
        n: The game number

    Returns:
        Timestamp string or None if nth game not reached
    """
    try:
        result = select_one(
            "results",
            columns="timestamp",
            where="username = ?",
            params=(username,),
            order_by="timestamp ASC",
            limit=1,
            offset=n-1,
        )
        return result.get("timestamp") if result else None

    except Exception as e:
        logger.error(f"Error getting {n}th game timestamp for user {username}: {e}")
        return None


def _get_perfect_score_timestamp(username: str) -> Optional[str]:
    """
    Get timestamp of user's first perfect score.

    Args:
        username: The username

    Returns:
        Timestamp string or None if no perfect score
    """
    try:
        result = select_one(
            "results",
            columns="timestamp",
            where="username = ? AND correct = 1",
            params=(username,),
            order_by="timestamp ASC",
        )
        return result.get("timestamp") if result else None

    except Exception as e:
        logger.error(f"Error getting perfect score timestamp for user {username}: {e}")
        return None


def _get_vocab_achievement_timestamp(username: str, count: int) -> Optional[str]:
    """
    Get timestamp when user reached vocabulary count milestone.

    Args:
        username: The username
        count: The vocabulary count milestone

    Returns:
        Timestamp string or None if milestone not reached
    """
    try:
        result = select_one(
            "vocab_log",
            columns="created_at",
            where="username = ?",
            params=(username,),
            order_by="created_at ASC",
            limit=1,
            offset=count-1,
        )
        return result.get("created_at") if result else None

    except Exception as e:
        logger.error(f"Error getting vocabulary {count} timestamp for user {username}: {e}")
        return None


def _get_first_lesson_timestamp(username: str) -> Optional[str]:
    """
    Get timestamp of user's first lesson completion.

    Args:
        username: The username

    Returns:
        Timestamp string or None if no lessons completed
    """
    try:
        result = select_one(
            "lesson_progress",
            columns="last_accessed",
            where="user_id = ? AND completed_blocks >= total_blocks",
            params=(username,),
            order_by="last_accessed ASC",
        )
        return result.get("last_accessed") if result else None

    except Exception as e:
        logger.error(f"Error getting first lesson timestamp for user {username}: {e}")
        return None


def _get_nth_lesson_timestamp(username: str, n: int) -> Optional[str]:
    """
    Get timestamp of user's nth lesson completion.

    Args:
        username: The username
        n: The lesson number

    Returns:
        Timestamp string or None if nth lesson not completed
    """
    try:
        result = select_one(
            "lesson_progress",
            columns="last_accessed",
            where="user_id = ? AND completed_blocks >= total_blocks",
            params=(username,),
            order_by="last_accessed ASC",
            limit=1,
            offset=n-1,
        )
        return result.get("last_accessed") if result else None

    except Exception as e:
        logger.error(f"Error getting {n}th lesson timestamp for user {username}: {e}")
        return None


def _get_streak_achievement_timestamp(username: str, days: int) -> Optional[str]:
    """
    Get timestamp when user reached streak milestone.

    Args:
        username: The username
        days: The streak milestone in days

    Returns:
        Timestamp string or None if milestone not reached
    """
    try:
        # This is a simplified implementation
        # In a real system, you'd track streak milestones more precisely
        recent_activity = select_rows(
            "results",
            columns="DISTINCT DATE(timestamp) as activity_date",
            where="username = ? AND timestamp >= date('now', '-60 days')",
            params=(username,),
            order_by="activity_date DESC",
        )

        if not recent_activity or len(recent_activity) < days:
            return None

        # Check if there's a streak of the required length
        streak_count = 0
        current_date = None

        for row in recent_activity:
            activity_date = row.get("activity_date")
            if current_date is None:
                current_date = activity_date
                streak_count = 1
            else:
                from datetime import datetime
                try:
                    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
                    activity_dt = datetime.strptime(activity_date, "%Y-%m-%d")
                    if (current_dt - activity_dt).days == 1:
                        streak_count += 1
                        current_date = activity_date
                        if streak_count >= days:
                            return activity_date
                    else:
                        break
                except:
                    break

        return None

    except Exception as e:
        logger.error(f"Error getting streak {days} timestamp for user {username}: {e}")
        return None
