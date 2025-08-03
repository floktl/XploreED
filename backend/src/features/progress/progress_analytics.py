"""
XplorED - Progress Analytics Module

This module provides progress analytics and trends functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Progress Analytics Components:
- Progress Summary: Get comprehensive user progress summaries
- Progress Trends: Analyze progress trends over time
- Performance Metrics: Calculate performance and improvement metrics
- Activity Analysis: Analyze user activity patterns

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import Optional, List, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query
from shared.exceptions import DatabaseError, ValidationError
from shared.types import AnalyticsData

logger = logging.getLogger(__name__)


def get_user_progress_summary(username: str, days: int = 30) -> AnalyticsData:
    """
    Get a comprehensive progress summary for a user.

    Args:
        username: The username to get summary for
        days: Number of days to look back for activity

    Returns:
        Dictionary containing progress summary

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if days <= 0:
            days = 30

        logger.info(f"Getting progress summary for user {username} (last {days} days)")

        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)

        summary = {
            "username": username,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_activities": 0,
            "lessons_completed": 0,
            "exercises_completed": 0,
            "vocabulary_reviews": 0,
            "games_played": 0,
            "total_time_spent": 0,
            "average_score": 0.0,
            "improvement_rate": 0.0,
            "streak_days": 0,
            "activity_breakdown": {},
            "recent_activity": [],
            "top_performing_areas": [],
            "areas_for_improvement": []
        }

        # Get lesson progress
        lesson_progress = select_rows(
            "lesson_progress",
            columns=["lesson_id", "block_id", "completed", "updated_at"],
            where="user_id = ? AND updated_at >= ?",
            params=(username, start_date.isoformat())
        )

        if lesson_progress:
            summary["lessons_completed"] = sum(1 for p in lesson_progress if p.get("completed", 0) == 1)
            summary["activity_breakdown"]["lessons"] = {
                "total_blocks": len(lesson_progress),
                "completed_blocks": summary["lessons_completed"],
                "completion_rate": (summary["lessons_completed"] / len(lesson_progress)) * 100 if lesson_progress else 0
            }

        # Get exercise progress
        exercise_progress = select_rows(
            "activity_progress",
            columns=["block_id", "score", "total_questions", "completion_percentage", "completed_at"],
            where="username = ? AND activity_type = 'exercise' AND completed_at >= ?",
            params=(username, start_date.isoformat())
        )

        if exercise_progress:
            summary["exercises_completed"] = len(exercise_progress)
            total_score = sum(p.get("score", 0) for p in exercise_progress)
            total_questions = sum(p.get("total_questions", 0) for p in exercise_progress)
            summary["average_score"] = (total_score / total_questions) * 100 if total_questions > 0 else 0
            summary["activity_breakdown"]["exercises"] = {
                "total_exercises": len(exercise_progress),
                "average_score": summary["average_score"],
                "total_questions": total_questions
            }

        # Get vocabulary progress
        vocab_progress = select_rows(
            "vocabulary_progress",
            columns=["word", "correct", "repetitions", "reviewed_at"],
            where="username = ? AND reviewed_at >= ?",
            params=(username, start_date.isoformat())
        )

        if vocab_progress:
            summary["vocabulary_reviews"] = len(vocab_progress)
            correct_reviews = sum(1 for p in vocab_progress if p.get("correct", 0) == 1)
            summary["activity_breakdown"]["vocabulary"] = {
                "total_reviews": len(vocab_progress),
                "correct_reviews": correct_reviews,
                "accuracy_rate": (correct_reviews / len(vocab_progress)) * 100 if vocab_progress else 0,
                "total_repetitions": sum(p.get("repetitions", 0) for p in vocab_progress)
            }

        # Get game progress
        game_progress = select_rows(
            "game_progress",
            columns=["game_type", "score", "level", "completed_at"],
            where="username = ? AND completed_at >= ?",
            params=(username, start_date.isoformat())
        )

        if game_progress:
            summary["games_played"] = len(game_progress)
            game_scores = [p.get("score", 0) for p in game_progress]
            summary["activity_breakdown"]["games"] = {
                "total_games": len(game_progress),
                "average_score": sum(game_scores) / len(game_scores) if game_scores else 0,
                "highest_level": max(p.get("level", 0) for p in game_progress) if game_progress else 0,
                "game_types": list(set(p.get("game_type", "") for p in game_progress))
            }

        # Calculate total activities
        summary["total_activities"] = (
            summary["lessons_completed"] +
            summary["exercises_completed"] +
            summary["vocabulary_reviews"] +
            summary["games_played"]
        )

        # Calculate streak days (consecutive days with activity)
        all_activities = []
        all_activities.extend(lesson_progress)
        all_activities.extend(exercise_progress)
        all_activities.extend(vocab_progress)
        all_activities.extend(game_progress)

        if all_activities:
            # Get unique dates with activity
            activity_dates = set()
            for activity in all_activities:
                date_field = activity.get("updated_at") or activity.get("completed_at") or activity.get("reviewed_at")
                if date_field:
                    try:
                        activity_date = datetime.datetime.fromisoformat(date_field.replace('Z', '+00:00')).date()
                        activity_dates.add(activity_date)
                    except:
                        continue

            # Calculate streak
            if activity_dates:
                sorted_dates = sorted(activity_dates, reverse=True)
                current_streak = 0
                current_date = datetime.date.today()

                for date in sorted_dates:
                    if (current_date - date).days == current_streak:
                        current_streak += 1
                    else:
                        break

                summary["streak_days"] = current_streak

        # Get recent activity (last 10 activities)
        recent_activities = []
        for activity in all_activities:
            date_field = activity.get("updated_at") or activity.get("completed_at") or activity.get("reviewed_at")
            if date_field:
                try:
                    activity_date = datetime.datetime.fromisoformat(date_field.replace('Z', '+00:00'))
                    recent_activities.append({
                        "type": "lesson" if "lesson_id" in activity else "exercise" if "score" in activity else "vocabulary" if "word" in activity else "game",
                        "date": activity_date.isoformat(),
                        "details": activity
                    })
                except:
                    continue

        # Sort by date and take last 10
        recent_activities.sort(key=lambda x: x["date"], reverse=True)
        summary["recent_activity"] = recent_activities[:10]

        # Calculate improvement rate (compare first and last week)
        if len(all_activities) >= 10:
            first_week_activities = [a for a in all_activities if a.get("updated_at") or a.get("completed_at") or a.get("reviewed_at")]
            last_week_activities = [a for a in all_activities if a.get("updated_at") or a.get("completed_at") or a.get("reviewed_at")]

            if len(first_week_activities) > 0 and len(last_week_activities) > 0:
                # Simple improvement calculation based on activity volume
                first_week_count = len(first_week_activities) // 4  # Approximate first week
                last_week_count = len(last_week_activities) // 4   # Approximate last week

                if first_week_count > 0:
                    improvement = ((last_week_count - first_week_count) / first_week_count) * 100
                    summary["improvement_rate"] = round(improvement, 2)

        logger.info(f"Generated progress summary for user {username}: {summary['total_activities']} activities, {summary['streak_days']} day streak")
        return summary

    except ValueError as e:
        logger.error(f"Validation error getting user progress summary: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting user progress summary: {e}")
        raise DatabaseError(f"Error getting user progress summary: {str(e)}")


