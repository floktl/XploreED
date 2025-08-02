"""
XplorED - Authentication Module

This module provides authentication functions for user and admin login,
following clean architecture principles as outlined in the documentation.

Authentication Components:
- User Authentication: Username/password verification and session creation
- Admin Authentication: Admin password verification and session management
- Security: Password hashing and validation

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple

from core.database.connection import fetch_one
from werkzeug.security import check_password_hash  # type: ignore
from shared.exceptions import ValidationError, AuthenticationError

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
            raise ValidationError("Username and password are required")

        username = username.strip()
        password = password.strip()

        if not username or not password:
            raise ValidationError("Username and password cannot be empty")

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
        from core.session import session_manager
        session_id = session_manager.create_session(username)

        logger.info(f"Authentication successful for user {username}")
        return True, session_id, None

    except ValidationError as e:
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
            raise ValidationError("Password is required")

        admin_password = os.getenv("ADMIN_PASSWORD")
        if not admin_password:
            logger.error("Admin password not configured")
            return False, None, "Admin access not configured"

        if password != admin_password:
            logger.warning("Admin authentication failed: invalid password")
            return False, None, "Invalid credentials"

        # Create admin session
        from core.session import session_manager
        session_id = session_manager.create_session("admin")

        logger.info("Admin authentication successful")
        return True, session_id, None

    except ValueError as e:
        logger.error(f"Validation error in admin authentication: {e}")
        return False, None, str(e)
    except Exception as e:
        logger.error(f"Error during admin authentication: {e}")
        return False, None, "Server error"
