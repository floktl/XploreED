"""
XplorED - Core Session Module

This module provides core session management functionality,
following clean architecture principles as outlined in the documentation.

Session Components:
- session_manager: Core session management functionality

For detailed architecture information, see: docs/backend_structure.md
"""

from .session_manager import SessionManager, session_manager

__all__ = [
    "SessionManager",
    "session_manager",
]
