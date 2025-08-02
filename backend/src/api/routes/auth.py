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
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from flask import request, jsonify, make_response # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from pydantic import ValidationError
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
from api.schemas import UserRegistrationSchema


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
        logger.error(f"Error in login: {e}")
        return jsonify({"error": "Authentication failed"}), 500


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
        logger.error(f"Error in logout: {e}")
        return jsonify({"error": "Logout failed"}), 500


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
                columns="session_id, created_at, expires_at, active, last_activity",
                where="session_id = ? AND active = 1",
                params=(session_id,)
            )

        if not session_info:
            return jsonify({"error": "Invalid session"}), 401

        return jsonify({
            "user": user,
            "session_id": session_info.get("session_id"),
            "created_at": session_info.get("created_at"),
            "expires_at": session_info.get("expires_at"),
            "is_active": session_info.get("active", False),
            "last_activity": session_info.get("last_activity")
        })

    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({"error": "Failed to get session information"}), 500


@auth_bp.route("/register", methods=["POST"])
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
        success, error_message = create_user_account(registration_data.username, registration_data.password)

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
        logger.error(f"Error in registration: {e}")
        return jsonify({"error": "Registration failed"}), 500


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


@auth_bp.route("/password/reset", methods=["POST"])
def reset_password_route():
    """
    Request password reset for user account.

    This endpoint initiates a password reset process by
    sending a reset token to the user's email.

    Request Body:
        - email (str, required): User's email address

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "reset_sent": bool                 # Whether reset was sent
        }

    Status Codes:
        - 200: Success
        - 400: Invalid email
        - 404: Email not found
        - 500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get("email", "").strip()

        if not email:
            return jsonify({"error": "Email is required"}), 400

        if "@" not in email or "." not in email:
            return jsonify({"error": "Invalid email format"}), 400

        # Check if user exists
        user = select_one(
            "users",
            columns="id, username",
            where="email = ?",
            params=(email,)
        )

        if not user:
            return jsonify({"error": "Email not found"}), 404

        # Generate reset token
        reset_token = f"reset_{user.get('id')}_{datetime.now().timestamp()}"
        expires_at = datetime.now() + timedelta(hours=24)

        # Store reset token
        insert_row(
            "password_resets",
            {
                "user_id": user.get("id"),
                "reset_token": reset_token,
                "expires_at": expires_at.isoformat(),
                "used": False
            }
        )

        # TODO: Send email with reset link
        # For now, just return success
        return jsonify({
            "message": "Password reset email sent",
            "reset_sent": True
        })

    except Exception as e:
        logger.error(f"Error in password reset: {e}")
        return jsonify({"error": "Password reset failed"}), 500


@auth_bp.route("/password/reset/confirm", methods=["POST"])
def confirm_password_reset_route():
    """
    Confirm password reset with token and new password.

    This endpoint completes the password reset process by
    validating the reset token and setting a new password.

    Request Body:
        - reset_token (str, required): Password reset token
        - new_password (str, required): New password
        - confirm_password (str, required): Password confirmation

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "password_changed": bool           # Whether password was changed
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or token expired
        - 404: Reset token not found
        - 500: Internal server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        reset_token = data.get("reset_token", "").strip()
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")

        if not reset_token:
            return jsonify({"error": "Reset token is required"}), 400

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        # Find reset token
        reset_record = select_one(
            "password_resets",
            columns="id, user_id, expires_at, used",
            where="reset_token = ?",
            params=(reset_token,)
        )

        if not reset_record:
            return jsonify({"error": "Invalid reset token"}), 404

        if reset_record.get("used"):
            return jsonify({"error": "Reset token already used"}), 400

        # Check if token expired
        expires_at = datetime.fromisoformat(reset_record.get("expires_at"))
        if datetime.now() > expires_at:
            return jsonify({"error": "Reset token expired"}), 400

        # Update password
        hashed_password = generate_password_hash(new_password)
        update_row(
            "users",
            {"password_hash": hashed_password},
            "WHERE id = ?",
            (reset_record.get("user_id"),)
        )

        # Mark reset token as used
        update_row(
            "password_resets",
            {"used": True, "used_at": datetime.now().isoformat()},
            "WHERE id = ?",
            (reset_record.get("id"),)
        )

        return jsonify({
            "message": "Password changed successfully",
            "password_changed": True
        })

    except Exception as e:
        logger.error(f"Error in password reset confirmation: {e}")
        return jsonify({"error": "Password reset confirmation failed"}), 500


