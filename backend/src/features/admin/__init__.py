"""
Admin Feature Module

This module contains administrative functions and user management functionality.

Author: German Class Tool Team
Date: 2025
"""

from .admin_helpers import (
    get_all_users,
    get_user_details,
    update_user_role,
    delete_user,
    get_system_statistics,
    get_lesson_progress_summary,
    get_individual_lesson_progress,
    get_admin_dashboard_data,
    manage_system_settings
)

__all__ = [
    # Admin Helpers
    'get_all_users',
    'get_user_details',
    'update_user_role',
    'delete_user',
    'get_system_statistics',
    'get_lesson_progress_summary',
    'get_individual_lesson_progress',
    'get_admin_dashboard_data',
    'manage_system_settings'
]
