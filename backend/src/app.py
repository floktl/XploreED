"""
XplorED - Backend Application Module

This module provides backward compatibility for the Flask application.
It imports the configured app from main.py to maintain existing deployment
and import patterns.

For new code, prefer importing directly from main.py:
    from main import app

For detailed architecture information, see: docs/backend_structure.md
"""

# Import the configured Flask application from main.py
from main import app

# Export the app for backward compatibility
__all__ = ['app']
