"""
XplorED - Core Authentication Module

This module provides pure business logic for user management operations,
following clean architecture principles as outlined in the documentation.

Authentication Components:
- user_management: Pure business logic for user operations
- User existence validation
- User data retrieval
- Credential validation

For detailed architecture information, see: docs/backend_structure.md
"""

from .user_management import (
    user_exists,
    get_user_by_username,
    is_user_admin,
    validate_user_credentials,
)

__all__ = [
    "user_exists",
    "get_user_by_username",
    "is_user_admin",
    "validate_user_credentials",
]
