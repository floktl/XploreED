"""
XplorED - Admin Game Management Module

This module provides game management functions for admin operations,
following clean architecture principles as outlined in the documentation.

Game Management Components:
- Game Results: Retrieval and analysis of game results
- User Performance: Individual user game performance tracking
- Statistics: Game statistics and analytics for admin review

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List

from core.database.connection import select_rows

logger = logging.getLogger(__name__)


def get_all_game_results() -> List[Dict[str, Any]]:
    """
    Retrieve all game results for admin review.

    Returns:
        List of game results with user and performance data

    Raises:
        Exception: If database operations fail
    """
    try:
        logger.info("Retrieving all game results for admin review")

        results = select_rows(
            "results",
            columns=["username", "level", "correct", "answer", "timestamp"],
            order_by="username ASC, timestamp DESC",
        )

        logger.info(f"Retrieved {len(results)} game results")
        return results

    except Exception as e:
        logger.error(f"Error retrieving game results: {e}")
        raise


def get_user_game_results(username: str) -> List[Dict[str, Any]]:
    """
    Get game results for a specific user.

    Args:
        username: The username to get results for

    Returns:
        List of game results for the user

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        username = username.strip()
        if not username:
            raise ValueError("Username cannot be empty")

        logger.info(f"Retrieving game results for user {username}")

        rows = select_rows(
            "results",
            columns=["level", "correct", "answer", "timestamp"],
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
        )

        results = [
            {
                "level": row["level"],
                "correct": bool(row["correct"]),
                "answer": row["answer"],
                "timestamp": row["timestamp"]
            }
            for row in rows
        ]

        logger.info(f"Retrieved {len(results)} game results for user {username}")
        return results

    except ValueError as e:
        logger.error(f"Validation error getting user game results: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting game results for user {username}: {e}")
        raise
