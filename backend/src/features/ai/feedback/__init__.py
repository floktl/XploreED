"""
XplorED - AI Feedback Package

This package provides AI feedback functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

AI Feedback Components:
- Session Management: Create and manage feedback generation sessions
- Feedback Generation: Generate AI-powered feedback for exercises
- Feedback Processing: Process and evaluate feedback data

For detailed architecture information, see: docs/backend_structure.md
"""

# Import feedback functions from modules
from .feedback_session import (
    create_feedback_session,
    get_feedback_progress,
    update_feedback_progress,
    get_feedback_result,
)

from .feedback_generation import (
    generate_feedback_with_progress,
    generate_ai_feedback_simple,
    get_cached_feedback_list,
    get_cached_feedback_item,
)

# Re-export all AI feedback functions for backward compatibility
__all__ = [
    # Feedback Session
    "create_feedback_session",
    "get_feedback_progress",
    "update_feedback_progress",
    "get_feedback_result",

    # Feedback Generation
    "generate_feedback_with_progress",
    "generate_ai_feedback_simple",
    "get_cached_feedback_list",
    "get_cached_feedback_item",
]
