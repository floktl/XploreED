"""
Lessons Feature Module

This module contains lesson management functionality.

Author: XplorED Team
Date: 2025
"""

from .lesson_helpers import (
    get_lesson_content,
    get_user_lessons_summary,
    get_lesson_progress,
    update_lesson_progress,
    get_lesson_statistics,
    validate_lesson_access,
    validate_block_completion,
    get_lesson_blocks,
    update_lesson_content,
    publish_lesson,
    get_lesson_analytics
)

__all__ = [
    # Lesson Helpers
    'get_lesson_content',
    'get_user_lessons_summary',
    'get_lesson_progress',
    'update_lesson_progress',
    'get_lesson_statistics',
    'validate_lesson_access',
    'validate_block_completion',
    'get_lesson_blocks',
    'update_lesson_content',
    'publish_lesson',
    'get_lesson_analytics'
]
