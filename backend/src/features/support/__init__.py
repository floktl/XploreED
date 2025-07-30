"""
Support Feature Module

This module contains help system and user support features functionality.

Author: German Class Tool Team
Date: 2025
"""

from .support_helpers import (
    get_help_topics,
    search_help_content,
    submit_support_ticket,
    get_support_tickets,
    update_support_ticket,
    get_faq_content,
    get_tutorial_content,
    get_contact_information
)

__all__ = [
    # Support Helpers
    'get_help_topics',
    'search_help_content',
    'submit_support_ticket',
    'get_support_tickets',
    'update_support_ticket',
    'get_faq_content',
    'get_tutorial_content',
    'get_contact_information'
]
