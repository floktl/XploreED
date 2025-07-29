"""
AI Text-to-Speech Routes

This module contains API routes for AI-powered text-to-speech conversion.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
import os
from typing import Dict, Any

from core.services.import_service import *

# Import ElevenLabs client
try:
    from elevenlabs.client import ElevenLabs # type: ignore
except ImportError:
    ElevenLabs = None
    logging.warning("ElevenLabs client not available")


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
        voice_id = data.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
        model_id = data.get("model_id", "eleven_multilingual_v2")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        if not ElevenLabs:
            logger.error("ElevenLabs client not available")
            return jsonify({"error": "TTS service not available"}), 500

        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return jsonify({"error": "TTS service not configured"}), 500

        try:
            client = ElevenLabs(api_key=api_key)
            audio = client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=model_id,
                output_format="mp3_44100_128",
            )
            logger.info(f"Successfully generated TTS audio for user {username}")
            return Response(audio, mimetype="audio/mpeg")
        except Exception as e:
            logger.error(f"ElevenLabs API error for user {username}: {e}")
            return jsonify({"error": "TTS service error"}), 500

    except ValueError as e:
        logger.error(f"Validation error in TTS request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in TTS request: {e}")
        return jsonify({"error": "Server error"}), 500



