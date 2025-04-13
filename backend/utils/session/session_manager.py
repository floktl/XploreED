# session_manager.py
import uuid
import sqlite3
from ..db_utils import get_connection

class SessionManager:
    def __init__(self, db_path="user_data.db"):
        self.db_path = db_path
        self._init_session_table()

    def _init_session_table(self):
        with get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def create_session(self, username):
        session_id = str(uuid.uuid4())
        with get_connection() as conn:
            conn.execute("INSERT INTO sessions (session_id, username) VALUES (?, ?)", (session_id, username))
        return session_id

    def get_user(self, session_id):
        if not session_id:
            return None
        with get_connection() as conn:
            result = conn.execute("SELECT username FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return result[0] if result else None

    def destroy_session(self, session_id):
        with get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    
    def destroy_user_sessions(self, username):
        with get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE username = ?", (username,))

session_manager = SessionManager()
