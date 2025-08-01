# utils/blueprint.py
"""Central definition of all Flask blueprints used by the API."""

from flask import Blueprint # type: ignore

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
auth_bp = Blueprint("auth", __name__, url_prefix="/api")
debug_bp = Blueprint("debug", __name__, url_prefix="/api/debug")
game_bp = Blueprint("game", __name__, url_prefix="/api")
lesson_progress_bp = Blueprint("lesson_progress", __name__, url_prefix="/api")
lessons_bp = Blueprint("lessons", __name__, url_prefix="/api")
profile_bp = Blueprint("profile", __name__, url_prefix="/api")
translate_bp = Blueprint("translate", __name__, url_prefix="/api")
user_bp = Blueprint("user", __name__, url_prefix="/api")
ai_bp = Blueprint("ai", __name__, url_prefix="/api")
support_bp = Blueprint("support", __name__, url_prefix="/api/support")
settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")
progress_test_bp = Blueprint("progress_test", __name__, url_prefix="/api")

# Register all Blueprints manually here
registered_blueprints = [
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
]

