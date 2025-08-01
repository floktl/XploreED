"""
AI Text-to-Speech Routes

This module contains API routes for AI-powered text-to-speech conversion.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging
from typing import Dict, Any

from flask import request, jsonify, Response  # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user
from config.blueprint import ai_bp
from external.tts import convert_text_to_speech_service

logger = logging.getLogger(__name__)


@ai_bp.route("/tts", methods=["POST"])
def tts():
    """
    Convert text to speech using the ElevenLabs API.

    This endpoint provides text-to-speech functionality for German language
    learning, allowing users to hear proper pronunciation of words and phrases.

    Returns:
        Audio response with synthesized speech or error details
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting text-to-speech conversion")

        data = request.get_json() or {}
        text = data.get("text", "").strip()
        voice_id = data.get("voice_id")
        model_id = data.get("model_id")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Use service layer for TTS conversion
        result = convert_text_to_speech_service(
            text=text,
            username=username,
            voice_id=voice_id,
            model_id=model_id
        )

        if result["success"]:
            logger.info(f"Successfully generated TTS audio for user {username}")
            return Response(result["audio"], mimetype="audio/mpeg")
        else:
            error_code = result.get("error_code", "UNKNOWN_ERROR")
            error_message = result.get("error", "TTS conversion failed")

            # Map error codes to HTTP status codes
            status_code = 500
            if error_code in ["MISSING_TEXT", "INVALID_TEXT"]:
                status_code = 400
            elif error_code == "SERVICE_UNAVAILABLE":
                status_code = 503

            logger.error(f"TTS conversion failed for user {username}: {error_code} - {error_message}")
            return jsonify({"error": error_message, "error_code": error_code}), status_code

    except ValueError as e:
        logger.error(f"Validation error in TTS request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in TTS request: {e}")
        return jsonify({"error": "Server error"}), 500



