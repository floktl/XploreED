"""
XplorED - Admin Package

This package provides admin functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Admin Modules:
- game_management: Game results and statistics management
- lesson_management: Lesson content and progress management
- user_management: User data and account management

For detailed architecture information, see: docs/backend_structure.md
"""

from .game_management import (
    get_all_game_results,
    get_user_game_results,
)

from .lesson_management import (
    create_lesson_content,
    get_all_lessons,
    get_lesson_by_id,
    update_lesson_content,
    delete_lesson_content,
    get_lesson_progress_summary,
    get_individual_lesson_progress,
)

from .user_management import (
    get_all_users,
    update_user_data,
    delete_user_data,
)

# Re-export all admin functions for backward compatibility
__all__ = [
    # Game management
    "get_all_game_results",
    "get_user_game_results",

    # Lesson management
    "create_lesson_content",
    "get_all_lessons",
    "get_lesson_by_id",
    "update_lesson_content",
    "delete_lesson_content",
    "get_lesson_progress_summary",
    "get_individual_lesson_progress",

    # User management
    "get_all_users",
    "update_user_data",
    "delete_user_data",
]
