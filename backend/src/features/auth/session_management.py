"""
XplorED - Session Management Module

This module provides session management functions for user authentication,
following clean architecture principles as outlined in the documentation.

Session Management Components:
- Session Validation: Check if sessions are active and valid
- Session Information: Retrieve session details and user information
- Session Cleanup: Destroy sessions and handle logout

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional

from core.database.connection import fetch_one

logger = logging.getLogger(__name__)


def destroy_user_session(session_id: str) -> bool:
    """
    Destroy a user session.

    Args:
        session_id: The session ID to destroy

    Returns:
        True if session was destroyed successfully, False otherwise
    """
    try:
        if not session_id:
            logger.warning("Attempted to destroy empty session ID")
            return False

        from api.middleware.session import session_manager
        session_manager.destroy_session(session_id)
        logger.info(f"Destroyed session {session_id}")
        return True

    except Exception as e:
        logger.error(f"Error destroying session {session_id}: {e}")
        return False


def get_user_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a user session.

    Args:
        session_id: The session ID to check

    Returns:
        Dictionary with session information or None if invalid
    """
    try:
        if not session_id:
            return None

        from api.middleware.session import session_manager
        username = session_manager.get_user(session_id)
        if not username:
            return None

        # Get additional user info
        user_info = fetch_one("users", "WHERE username = ?", (username,))
        if not user_info:
            return None

        return {
            "username": username,
            "session_id": session_id,
            "created_at": user_info.get("created_at"),
            "is_admin": username == "admin"
        }

    except Exception as e:
        logger.error(f"Error getting session info for {session_id}: {e}")
        return None


def validate_session(session_id: str) -> bool:
    """
    Validate if a session is still active.

    Args:
        session_id: The session ID to validate

    Returns:
        True if session is valid, False otherwise
    """
    try:
        if not session_id:
            return False

        from api.middleware.session import session_manager
        username = session_manager.get_user(session_id)
        return username is not None

    except Exception as e:
        logger.error(f"Error validating session {session_id}: {e}")
        return False
