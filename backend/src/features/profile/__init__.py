"""
Profile Feature Module

This module contains user profile management and customization functionality.

Author: German Class Tool Team
Date: 2025
"""

from .profile_helpers import (
    get_user_profile,
    update_user_profile,
    get_profile_statistics,
    get_learning_achievements,
    get_user_preferences,
    update_user_preferences,
    get_profile_analytics
)

__all__ = [
    # Profile Helpers
    'get_user_profile',
    'update_user_profile',
    'get_profile_statistics',
    'get_learning_achievements',
    'get_user_preferences',
    'update_user_preferences',
    'get_profile_analytics'
]
