"""
Authentication Helper Functions

This module contains helper functions for authentication operations that are used
by the auth routes but should not be in the route files themselves.

Author: XplorED Team
Date: 2025
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple

from core.services.import_service import *
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from core.utils.helpers import user_exists
from features.ai.memory.level_manager import initialize_topic_memory_for_level


logger = logging.getLogger(__name__)


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Authenticate a user with username and password.

    Args:
        username: The username to authenticate
        password: The password to verify

    Returns:
        Tuple of (success, session_id, error_message)

    Raises:
        ValueError: If username or password is invalid
    """
    try:
        if not username or not password:
            raise ValueError("Username and password are required")

        username = username.strip()
        password = password.strip()

        if not username or not password:
            raise ValueError("Username and password cannot be empty")

        logger.info(f"Attempting authentication for user {username}")

        # Fetch user from database
        row = fetch_one("users", "WHERE username = ?", (username,))

        if not row:
            logger.warning(f"Authentication failed: user {username} not found")
            return False, None, "Invalid username or password"

        # Verify password
        if not check_password_hash(row["password"], password):
            logger.warning(f"Authentication failed: invalid password for user {username}")
            return False, None, "Invalid username or password"

        # Create session
        from api.middleware.session import session_manager
        session_id = session_manager.create_session(username)

        logger.info(f"Authentication successful for user {username}")
        return True, session_id, None

    except ValueError as e:
        logger.error(f"Validation error in authentication: {e}")
        return False, None, str(e)
    except Exception as e:
        logger.error(f"Error during authentication for user {username}: {e}")
        return False, None, "Server error"


def authenticate_admin(password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Authenticate admin user with password.

    Args:
        password: The admin password to verify

    Returns:
        Tuple of (success, session_id, error_message)

    Raises:
        ValueError: If password is invalid
    """
    try:
        if not password:
            raise ValueError("Password is required")

        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            logger.error("Admin password not configured")
            return False, None, "Admin access not configured"

        if password != admin_password:
            logger.warning("Admin authentication failed: invalid password")
            return False, None, "Invalid credentials"

        # Create admin session
        from api.middleware.session import session_manager
        session_id = session_manager.create_session("admin")

        logger.info("Admin authentication successful")
        return True, session_id, None

    except ValueError as e:
        logger.error(f"Validation error in admin authentication: {e}")
        return False, None, str(e)
    except Exception as e:
        logger.error(f"Error during admin authentication: {e}")
        return False, None, "Server error"


def create_user_account(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Create a new user account with proper initialization.

    Args:
        username: The username for the new account
        password: The password for the new account

    Returns:
        Tuple of (success, error_message)

    Raises:
        ValueError: If username or password is invalid
    """
    try:
        if not username or not password:
            raise ValueError("Username and password are required")

        username = username.strip()
        password = password.strip()

        if not username or not password:
            raise ValueError("Username and password cannot be empty")

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        logger.info(f"Creating new user account for {username}")

        # Check if user already exists
        if user_exists(username):
            logger.warning(f"User creation failed: username {username} already exists")
            return False, "Username already exists"

        # Hash password
        hashed_password = generate_password_hash(password)

        # Ensure users table exists
        if not _ensure_users_table():
            return False, "Database initialization failed"

        # Insert new user
        success = insert_row("users", {
            "username": username,
            "password": hashed_password
        })

        if not success:
            logger.error(f"Failed to insert user {username} into database")
            return False, "User could not be created"

        # Initialize topic memory for new user
        try:
            initialize_topic_memory_for_level(username, 0)
            logger.info(f"Initialized topic memory for user {username}")
        except Exception as e:
            logger.warning(f"Failed to initialize topic memory for user {username}: {e}")
            # Don't fail user creation if topic memory fails

        logger.info(f"Successfully created user account for {username}")
        return True, None

    except ValueError as e:
        logger.error(f"Validation error creating user account: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error creating user account for {username}: {e}")
        return False, "Database error"


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


def _ensure_users_table() -> bool:
    """
    Ensure the users table exists in the database.

    Returns:
        True if table exists or was created successfully, False otherwise
    """
    try:
        success = execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        if not success:
            logger.error("Failed to create users table")
            return False

        logger.debug("Users table ensured")
        return True

    except Exception as e:
        logger.error(f"Error ensuring users table: {e}")
        return False


def get_user_statistics(username: str) -> Dict[str, Any]:
    """
    Get authentication-related statistics for a user.

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

        logger.info(f"Getting authentication statistics for user {username}")

        # Get user info
        user_info = fetch_one("users", "WHERE username = ?", (username,))
        if not user_info:
            return {
                "username": username,
                "exists": False,
                "created_at": None,
                "session_active": False
            }

        # Check if user has active session
        from api.middleware.session import session_manager
        # For now, we'll check if the user has any session by trying to get their session info
        # This is a simplified approach - in a real implementation, you'd want to query all sessions for the user
        active_sessions = []  # Placeholder - would need to implement get_active_sessions method

        stats = {
            "username": username,
            "exists": True,
            "created_at": user_info.get("created_at"),
            "session_active": len(active_sessions) > 0,
            "active_sessions": len(active_sessions)
        }

        logger.info(f"Retrieved authentication statistics for user {username}")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting user statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting authentication statistics for user {username}: {e}")
        raise
