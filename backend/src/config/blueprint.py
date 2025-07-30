"""
German Class Tool - Blueprint Configuration

This module provides centralized Flask blueprint definitions and registration,
following clean architecture principles as outlined in the documentation.

Blueprint Categories:
- Authentication: User login, registration, and session management
- Content Management: Lessons, exercises, and learning materials
- User Management: Profiles, settings, and user data
- AI Integration: AI-powered features and interactions
- Administrative: Admin dashboard and management tools
- Support: Help and feedback systems

For detailed architecture information, see: docs/backend_structure.md
"""

from flask import Blueprint  # type: ignore

# === Authentication Blueprints ===
auth_bp = Blueprint("auth", __name__, url_prefix="/api")

# === Content Management Blueprints ===
lessons_bp = Blueprint("lessons", __name__, url_prefix="/api")
lesson_progress_bp = Blueprint("lesson_progress", __name__, url_prefix="/api")
game_bp = Blueprint("game", __name__, url_prefix="/api")

# === User Management Blueprints ===
profile_bp = Blueprint("profile", __name__, url_prefix="/api")
user_bp = Blueprint("user", __name__, url_prefix="/api")
settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

# === AI Integration Blueprints ===
ai_bp = Blueprint("ai", __name__, url_prefix="/api")

# === Administrative Blueprints ===
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
debug_bp = Blueprint("debug", __name__, url_prefix="/api/debug")

# === Support and Utility Blueprints ===
support_bp = Blueprint("support", __name__, url_prefix="/api/support")
translate_bp = Blueprint("translate", __name__, url_prefix="/api")
progress_test_bp = Blueprint("progress_test", __name__, url_prefix="/api")

# === Blueprint Registration ===
# Register all blueprints in a centralized list for easy management
registered_blueprints = [
    # Authentication
    auth_bp,

    # Content Management
    lessons_bp,
    lesson_progress_bp,
    game_bp,

    # User Management
    profile_bp,
    user_bp,
    settings_bp,

    # AI Integration
    ai_bp,

    # Administrative
    admin_bp,
    debug_bp,

    # Support and Utility
    support_bp,
    translate_bp,
    progress_test_bp,
]


# === Export Configuration ===
__all__ = [
    # Individual blueprints
    "admin_bp",
    "auth_bp",
    "debug_bp",
    "game_bp",
    "lesson_progress_bp",
    "lessons_bp",
    "profile_bp",
    "translate_bp",
    "user_bp",
    "ai_bp",
    "support_bp",
    "settings_bp",
    "progress_test_bp",

    # Registration list
    "registered_blueprints",
]

