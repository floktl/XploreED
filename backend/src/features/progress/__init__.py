"""
Progress Feature Module

This module contains progress tracking functionality.

Author: German Class Tool Team
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
    get_progress_trends
)

__all__ = [
    # Progress Tracker
    'track_lesson_progress',
    'get_lesson_progress',
    'track_exercise_progress',
    'track_vocabulary_progress',
    'track_game_progress',
    'get_user_progress_summary',
    'reset_user_progress',
    'get_progress_trends'
]
