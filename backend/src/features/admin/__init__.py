"""
Admin Feature Module

This module contains administrative functions and user management functionality.

Author: XplorED Team
Date: 2025
"""

from .admin_helpers import (
    get_all_game_results,
    get_user_game_results,
    create_lesson_content,
    get_all_lessons,
    get_lesson_by_id,
    update_lesson_content,
    delete_lesson_content,
    get_lesson_progress_summary,
    get_individual_lesson_progress,
    get_all_users,
    update_user_data,
    delete_user_data
)

__all__ = [
    # Admin Helpers
    'get_all_game_results',
    'get_user_game_results',
    'create_lesson_content',
    'get_all_lessons',
    'get_lesson_by_id',
    'update_lesson_content',
    'delete_lesson_content',
    'get_lesson_progress_summary',
    'get_individual_lesson_progress',
    'get_all_users',
    'update_user_data',
    'delete_user_data'
]
