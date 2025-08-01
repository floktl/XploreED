"""
XplorED - Support Package

This package provides support and help system functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Support Modules:
- feedback_management: Feedback submission and management
- support_tickets: Support ticket and request management
- system_support: System status and help content

For detailed architecture information, see: docs/backend_structure.md
"""

from .feedback_management import (
    submit_feedback,
    get_feedback_list,
    get_feedback_by_id,
    delete_feedback,
    get_feedback_statistics,
    search_feedback,
    get_user_feedback,
)

from .support_tickets import (
    create_support_ticket,
    create_support_request,
    get_support_request,
    update_support_request_status,
    get_user_support_requests,
    get_pending_support_requests,
)

from .system_support import (
    get_system_status,
    get_help_content,
    get_help_topics,
    search_help_content,
)

# Re-export all support functions for backward compatibility
__all__ = [
    # Feedback management
    "submit_feedback",
    "get_feedback_list",
    "get_feedback_by_id",
    "delete_feedback",
    "get_feedback_statistics",
    "search_feedback",
    "get_user_feedback",

    # Support tickets
    "create_support_ticket",
    "create_support_request",
    "get_support_request",
    "update_support_request_status",
    "get_user_support_requests",
    "get_pending_support_requests",

    # System support
    "get_system_status",
    "get_help_content",
    "get_help_topics",
    "search_help_content",
]
