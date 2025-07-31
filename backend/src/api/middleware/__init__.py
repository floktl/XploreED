"""
XplorED - API Middleware Module

This module provides middleware components for the API layer,
following clean architecture principles as outlined in the documentation.

Components:
- session: Session management and authentication middleware
- Request/response processing and validation
- Error handling and logging middleware

For detailed architecture information, see: docs/backend_structure.md
"""

from . import session

# Re-export commonly used items for convenience
from .session import SessionManager, session_manager

__all__ = [
    # Module imports
    "session",

    # Session management
    "SessionManager",
    "session_manager",
]