@auth_bp.route("/password/change", methods=["POST"])
def change_password_route():
    """
    Change user password with current password verification.

    This endpoint allows authenticated users to change their
    password by providing their current password.

    Request Body:
        - current_password (str, required): Current password
        - new_password (str, required): New password
        - confirm_password (str, required): Password confirmation

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "password_changed": bool           # Whether password was changed
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or passwords don't match
        - 401: Unauthorized or invalid current password
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")

        if not current_password:
            return jsonify({"error": "Current password is required"}), 400

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        # Get current password hash
        user_data = select_one(
            "users",
            columns="password_hash",
            where="username = ?",
            params=(user,)
        )

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        # Verify current password
        if not check_password_hash(user_data.get("password_hash"), current_password):
            return jsonify({"error": "Invalid current password"}), 401

        # Update password
        hashed_password = generate_password_hash(new_password)
        update_row(
            "users",
            {"password_hash": hashed_password},
            "WHERE username = ?",
            (user,)
        )

        return jsonify({
            "message": "Password changed successfully",
            "password_changed": True
        })

    except Exception as e:
        logger.error(f"Error in password change: {e}")
        return jsonify({"error": "Password change failed"}), 500


@auth_bp.route("/2fa/enable", methods=["POST"])
def enable_2fa_route():
    """
    Enable two-factor authentication for user account.

    This endpoint enables 2FA by generating a secret key
    and QR code for the user to set up their authenticator app.

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "secret_key": str,                 # 2FA secret key
            "qr_code_url": str,                # QR code URL for authenticator
            "backup_codes": [str]              # Backup codes for account recovery
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()

        # Generate 2FA secret
        import secrets
        import base64
        import qrcode
        from io import BytesIO

        secret_key = base64.b32encode(secrets.token_bytes(20)).decode('utf-8')

        # Generate QR code URL
        qr_data = f"otpauth://totp/XplorED:{user}?secret={secret_key}&issuer=XplorED"

        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_base64}"

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]

        # Store 2FA data
        update_row(
            "users",
            {
                "two_factor_secret": secret_key,
                "two_factor_enabled": True,
                "backup_codes": ",".join(backup_codes)
            },
            "WHERE username = ?",
            (user,)
        )

        return jsonify({
            "message": "Two-factor authentication enabled",
            "secret_key": secret_key,
            "qr_code_url": qr_code_url,
            "backup_codes": backup_codes
        })

    except Exception as e:
        logger.error(f"Error enabling 2FA: {e}")
        return jsonify({"error": "Failed to enable 2FA"}), 500


@auth_bp.route("/2fa/verify", methods=["POST"])
def verify_2fa_route():
    """
    Verify two-factor authentication code.

    This endpoint verifies the 2FA code provided by the user
    during login or account access.

    Request Body:
        - code (str, required): 2FA verification code
        - backup_code (str, optional): Backup code (alternative to 2FA code)

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "verified": bool,                  # Whether verification succeeded
            "backup_code_used": bool           # Whether backup code was used
        }

    Status Codes:
        - 200: Success
        - 400: Invalid code
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        code = data.get("code", "").strip()
        backup_code = data.get("backup_code", "").strip()

        if not code and not backup_code:
            return jsonify({"error": "Verification code or backup code required"}), 400

        # Get user's 2FA data
        user_data = select_one(
            "users",
            columns="two_factor_secret, backup_codes, two_factor_enabled",
            where="username = ?",
            params=(user,)
        )

        if not user_data or not user_data.get("two_factor_enabled"):
            return jsonify({"error": "2FA not enabled"}), 400

        verified = False
        backup_code_used = False

        if backup_code:
            # Verify backup code
            stored_backup_codes = user_data.get("backup_codes", "").split(",")
            if backup_code in stored_backup_codes:
                verified = True
                backup_code_used = True

                # Remove used backup code
                stored_backup_codes.remove(backup_code)
                update_row(
                    "users",
                    {"backup_codes": ",".join(stored_backup_codes)},
                    "WHERE username = ?",
                    (user,)
                )
        else:
            # Verify 2FA code
            import pyotp
            totp = pyotp.TOTP(user_data.get("two_factor_secret"))
            verified = totp.verify(code)

        if verified:
            return jsonify({
                "message": "2FA verification successful",
                "verified": True,
                "backup_code_used": backup_code_used
            })
        else:
            return jsonify({
                "error": "Invalid verification code",
                "verified": False
            }), 400

    except Exception as e:
        logger.error(f"Error in 2FA verification: {e}")
        return jsonify({"error": "2FA verification failed"}), 500


@auth_bp.route("/2fa/disable", methods=["POST"])
def disable_2fa_route():
    """
    Disable two-factor authentication for user account.

    This endpoint disables 2FA for the user account,
    removing the security layer.

    Request Body:
        - password (str, required): User's password for confirmation

    JSON Response Structure:
        {
            "message": str,                    # Success message
            "disabled": bool                   # Whether 2FA was disabled
        }

    Status Codes:
        - 200: Success
        - 400: Invalid password
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        user = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        password = data.get("password", "")

        if not password:
            return jsonify({"error": "Password is required"}), 400

        # Verify password
        user_data = select_one(
            "users",
            columns="password_hash, two_factor_enabled",
            where="username = ?",
            params=(user,)
        )

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user_data.get("password_hash"), password):
            return jsonify({"error": "Invalid password"}), 400

        if not user_data.get("two_factor_enabled"):
            return jsonify({"error": "2FA not enabled"}), 400

        # Disable 2FA
        update_row(
            "users",
            {
                "two_factor_secret": None,
                "two_factor_enabled": False,
                "backup_codes": None
            },
            "WHERE username = ?",
            (user,)
        )

        return jsonify({
            "message": "Two-factor authentication disabled",
            "disabled": True
        })

    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        return jsonify({"error": "Failed to disable 2FA"}), 500
