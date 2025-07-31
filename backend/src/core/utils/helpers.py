"""
XplorED - Core Utility Helpers

This module provides core utility functions for user session management and authentication,
following clean architecture principles as outlined in the documentation.

Utility Categories:
- Authentication: User session validation and management
- Authorization: Admin privileges and access control
- Background Processing: Asynchronous task execution
- User Management: User existence and current user retrieval

For detailed architecture information, see: docs/backend_structure.md
"""

from flask import request, jsonify, abort, make_response  # type: ignore
from core.database.connection import select_one
import threading
from typing import Optional, Any, Callable


# === Authentication Utilities ===
def is_admin() -> bool:
    """
    Check if the current session user has admin privileges.

    Returns:
        bool: True if current user is 'admin', False otherwise
    """
    from api.middleware.session import session_manager
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    return user == "admin"


def user_exists(username: str) -> bool:
    """
    Check if a user exists in the users table.

    Args:
        username: Username to check for existence

    Returns:
        bool: True if user exists, False otherwise
    """
    row = select_one(
        "users",
        columns="1",
        where="username = ?",
        params=(username,),
    )
    return row is not None


def get_current_user() -> Optional[str]:
    """
    Get the current logged-in user based on session cookie.

    Returns:
        Optional[str]: Current username if authenticated, None otherwise
    """
    from api.middleware.session import session_manager
    session_id = request.cookies.get("session_id")
    return session_manager.get_user(session_id)


def require_user() -> str:
    """
    Get the current user or abort with a 401 Unauthorized response.

    This function ensures that the request is authenticated before proceeding.

    Returns:
        str: Current username if authenticated

    Raises:
        HTTPException: 401 Unauthorized if no valid session found
    """
    from api.middleware.session import session_manager
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        abort(make_response(jsonify({"msg": "Unauthorized"}), 401))
    return username


# === Background Processing Utilities ===
def run_in_background(func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """
    Execute a function asynchronously in a daemon thread.

    This utility allows for non-blocking execution of time-consuming operations
    such as AI processing, database updates, or external API calls.

    Args:
        func: Function to execute in background
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()


# === Export Configuration ===
__all__ = [
    # Authentication utilities
    "is_admin",
    "user_exists",
    "get_current_user",
    "require_user",

    # Background processing
    "run_in_background",
]