def get_progress_trends(username: str, days: int = 7) -> AnalyticsData:
    """
    Get progress trends for a user over a specified period.

    Args:
        username: The username to get trends for
        days: Number of days to analyze

    Returns:
        Dictionary containing progress trends

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if days <= 0:
            days = 7

        logger.info(f"Getting progress trends for user {username} (last {days} days)")

        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)

        trends = {
            "username": username,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_activity": {},
            "activity_trends": {},
            "performance_trends": {},
            "learning_patterns": {},
            "recommendations": []
        }

        # Get daily activity breakdown
        for i in range(days):
            current_date = end_date - datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            # Count activities for this date
            lesson_count = len(select_rows(
                "lesson_progress",
                columns=["id"],
                where="user_id = ? AND DATE(updated_at) = ?",
                params=(username, date_str)
            ))

            exercise_count = len(select_rows(
                "activity_progress",
                columns=["id"],
                where="username = ? AND activity_type = 'exercise' AND DATE(completed_at) = ?",
                params=(username, date_str)
            ))

            vocab_count = len(select_rows(
                "vocabulary_progress",
                columns=["id"],
                where="username = ? AND DATE(reviewed_at) = ?",
                params=(username, date_str)
            ))

            game_count = len(select_rows(
                "game_progress",
                columns=["id"],
                where="username = ? AND DATE(completed_at) = ?",
                params=(username, date_str)
            ))

            trends["daily_activity"][date_str] = {
                "lessons": lesson_count,
                "exercises": exercise_count,
                "vocabulary": vocab_count,
                "games": game_count,
                "total": lesson_count + exercise_count + vocab_count + game_count
            }

        # Calculate activity trends
        total_activities = sum(day["total"] for day in trends["daily_activity"].values())
        avg_daily_activities = total_activities / days if days > 0 else 0

        trends["activity_trends"] = {
            "total_activities": total_activities,
            "average_daily_activities": round(avg_daily_activities, 2),
            "most_active_day": max(trends["daily_activity"].items(), key=lambda x: x[1]["total"])[0] if trends["daily_activity"] else None,
            "least_active_day": min(trends["daily_activity"].items(), key=lambda x: x[1]["total"])[0] if trends["daily_activity"] else None,
            "activity_consistency": "consistent" if avg_daily_activities > 5 else "moderate" if avg_daily_activities > 2 else "low"
        }

        # Calculate performance trends
        exercise_scores = []
        for i in range(days):
            current_date = end_date - datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            exercises = select_rows(
                "activity_progress",
                columns=["score", "total_questions"],
                where="username = ? AND activity_type = 'exercise' AND DATE(completed_at) = ?",
                params=(username, date_str)
            )

            for exercise in exercises:
                score = exercise.get("score", 0)
                total = exercise.get("total_questions", 1)
                if total > 0:
                    exercise_scores.append((date_str, (score / total) * 100))

        if exercise_scores:
            # Calculate performance improvement
            recent_scores = [score for date, score in exercise_scores if date >= (end_date - datetime.timedelta(days=3)).strftime("%Y-%m-%d")]
            older_scores = [score for date, score in exercise_scores if date < (end_date - datetime.timedelta(days=3)).strftime("%Y-%m-%d")]

            if recent_scores and older_scores:
                recent_avg = sum(recent_scores) / len(recent_scores)
                older_avg = sum(older_scores) / len(older_scores)
                performance_change = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
            else:
                performance_change = 0

            trends["performance_trends"] = {
                "average_score": sum(score for _, score in exercise_scores) / len(exercise_scores),
                "performance_change": round(performance_change, 2),
                "total_exercises": len(exercise_scores),
                "trend_direction": "improving" if performance_change > 5 else "declining" if performance_change < -5 else "stable"
            }

        # Analyze learning patterns
        activity_times = []
        for i in range(days):
            current_date = end_date - datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            activities = select_rows(
                "activity_progress",
                columns=["completed_at"],
                where="username = ? AND DATE(completed_at) = ?",
                params=(username, date_str)
            )

            for activity in activities:
                try:
                    activity_time = datetime.datetime.fromisoformat(activity["completed_at"].replace('Z', '+00:00'))
                    activity_times.append(activity_time.hour)
                except:
                    continue

        if activity_times:
            # Find most common activity time
            from collections import Counter
            time_counts = Counter(activity_times)
            most_common_time = time_counts.most_common(1)[0][0] if time_counts else None

            trends["learning_patterns"] = {
                "most_active_hour": most_common_time,
                "activity_distribution": dict(time_counts),
                "preferred_time": "morning" if most_common_time and 6 <= most_common_time < 12 else "afternoon" if 12 <= most_common_time < 18 else "evening" if 18 <= most_common_time < 22 else "night"
            }

        # Generate recommendations
        recommendations = []

        if avg_daily_activities < 3:
            recommendations.append("Try to complete at least 3 activities per day to maintain consistent progress")

        if trends.get("performance_trends", {}).get("trend_direction") == "declining":
            recommendations.append("Consider reviewing previous lessons to strengthen your understanding")

        if not trends["daily_activity"] or all(day["total"] == 0 for day in trends["daily_activity"].values()):
            recommendations.append("Start with a simple lesson or vocabulary review to get back into learning")

        trends["recommendations"] = recommendations

        logger.info(f"Generated progress trends for user {username}: {total_activities} total activities, {trends['activity_trends']['activity_consistency']} consistency")
        return trends

    except ValueError as e:
        logger.error(f"Validation error getting progress trends: {e}")
        raise
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting progress trends: {e}")
        raise DatabaseError(f"Error getting progress trends: {str(e)}")
