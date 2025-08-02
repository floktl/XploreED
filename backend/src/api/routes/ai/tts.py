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
from api.middleware.auth import require_user
from config.blueprint import ai_bp
from external.tts import convert_text_to_speech_service

logger = logging.getLogger(__name__)


@ai_bp.route("/tts", methods=["POST"])
def tts():
    """
    Convert text to speech using AI-powered TTS service.

    This endpoint provides text-to-speech functionality for language learning,
    allowing users to hear proper pronunciation of words, phrases, and sentences.
    The service supports multiple voices and languages for enhanced learning experience.

    Request Body:
        - text (str, required): Text to convert to speech
        - voice_id (str, optional): Specific voice identifier
        - model_id (str, optional): TTS model identifier
        - language (str, optional): Target language code (default: de)
        - speed (float, optional): Speech speed (0.5-2.0, default: 1.0)
        - pitch (float, optional): Speech pitch adjustment (-20 to 20, default: 0)

    Supported Languages:
        - de: German (default)
        - en: English
        - es: Spanish
        - fr: French
        - it: Italian
        - pt: Portuguese
        - ru: Russian
        - ja: Japanese
        - ko: Korean
        - zh: Chinese

    Available Voices:
        - german_male: German male voice
        - german_female: German female voice
        - english_male: English male voice
        - english_female: English female voice
        - custom: Custom voice (requires voice_id)

    JSON Response Structure (Success):
        Audio file (MP3 format) with synthesized speech

    JSON Response Structure (Error):
        {
            "error": str,                             # Error message
            "error_code": str,                        # Error code
            "details": str                            # Additional error details
        }

    Error Codes:
        - MISSING_TEXT: No text provided
        - INVALID_TEXT: Text contains invalid characters or is too long
        - INVALID_VOICE: Specified voice is not available
        - INVALID_LANGUAGE: Language is not supported
        - SERVICE_UNAVAILABLE: TTS service is temporarily unavailable
        - RATE_LIMIT_EXCEEDED: Too many requests
        - UNKNOWN_ERROR: Unexpected error occurred

    Status Codes:
        - 200: Success (returns audio file)
        - 400: Bad request (missing/invalid text, invalid parameters)
        - 401: Unauthorized
        - 429: Rate limit exceeded
        - 503: Service unavailable
        - 500: Internal server error

    Usage Examples:
        Basic text-to-speech:
        {
            "text": "Hallo, wie geht es dir?"
        }

        With specific voice and speed:
        {
            "text": "Das ist ein Beispielsatz.",
            "voice_id": "german_female",
            "speed": 0.8
        }

        Multi-language support:
        {
            "text": "Hello, how are you?",
            "language": "en",
            "voice_id": "english_male"
        }
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



