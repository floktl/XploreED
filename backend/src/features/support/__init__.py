"""
Support Feature Module

This module contains help system and user support features functionality.

Author: XplorED Team
Date: 2025
"""

from .support_helpers import (
    submit_feedback,
    get_feedback_list,
    get_feedback_by_id,
    delete_feedback,
    get_feedback_statistics,
    search_feedback,
    get_user_feedback,
    create_support_ticket,
    create_support_request,
    get_system_status,
    get_help_content
)

__all__ = [
    # Support Helpers
    'submit_feedback',
    'get_feedback_list',
    'get_feedback_by_id',
    'delete_feedback',
    'get_feedback_statistics',
    'search_feedback',
    'get_user_feedback',
    'create_support_ticket',
    'create_support_request',
    'get_system_status',
    'get_help_content'
]
