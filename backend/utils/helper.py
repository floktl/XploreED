from flask import request
from utils.session.session_manager import session_manager
from utils.db_utils import fetch_one


def is_admin():
    """Returns True if the current session user is 'admin'."""
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    return user == "admin"


def user_exists(username):
    """Checks if a user exists in the users table."""
    row = fetch_one("SELECT 1 FROM users WHERE username = ?", (username,))
    return row is not None


def get_current_user():
    """Returns the current logged-in user based on session cookie."""
    session_id = request.cookies.get("session_id")
    return session_manager.get_user(session_id)
