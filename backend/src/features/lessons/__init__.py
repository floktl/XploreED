"""
Lessons Feature Module

This module contains lesson management and progress tracking functionality.

Author: German Class Tool Team
Date: 2025
"""

from .lesson_helpers import (
    get_lesson_content,
    get_user_lessons,
    create_lesson,
    update_lesson,
    delete_lesson,
    get_lesson_statistics
)

from .lesson_progress_helpers import (
    get_user_lesson_progress,
    update_block_progress,
    mark_lesson_complete,
    check_lesson_completion_status,
    mark_lesson_as_completed,
    get_lesson_progress_summary,
    reset_lesson_progress
)

__all__ = [
    # Lesson Helpers
    'get_lesson_content',
    'get_user_lessons',
    'create_lesson',
    'update_lesson',
    'delete_lesson',
    'get_lesson_statistics',

    # Lesson Progress Helpers
    'get_user_lesson_progress',
    'update_block_progress',
    'mark_lesson_complete',
    'check_lesson_completion_status',
    'mark_lesson_as_completed',
    'get_lesson_progress_summary',
    'reset_lesson_progress'
]
