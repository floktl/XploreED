"""
XplorED - User Package

This package provides user management and analytics functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

User Modules:
- user_analytics: Core user analytics and data collection functions
- user_insights: User insights and recommendations functions

For detailed architecture information, see: docs/backend_structure.md
"""

from .user_analytics import (
    create_user_analytics_report,
    UserAnalyticsManager,
    UserAnalyticsData,
)

from .user_insights import (
    generate_learning_insights,
    create_comprehensive_user_report,
)

# Re-export all user functions for backward compatibility
__all__ = [
    # User analytics
    "create_user_analytics_report",
    "UserAnalyticsManager",
    "UserAnalyticsData",

    # User insights
    "generate_learning_insights",
    "create_comprehensive_user_report",
]
