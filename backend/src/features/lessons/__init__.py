"""
XplorED - Lessons Package

This package provides lesson management and progress tracking functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Lessons Modules:
- lesson_retrieval: Lesson content and summary retrieval functions
- lesson_progress: Lesson progress tracking and validation functions
- lesson_management: Lesson content management and analytics functions

For detailed architecture information, see: docs/backend_structure.md
"""

from .lesson_retrieval import (
    get_user_lessons_summary,
    get_lesson_content,
    get_lesson_blocks,
    validate_lesson_access,
)

from .lesson_progress import (
    get_lesson_progress,
    update_lesson_progress,
    get_lesson_statistics,
    validate_block_completion,
)

from .lesson_management import (
    update_lesson_content,
    publish_lesson,
    get_lesson_analytics,
)

# Re-export all lessons functions for backward compatibility
__all__ = [
    # Lesson retrieval
    "get_user_lessons_summary",
    "get_lesson_content",
    "get_lesson_blocks",
    "validate_lesson_access",

    # Lesson progress
    "get_lesson_progress",
    "update_lesson_progress",
    "get_lesson_statistics",
    "validate_block_completion",

    # Lesson management
    "update_lesson_content",
    "publish_lesson",
    "get_lesson_analytics",
]
