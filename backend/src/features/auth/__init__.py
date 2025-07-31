"""
XplorED - Authentication Package

This package provides authentication functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Authentication Modules:
- authentication: User and admin authentication functions
- session_management: Session handling and validation
- user_accounts: User account creation and management

For detailed architecture information, see: docs/backend_structure.md
"""

from .authentication import (
    authenticate_user,
    authenticate_admin,
)

from .session_management import (
    destroy_user_session,
    get_user_session_info,
    validate_session,
)

from .user_accounts import (
    create_user_account,
    get_user_statistics,
)

# Re-export all auth functions for backward compatibility
__all__ = [
    # Authentication
    "authenticate_user",
    "authenticate_admin",

    # Session management
    "destroy_user_session",
    "get_user_session_info",
    "validate_session",

    # User accounts
    "create_user_account",
    "get_user_statistics",
]
