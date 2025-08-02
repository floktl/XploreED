"""
XplorED - Game Management Module

This module provides game session and progress management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Game Management Components:
- Session Management: Create and manage game sessions
- Progress Tracking: Update and track game progress
- Score Calculation: Calculate game scores and performance metrics

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import uuid
import datetime
from typing import Dict, Any, List

from core.database.connection import insert_row, update_row, select_one
from core.services import GameService

logger = logging.getLogger(__name__)


def create_game_session(session_data: Dict[str, Any]) -> str:
    """
    Create a new game session.

    Args:
        session_data: Dictionary containing session information

    Returns:
        Session ID if creation was successful

    Raises:
        ValueError: If session_data is invalid
    """
    try:
        if not session_data:
            raise ValueError("Session data is required")

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Add session ID and timestamp to data
        session_data["session_id"] = session_id
        session_data["created_at"] = datetime.datetime.now().isoformat()
        session_data["status"] = "active"

        # Insert into database
        success = insert_row("game_sessions", session_data)

        if success:
            logger.info(f"Successfully created game session {session_id}")
            return session_id
        else:
            logger.error(f"Failed to create game session")
            return ""

    except ValueError as e:
        logger.error(f"Validation error creating game session: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating game session: {e}")
        return ""


def update_game_progress(session_id: str, progress_data: Dict[str, Any]) -> bool:
    """
    Update game progress for a session.

    Args:
        session_id: The session ID to update
        progress_data: Dictionary containing progress information

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not session_id:
            raise ValueError("Session ID is required")

        if not progress_data:
            raise ValueError("Progress data is required")

        # Add timestamp to progress data
        progress_data["updated_at"] = datetime.datetime.now().isoformat()

        # Update session in database
        success = update_row(
            "game_sessions",
            progress_data,
            "WHERE session_id = ?",
            (session_id,)
        )

        if success:
            logger.info(f"Successfully updated game progress for session {session_id}")
            return True
        else:
            logger.warning(f"Game session {session_id} not found for update")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating game progress: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating game progress for session {session_id}: {e}")
        return False


def calculate_game_score(session_id: str, answers: List[Dict[str, Any]],
                        time_taken: int, difficulty: str) -> Dict[str, Any]:
    """
    Calculate game score based on answers, time, and difficulty.

    Args:
        session_id: The session ID
        answers: List of answer dictionaries
        time_taken: Time taken in seconds
        difficulty: Difficulty level of the game

    Returns:
        Dictionary containing score calculation results

    Raises:
        ValueError: If parameters are invalid
    """
    # Use core service for score calculation
    score_result = GameService.calculate_game_score(answers)

    # Add session-specific data
    score_result["session_id"] = session_id
    score_result["time_taken"] = time_taken
    score_result["difficulty"] = difficulty
    score_result["calculated_at"] = datetime.datetime.now().isoformat()

    return score_result
