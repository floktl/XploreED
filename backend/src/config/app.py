"""
XplorED - Flask Application Configuration

This module provides Flask application configuration management,
following clean architecture principles as outlined in the documentation.

Configuration Categories:
- JWT Configuration: Token handling and security settings
- Session Configuration: Cookie and session management
- Environment-specific Settings: Development vs production modes

For detailed architecture information, see: docs/backend_structure.md
"""

import os
import logging
from pathlib import Path

# === Logging Configuration ===
# Suppress werkzeug info logs except for errors
logging.getLogger('werkzeug').disabled = True


def create_app_config() -> dict:
    """
    Create and return Flask application configuration dictionary.

    This function centralizes all Flask configuration settings,
    providing environment-specific behavior for development and production.

    Configuration includes:
    - JWT token handling and security
    - Session cookie settings
    - Environment-specific security policies
    - Database and external service settings

    Returns:
        dict: Complete Flask configuration dictionary

    Environment Variables Used:
        FLASK_ENV: Determines debug mode (development/production)
        SECRET_KEY: Application secret key for security
        JWT_COOKIE_SECURE: Enable secure cookies in production
        JWT_COOKIE_CSRF_PROTECT: Enable CSRF protection in production
    """
    # === Environment Detection ===
    debug_mode = os.getenv("FLASK_ENV", "development") == "development"

    # === Base Configuration ===
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
        # === Development Mode Configuration ===
        # Relaxed security for local development and testing
        config.update({
            "SESSION_COOKIE_SAMESITE": "Lax",
            "SESSION_COOKIE_SECURE": False,
            "JWT_COOKIE_SECURE": False,
            "JWT_COOKIE_CSRF_PROTECT": False,
        })
    else:
        # === Production Mode Configuration ===
        # Strict security settings for production deployment
        config.update({
            "SESSION_COOKIE_SAMESITE": "None",
            "SESSION_COOKIE_SECURE": True,
            "JWT_COOKIE_SECURE": True,
            "JWT_COOKIE_CSRF_PROTECT": True,
        })

    return config


# === Export Configuration ===
__all__ = [
    "create_app_config",
]
