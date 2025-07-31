"""
XplorED - Session Management Middleware

This module provides SQLite-backed session management for the API,
following clean architecture principles as outlined in the documentation.

Features:
- Session creation and validation
- User session tracking
- Session cleanup and management
- Database-backed persistence

For detailed architecture information, see: docs/backend_structure.md
"""

import os
import uuid
from typing import Optional
from core.database.connection import execute_query, insert_row, fetch_one, delete_rows
from shared.exceptions import DatabaseError


# === Session Management Class ===
class SessionManager:
    """
    SQLite-backed session manager for user authentication and session tracking.

    Provides methods for creating, validating, and destroying user sessions
    with persistent storage in the database.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the session manager and ensure the sessions table exists.

        Args:
            db_path: Path to the SQLite database file (optional, uses DB_FILE env var if not provided)
        """
        self.db_path = db_path or os.getenv("DB_FILE")
        self._init_session_table()

    def _init_session_table(self) -> None:
        """Create the sessions table if it doesn't exist."""
        try:
            execute_query(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        except Exception as e:
            raise DatabaseError(f"Failed to initialize sessions table: {str(e)}")

    def create_session(self, username: str) -> str:
        """
        Create a new session for the specified user.

        Args:
            username: The username to associate with the session

        Returns:
            str: The generated session ID

        Raises:
            DatabaseError: When session creation fails
        """
        try:
            session_id = str(uuid.uuid4())
            insert_row(
                "sessions",
                {"session_id": session_id, "username": username},
            )
            return session_id
        except Exception as e:
            raise DatabaseError(f"Failed to create session for user {username}: {str(e)}")

    def get_user(self, session_id: str) -> Optional[str]:
        """
        Retrieve the username associated with a session ID.

        Args:
            session_id: The session ID to look up

        Returns:
            Optional[str]: The username if session exists, None otherwise
        """
        if not session_id:
            return None

        try:
            row = fetch_one(
                "sessions",
                "WHERE session_id = ?",
                (session_id,),
                columns="username",
            )
            return row.get("username") if row else None
        except Exception as e:
            raise DatabaseError(f"Failed to retrieve user for session {session_id}: {str(e)}")

    def destroy_session(self, session_id: str) -> None:
        """
        Remove a specific session from the database.

        Args:
            session_id: The session ID to destroy

        Raises:
            DatabaseError: When session destruction fails
        """
        try:
            delete_rows("sessions", "WHERE session_id = ?", (session_id,))
        except Exception as e:
            raise DatabaseError(f"Failed to destroy session {session_id}: {str(e)}")

    def destroy_user_sessions(self, username: str) -> None:
        """
        Remove all sessions belonging to a specific user.

        Args:
            username: The username whose sessions should be destroyed

        Raises:
            DatabaseError: When session destruction fails
        """
        try:
            delete_rows("sessions", "WHERE username = ?", (username,))
        except Exception as e:
            raise DatabaseError(f"Failed to destroy sessions for user {username}: {str(e)}")


# === Global Instance ===
session_manager = SessionManager()


# === Export Configuration ===
__all__ = [
    "SessionManager",
    "session_manager",
]
