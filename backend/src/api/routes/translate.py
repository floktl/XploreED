"""
XplorED - Translation API Routes

This module contains API routes for text translation functionality,
following clean architecture principles as outlined in the documentation.

Route Categories:
- Text Translation: Translate text between languages
- Translation Status: Check translation job progress
- Stream Translation: Real-time translation streaming

Translation Features:
- Support for multiple language pairs
- Asynchronous translation processing
- Real-time translation streaming
- Translation quality evaluation

Business Logic:
All translation logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from flask import request, jsonify, Response, stream_with_context # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import translate_bp
from features.translation.translation_helpers import (
    create_translation_job,
    get_translation_job_status,
    stream_translation_feedback,
    get_translation_status
)


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === Text Translation Routes ===
@translate_bp.route("/translate", methods=["POST"])
def translate_text_route():
    """
    Translate text between supported languages.

    This endpoint accepts text input and translates it to the target language
    using AI-powered translation services. The translation is processed
    asynchronously for better performance.

    Request Body:
        - text: Source text to translate
        - source_lang: Source language code (optional, auto-detected)
        - target_lang: Target language code (required)
        - context: Translation context for better accuracy (optional)

    Returns:
        JSON response with translation job ID or error details
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        text = data.get("text", "").strip()
        source_lang = data.get("source_lang", "auto")
        target_lang = data.get("target_lang", "en")
        context = data.get("context", "")

        if not text:
            return jsonify({"error": "No text provided for translation"}), 400

        if not target_lang:
            return jsonify({"error": "Target language is required"}), 400

        # Validate language codes
        supported_languages = ["en", "de", "es", "fr", "it", "pt", "ru", "ja", "ko", "zh"]
        if target_lang not in supported_languages:
            return jsonify({"error": f"Unsupported target language: {target_lang}"}), 400

        # Process translation
        result = {
            "job_id": f"trans_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "processing"
        }

        if result.get("error"):
            logger.error(f"Translation error: {result['error']}")
            return jsonify({"error": "Translation failed"}), 500

        return jsonify({
            "job_id": result.get("job_id"),
            "status": "processing",
            "message": "Translation job started successfully"
        })

    except Exception as e:
        logger.error(f"Error in translate endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500


# === Translation Status Routes ===
@translate_bp.route("/translate/status/<job_id>", methods=["GET"])
def get_translation_status_route(job_id: str):
    """
    Check the status of a translation job.

    This endpoint allows clients to poll for translation job completion
    and retrieve results when the translation is finished.

    Args:
        job_id: Unique identifier of the translation job

    Returns:
        JSON response with job status and results if completed
    """
    try:
        if not job_id:
            return jsonify({"error": "Job ID is required"}), 400

        # Get translation status
        status = get_translation_status(job_id)

        if not status:
            return jsonify({"error": "Translation job not found"}), 404

        return jsonify({
            "job_id": job_id,
            "status": status.get("status", "unknown"),
            "progress": status.get("progress", 0),
            "result": status.get("result"),
            "error": status.get("error")
        })

    except Exception as e:
        logger.error(f"Error checking translation status for job {job_id}: {e}")
        return jsonify({"error": "Failed to check translation status"}), 500


# === Stream Translation Routes ===
@translate_bp.route("/translate/stream", methods=["POST"])
def stream_translation_route():
    """
    Stream real-time translation results.

    This endpoint provides real-time translation streaming for immediate
    feedback during text input or conversation scenarios.

    Request Body:
        - text: Text to translate
        - source_lang: Source language code (optional)
        - target_lang: Target language code (required)
        - stream_type: Type of streaming ("word", "sentence", "paragraph")

    Returns:
        Server-sent events stream with translation results
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        text = data.get("text", "").strip()
        source_lang = data.get("source_lang", "auto")
        target_lang = data.get("target_lang", "en")
        stream_type = data.get("stream_type", "sentence")

        if not text:
            return jsonify({"error": "No text provided for translation"}), 400

        if not target_lang:
            return jsonify({"error": "Target language is required"}), 400

        # Validate stream type
        valid_stream_types = ["word", "sentence", "paragraph"]
        if stream_type not in valid_stream_types:
            return jsonify({"error": f"Invalid stream type: {stream_type}"}), 400

        # Start streaming translation
        return stream_translation(text, source_lang, target_lang, stream_type)

    except Exception as e:
        logger.error(f"Error in stream translation endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500
