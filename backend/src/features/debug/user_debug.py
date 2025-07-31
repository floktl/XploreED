"""
XplorED - User Debug Module

This module provides user-specific debugging functions for development and troubleshooting,
following clean architecture principles as outlined in the documentation.

User Debug Components:
- User Statistics: Comprehensive user data analysis and statistics
- User Data Validation: Check user data integrity and completeness
- Performance Analysis: User performance metrics and debugging information

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any

from core.database.connection import select_one, select_rows

logger = logging.getLogger(__name__)


def get_user_statistics(username: str) -> Dict[str, Any]:
    """
    Get comprehensive user statistics for debugging.

    Args:
        username: The username to get statistics for

    Returns:
        Dictionary containing user statistics

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting statistics for user {username}")

        stats = {
            "username": username,
            "vocabulary": {},
            "results": {},
            "ai_data": {},
            "topic_memory": {}
        }

        # Vocabulary statistics
        vocab_count = select_rows(
            "vocab_log",
            columns=["COUNT(*) as count"],
            where="username = ?",
            params=(username,)
        )
        stats["vocabulary"]["total_words"] = vocab_count[0]["count"] if vocab_count else 0

        # Results statistics
        results_count = select_rows(
            "results",
            columns=["COUNT(*) as count, AVG(correct) as avg_correct"],
            where="username = ?",
            params=(username,)
        )
        if results_count:
            stats["results"]["total_exercises"] = results_count[0]["count"]
            stats["results"]["average_correct"] = float(results_count[0]["avg_correct"] or 0)
        else:
            stats["results"]["total_exercises"] = 0
            stats["results"]["average_correct"] = 0.0

        # AI data statistics
        ai_data = select_one(
            "ai_user_data",
            columns="exercises, next_exercises",
            where="username = ?",
            params=(username,)
        )
        stats["ai_data"]["has_exercises"] = bool(ai_data and ai_data.get("exercises"))
        stats["ai_data"]["has_next_exercises"] = bool(ai_data and ai_data.get("next_exercises"))

        # Topic memory statistics
        topic_count = select_rows(
            "topic_memory",
            columns=["COUNT(*) as count"],
            where="username = ?",
            params=(username,)
        )
        stats["topic_memory"]["total_topics"] = topic_count[0]["count"] if topic_count else 0

        logger.info(f"Retrieved statistics for user {username}")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting user statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for user {username}: {e}")
        raise
