"""Helper utilities for user session management."""

from flask import request, jsonify, abort, make_response  # type: ignore
from utils.session.session_manager import session_manager
from database import select_one
import threading


def is_admin():
    """Returns True if the current session user is 'admin'."""
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    return user == "admin"


def user_exists(username):
    """Checks if a user exists in the users table."""
    row = select_one(
        "users",
        columns="1",
        where="username = ?",
        params=(username,),
    )
    return row is not None


def get_current_user():
    """Returns the current logged-in user based on session cookie."""
    session_id = request.cookies.get("session_id")
    return session_manager.get_user(session_id)


def require_user():
    """Return the current user or abort with a 401 JSON response."""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        abort(make_response(jsonify({"msg": "Unauthorized"}), 401))
    return username


def run_in_background(func, *args, **kwargs):
    """Execute ``func`` asynchronously in a daemon thread."""
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
