"""
XplorED - Debug Package

This package provides debugging functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Debug Modules:
- database_debug: Database inspection and schema analysis
- user_debug: User-specific debugging and statistics
- ai_debug: AI-related debugging and evaluation status

For detailed architecture information, see: docs/backend_structure.md
"""

from .database_debug import (
    get_all_database_data,
    get_database_schema,
)

from .user_debug import (
    get_user_statistics,
)

from .ai_debug import (
    debug_user_ai_data,
)

# Re-export all debug functions for backward compatibility
__all__ = [
    # Database debug
    "get_all_database_data",
    "get_database_schema",

    # User debug
    "get_user_statistics",

    # AI debug
    "debug_user_ai_data",
]
