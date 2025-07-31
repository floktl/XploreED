"""
XplorED - User Account Management Module

This module provides user account management functions for authentication,
following clean architecture principles as outlined in the documentation.

User Account Components:
- Account Creation: New user registration and initialization
- Account Statistics: User authentication statistics and information
- Database Management: User table creation and maintenance

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional, Tuple

from core.database.connection import insert_row, execute_query, fetch_one
from core.utils.helpers import user_exists
from werkzeug.security import generate_password_hash  # type: ignore
from features.ai.memory.level_manager import initialize_topic_memory_for_level

logger = logging.getLogger(__name__)


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
