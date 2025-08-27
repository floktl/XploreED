"""
Development Auto-Login Module

This module provides automatic login functionality for development mode.
It creates a test user with level 3 and automatically logs them in.
"""

import os
import logging
from datetime import datetime, timedelta
from core.database.connection import select_one, insert_row, update_row
from core.session.session_manager import SessionManager
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)


def setup_dev_test_user():
    """
    Set up the test user for development mode.
    Creates the user if it doesn't exist and sets their level to 3.
    """
    try:
        test_username = os.getenv("TEST_USER", "tester1234")
        test_password = os.getenv("TEST_PWD", "thisisatest")

        # Check if test user exists
        existing_user = select_one(
            "users",
            columns="username, skill_level",
            where="username = ?",
            params=(test_username,)
        )

        if existing_user:
            # Update existing user to level 3 and ensure password is correct
            update_row(
                "users",
                {
                    "skill_level": 3,
                    "password": generate_password_hash(test_password)
                },
                "username = ?",
                (test_username,)
            )
            logger.info(f"✅ Updated existing test user '{test_username}' to level 3")
        else:
            # Create new test user with level 3
            insert_row("users", {
                "username": test_username,
                "password": generate_password_hash(test_password),
                "skill_level": 3,
                "created_at": datetime.now().isoformat()
            })
            logger.info(f"✅ Created new test user '{test_username}' with level 3")

        return test_username

    except Exception as e:
        logger.error(f"❌ Failed to setup test user: {e}")
        return None


def auto_login_dev_user():
    """
    Automatically log in the test user in development mode.
    Returns the session ID if successful, None otherwise.
    """
    try:
        # Only run in development mode
        if os.getenv("FLASK_ENV") != "development":
            return None

        test_username = os.getenv("TEST_USER", "tester1234")

        # Set up the test user
        username = setup_dev_test_user()
        if not username:
            return None

        # Create a session for the test user
        session_manager = SessionManager()
        session_id = session_manager.create_session(username)
        if session_id:
            logger.info(f"✅ Auto-logged in test user '{username}' with session {session_id}")
            return session_id
        else:
            logger.error(f"❌ Failed to create session for test user '{username}'")
            return None

    except Exception as e:
        logger.error(f"❌ Auto-login failed: {e}")
        return None


def get_dev_session_cookie():
    """
    Get the session cookie for development mode.
    Returns the cookie string if successful, None otherwise.
    """
    try:
        session_id = auto_login_dev_user()
        if session_id:
            # Return cookie string for development
            return f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax"
        return None
    except Exception as e:
        logger.error(f"❌ Failed to get dev session cookie: {e}")
        return None
