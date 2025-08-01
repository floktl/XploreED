"""
XplorED - Settings Package

This package provides settings and account management functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Settings Modules:
- account_management: Account-related functions (password, deactivation, deletion)
- user_settings: User settings and preferences management
- data_management: Data export/import and statistics

For detailed architecture information, see: docs/backend_structure.md
"""

from .account_management import (
    update_user_password,
    deactivate_user_account,
    debug_delete_user_data,
)

from .user_settings import (
    get_user_settings,
    update_user_settings,
    get_account_statistics,
)

from .data_management import (
    export_user_data,
    import_user_data,
    validate_import_data,
)

# Re-export all settings functions for backward compatibility
__all__ = [
    # Account management
    "update_user_password",
    "deactivate_user_account",
    "debug_delete_user_data",

    # User settings
    "get_user_settings",
    "update_user_settings",
    "get_account_statistics",

    # Data management
    "export_user_data",
    "import_user_data",
    "validate_import_data",
]
