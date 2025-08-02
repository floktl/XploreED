"""
XplorED - Progress Service

This module provides core progress business logic services,
following clean architecture principles as outlined in the documentation.

Progress Service Components:
- Cross-activity progress tracking and analytics
- Progress trends and performance analysis
- Activity pattern analysis and recommendations
- Progress reset and management operations

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter

from core.database.connection import select_rows, select_one, update_row, insert_row, delete_rows
from core.authentication import user_exists
from core.services import LessonService, VocabularyService, UserService
from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ProgressService:
    """Core progress business logic service."""

    @staticmethod
    def get_user_progress_summary(username: str, days: int = 30) -> Dict[str, Any]:
        """
        Get a comprehensive progress summary for a user across all activity types.

        Args:
            username: The username to get summary for
            days: Number of days to look back for activity

        Returns:
            Dictionary containing comprehensive progress summary

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            if days <= 0:
                days = 30

            logger.info(f"Getting progress summary for user {username} (last {days} days)")

            # Calculate date range
            end_date = datetime.datetime.utcnow()
            start_date = end_date - datetime.timedelta(days=days)

            summary = ProgressService._build_base_summary(username, days, start_date, end_date)

            # Get activity data for each type
            lesson_data = ProgressService._get_lesson_activity_data(username, start_date)
            exercise_data = ProgressService._get_exercise_activity_data(username, start_date)
            vocabulary_data = ProgressService._get_vocabulary_activity_data(username, start_date)
            game_data = ProgressService._get_game_activity_data(username, start_date)

            # Update summary with activity data
            summary.update(ProgressService._process_lesson_activity(lesson_data, summary))
            summary.update(ProgressService._process_exercise_activity(exercise_data, summary))
            summary.update(ProgressService._process_vocabulary_activity(vocabulary_data, summary))
            summary.update(ProgressService._process_game_activity(game_data, summary))

            # Calculate derived metrics
            summary.update(ProgressService._calculate_derived_metrics(summary, lesson_data, exercise_data, vocabulary_data, game_data))

            logger.info(f"Generated progress summary for user {username}: {summary['total_activities']} activities, {summary['streak_days']} day streak")
            return summary

        except ValidationError as e:
            logger.error(f"Validation error getting user progress summary: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user progress summary for user {username}: {e}")
            return ProgressService._build_error_summary(username, str(e))

    @staticmethod
    def get_progress_trends(username: str, days: int = 7) -> Dict[str, Any]:
        """
        Get progress trends for a user over a specified period.

        Args:
            username: The username to get trends for
            days: Number of days to analyze

        Returns:
            Dictionary containing progress trends and analysis

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            if days <= 0:
                days = 7

            logger.info(f"Getting progress trends for user {username} (last {days} days)")

            # Calculate date range
            end_date = datetime.datetime.utcnow()
            start_date = end_date - datetime.timedelta(days=days)

            trends = ProgressService._build_base_trends(username, days, start_date, end_date)

            # Get daily activity breakdown
            trends["daily_activity"] = ProgressService._get_daily_activity_breakdown(username, start_date, days)

            # Calculate activity trends
            trends["activity_trends"] = ProgressService._calculate_activity_trends(trends["daily_activity"], days)

            # Calculate performance trends
            trends["performance_trends"] = ProgressService._calculate_performance_trends(username, start_date, days)

            # Analyze learning patterns
            trends["learning_patterns"] = ProgressService._analyze_learning_patterns(username, start_date, days)

            # Generate recommendations
            trends["recommendations"] = ProgressService._generate_recommendations(trends)

            logger.info(f"Generated progress trends for user {username}: {trends['activity_trends']['total_activities']} total activities")
            return trends

        except ValidationError as e:
            logger.error(f"Validation error getting progress trends: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting progress trends for user {username}: {e}")
            return ProgressService._build_error_trends(username, days, str(e))

    @staticmethod
    def track_exercise_progress(username: str, block_id: str, score: float, total_questions: int) -> bool:
        """
        Track progress for exercise completion.

        Args:
            username: The username to track progress for
            block_id: The exercise block ID
            score: The score achieved
            total_questions: Total number of questions

        Returns:
            True if progress was tracked successfully

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            if not block_id:
                raise ValidationError("Block ID is required")

            if score < 0 or total_questions <= 0:
                raise ValidationError("Valid score and total questions are required")

            logger.info(f"Tracking exercise progress for user {username}, block {block_id}")

            # Calculate completion percentage
            completion_percentage = (score / total_questions) * 100 if total_questions > 0 else 0

            # Track exercise progress
            progress_data = {
                "username": username,
                "block_id": block_id,
                "score": score,
                "total_questions": total_questions,
                "completion_percentage": completion_percentage,
                "completed_at": datetime.datetime.utcnow().isoformat(),
                "activity_type": "exercise"
            }

            success = insert_row("activity_progress", progress_data)

            if success:
                logger.info(f"Successfully tracked exercise progress for user {username}, block {block_id}")
            else:
                logger.error(f"Failed to track exercise progress for user {username}, block {block_id}")

            return success

        except ValidationError as e:
            logger.error(f"Validation error tracking exercise progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error tracking exercise progress for user {username}, block {block_id}: {e}")
            return False

    @staticmethod
    def track_vocabulary_progress(username: str, word: str, correct: bool, repetitions: int) -> bool:
        """
        Track progress for vocabulary learning.

        Args:
            username: The username to track progress for
            word: The vocabulary word
            correct: Whether the answer was correct
            repetitions: Number of repetitions

        Returns:
            True if progress was tracked successfully

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            if not word:
                raise ValidationError("Word is required")

            if repetitions < 0:
                raise ValidationError("Valid repetitions count is required")

            logger.info(f"Tracking vocabulary progress for user {username}, word {word}")

            # Track vocabulary progress
            progress_data = {
                "username": username,
                "word": word,
                "correct": int(correct),
                "repetitions": repetitions,
                "reviewed_at": datetime.datetime.utcnow().isoformat(),
                "activity_type": "vocabulary"
            }

            success = insert_row("vocabulary_progress", progress_data)

            if success:
                logger.info(f"Successfully tracked vocabulary progress for user {username}, word {word}")
            else:
                logger.error(f"Failed to track vocabulary progress for user {username}, word {word}")

            return success

        except ValidationError as e:
            logger.error(f"Validation error tracking vocabulary progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error tracking vocabulary progress for user {username}, word {word}: {e}")
            return False

    @staticmethod
    def track_game_progress(username: str, game_type: str, score: float, level: int) -> bool:
        """
        Track progress for game completion.

        Args:
            username: The username to track progress for
            game_type: The type of game
            score: The score achieved
            level: The game level

        Returns:
            True if progress was tracked successfully

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            if not game_type:
                raise ValidationError("Game type is required")

            if score < 0 or level < 0:
                raise ValidationError("Valid score and level are required")

            logger.info(f"Tracking game progress for user {username}, game {game_type}, level {level}")

            # Track game progress
            progress_data = {
                "username": username,
                "game_type": game_type,
                "score": score,
                "level": level,
                "completed_at": datetime.datetime.utcnow().isoformat(),
                "activity_type": "game"
            }

            success = insert_row("game_progress", progress_data)

            if success:
                logger.info(f"Successfully tracked game progress for user {username}, game {game_type}, level {level}")
            else:
                logger.error(f"Failed to track game progress for user {username}, game {game_type}, level {level}")

            return success

        except ValidationError as e:
            logger.error(f"Validation error tracking game progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error tracking game progress for user {username}, game {game_type}, level {level}: {e}")
            return False

    @staticmethod
    def reset_user_progress(username: str, activity_type: Optional[str] = None) -> bool:
        """
        Reset progress for a user, optionally for a specific activity type.

        Args:
            username: The username to reset progress for
            activity_type: Optional activity type to reset (lesson, exercise, vocabulary, game)

        Returns:
            True if progress was reset successfully

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            logger.info(f"Resetting progress for user {username}" + (f", activity type {activity_type}" if activity_type else ""))

            if activity_type:
                # Reset specific activity type
                table_name = f"{activity_type}_progress"
                success = delete_rows(table_name, "WHERE username = ?", (username,))
            else:
                # Reset all progress types
                tables = ["lesson_progress", "activity_progress", "vocabulary_progress", "game_progress"]
                success = True

                for table in tables:
                    table_success = delete_rows(table, "WHERE username = ?", (username,))
                    if not table_success:
                        success = False
                        logger.error(f"Failed to reset progress for table {table}")

            if success:
                logger.info(f"Successfully reset progress for user {username}")
            else:
                logger.error(f"Failed to reset progress for user {username}")

            return success

        except ValueError as e:
            logger.error(f"Validation error resetting user progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error resetting progress for user {username}: {e}")
            return False

    # Private helper methods

    @staticmethod
    def _build_base_summary(username: str, days: int, start_date: datetime.datetime, end_date: datetime.datetime) -> Dict[str, Any]:
        """Build base summary structure."""
        return {
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

    @staticmethod
    def _build_error_summary(username: str, error_message: str) -> Dict[str, Any]:
        """Build error summary structure."""
        return {
            "username": username,
            "error": error_message,
            "total_activities": 0,
            "lessons_completed": 0,
            "exercises_completed": 0,
            "vocabulary_reviews": 0,
            "games_played": 0,
            "average_score": 0.0,
            "improvement_rate": 0.0,
            "streak_days": 0,
            "activity_breakdown": {},
            "recent_activity": [],
            "top_performing_areas": [],
            "areas_for_improvement": []
        }

    @staticmethod
    def _build_base_trends(username: str, days: int, start_date: datetime.datetime, end_date: datetime.datetime) -> Dict[str, Any]:
        """Build base trends structure."""
        return {
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

    @staticmethod
    def _build_error_trends(username: str, days: int, error_message: str) -> Dict[str, Any]:
        """Build error trends structure."""
        return {
            "username": username,
            "error": error_message,
            "period_days": days,
            "daily_activity": {},
            "activity_trends": {},
            "performance_trends": {},
            "learning_patterns": {},
            "recommendations": []
        }

    @staticmethod
    def _get_lesson_activity_data(username: str, start_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Get lesson activity data for the period."""
        return select_rows(
                "lesson_progress",
            columns=["lesson_id", "block_id", "completed", "updated_at"],
            where="user_id = ? AND updated_at >= ?",
            params=(username, start_date.isoformat())
        ) or []

    @staticmethod
    def _get_exercise_activity_data(username: str, start_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Get exercise activity data for the period."""
        return select_rows(
            "activity_progress",
            columns=["block_id", "score", "total_questions", "completion_percentage", "completed_at"],
            where="username = ? AND activity_type = 'exercise' AND completed_at >= ?",
            params=(username, start_date.isoformat())
        ) or []

    @staticmethod
    def _get_vocabulary_activity_data(username: str, start_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Get vocabulary activity data for the period."""
        return select_rows(
            "vocabulary_progress",
            columns=["word", "correct", "repetitions", "reviewed_at"],
            where="username = ? AND reviewed_at >= ?",
            params=(username, start_date.isoformat())
        ) or []

    @staticmethod
    def _get_game_activity_data(username: str, start_date: datetime.datetime) -> List[Dict[str, Any]]:
        """Get game activity data for the period."""
        return select_rows(
            "game_progress",
            columns=["game_type", "score", "level", "completed_at"],
            where="username = ? AND completed_at >= ?",
            params=(username, start_date.isoformat())
        ) or []

    @staticmethod
    def _process_lesson_activity(lesson_data: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process lesson activity data and update summary."""
        if not lesson_data:
            return {"lessons_completed": 0, "activity_breakdown": {"lessons": {}}}

        completed_lessons = sum(1 for p in lesson_data if p.get("completed", 0) == 1)

        return {
            "lessons_completed": completed_lessons,
            "activity_breakdown": {
                "lessons": {
                    "total_blocks": len(lesson_data),
                    "completed_blocks": completed_lessons,
                    "completion_rate": (completed_lessons / len(lesson_data)) * 100 if lesson_data else 0
                }
            }
        }

    @staticmethod
    def _process_exercise_activity(exercise_data: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process exercise activity data and update summary."""
        if not exercise_data:
            return {"exercises_completed": 0, "average_score": 0.0, "activity_breakdown": {"exercises": {}}}

        total_score = sum(p.get("score", 0) for p in exercise_data)
        total_questions = sum(p.get("total_questions", 0) for p in exercise_data)
        average_score = (total_score / total_questions) * 100 if total_questions > 0 else 0

        return {
            "exercises_completed": len(exercise_data),
            "average_score": average_score,
            "activity_breakdown": {
                "exercises": {
                    "total_exercises": len(exercise_data),
                    "average_score": average_score,
                    "total_questions": total_questions
                }
            }
        }

    @staticmethod
    def _process_vocabulary_activity(vocab_data: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process vocabulary activity data and update summary."""
        if not vocab_data:
            return {"vocabulary_reviews": 0, "activity_breakdown": {"vocabulary": {}}}

        correct_reviews = sum(1 for p in vocab_data if p.get("correct", 0) == 1)

        return {
            "vocabulary_reviews": len(vocab_data),
            "activity_breakdown": {
                "vocabulary": {
                    "total_reviews": len(vocab_data),
                    "correct_reviews": correct_reviews,
                    "accuracy_rate": (correct_reviews / len(vocab_data)) * 100 if vocab_data else 0,
                    "total_repetitions": sum(p.get("repetitions", 0) for p in vocab_data)
                }
            }
        }

    @staticmethod
    def _process_game_activity(game_data: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process game activity data and update summary."""
        if not game_data:
            return {"games_played": 0, "activity_breakdown": {"games": {}}}

        game_scores = [p.get("score", 0) for p in game_data]

        return {
            "games_played": len(game_data),
            "activity_breakdown": {
                "games": {
                    "total_games": len(game_data),
                    "average_score": sum(game_scores) / len(game_scores) if game_scores else 0,
                    "highest_level": max(p.get("level", 0) for p in game_data) if game_data else 0,
                    "game_types": list(set(p.get("game_type", "") for p in game_data))
                }
            }
        }

    @staticmethod
    def _calculate_derived_metrics(summary: Dict[str, Any], lesson_data: List[Dict[str, Any]],
                                 exercise_data: List[Dict[str, Any]], vocab_data: List[Dict[str, Any]],
                                 game_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate derived metrics from activity data."""
        # Calculate total activities
        total_activities = (
            summary["lessons_completed"] +
            summary["exercises_completed"] +
            summary["vocabulary_reviews"] +
            summary["games_played"]
        )

        # Calculate streak days
        all_activities = lesson_data + exercise_data + vocab_data + game_data
        streak_days = ProgressService._calculate_streak_days(all_activities)

        # Calculate recent activity
        recent_activity = ProgressService._get_recent_activity(all_activities)

        return {
            "total_activities": total_activities,
            "streak_days": streak_days,
            "recent_activity": recent_activity
        }

    @staticmethod
    def _calculate_streak_days(all_activities: List[Dict[str, Any]]) -> int:
        """Calculate consecutive days with activity."""
        if not all_activities:
            return 0

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

        if not activity_dates:
            return 0

        # Calculate streak
        sorted_dates = sorted(activity_dates, reverse=True)
        current_streak = 0
        current_date = datetime.date.today()

        for date in sorted_dates:
            if (current_date - date).days == current_streak:
                current_streak += 1
            else:
                break

        return current_streak

    @staticmethod
    def _get_recent_activity(all_activities: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity from all activities."""
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

        # Sort by date and take last N
        recent_activities.sort(key=lambda x: x["date"], reverse=True)
        return recent_activities[:limit]

    @staticmethod
    def _get_daily_activity_breakdown(username: str, start_date: datetime.datetime, days: int) -> Dict[str, Any]:
        """Get daily activity breakdown for the period."""
        daily_activity = {}
        end_date = datetime.datetime.utcnow()

        for i in range(days):
            current_date = end_date - datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            # Count activities for this date
            lesson_count = len(select_rows(
                "lesson_progress",
                columns=["id"],
                where="user_id = ? AND DATE(updated_at) = ?",
                params=(username, date_str)
            ) or [])

            exercise_count = len(select_rows(
                "activity_progress",
                columns=["id"],
                where="username = ? AND activity_type = 'exercise' AND DATE(completed_at) = ?",
                params=(username, date_str)
            ) or [])

            vocab_count = len(select_rows(
                "vocabulary_progress",
                columns=["id"],
                where="username = ? AND DATE(reviewed_at) = ?",
                params=(username, date_str)
            ) or [])

            game_count = len(select_rows(
                "game_progress",
                columns=["id"],
                where="username = ? AND DATE(completed_at) = ?",
                params=(username, date_str)
            ) or [])

            daily_activity[date_str] = {
                "lessons": lesson_count,
                "exercises": exercise_count,
                "vocabulary": vocab_count,
                "games": game_count,
                "total": lesson_count + exercise_count + vocab_count + game_count
            }

            return daily_activity

    @staticmethod
    def _calculate_activity_trends(daily_activity: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Calculate activity trends from daily activity data."""
        total_activities = sum(day["total"] for day in daily_activity.values())
        avg_daily_activities = total_activities / days if days > 0 else 0

        return {
            "total_activities": total_activities,
            "average_daily_activities": round(avg_daily_activities, 2),
            "most_active_day": max(daily_activity.items(), key=lambda x: x[1]["total"])[0] if daily_activity else None,
            "least_active_day": min(daily_activity.items(), key=lambda x: x[1]["total"])[0] if daily_activity else None,
            "activity_consistency": "consistent" if avg_daily_activities > 5 else "moderate" if avg_daily_activities > 2 else "low"
        }

    @staticmethod
    def _calculate_performance_trends(username: str, start_date: datetime.datetime, days: int) -> Dict[str, Any]:
        """Calculate performance trends for the period."""
        exercise_scores = []
        end_date = datetime.datetime.utcnow()

        for i in range(days):
            current_date = end_date - datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            exercises = select_rows(
                "activity_progress",
                columns=["score", "total_questions"],
                where="username = ? AND activity_type = 'exercise' AND DATE(completed_at) = ?",
                params=(username, date_str)
            ) or []

            for exercise in exercises:
                score = exercise.get("score", 0)
                total = exercise.get("total_questions", 1)
                if total > 0:
                    exercise_scores.append((date_str, (score / total) * 100))

        if not exercise_scores:
            return {
                "average_score": 0,
                "performance_change": 0,
                "total_exercises": 0,
                "trend_direction": "stable"
            }

        # Calculate performance improvement
        recent_scores = [score for date, score in exercise_scores if date >= (end_date - datetime.timedelta(days=3)).strftime("%Y-%m-%d")]
        older_scores = [score for date, score in exercise_scores if date < (end_date - datetime.timedelta(days=3)).strftime("%Y-%m-%d")]

        if recent_scores and older_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            performance_change = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            performance_change = 0

        return {
            "average_score": sum(score for _, score in exercise_scores) / len(exercise_scores),
            "performance_change": round(performance_change, 2),
            "total_exercises": len(exercise_scores),
            "trend_direction": "improving" if performance_change > 5 else "declining" if performance_change < -5 else "stable"
        }

    @staticmethod
    def _analyze_learning_patterns(username: str, start_date: datetime.datetime, days: int) -> Dict[str, Any]:
        """Analyze learning patterns for the period."""
        activity_times = []
        end_date = datetime.datetime.utcnow()

        for i in range(days):
            current_date = end_date - datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            activities = select_rows(
                "activity_progress",
                columns=["completed_at"],
                where="username = ? AND DATE(completed_at) = ?",
                params=(username, date_str)
            ) or []

            for activity in activities:
                try:
                    activity_time = datetime.datetime.fromisoformat(activity["completed_at"].replace('Z', '+00:00'))
                    activity_times.append(activity_time.hour)
                except:
                    continue

        if not activity_times:
            return {
                "most_active_hour": None,
                "activity_distribution": {},
                "preferred_time": "unknown"
            }

        # Find most common activity time
        time_counts = Counter(activity_times)
        most_common_time = time_counts.most_common(1)[0][0] if time_counts else None

        return {
            "most_active_hour": most_common_time,
            "activity_distribution": dict(time_counts),
            "preferred_time": "morning" if most_common_time and 6 <= most_common_time < 12 else "afternoon" if 12 <= most_common_time < 18 else "evening" if 18 <= most_common_time < 22 else "night"
        }

    @staticmethod
    def _generate_recommendations(trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []
        activity_trends = trends.get("activity_trends", {})
        performance_trends = trends.get("performance_trends", {})
        daily_activity = trends.get("daily_activity", {})

        avg_daily_activities = activity_trends.get("average_daily_activities", 0)
        trend_direction = performance_trends.get("trend_direction", "stable")
        has_activity = any(day["total"] > 0 for day in daily_activity.values())

        if avg_daily_activities < 3:
            recommendations.append("Try to complete at least 3 activities per day to maintain consistent progress")

        if trend_direction == "declining":
            recommendations.append("Consider reviewing previous lessons to strengthen your understanding")

        if not has_activity:
            recommendations.append("Start with a simple lesson or vocabulary review to get back into learning")

        return recommendations
