"""
Authentication Routes

This module contains API routes for user authentication and session management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging

from core.services.import_service import *
from features.auth.auth_helpers import (
    authenticate_user,
    authenticate_admin,
    create_user_account,
    destroy_user_session,
    get_user_session_info,
    validate_session,
    get_user_statistics
)


logger = logging.getLogger(__name__)


@auth_bp.route("/debug-login", methods=["GET"])
def debug_login():
    """
    Simple health check endpoint used during development.

    This endpoint provides a basic health check for the authentication
    system during development and testing.

    Returns:
        JSON response confirming the endpoint is working
    """
    try:
        logger.debug("Debug login endpoint accessed")
        return jsonify({"msg": "working"})

    except Exception as e:
        logger.error(f"Error in debug login endpoint: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute")
def login():
    """
    Authenticate the user and return a session cookie.

    This endpoint validates user credentials and creates a new session
    if authentication is successful. Rate limited to prevent brute force attacks.

    Returns:
        JSON response with login status and session cookie
    """
    try:
        if request.method == "OPTIONS":
            return '', 200

        data = request.get_json() or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        # Authenticate user
        success, session_id, error_message = authenticate_user(username, password)

        if not success:
            return jsonify({"error": error_message}), 401

        # Create response with session cookie
        resp = make_response(jsonify({"msg": "Login successful"}))
        resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")

        logger.info(f"User {username} logged in successfully")
        return resp

    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/admin/login", methods=["POST", "OPTIONS"])
def admin_login():
    """
    Login route for the admin account only.

    This endpoint provides authentication for admin users using
    environment-based password verification.

    Returns:
        JSON response with login status and session cookie
    """
    try:
        if request.method == "OPTIONS":
            return '', 200

        data = request.get_json() or {}
        password = data.get("password", "").strip()

        if not password:
            return jsonify({"error": "Password is required"}), 400

        # Authenticate admin
        success, session_id, error_message = authenticate_admin(password)

        if not success:
            return jsonify({"error": error_message}), 401

        # Create response with session cookie
        resp = make_response(jsonify({"msg": "Login successful"}))
        resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")

        logger.info("Admin logged in successfully")
        return resp

    except Exception as e:
        logger.error(f"Error during admin login: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Destroy the current session and clear the cookie.

    This endpoint invalidates the current user session and removes
    the session cookie from the response.

    Returns:
        JSON response confirming logout success
    """
    try:
        session_id = request.cookies.get("session_id")

        if session_id:
            destroy_user_session(session_id)

        # Create response with cleared cookie
        resp = make_response(jsonify({"msg": "Logout successful"}))
        resp.set_cookie("session_id", "", max_age=0)

        logger.info("User logged out successfully")
        return resp

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    Create a new user account and initialize topic memory.

    This endpoint creates a new user account with proper validation,
    password hashing, and topic memory initialization.

    Returns:
        JSON response with signup status
    """
    try:
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

        # Create user account
        success, error_message = create_user_account(username, password)

        if not success:
            return jsonify({"error": error_message}), 400

        logger.info(f"New user account created for {username}")
        return jsonify({"msg": "User created"}), 201

    except Exception as e:
        logger.error(f"Error during signup: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/session/validate", methods=["GET"])
def validate_current_session():
    """
    Validate the current user session.

    This endpoint checks if the current session is still valid
    and returns session information.

    Returns:
        JSON response with session validation status
    """
    try:
        session_id = request.cookies.get("session_id")

        if not session_id:
            return jsonify({"valid": False, "message": "No session found"}), 401

        # Validate session
        is_valid = validate_session(session_id)

        if not is_valid:
            return jsonify({"valid": False, "message": "Invalid session"}), 401

        # Get session info
        session_info = get_user_session_info(session_id)

        if not session_info:
            return jsonify({"valid": False, "message": "Session info not found"}), 401

        return jsonify({
            "valid": True,
            "session_info": session_info
        })

    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/session/info", methods=["GET"])
def get_session_info():
    """
    Get detailed information about the current session.

    This endpoint returns comprehensive information about the
    current user session including user details.

    Returns:
        JSON response with session information
    """
    try:
        session_id = request.cookies.get("session_id")

        if not session_id:
            return jsonify({"error": "No session found"}), 401

        session_info = get_user_session_info(session_id)

        if not session_info:
            return jsonify({"error": "Invalid session"}), 401

        return jsonify(session_info)

    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return jsonify({"error": "Server error"}), 500


@auth_bp.route("/user/stats", methods=["GET"])
def get_user_auth_stats():
    """
    Get authentication statistics for the current user.

    This endpoint returns authentication-related statistics
    for the currently logged-in user.

    Returns:
        JSON response with user authentication statistics
    """
    try:
        username = require_user()

        stats = get_user_statistics(str(username))
        return jsonify(stats)

    except ValueError as e:
        logger.error(f"Validation error getting user auth stats: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting user auth stats: {e}")
        return jsonify({"error": "Server error"}), 500
