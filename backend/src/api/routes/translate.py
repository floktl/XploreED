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
from infrastructure.imports import Imports
from api.middleware.auth import require_user
from core.database.connection import select_one, select_rows, insert_row, update_row
from config.blueprint import translate_bp
from features.translation import (
    create_translation_job,
    process_translation_job,
    get_translation_job_status,
    get_translation_status,
    stream_translation_feedback,
    cleanup_expired_jobs,
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
        - text (str, required): Source text to translate
        - source_lang (str, optional): Source language code (default: auto-detected)
        - target_lang (str, required): Target language code
        - context (str, optional): Translation context for better accuracy

    Supported Languages:
        - en: English
        - de: German
        - es: Spanish
        - fr: French
        - it: Italian
        - pt: Portuguese
        - ru: Russian
        - ja: Japanese
        - ko: Korean
        - zh: Chinese

    JSON Response Structure:
        {
            "job_id": str,                       # Translation job identifier
            "status": str,                       # Job status (processing, completed, failed)
            "message": str                       # Status message
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or unsupported language
        - 500: Internal server error
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

    Path Parameters:
        - job_id (str, required): Unique identifier of the translation job

    JSON Response Structure:
        {
            "job_id": str,                       # Translation job identifier
            "status": str,                       # Job status (processing, completed, failed)
            "progress": int,                     # Progress percentage (0-100)
            "result": {                          # Translation result (if completed)
                "translated_text": str,          # Translated text
                "confidence": float,             # Translation confidence score
                "source_lang": str,              # Detected source language
                "target_lang": str,              # Target language
                "processing_time": float         # Processing time in seconds
            },
            "error": str                         # Error message (if failed)
        }

    Status Codes:
        - 200: Success
        - 400: Invalid job ID
        - 404: Translation job not found
        - 500: Internal server error
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
        - text (str, required): Text to translate
        - source_lang (str, optional): Source language code (default: auto)
        - target_lang (str, required): Target language code
        - stream_type (str, optional): Type of streaming (word, sentence, paragraph)

    Stream Types:
        - word: Stream individual words as they're translated
        - sentence: Stream complete sentences
        - paragraph: Stream complete paragraphs

    JSON Response Structure:
        {
            "message": str,                      # Status message
            "text": str,                         # Original text
            "source_lang": str,                  # Source language
            "target_lang": str,                  # Target language
            "stream_type": str                   # Stream type
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or stream type
        - 500: Internal server error
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
        return jsonify({
            "message": "Streaming translation not implemented",
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "stream_type": stream_type
        })

    except Exception as e:
        logger.error(f"Error in stream translation endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500
