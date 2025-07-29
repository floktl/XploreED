"""Blueprint module that re-exports blueprints from config."""

from config.blueprint import (
    admin_bp,
    auth_bp,
    debug_bp,
    game_bp,
    lesson_progress_bp,
    lessons_bp,
    profile_bp,
    translate_bp,
    user_bp,
    ai_bp,
    support_bp,
    settings_bp,
    progress_test_bp,
    registered_blueprints,
)

__all__ = [
    'admin_bp',
    'auth_bp',
    'debug_bp',
    'game_bp',
    'lesson_progress_bp',
    'lessons_bp',
    'profile_bp',
    'translate_bp',
    'user_bp',
    'ai_bp',
    'support_bp',
    'settings_bp',
    'progress_test_bp',
    'registered_blueprints',
]
