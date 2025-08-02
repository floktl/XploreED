"""
XplorED - User Management Utilities

This module provides pure business logic for user management operations,
following clean architecture principles as outlined in the documentation.

User Management Components:
- User existence validation
- User data retrieval
- Pure business logic operations

For detailed architecture information, see: docs/backend_structure.md
"""

from typing import Optional, Dict, Any
from core.database.connection import select_one


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


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user data by username.

    Args:
        username: Username to retrieve data for

    Returns:
        Optional[Dict[str, Any]]: User data if found, None otherwise
    """
    return select_one(
        "users",
        columns="*",
        where="username = ?",
        params=(username,),
    )


def is_user_admin(username: str) -> bool:
    """
    Check if a user has admin privileges.

    Args:
        username: Username to check admin status for

    Returns:
        bool: True if user is admin, False otherwise
    """
    user_data = get_user_by_username(username)
    return user_data.get("is_admin", False) if user_data else False


def validate_user_credentials(username: str, password_hash: str) -> bool:
    """
    Validate user credentials against stored password hash.

    Args:
        username: Username to validate
        password_hash: Password hash to validate against

    Returns:
        bool: True if credentials are valid, False otherwise
    """
    user_data = get_user_by_username(username)
    if not user_data:
        return False

    stored_password = user_data.get("password", "")
    return stored_password == password_hash


__all__ = [
    "user_exists",
    "get_user_by_username",
    "is_user_admin",
    "validate_user_credentials",
]
