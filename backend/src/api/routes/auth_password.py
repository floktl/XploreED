"""
Password management routes split from auth.py for clarity.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from flask import request, jsonify  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore

from config.blueprint import auth_bp
from api.middleware.auth import require_user
from core.database.connection import select_one, insert_row, update_row


logger = logging.getLogger(__name__)


@auth_bp.route("/password/reset", methods=["POST"])
def reset_password_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        email = data.get("email", "").strip()
        if not email:
            return jsonify({"error": "Email is required"}), 400
        if "@" not in email or "." not in email:
            return jsonify({"error": "Invalid email format"}), 400

        user = select_one("users", columns="id, username", where="email = ?", params=(email,))
        if not user:
            return jsonify({"error": "Email not found"}), 404

        reset_token = f"reset_{user.get('id')}_{datetime.now().timestamp()}"
        expires_at = datetime.now() + timedelta(hours=24)

        insert_row(
            "password_resets",
            {
                "user_id": user.get("id"),
                "reset_token": reset_token,
                "expires_at": expires_at.isoformat(),
                "used": False,
            },
        )

        return jsonify({"message": "Password reset email sent", "reset_sent": True})
    except Exception as e:
        logger.error(f"Error requesting password reset: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/password/reset/confirm", methods=["POST"])
def confirm_password_reset_route():
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

        reset_record = select_one(
            "password_resets",
            columns="id, user_id, expires_at, used",
            where="reset_token = ?",
            params=(reset_token,),
        )
        if not reset_record:
            return jsonify({"error": "Invalid reset token"}), 404
        if reset_record.get("used"):
            return jsonify({"error": "Reset token already used"}), 400

        expires_at_str = reset_record.get("expires_at")
        if not isinstance(expires_at_str, str):
            return jsonify({"error": "Invalid reset token"}), 400
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now() > expires_at:
            return jsonify({"error": "Reset token expired"}), 400

        hashed_password = generate_password_hash(new_password)
        update_row("users", {"password_hash": hashed_password}, "WHERE id = ?", (reset_record.get("user_id"),))

        update_row(
            "password_resets",
            {"used": True, "used_at": datetime.now().isoformat()},
            "WHERE id = ?",
            (reset_record.get("id"),),
        )

        return jsonify({"message": "Password changed successfully", "password_changed": True})
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/password/change", methods=["POST"])
def change_password_route():
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

        user_data = select_one("users", columns="password_hash", where="username = ?", params=(user,))
        if not user_data:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user_data.get("password_hash"), current_password):
            return jsonify({"error": "Invalid current password"}), 401

        hashed_password = generate_password_hash(new_password)
        update_row("users", {"password_hash": hashed_password}, "WHERE username = ?", (user,))

        return jsonify({"message": "Password changed successfully", "password_changed": True})
    except Exception as e:
        logger.error(f"Error in password change: {e}")
        return jsonify({"error": "Password change failed"}), 500

