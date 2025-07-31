"""
Authentication Feature Module

This module contains authentication and authorization functionality.

Author: XplorED Team
Date: 2025
"""

from .auth_helpers import (
    authenticate_user,
    authenticate_admin,
    create_user_account,
    destroy_user_session,
    get_user_session_info,
    validate_session,
    get_user_statistics
)

__all__ = [
    # Authentication
    'authenticate_user',
    'authenticate_admin',
    'create_user_account',
    'destroy_user_session',
    'get_user_session_info',
    'validate_session',
    'get_user_statistics'
]
