# session_manager.py
"""SQLite backed session management for the API."""

import uuid
from database import execute_query, insert_row, fetch_one, delete_rows

class SessionManager:
    def __init__(self, db_path="user_data.db"):
        """Create a new manager and ensure the ``sessions`` table exists."""
        self.db_path = db_path
        self._init_session_table()

    def _init_session_table(self):
        """Create the ``sessions`` table if missing."""
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    def create_session(self, username):
        """Return a new session ID associated with ``username``."""
        session_id = str(uuid.uuid4())
        insert_row(
            "sessions",
            {"session_id": session_id, "username": username},
        )
        return session_id

    def get_user(self, session_id):
        """Return the username stored for ``session_id``."""
        if not session_id:
            return None
        row = fetch_one(
            "sessions",
            "WHERE session_id = ?",
            (session_id,),
            columns="username",
        )
        return row.get("username") if row else None

    def destroy_session(self, session_id):
        """Remove a single session entry from the database."""
        delete_rows("sessions", "WHERE session_id = ?", (session_id,))

    def destroy_user_sessions(self, username):
        """Remove all sessions belonging to ``username``."""
        delete_rows("sessions", "WHERE username = ?", (username,))

session_manager = SessionManager()
