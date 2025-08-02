"""
XplorED - Progress Package

This package provides progress tracking functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Progress Modules:
- progress_tracking: Core progress tracking functions
- lesson_progress: Lesson-specific progress functions
- progress_analytics: Progress analytics and trends

For detailed architecture information, see: docs/backend_structure.md
"""

from .progress_tracking import (
    track_lesson_progress,
    track_exercise_progress,
    track_vocabulary_progress,
    track_game_progress,
    reset_user_progress,
)

from .lesson_progress import (
    get_user_lesson_progress,
    update_block_progress,
    mark_lesson_complete,
    check_lesson_completion_status,
    mark_lesson_as_completed,
    reset_lesson_progress,
)

from .progress_analytics import (
    get_user_progress_summary,
    get_progress_trends,
)

# Re-export all progress functions for backward compatibility
__all__ = [
    # Progress tracking
    "track_lesson_progress",
    "track_exercise_progress",
    "track_vocabulary_progress",
    "track_game_progress",
    "reset_user_progress",

    # Lesson progress
    "get_user_lesson_progress",
    "update_block_progress",
    "mark_lesson_complete",
    "check_lesson_completion_status",
    "mark_lesson_as_completed",
    "reset_lesson_progress",

    # Progress analytics
    "get_user_progress_summary",
    "get_progress_trends",
]
