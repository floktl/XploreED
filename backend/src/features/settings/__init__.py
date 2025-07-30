"""
Settings Feature Module

This module contains application and user settings management functionality.

Author: German Class Tool Team
Date: 2025
"""

from .settings_helpers import (
    get_user_settings,
    update_user_settings,
    get_application_settings,
    update_application_settings,
    get_notification_settings,
    update_notification_settings,
    get_privacy_settings,
    update_privacy_settings
)

__all__ = [
    # Settings Helpers
    'get_user_settings',
    'update_user_settings',
    'get_application_settings',
    'update_application_settings',
    'get_notification_settings',
    'update_notification_settings',
    'get_privacy_settings',
    'update_privacy_settings'
]
