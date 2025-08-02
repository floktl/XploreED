"""
XplorED - Authentication Middleware

This module provides web framework dependent authentication utilities,
following clean architecture principles as outlined in the documentation.

Middleware Components:
- Session-based authentication helpers
- HTTP request/response handling
- Web framework specific authentication logic

For detailed architecture information, see: docs/backend_structure.md
"""

from flask import request, jsonify, abort, make_response  # type: ignore
from typing import Optional
from core.session import session_manager


def is_admin() -> bool:
    """
    Check if the current session user has admin privileges.

    Returns:
        bool: True if current user is 'admin', False otherwise
    """
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    return user == "admin"


def get_current_user() -> Optional[str]:
    """
    Get the current logged-in user based on session cookie.

    Returns:
        Optional[str]: Current username if authenticated, None otherwise
    """
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
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        abort(make_response(jsonify({"msg": "Unauthorized"}), 401))
    return username  # type: ignore


def require_admin() -> str:
    """
    Get the current user and ensure they have admin privileges.

    Returns:
        str: Current username if authenticated and admin

    Raises:
        HTTPException: 401 Unauthorized if no valid session found
        HTTPException: 403 Forbidden if user is not admin
    """
    username = require_user()
    if not is_admin():
        abort(make_response(jsonify({"msg": "Admin access required"}), 403))
    return username


__all__ = [
    "is_admin",
    "get_current_user",
    "require_user",
    "require_admin",
]
