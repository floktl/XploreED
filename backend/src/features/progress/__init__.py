"""
Progress Feature Module

This module contains progress tracking functionality.

Author: XplorED Team
Date: 2025
"""

from .progress_tracker import (
    track_lesson_progress,
    get_lesson_progress,
    track_exercise_progress,
    track_vocabulary_progress,
    track_game_progress,
    get_user_progress_summary,
    reset_user_progress,
    get_progress_trends,
    # Lesson Progress Functions (Moved from lessons module)
    get_user_lesson_progress,
    update_block_progress,
    mark_lesson_complete,
    check_lesson_completion_status,
    mark_lesson_as_completed,
    get_lesson_progress_summary,
    reset_lesson_progress
)

__all__ = [
    # Progress Tracking
    'track_lesson_progress',
    'get_lesson_progress',
    'track_exercise_progress',
    'track_vocabulary_progress',
    'track_game_progress',
    'get_user_progress_summary',
    'reset_user_progress',
    'get_progress_trends',

    # Lesson Progress Functions (Moved from lessons module)
    'get_user_lesson_progress',
    'update_block_progress',
    'mark_lesson_complete',
    'check_lesson_completion_status',
    'mark_lesson_as_completed',
    'get_lesson_progress_summary',
    'reset_lesson_progress'
]
