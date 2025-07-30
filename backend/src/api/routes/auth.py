"""
German Class Tool - Authentication API Routes

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
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from flask import request, jsonify, make_response # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

from core.services.import_service import *
from core.database.connection import select_one, update_row, insert_row
from core.utils.helpers import get_current_user, require_user, is_admin
from api.middleware.session import session_manager
from features.auth.auth_helpers import (
    authenticate_user,
    validate_session
)
from config.blueprint import auth_bp


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === User Authentication Routes ===
@auth_bp.route("/login", methods=["POST"])
def login_route():
    """
    Authenticate user and create session.

    This endpoint authenticates a user with their credentials and
    creates a new session with appropriate security tokens.

    Request Body:
        - username: User's username or email
        - password: User's password
        - remember_me: Whether to create a long-term session

    Returns:
        JSON response with authentication status and session tokens
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
            return jsonify({
                "error": "Invalid credentials",
                "message": error_message or "Authentication failed"
            }), 401

        # Get user data
        user_data = select_one(
            "users",
            columns="username, skill_level, is_admin",
            where="username = ?",
            params=(username,)
        )

        if not user_data:
            return jsonify({"error": "User data not found"}), 500

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
        response.set_cookie(
            "session_id",
            session_result.get("session_id"),
            max_age=max_age,
            httponly=True,
            secure=request.is_secure,
            samesite="Lax"
        )

        return response

    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({"error": "Authentication failed"}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout_route():
    """
    Logout user and invalidate session.

    This endpoint logs out the current user and invalidates
    their session token.

    Returns:
        JSON response with logout status or unauthorized error
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
        response.set_cookie("session_id", "", max_age=0, httponly=True, secure=request.is_secure)

        return response

    except Exception as e:
        logger.error(f"Error in logout: {e}")
        return jsonify({"error": "Logout failed"}), 500


@auth_bp.route("/session", methods=["GET"])
def get_session_route():
    """
    Get current session information.

    This endpoint retrieves information about the current
    user session and validates its status.

    Returns:
        JSON response with session information or unauthorized error
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
                columns="session_id, created_at, last_activity, ip_address, user_agent",
                where="session_id = ? AND active = 1",
                params=(session_id,)
            )

        return jsonify({
            "authenticated": True,
            "user": {
                "username": user,
                "is_admin": is_admin()
            },
            "session": session_info,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({"error": "Failed to retrieve session information"}), 500


# === User Registration Routes ===
@auth_bp.route("/register", methods=["POST"])
def register_route():
    """
    Register a new user account.

    This endpoint creates a new user account with the provided
    credentials and initializes their profile.

    Request Body:
        - username: Desired username
        - password: User password
        - email: User email address (optional)
        - skill_level: Initial skill level (optional)

    Returns:
        JSON response with registration status or error details
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()
        password = data.get("password", "")
        email = data.get("email", "").strip()
        skill_level = data.get("skill_level", 1)

        # Validate input
        if not username:
            return jsonify({"error": "Username is required"}), 400

        if len(username) < 3 or len(username) > 20:
            return jsonify({"error": "Username must be between 3 and 20 characters"}), 400

        if not password:
            return jsonify({"error": "Password is required"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Validate skill level
        if not isinstance(skill_level, int) or skill_level < 1 or skill_level > 10:
            return jsonify({"error": "Skill level must be between 1 and 10"}), 400

        # Check if username already exists
        existing_user = select_one(
            "users",
            columns="username",
            where="username = ?",
            params=(username,)
        )

        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        # Create user account
        user_data = {
            "username": username,
            "password": generate_password_hash(password),  # Hash the password
            "email": email if email else None,
            "skill_level": skill_level,
            "created_at": datetime.now().isoformat(),
            "is_admin": False
        }

        success = insert_row("users", user_data)

        if success:
            return jsonify({
                "message": "Registration successful",
                "username": username
            })
        else:
            return jsonify({"error": "Failed to create user account"}), 500

    except Exception as e:
        logger.error(f"Error in registration: {e}")
        return jsonify({"error": "Registration failed"}), 500


@auth_bp.route("/register/validate", methods=["POST"])
def validate_registration_route():
    """
    Validate registration data before creating account.

    This endpoint validates registration data to ensure it meets
    requirements before creating the actual account.

    Request Body:
        - username: Desired username
        - email: User email address (optional)

    Returns:
        JSON response with validation results
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()

        validation_results = {
            "username_valid": False,
            "email_valid": False,
            "username_available": False,
            "email_available": False,
            "errors": []
        }

        # Validate username
        if username:
            if len(username) >= 3 and len(username) <= 20:
                validation_results["username_valid"] = True

                # Check username availability
                existing_user = select_one(
                    "users",
                    columns="username",
                    where="username = ?",
                    params=(username,)
                )

                if not existing_user:
                    validation_results["username_available"] = True
                else:
                    validation_results["errors"].append("Username already exists")
            else:
                validation_results["errors"].append("Username must be between 3 and 20 characters")
        else:
            validation_results["errors"].append("Username is required")

        # Validate email (if provided)
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, email):
                validation_results["email_valid"] = True

                # Check email availability
                existing_email = select_one(
                    "users",
                    columns="email",
                    where="email = ?",
                    params=(email,)
                )

                if not existing_email:
                    validation_results["email_available"] = True
                else:
                    validation_results["errors"].append("Email already registered")
            else:
                validation_results["errors"].append("Invalid email format")

        return jsonify({
            "validation_results": validation_results,
            "is_valid": len(validation_results["errors"]) == 0
        })

    except Exception as e:
        logger.error(f"Error in registration validation: {e}")
        return jsonify({"error": "Validation failed"}), 500


# === Password Management Routes ===
@auth_bp.route("/password/reset", methods=["POST"])
def reset_password_route():
    """
    Request password reset for user account.

    This endpoint initiates a password reset process for the
    specified user account.

    Request Body:
        - username: Username or email of the account

    Returns:
        JSON response with reset status or error details
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        username = data.get("username", "").strip()

        if not username:
            return jsonify({"error": "Username is required"}), 400

        # Check if user exists
        user = select_one(
            "users",
            columns="username, email",
            where="username = ? OR email = ?",
            params=(username, username)
        )

        if not user:
            # Don't reveal if user exists or not for security
            return jsonify({
                "message": "If the account exists, a password reset email has been sent"
            })

        # Generate reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)
        reset_expires = (datetime.now() + timedelta(hours=24)).isoformat()

        # Store reset token
        reset_data = {
            "username": user.get("username"),
            "reset_token": reset_token,
            "expires_at": reset_expires,
            "created_at": datetime.now().isoformat()
        }

        insert_row("password_resets", reset_data)

        # In a real application, send email with reset link
        # For now, just return the token (in production, this would be sent via email)
        return jsonify({
            "message": "Password reset initiated",
            "reset_token": reset_token,  # Remove this in production
            "expires_at": reset_expires
        })

    except Exception as e:
        logger.error(f"Error in password reset: {e}")
        return jsonify({"error": "Password reset failed"}), 500


@auth_bp.route("/password/reset/confirm", methods=["POST"])
def confirm_password_reset_route():
    """
    Confirm password reset with token and new password.

    This endpoint confirms a password reset using the provided
    token and sets the new password.

    Request Body:
        - reset_token: Password reset token
        - new_password: New password

    Returns:
        JSON response with reset confirmation status
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        reset_token = data.get("reset_token", "").strip()
        new_password = data.get("new_password", "")

        if not reset_token:
            return jsonify({"error": "Reset token is required"}), 400

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Validate reset token
        reset_record = select_one(
            "password_resets",
            columns="username, expires_at",
            where="reset_token = ? AND used = 0",
            params=(reset_token,)
        )

        if not reset_record:
            return jsonify({"error": "Invalid or expired reset token"}), 400

        # Check if token has expired
        expires_at_str = reset_record.get("expires_at")
        if not expires_at_str:
            return jsonify({"error": "Invalid reset token"}), 400
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() > expires_at:
            return jsonify({"error": "Reset token has expired"}), 400

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update user password
        success = update_row(
            "users",
            {"password": hashed_password},
            "WHERE username = ?",
            (reset_record.get("username"),)
        )

        # Mark reset token as used
        if success:
            update_row(
                "password_resets",
                {"used": True, "used_at": datetime.now().isoformat()},
                "WHERE reset_token = ?",
                (reset_token,)
            )

        if success:
            return jsonify({"message": "Password reset successful"})
        else:
            return jsonify({"error": "Failed to reset password"}), 500

    except Exception as e:
        logger.error(f"Error in password reset confirmation: {e}")
        return jsonify({"error": "Password reset confirmation failed"}), 500


@auth_bp.route("/password/change", methods=["POST"])
def change_password_route():
    """
    Change user password (requires current password).

    This endpoint allows authenticated users to change their
    password by providing their current password.

    Request Body:
        - current_password: Current password
        - new_password: New password

    Returns:
        JSON response with password change status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not current_password:
            return jsonify({"error": "Current password is required"}), 400

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400

        # Change password
        # Verify current password first
        user_data = select_one("users", columns="password", where="username = ?", params=(user,))
        if not user_data or not check_password_hash(user_data.get("password", ""), current_password):
            return jsonify({"error": "Current password is incorrect"}), 401

        # Hash and update new password
        hashed_password = generate_password_hash(new_password)
        success = update_row("users", {"password": hashed_password}, "WHERE username = ?", (user,))

        if success:
            return jsonify({"message": "Password changed successfully"})
        else:
            return jsonify({"error": "Failed to change password"}), 500

    except Exception as e:
        logger.error(f"Error in password change: {e}")
        return jsonify({"error": "Password change failed"}), 500


# === Security Features Routes ===
@auth_bp.route("/2fa/enable", methods=["POST"])
def enable_2fa_route():
    """
    Enable two-factor authentication for user account.

    This endpoint enables 2FA for the current user account
    and generates the necessary setup information.

    Returns:
        JSON response with 2FA setup information or error details
    """
    try:
        user = require_user()
        data = request.get_json() or {}
        method = data.get("method", "totp")  # Time-based One-Time Password

        # Validate method
        valid_methods = ["totp", "sms", "email"]
        if method not in valid_methods:
            return jsonify({"error": f"Invalid 2FA method: {method}"}), 400

        # Generate 2FA setup data
        import secrets
        import base64

        # Generate secret key for TOTP
        secret_key = base64.b32encode(secrets.token_bytes(20)).decode('utf-8')

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]

        # Store 2FA setup data
        twofa_data = {
            "username": user,
            "method": method,
            "secret_key": secret_key,
            "backup_codes": ",".join(backup_codes),
            "enabled": False,  # Will be enabled after verification
            "created_at": datetime.now().isoformat()
        }

        # Check if 2FA already exists
        existing_2fa = select_one(
            "two_factor_auth",
            columns="id",
            where="username = ?",
            params=(user,)
        )

        if existing_2fa:
            # Update existing 2FA
            update_row(
                "two_factor_auth",
                twofa_data,
                "WHERE username = ?",
                (user,)
            )
        else:
            # Create new 2FA
            insert_row("two_factor_auth", twofa_data)

        return jsonify({
            "message": "2FA setup initiated",
            "method": method,
            "secret_key": secret_key,
            "backup_codes": backup_codes,
            "qr_code_url": f"otpauth://totp/GermanClassTool:{user}?secret={secret_key}&issuer=GermanClassTool"
        })

    except Exception as e:
        logger.error(f"Error enabling 2FA: {e}")
        return jsonify({"error": "Failed to enable 2FA"}), 500


@auth_bp.route("/2fa/verify", methods=["POST"])
def verify_2fa_route():
    """
    Verify two-factor authentication setup.

    This endpoint verifies the 2FA setup by validating the
    provided code and enabling 2FA for the account.

    Request Body:
        - code: 2FA verification code
        - backup_code: Backup code (alternative to regular code)

    Returns:
        JSON response with verification status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        code = data.get("code", "").strip()
        backup_code = data.get("backup_code", "").strip()

        if not code and not backup_code:
            return jsonify({"error": "Verification code is required"}), 400

        # Get 2FA setup data
        twofa_data = select_one(
            "two_factor_auth",
            columns="*",
            where="username = ? AND enabled = 0",
            params=(user,)
        )

        if not twofa_data:
            return jsonify({"error": "No pending 2FA setup found"}), 400

        # Verify code
        if backup_code:
            # Verify backup code
            backup_codes = twofa_data.get("backup_codes", "").split(",")
            if backup_code in backup_codes:
                # Remove used backup code
                backup_codes.remove(backup_code)
                update_row(
                    "two_factor_auth",
                    {"backup_codes": ",".join(backup_codes)},
                    "WHERE username = ?",
                    (user,)
                )
                verification_success = True
            else:
                verification_success = False
        else:
            # Verify TOTP code
            import pyotp # type: ignore
            totp = pyotp.TOTP(twofa_data.get("secret_key"))
            verification_success = totp.verify(code)

        if verification_success:
            # Enable 2FA
            update_row(
                "two_factor_auth",
                {"enabled": True, "verified_at": datetime.now().isoformat()},
                "WHERE username = ?",
                (user,)
            )

            return jsonify({"message": "2FA enabled successfully"})
        else:
            return jsonify({"error": "Invalid verification code"}), 400

    except Exception as e:
        logger.error(f"Error verifying 2FA: {e}")
        return jsonify({"error": "2FA verification failed"}), 500


@auth_bp.route("/2fa/disable", methods=["POST"])
def disable_2fa_route():
    """
    Disable two-factor authentication for user account.

    This endpoint disables 2FA for the current user account
    after verifying their identity.

    Request Body:
        - password: Current password for verification

    Returns:
        JSON response with disable status or error details
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        password = data.get("password", "")

        if not password:
            return jsonify({"error": "Password is required for verification"}), 400

        # Verify password
        success, session_id, error_message = authenticate_user(user, password)
        if not success:
            return jsonify({"error": "Invalid password"}), 401

        # Disable 2FA
        update_row(
            "two_factor_auth",
            {"enabled": False, "disabled_at": datetime.now().isoformat()},
            "WHERE username = ?",
            (user,)
        )

        return jsonify({"message": "2FA disabled successfully"})

    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        return jsonify({"error": "Failed to disable 2FA"}), 500
