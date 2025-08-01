"""
XplorED - Vocabulary Analytics Module

This module provides vocabulary analytics and learning insights functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Vocabulary Analytics Components:
- Learning Progress: Track vocabulary learning progress over time
- Difficulty Analysis: Analyze vocabulary difficulty and learning patterns
- Study Recommendations: Generate personalized study recommendations
- Data Export: Export vocabulary data in various formats

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple

from core.database.connection import select_one, select_rows, fetch_custom, execute_query

logger = logging.getLogger(__name__)


def get_vocabulary_learning_progress(user: str, days: int = 30) -> Dict[str, Any]:
    """
    Get vocabulary learning progress over time.

    Args:
        user: The username to get progress for
        days: Number of days to look back

    Returns:
        Dictionary containing learning progress data

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        if days <= 0:
            days = 30

        logger.info(f"Getting vocabulary learning progress for user '{user}' over {days} days")

        # Get vocabulary added per day
        daily_additions = fetch_custom("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as new_words
            FROM vocab_log
            WHERE username = ?
                AND created_at >= date('now', '-{} days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """.format(days), (user,))

        # Get vocabulary reviewed per day
        daily_reviews = fetch_custom("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as reviews
            FROM vocab_log
            WHERE username = ?
                AND repetitions > 0
                AND created_at >= date('now', '-{} days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """.format(days), (user,))

        # Calculate total progress
        total_words = select_one("vocab_log", columns="COUNT(*) as count", where="username = ?", params=(user,))
        total = total_words.get("count", 0) if total_words else 0

        # Calculate retention rate (words with repetitions > 0)
        retention_data = select_one("vocab_log", columns="COUNT(*) as count", where="username = ? AND repetitions > 0", params=(user,))
        retention_count = retention_data.get("count", 0) if retention_data else 0
        retention_rate = (retention_count / total * 100) if total > 0 else 0

        progress = {
            "total_vocabulary": total,
            "retention_rate": round(retention_rate, 2),
            "daily_additions": {row["date"]: row["new_words"] for row in daily_additions},
            "daily_reviews": {row["date"]: row["reviews"] for row in daily_reviews},
            "period_days": days
        }

        logger.info(f"Retrieved vocabulary progress for user '{user}': {total} total words, {retention_rate:.1f}% retention")
        return progress

    except ValueError as e:
        logger.error(f"Validation error getting vocabulary progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting vocabulary progress for user '{user}': {e}")
        return {"total_vocabulary": 0, "retention_rate": 0, "daily_additions": {}, "daily_reviews": {}, "period_days": days}


def get_vocabulary_difficulty_analysis(user: str) -> Dict[str, Any]:
    """
    Analyze vocabulary difficulty and learning patterns.

    Args:
        user: The username to analyze

    Returns:
        Dictionary containing difficulty analysis

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Analyzing vocabulary difficulty for user '{user}'")

        # Get vocabulary by repetition count (difficulty indicator)
        difficulty_distribution = fetch_custom("""
            SELECT
                repetitions,
                COUNT(*) as count
            FROM vocab_log
            WHERE username = ?
            GROUP BY repetitions
            ORDER BY repetitions
        """, (user,))

        # Get vocabulary by word type difficulty
        word_type_difficulty = fetch_custom("""
            SELECT
                word_type,
                AVG(repetitions) as avg_repetitions,
                COUNT(*) as count
            FROM vocab_log
            WHERE username = ? AND word_type IS NOT NULL AND word_type != ''
            GROUP BY word_type
            ORDER BY avg_repetitions DESC
        """, (user,))

        # Get most difficult words (highest repetitions)
        difficult_words = fetch_custom("""
            SELECT
                vocab,
                translation,
                word_type,
                repetitions,
                ef
            FROM vocab_log
            WHERE username = ?
            ORDER BY repetitions DESC, ef ASC
            LIMIT 10
        """, (user,))

        # Get easiest words (lowest repetitions, high EF)
        easy_words = fetch_custom("""
            SELECT
                vocab,
                translation,
                word_type,
                repetitions,
                ef
            FROM vocab_log
            WHERE username = ?
            ORDER BY repetitions ASC, ef DESC
            LIMIT 10
        """, (user,))

        analysis = {
            "difficulty_distribution": {row["repetitions"]: row["count"] for row in difficulty_distribution},
            "word_type_difficulty": [
                {
                    "word_type": row["word_type"],
                    "avg_repetitions": round(row["avg_repetitions"], 2),
                    "count": row["count"]
                }
                for row in word_type_difficulty
            ],
            "most_difficult_words": [
                {
                    "word": row["vocab"],
                    "translation": row["translation"],
                    "word_type": row["word_type"],
                    "repetitions": row["repetitions"],
                    "ef": row["ef"]
                }
                for row in difficult_words
            ],
            "easiest_words": [
                {
                    "word": row["vocab"],
                    "translation": row["translation"],
                    "word_type": row["word_type"],
                    "repetitions": row["repetitions"],
                    "ef": row["ef"]
                }
                for row in easy_words
            ]
        }

        logger.info(f"Completed vocabulary difficulty analysis for user '{user}'")
        return analysis

    except ValueError as e:
        logger.error(f"Validation error in vocabulary difficulty analysis: {e}")
        raise
    except Exception as e:
        logger.error(f"Error analyzing vocabulary difficulty for user '{user}': {e}")
        return {"difficulty_distribution": {}, "word_type_difficulty": [], "most_difficult_words": [], "easiest_words": []}


def get_vocabulary_study_recommendations(user: str) -> Dict[str, Any]:
    """
    Generate study recommendations based on vocabulary analysis.

    Args:
        user: The username to get recommendations for

    Returns:
        Dictionary containing study recommendations

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Generating vocabulary study recommendations for user '{user}'")

        # Get words due for review
        due_words = fetch_custom("""
            SELECT
                vocab,
                translation,
                word_type,
                repetitions,
                ef,
                next_review
            FROM vocab_log
            WHERE username = ? AND next_review <= datetime('now')
            ORDER BY next_review ASC
            LIMIT 20
        """, (user,))

        # Get words that need more practice (low EF, high repetitions)
        need_practice = fetch_custom("""
            SELECT
                vocab,
                translation,
                word_type,
                repetitions,
                ef
            FROM vocab_log
            WHERE username = ? AND ef < 2.0 AND repetitions > 2
            ORDER BY ef ASC, repetitions DESC
            LIMIT 15
        """, (user,))

        # Get words by word type that need attention
        word_type_recommendations = fetch_custom("""
            SELECT
                word_type,
                COUNT(*) as count,
                AVG(ef) as avg_ef
            FROM vocab_log
            WHERE username = ? AND word_type IS NOT NULL AND word_type != ''
            GROUP BY word_type
            HAVING avg_ef < 2.5
            ORDER BY avg_ef ASC
        """, (user,))

        # Calculate study session recommendations
        total_due = len(due_words)
        total_practice = len(need_practice)

        if total_due > 0:
            session_duration = min(30, total_due * 2)  # 2 minutes per word, max 30 minutes
        else:
            session_duration = 15

        recommendations = {
            "due_for_review": [
                {
                    "word": row["vocab"],
                    "translation": row["translation"],
                    "word_type": row["word_type"],
                    "repetitions": row["repetitions"],
                    "ef": row["ef"],
                    "next_review": row["next_review"]
                }
                for row in due_words
            ],
            "need_practice": [
                {
                    "word": row["vocab"],
                    "translation": row["translation"],
                    "word_type": row["word_type"],
                    "repetitions": row["repetitions"],
                    "ef": row["ef"]
                }
                for row in need_practice
            ],
            "word_type_focus": [
                {
                    "word_type": row["word_type"],
                    "count": row["count"],
                    "avg_ef": round(row["avg_ef"], 2)
                }
                for row in word_type_recommendations
            ],
            "study_session": {
                "recommended_duration_minutes": session_duration,
                "words_to_review": total_due,
                "words_to_practice": total_practice,
                "priority": "high" if total_due > 10 else "medium" if total_due > 5 else "low"
            }
        }

        logger.info(f"Generated study recommendations for user '{user}': {total_due} due, {total_practice} need practice")
        return recommendations

    except ValueError as e:
        logger.error(f"Validation error generating study recommendations: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating study recommendations for user '{user}': {e}")
        return {"due_for_review": [], "need_practice": [], "word_type_focus": [], "study_session": {"recommended_duration_minutes": 0, "words_to_review": 0, "words_to_practice": 0, "priority": "low"}}


def get_vocabulary_export_data(user: str, format_type: str = "json") -> Dict[str, Any]:
    """
    Prepare vocabulary data for export.

    Args:
        user: The username to export data for
        format_type: Export format (json, csv, etc.)

    Returns:
        Dictionary containing export data

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Preparing vocabulary export for user '{user}' in {format_type} format")

        # Get all vocabulary entries
        vocabulary_data = fetch_custom("""
            SELECT
                vocab,
                translation,
                word_type,
                article,
                details,
                repetitions,
                ef,
                next_review,
                created_at,
                context,
                exercise
            FROM vocab_log
            WHERE username = ?
            ORDER BY created_at DESC
        """, (user,))

        # Get metadata
        metadata = {
            "user": user,
            "export_date": datetime.datetime.now().isoformat(),
            "format": format_type,
            "total_entries": len(vocabulary_data),
            "version": "1.0"
        }

        # Prepare export data
        export_data = {
            "metadata": metadata,
            "vocabulary": [
                {
                    "word": row["vocab"],
                    "translation": row["translation"],
                    "word_type": row["word_type"],
                    "article": row["article"],
                    "details": row["details"],
                    "repetitions": row["repetitions"],
                    "ef": row["ef"],
                    "next_review": row["next_review"],
                    "created_at": row["created_at"],
                    "context": row["context"],
                    "exercise": row["exercise"]
                }
                for row in vocabulary_data
            ]
        }

        logger.info(f"Prepared vocabulary export for user '{user}': {len(vocabulary_data)} entries")
        return export_data

    except ValueError as e:
        logger.error(f"Validation error preparing vocabulary export: {e}")
        raise
    except Exception as e:
        logger.error(f"Error preparing vocabulary export for user '{user}': {e}")
        return {"metadata": {"user": user, "error": str(e)}, "vocabulary": []}
