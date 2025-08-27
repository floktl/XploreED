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
    # Skip loading .env file if SKIP_DOTENV is set
    if os.getenv('SKIP_DOTENV', 'false').lower() == 'true':
        return

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
env = os.getenv("FLASK_ENV", os.getenv("ENV", "development")).lower()
default_level = "DEBUG" if env == "development" else "INFO"
log_level = os.getenv("LOG_LEVEL", default_level)
setup_logging(log_level=log_level)

# === Import Flask and Core Dependencies ===
from flask import Flask, jsonify, render_template, request  # type: ignore
from flask_cors import CORS  # type: ignore

# === Import Application Configuration ===
from config.extensions import limiter
from config.blueprint import registered_blueprints
from config.app import create_app_config

# === Import API Routes (Features Layer) ===
# These imports register the blueprints with the application
import api.routes.auth  # noqa: F401
import api.routes.auth_password  # noqa: F401
import api.routes.auth_2fa  # noqa: F401
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

    # === Development Auto-Login Middleware ===
    if os.getenv("FLASK_ENV") == "development":
        from api.middleware.dev_auto_login import dev_auto_login_middleware

        @app.before_request
        def auto_login_dev():
            response = dev_auto_login_middleware()
            if response:
                return response

    # === Register Error Handlers ===
    register_error_handlers(app)

    # === Security Headers ===
    @app.after_request
    def add_security_headers(response):  # type: ignore
        # Basic secure defaults; tune CSP as needed
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if os.getenv("FLASK_ENV", "development") != "development":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    # === Debug Information ===
    if app.debug:
        print_debug_info(app)

    return app

def register_error_handlers(app: Flask) -> None:
    """Register custom error handlers for the application.

    Provides JSON responses for API routes and HTML for others.
    """
    from shared.exceptions import (
        XplorEDException,
        AuthenticationError,
        DatabaseError,
        ValidationError,
        ProcessingError,
    )

    def wants_json() -> bool:
        return request.path.startswith("/api") or request.accept_mimetypes.best == "application/json"

    @app.errorhandler(404)
    def handle_404(_):  # noqa: F841
        if wants_json():
            return jsonify({
                "error": "not_found",
                "message": "The requested resource was not found.",
            }), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def handle_500(e):  # noqa: F841
        if wants_json():
            return jsonify({
                "error": "internal_error",
                "message": "An unexpected error occurred.",
            }), 500
        return render_template("500.html"), 500

    # Map custom exceptions to structured JSON
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(e):  # noqa: F841
        return jsonify({
            "error": "authentication_error",
            "message": str(e) or "Authentication failed",
        }), 401

    @app.errorhandler(DatabaseError)
    def handle_db_error(e):  # noqa: F841
        return jsonify({
            "error": "database_error",
            "message": str(e) or "A database error occurred",
        }), 500

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):  # noqa: F841
        return jsonify({
            "error": "validation_error",
            "message": str(e) or "Invalid input",
        }), 400

    @app.errorhandler(ProcessingError)
    def handle_processing_error(e):  # noqa: F841
        return jsonify({
            "error": "processing_error",
            "message": str(e) or "Processing failed",
        }), 422

    @app.errorhandler(XplorEDException)
    def handle_generic_app_error(e):  # noqa: F841
        return jsonify({
            "error": "application_error",
            "message": str(e) or "Application error",
        }), 400

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
    # Set up auto-login for development mode
    if os.getenv("FLASK_ENV") == "development":
        try:
            from core.development_auto_login import auto_login_dev_user
            session_id = auto_login_dev_user()
            if session_id:
                print(f"🔐 Development auto-login enabled")
                print(f"   Test user: {os.getenv('TEST_USER', 'tester1234')}")
                print(f"   Session ID: {session_id}")
                print(f"   Level: 3")
            else:
                print(f"⚠️  Development auto-login failed")
        except Exception as e:
            print(f"❌ Development auto-login error: {e}")

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
