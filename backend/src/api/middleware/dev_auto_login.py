"""
Development Auto-Login Middleware

This middleware automatically logs in the test user in development mode
by setting the session cookie for all requests.
"""

import os
import logging
from flask import request, make_response
from core.development_auto_login import get_dev_session_cookie

logger = logging.getLogger(__name__)


def dev_auto_login_middleware():
    """
    Middleware function that automatically sets the session cookie
    for the test user in development mode.
    """
    # Only run in development mode
    if os.getenv("FLASK_ENV") != "development":
        return None

    # Skip for API routes that don't need authentication
    skip_paths = ["/api/health", "/api/status"]
    if any(request.path.startswith(path) for path in skip_paths):
        return None

    # Check if session cookie is already set
    if request.cookies.get("session_id"):
        return None

    try:
        # Get the development session cookie
        session_cookie = get_dev_session_cookie()
        if session_cookie:
            # Create a response with the session cookie
            response = make_response()
            response.set_cookie(
                "session_id",
                session_cookie.split("session_id=")[1].split(";")[0],
                max_age=24 * 60 * 60,  # 1 day
                httponly=True,
                secure=False,  # False for development
                samesite="Lax"
            )
            logger.debug(f"🔐 Auto-set session cookie for development")
            return response
    except Exception as e:
        logger.error(f"❌ Development auto-login middleware error: {e}")

    return None
