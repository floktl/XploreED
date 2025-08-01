"""
XplorED - Core Utilities Module

This module provides core utility functions and helpers for the backend application,
following clean architecture principles as outlined in the documentation.

Utility Components:
- helpers: Authentication and session management utilities
- html_helpers: HTML processing and manipulation functions
- json_helpers: JSON parsing and extraction utilities

For detailed architecture information, see: docs/backend_structure.md
"""

from . import helpers
from . import html_helpers
from . import json_helpers

# Re-export commonly used items for convenience
from .helpers import (
    is_admin,
    user_exists,
    get_current_user,
    require_user,
    run_in_background,
)
from .html_helpers import (
    clean_html,
    update_lesson_blocks_from_html,
    inject_block_ids,
    strip_ai_data,
    ansi_to_html,
)
from .json_helpers import extract_json


# === Export Configuration ===
__all__ = [
    # Module imports
    "helpers",
    "html_helpers",
    "json_helpers",

    # Helper functions
    "is_admin",
    "user_exists",
    "get_current_user",
    "require_user",
    "run_in_background",

    # HTML utilities
    "clean_html",
    "update_lesson_blocks_from_html",
    "inject_block_ids",
    "strip_ai_data",
    "ansi_to_html",

    # JSON utilities
    "extract_json",
]
