"""
XplorED - AI Feedback Session Module

This module provides feedback session management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Feedback Session Components:
- Session Management: Create and manage feedback generation sessions
- Progress Tracking: Track feedback generation progress
- Session Storage: Store and retrieve session data
- Progress Updates: Update session progress and status

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import os
import json
import uuid
import redis
from typing import Dict, Any, Optional

from core.services.import_service import *

logger = logging.getLogger(__name__)

# Connect to Redis (host from env, default 'localhost')
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


def create_feedback_session() -> str:
    """
    Create a new feedback generation session.

    Returns:
        Session ID for the new feedback session
    """
    try:
        session_id = str(uuid.uuid4())
        progress = {
            "percentage": 0,
            "status": "Starting feedback generation...",
            "step": "init",
            "completed": False
        }
        redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
        logger.info(f"Created feedback session: {session_id}")
        return session_id

    except Exception as e:
        logger.error(f"Error creating feedback session: {e}")
        raise


def get_feedback_progress(session_id: str) -> Dict[str, Any]:
    """
    Get the current progress of AI feedback generation.

    Args:
        session_id: The feedback session ID

    Returns:
        Dictionary containing progress information
    """
    try:
        progress_json = redis_client.get(f"feedback_progress:{session_id}")
        if not progress_json:
            return {"error": "Session not found"}

        progress = json.loads(progress_json)
        logger.debug(f"Feedback progress for session {session_id}: {progress['percentage']}% - {progress['status']}")
        return progress

    except Exception as e:
        logger.error(f"Error getting feedback progress: {e}")
        return {"error": "Failed to get progress"}


def update_feedback_progress(session_id: str, percentage: int, status: str, step: str) -> bool:
    """
    Update the progress of a feedback generation session.

    Args:
        session_id: The feedback session ID
        percentage: Progress percentage (0-100)
        status: Current status message
        step: Current step identifier

    Returns:
        True if update successful, False otherwise
    """
    try:
        progress = {
            "percentage": percentage,
            "status": status,
            "step": step,
            "completed": percentage >= 100
        }
        redis_client.set(f"feedback_progress:{session_id}", json.dumps(progress))
        logger.debug(f"Updated feedback progress for session {session_id}: {percentage}% - {status}")
        return True

    except Exception as e:
        logger.error(f"Error updating feedback progress: {e}")
        return False


def get_feedback_result(session_id: str) -> Dict[str, Any]:
    """
    Get the final result of a feedback generation session.

    Args:
        session_id: The feedback session ID

    Returns:
        Dictionary containing the feedback result
    """
    try:
        result_json = redis_client.get(f"feedback_result:{session_id}")
        if not result_json:
            return {"error": "Result not found"}

        result = json.loads(result_json)
        logger.debug(f"Retrieved feedback result for session {session_id}")
        return result

    except Exception as e:
        logger.error(f"Error getting feedback result: {e}")
        return {"error": "Failed to get result"}


def _store_feedback_result(session_id: str, result: Dict[str, Any]) -> None:
    """
    Store the final result of a feedback generation session.

    Args:
        session_id: The feedback session ID
        result: The feedback result to store
    """
    try:
        redis_client.set(f"feedback_result:{session_id}", json.dumps(result))
        logger.debug(f"Stored feedback result for session {session_id}")

    except Exception as e:
        logger.error(f"Error storing feedback result: {e}")


def _mark_feedback_complete(session_id: str, result: Dict[str, Any]) -> None:
    """
    Mark a feedback session as complete and store the result.

    Args:
        session_id: The feedback session ID
        result: The feedback result to store
    """
    try:
        # Update progress to 100%
        update_feedback_progress(session_id, 100, "Feedback generation complete", "complete")

        # Store the result
        _store_feedback_result(session_id, result)

        logger.info(f"Marked feedback session {session_id} as complete")

    except Exception as e:
        logger.error(f"Error marking feedback complete: {e}")


def _ensure_feedback_completion(session_id: str) -> None:
    """
    Ensure a feedback session is marked as complete.

    Args:
        session_id: The feedback session ID
    """
    try:
        progress = get_feedback_progress(session_id)
        if not progress.get("error") and not progress.get("completed"):
            update_feedback_progress(session_id, 100, "Feedback generation complete", "complete")
            logger.info(f"Ensured feedback session {session_id} is marked complete")

    except Exception as e:
        logger.error(f"Error ensuring feedback completion: {e}")
