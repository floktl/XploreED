"""
XplorED - Authentication API Routes

This module contains API routes for user authentication and session management,
following clean architecture principles as outlined in the documentation.

Route Categories:
- User Authentication: Login, logout, and session management
- User Registration: Account creation and validation
- Password Management: Password reset and change functionality
- Session Management: Session validation and token handling
- Security Features: Two-factor authentication and security controls

Authentication Features:
- Secure user authentication with JWT tokens
- Session management and validation
- Password reset and change functionality
- Two-factor authentication support
- Security controls and access management

Business Logic:
All authentication logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from flask import request, jsonify, make_response # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from pydantic import ValidationError  # type: ignore
import os

from infrastructure.imports import Imports
from core.database.connection import select_one, update_row, insert_row
from api.middleware.auth import get_current_user, require_user, is_admin
from features.auth import (
    authenticate_user,
    authenticate_admin,
    create_user_account,
    destroy_user_session,
    get_user_session_info,
    validate_session,
    get_auth_user_statistics,
)
from config.blueprint import auth_bp
from config.extensions import limiter
from api.schemas import UserRegistrationSchema
from shared.exceptions import DatabaseError, AuthenticationError


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === User Authentication Routes ===

@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login_route():
    """
    Authenticate user and create session.

    This endpoint authenticates a user with their credentials and
    creates a new session with appropriate security tokens.

    Request Body:
        - username (str, required): User's username or email
        - password (str, required): User's password
        - remember_me (bool, optional): Whether to create a long-term session

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "user": {
                "username": str,               # User's username
                "skill_level": str,            # User's skill level
                "is_admin": bool               # Admin status
            },
            "session_id": str                  # Session identifier
        }

    Status Codes:
        - 200: Success
        - 400: Missing required fields
        - 401: Invalid credentials
        - 500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()
        password = data.get("password", "")
        remember_me = data.get("remember_me", False)

        if not username:
            return jsonify({"error": "Username is required"}), 400

        if not password:
            return jsonify({"error": "Password is required"}), 400

        # Authenticate user
        success, session_id, error_message = authenticate_user(username, password)

        if not success:
            # Map specific errors to clearer API responses
            if error_message == "USER_NOT_FOUND":
                return jsonify({
                    "error": "USER_NOT_FOUND",
                    "message": "No user found with that name"
                }), 404
            if error_message == "WRONG_PASSWORD":
                return jsonify({
                    "error": "WRONG_PASSWORD",
                    "message": "Wrong password"
                }), 401
            return jsonify({
                "error": "Invalid credentials",
                "message": error_message or "Authentication failed"
            }), 401

        # Get user data (backward-compatible: handle older schemas without is_admin)
        try:
            user_data = select_one(
                "users",
                columns="username, skill_level, is_admin",
                where="username = ?",
                params=(username,)
            )
        except Exception as e:
            logger.error(f"User select with is_admin failed, retrying without is_admin: {e}")
            user_row_fallback = select_one(
                "users",
                columns="username, skill_level",
                where="username = ?",
                params=(username,)
            )
            if user_row_fallback:
                user_row_fallback["is_admin"] = False
            user_data = user_row_fallback

        if not user_data:
            logger.error(f"User data not found for username: {username}")
            return jsonify({
                "error": "Invalid credentials",
                "message": "Username or password is incorrect"
            }), 401

        # Session is already created in authenticate_user function
        session_result = {"success": True, "session_id": session_id}

        # Set session cookie
        response = jsonify({
            "message": "Login successful",
            "user": {
                "username": user_data.get("username"),
                "skill_level": user_data.get("skill_level"),
                "is_admin": user_data.get("is_admin", False)
            },
            "session_id": session_result.get("session_id")
        })

        # Set secure cookie
        max_age = 30 * 24 * 60 * 60 if remember_me else 24 * 60 * 60  # 30 days or 1 day
        # In development, don't require secure cookies
        is_development = os.getenv("FLASK_ENV", "development") == "development"
        response.set_cookie(
            "session_id",
            session_result.get("session_id"),
            max_age=max_age,
            httponly=True,
            secure=request.is_secure and not is_development,
            samesite="Lax"
        )

        return response

    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout_route():
    """
    Logout user and invalidate session.

    This endpoint logs out the current user and invalidates
    their session token.

    JSON Response Structure:
        {
            "message": str                     # Success message
        }

    Status Codes:
        - 200: Success
        - 401: No active session
        - 500: Internal server error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "No active session"}), 401

        # Get session ID from cookie
        session_id = request.cookies.get("session_id")

        if session_id:
            # Invalidate session
            update_row(
                "sessions",
                {"active": False, "ended_at": datetime.now().isoformat()},
                "WHERE session_id = ?",
                (session_id,)
            )

        # Clear session cookie
        response = jsonify({"message": "Logout successful"})
        is_development = os.getenv("FLASK_ENV", "development") == "development"
        response.set_cookie("session_id", "", max_age=0, httponly=True, secure=request.is_secure and not is_development)

        return response

    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/session", methods=["GET"])
def get_session_route():
    """
    Get current session information.

    This endpoint retrieves information about the current
    user session and validates its status.

    JSON Response Structure:
        {
            "user": str,                        # User identifier
            "session_id": str,                  # Session identifier
            "created_at": str,                  # Session creation timestamp
            "expires_at": str,                  # Session expiration timestamp
            "is_active": bool,                  # Session active status
            "last_activity": str                # Last activity timestamp
        }

    Status Codes:
        - 200: Success
        - 401: No active session
        - 500: Internal server error
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({"error": "No active session"}), 401

        # Get session details
        session_id = request.cookies.get("session_id")
        session_info = None

        if session_id:
            session_info = select_one(
                "sessions",
                columns="session_id, username, created_at",
                where="session_id = ?",
                params=(session_id,)
            )

        if not session_info:
            return jsonify({"error": "Invalid session"}), 401

        return jsonify({
            "user": user,
            "session_id": session_info.get("session_id"),
            "created_at": session_info.get("created_at"),
            "is_active": True  # Sessions are active if they exist
        })

    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({"error": "Failed to get session information"}), 500


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("3 per minute")
def register_route():
    """
    Register a new user account.

    This endpoint creates a new user account with the provided
    registration information.

    Request Body:
        - username (str, required): Unique username
        - email (str, required): Valid email address
        - password (str, required): Secure password
        - confirm_password (str, required): Password confirmation
        - skill_level (str, optional): Initial skill level

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "user": {
                "username": str,               # Created username
                "email": str,                  # User email
                "skill_level": str,            # Skill level
                "created_at": str              # Account creation timestamp
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or validation error
        - 409: Username or email already exists
        - 500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate registration data
        try:
            registration_data = UserRegistrationSchema(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.errors()}), 400

        # Check if username already exists
        existing_user = select_one(
            "users",
            columns="username",
            where="username = ?",
            params=(registration_data.username,)
        )

        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        # Check if email already exists
        existing_email = select_one(
            "users",
            columns="email",
            where="email = ?",
            params=(registration_data.email,)
        )

        if existing_email:
            return jsonify({"error": "Email already exists"}), 409

        # Create user account
        success, error_message = create_user_account(
            registration_data.username,
            registration_data.password,
            email=registration_data.email,
            skill_level=registration_data.skill_level
        )

        if not success:
            return jsonify({"error": "Failed to create account", "message": error_message}), 500

        return jsonify({
            "message": "Account created successfully",
            "user": {
                "username": registration_data.username,
                "email": registration_data.email,
                "skill_level": registration_data.skill_level,
                "created_at": datetime.now().isoformat()
            }
        })

    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/register/validate", methods=["POST"])
def validate_registration_route():
    """
    Validate registration data before account creation.

    This endpoint validates registration information without
    creating an account, useful for real-time validation.

    Request Body:
        - username (str, required): Username to validate
        - email (str, required): Email to validate
        - password (str, required): Password to validate

    JSON Response Structure:
        {
            "valid": bool,                     # Overall validation status
            "username": {
                "valid": bool,                 # Username validity
                "available": bool,             # Username availability
                "errors": [str]                # Username errors
            },
            "email": {
                "valid": bool,                 # Email validity
                "available": bool,             # Email availability
                "errors": [str]                # Email errors
            },
            "password": {
                "valid": bool,                 # Password validity
                "strength": str,               # Password strength level
                "errors": [str]                # Password errors
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        validation_result = {
            "valid": True,
            "username": {"valid": True, "available": True, "errors": []},
            "email": {"valid": True, "available": True, "errors": []},
            "password": {"valid": True, "strength": "weak", "errors": []}
        }

        # Validate username
        if not username:
            validation_result["username"]["valid"] = False
            validation_result["username"]["errors"].append("Username is required")
        elif len(username) < 3:
            validation_result["username"]["valid"] = False
            validation_result["username"]["errors"].append("Username must be at least 3 characters")
        elif len(username) > 20:
            validation_result["username"]["valid"] = False
            validation_result["username"]["errors"].append("Username must be less than 20 characters")

        # Check username availability
        if username:
            existing_user = select_one(
                "users",
                columns="username",
                where="username = ?",
                params=(username,)
            )
            if existing_user:
                validation_result["username"]["available"] = False
                validation_result["username"]["errors"].append("Username already exists")

        # Validate email
        if not email:
            validation_result["email"]["valid"] = False
            validation_result["email"]["errors"].append("Email is required")
        elif "@" not in email or "." not in email:
            validation_result["email"]["valid"] = False
            validation_result["email"]["errors"].append("Invalid email format")

        # Check email availability
        if email:
            existing_email = select_one(
                "users",
                columns="email",
                where="email = ?",
                params=(email,)
            )
            if existing_email:
                validation_result["email"]["available"] = False
                validation_result["email"]["errors"].append("Email already exists")

        # Validate password
        if not password:
            validation_result["password"]["valid"] = False
            validation_result["password"]["errors"].append("Password is required")
        elif len(password) < 8:
            validation_result["password"]["valid"] = False
            validation_result["password"]["errors"].append("Password must be at least 8 characters")
        else:
            # Check password strength
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

            if has_upper and has_lower and has_digit and has_special:
                validation_result["password"]["strength"] = "strong"
            elif (has_upper and has_lower and has_digit) or (has_upper and has_lower and has_special):
                validation_result["password"]["strength"] = "medium"
            else:
                validation_result["password"]["strength"] = "weak"
                validation_result["password"]["errors"].append("Password should include uppercase, lowercase, numbers, and special characters")

        # Set overall validity
        validation_result["valid"] = (
            validation_result["username"]["valid"] and
            validation_result["email"]["valid"] and
            validation_result["password"]["valid"] and
            validation_result["username"]["available"] and
            validation_result["email"]["available"]
        )

        return jsonify(validation_result)

    except Exception as e:
        logger.error(f"Error in registration validation: {e}")
        return jsonify({"error": "Validation failed"}), 500



