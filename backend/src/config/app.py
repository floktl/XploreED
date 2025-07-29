"""Flask application configuration and setup."""

import os
import logging
from pathlib import Path

# Suppress werkzeug info logs except for errors
logging.getLogger('werkzeug').disabled = True

def create_app_config() -> dict:
    """
    Create and return Flask application configuration.

    Returns:
        dict: Flask configuration dictionary
    """
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"

    config = {
        # === JWT Configuration ===
        "JWT_TOKEN_LOCATION": ["cookies"],
        "JWT_ACCESS_COOKIE_NAME": "access_token_cookie",
        "JWT_ACCESS_CSRF_HEADER_NAME": "X-CSRF-TOKEN",
        "JWT_ACCESS_CSRF_FIELD_NAME": "csrf_token",

        # === Session Configuration ===
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
    }

    # === Environment-specific Configuration ===
    if debug_mode:
        # Development mode: relaxed security for local development
        config.update({
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_SECURE": False,
            "JWT_COOKIE_SECURE": False,
            "JWT_COOKIE_CSRF_PROTECT": False,
        })
    else:
        # Production mode: strict security settings
        config.update({
            "SESSION_COOKIE_SAMESITE": "None",
            "SESSION_COOKIE_SECURE": True,
            "JWT_COOKIE_SECURE": os.getenv("JWT_COOKIE_SECURE", "true").lower() == "true",
            "JWT_COOKIE_CSRF_PROTECT": os.getenv("JWT_COOKIE_CSRF_PROTECT", "true").lower() == "true",
        })

    return config
