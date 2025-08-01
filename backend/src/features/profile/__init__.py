"""
XplorED - Profile Package

This package provides user profile management and customization functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Profile Modules:
- profile_summary: Profile summary and basic profile functions
- profile_achievements: User achievements and activity timeline functions

For detailed architecture information, see: docs/backend_structure.md
"""

from .profile_summary import (
    get_user_profile_summary,
    get_user_game_results,
)

from .profile_achievements import (
    get_user_achievements,
    get_user_activity_timeline,
)

# Re-export all profile functions for backward compatibility
__all__ = [
    # Profile summary
    "get_user_profile_summary",
    "get_user_game_results",

    # Profile achievements
    "get_user_achievements",
    "get_user_activity_timeline",
]
