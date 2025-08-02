"""
XplorED - Core Processing Module

This module provides content processing and manipulation utilities for the backend application,
following clean architecture principles as outlined in the documentation.

Processing Components:
- html_processor: HTML content processing and lesson block management
- background: Background processing and async task execution
- Content Cleaning: Remove unwanted HTML elements and styling
- Block Management: Lesson block identification and manipulation
- AI Data Handling: Exercise payload processing and cleanup

For detailed architecture information, see: docs/backend_structure.md
"""

from .html_processor import (
    clean_html,
    extract_block_ids_from_html,
    inject_block_ids,
    strip_ai_data,
    ansi_to_html,
)

from .background import (
    run_in_background,
    run_with_timeout,
)

__all__ = [
    # HTML processing
    "clean_html",
    "extract_block_ids_from_html",
    "inject_block_ids",
    "strip_ai_data",
    "ansi_to_html",

    # Background processing
    "run_in_background",
    "run_with_timeout",
]
