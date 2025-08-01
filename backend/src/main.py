"""
XplorED - Backend Application Entry Point

This module serves as the main entry point for the Flask application,
following clean architecture principles as outlined in the documentation.

Architecture Layers:
- API Layer: HTTP endpoints and request handling
- Features Layer: Business logic organized by domain
- Core Layer: Database, services, and utilities
- External Layer: Third-party integrations
- Shared Layer: Constants, exceptions, and types

For detailed architecture information, see: docs/backend_structure.md
"""

import os
import sys
from pathlib import Path
from typing import List

# === Environment Configuration ===
def load_environment() -> None:
    """Load environment variables from .env file."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        def load_dotenv(dotenv_path=None, **_):  # type: ignore
            """Fallback environment loader if python-dotenv is not available."""
            if dotenv_path and os.path.exists(dotenv_path):
                with open(dotenv_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ.setdefault(key, value)

    # Load from secrets directory first, then fallback to root
    env_paths = [
        Path(__file__).resolve().parent / 'secrets' / '.env',
        Path(__file__).resolve().parent.parent / '.env'
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=str(env_path))
            break

# Load environment variables early
load_environment()

# === Setup Logging ===
from config.logging_config import setup_logging

# Configure logging with environment-based settings
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level=log_level)

# === Import Flask and Core Dependencies ===
from flask import Flask, jsonify, render_template  # type: ignore
from flask_cors import CORS  # type: ignore

# === Import Application Configuration ===
from config.extensions import limiter
from config.blueprint import registered_blueprints
from config import create_app_config

# === Import API Routes (Features Layer) ===
# These imports register the blueprints with the application
import api.routes.auth  # noqa: F401
import api.routes.admin  # noqa: F401
import api.routes.debug  # noqa: F401
import api.routes.game  # noqa: F401
import api.routes.lesson_progress  # noqa: F401
import api.routes.lessons  # noqa: F401
import api.routes.profile  # noqa: F401
import api.routes.translate  # noqa: F401
import api.routes.user  # noqa: F401
import api.routes.ai  # noqa: F401
import api.routes.support  # noqa: F401
import api.routes.settings  # noqa: F401

def create_app() -> Flask:
    """
    Application factory following Flask best practices.

    Creates and configures the Flask application with all necessary
    extensions, blueprints, and middleware.

    Returns:
        Flask: Configured Flask application instance
    """
    # === Create Flask Application ===
    template_dir = Path(__file__).parent / 'api' / 'templates'
    app = Flask(__name__, template_folder=str(template_dir))

    # === Apply Configuration ===
    app_config = create_app_config()
    app.config.update(app_config)

    # === Register Extensions ===
    # Rate limiting
    limiter.init_app(app)

    # === Register Blueprints (API Layer) ===
    for blueprint in registered_blueprints:
        app.register_blueprint(blueprint)

    # === Configure CORS (External Layer) ===
    allowed_origins = os.getenv("FRONTEND_URL", "").split(",")
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # === Register Error Handlers ===
    register_error_handlers(app)

    # === Debug Information ===
    if app.debug:
        print_debug_info(app)

    return app

def register_error_handlers(app: Flask) -> None:
    """Register custom error handlers for the application."""

    @app.errorhandler(500)
    def server_error(_):  # noqa: F841
        """Return custom 500 error page."""
        return render_template("500.html"), 500

    @app.errorhandler(404)
    def not_found(_):  # noqa: F841
        """Return custom 404 error page."""
        return render_template("404.html"), 404

def print_debug_info(app: Flask) -> None:
    """Print debug information about registered blueprints and routes."""
    print("\n🔍 Registered Blueprints:", file=sys.stderr, flush=True)
    for name, bp in app.blueprints.items():
        print(f"  - {name}: {bp.url_prefix}", file=sys.stderr, flush=True)

    print("\n🔍 Registered Routes:", file=sys.stderr, flush=True)
    for rule in app.url_map.iter_rules():
        methods = ",".join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  - {rule.rule} [{methods}] → {rule.endpoint}", file=sys.stderr, flush=True)

def get_environment_info() -> dict:
    """Get current environment configuration information."""
    return {
        "environment": os.getenv("FLASK_ENV", "development"),
        "debug_mode": os.getenv("FLASK_ENV", "development") == "development",
        "port": int(os.getenv("PORT", 5050)),
        "frontend_url": os.getenv("FRONTEND_URL", ""),
        "jwt_secure": os.getenv("JWT_COOKIE_SECURE", "false").lower() == "true",
        "jwt_csrf": os.getenv("JWT_COOKIE_CSRF_PROTECT", "false").lower() == "true"
    }

# === Application Instance ===
app = create_app()

# === Main Entry Point ===
if __name__ == "__main__":
    env_info = get_environment_info()
    port = env_info["port"]
    debug_mode = env_info["debug_mode"]

    print(f"🚀 Starting XplorED Backend...")
    print(f"   Environment: {env_info['environment']}")
    print(f"   Debug Mode: {debug_mode}")
    print(f"   Port: {port}")
    print(f"   Frontend URL: {env_info['frontend_url']}")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode
    )
