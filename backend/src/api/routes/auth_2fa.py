"""
2FA routes split from auth.py for clarity.
"""

from __future__ import annotations

import logging
import base64
import secrets
from io import BytesIO
from flask import request, jsonify  # type: ignore

from config.blueprint import auth_bp
from api.middleware.auth import require_user
from core.database.connection import select_one, update_row

logger = logging.getLogger(__name__)


@auth_bp.route("/2fa/enable", methods=["POST"])
def enable_2fa_route():
    try:
        user = require_user()

        import qrcode  # type: ignore

        secret_key = base64.b32encode(secrets.token_bytes(20)).decode("utf-8")
        qr_data = f"otpauth://totp/XplorED:{user}?secret={secret_key}&issuer=XplorED"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, "PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_base64}"

        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]

        update_row(
            "users",
            {
                "two_factor_secret": secret_key,
                "two_factor_enabled": True,
                "backup_codes": ",".join(backup_codes),
            },
            "WHERE username = ?",
            (user,),
        )

        return jsonify(
            {
                "message": "Two-factor authentication enabled",
                "secret_key": secret_key,
                "qr_code_url": qr_code_url,
                "backup_codes": backup_codes,
            }
        )
    except Exception as e:
        logger.error(f"Error enabling 2FA: {e}")
        return jsonify({"error": "Failed to enable 2FA"}), 500


@auth_bp.route("/2fa/verify", methods=["POST"])
def verify_2fa_route():
    try:
        user = require_user()
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        code = data.get("code", "").strip()
        backup_code = data.get("backup_code", "").strip()
        if not code and not backup_code:
            return jsonify({"error": "Verification code or backup code required"}), 400

        user_data = select_one(
            "users",
            columns="two_factor_secret, backup_codes, two_factor_enabled",
            where="username = ?",
            params=(user,),
        )
        if not user_data or not user_data.get("two_factor_enabled"):
            return jsonify({"error": "2FA not enabled"}), 400

        verified = False
        backup_code_used = False

        if backup_code:
            stored_backup_codes = user_data.get("backup_codes", "").split(",")
            if backup_code in stored_backup_codes:
                verified = True
                backup_code_used = True
                stored_backup_codes.remove(backup_code)
                update_row(
                    "users",
                    {"backup_codes": ",".join(stored_backup_codes)},
                    "WHERE username = ?",
                    (user,),
                )
        else:
            import pyotp  # type: ignore

            totp = pyotp.TOTP(user_data.get("two_factor_secret"))
            verified = totp.verify(code)

        if verified:
            return jsonify(
                {
                    "message": "2FA verification successful",
                    "verified": True,
                    "backup_code_used": backup_code_used,
                }
            )
        else:
            return jsonify({"error": "Invalid verification code", "verified": False}), 400
    except Exception as e:
        logger.error(f"Error in 2FA verification: {e}")
        return jsonify({"error": "2FA verification failed"}), 500


@auth_bp.route("/2fa/disable", methods=["POST"])
def disable_2fa_route():
    try:
        user = require_user()
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        password = data.get("password", "")
        if not password:
            return jsonify({"error": "Password is required"}), 400

        user_data = select_one(
            "users",
            columns="password_hash, two_factor_enabled",
            where="username = ?",
            params=(user,),
        )
        if not user_data or not user_data.get("two_factor_enabled"):
            return jsonify({"error": "2FA not enabled"}), 400

        from werkzeug.security import check_password_hash  # type: ignore

        if not check_password_hash(user_data.get("password_hash"), password):
            return jsonify({"error": "Invalid password"}), 400

        update_row(
            "users",
            {"two_factor_enabled": False, "two_factor_secret": None, "backup_codes": None},
            "WHERE username = ?",
            (user,),
        )

        return jsonify({"message": "Two-factor authentication disabled", "disabled": True})
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        return jsonify({"error": "Failed to disable 2FA"}), 500

