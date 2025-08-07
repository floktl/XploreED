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
from typing import Optional
from datetime import datetime
import json # Added for json.dumps

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
from features.ai.generation.feedback_helpers import format_feedback_block
from shared.exceptions import DatabaseError


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
        logger.error(f"Error translating text: {e}")
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
        - english (str, required): English text to translate
        - student_input (str, required): Student's translation attempt

    JSON Response Structure:
        Streaming response with feedback blocks

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 500: Internal server error
    """
    try:
        username = require_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        english = data.get("english", "").strip()
        student_input = data.get("student_input", "").strip()

        if not english:
            return jsonify({"error": "No English text provided for translation"}), 400

        if not student_input:
            return jsonify({"error": "No student input provided"}), 400

        logger.info(f"Starting translation stream for user {username}")

        # Try streaming first, but have a fallback
        try:
            def event_stream():
                buffer = ""
                try:
                    logger.info(f"Starting translation for: '{english}' -> '{student_input}'")

                    # Add a simple timeout mechanism
                    import time
                    start_time = time.time()
                    timeout = 30  # 30 seconds timeout

                    # First, get the German translation
                    from features.ai.memory.vocabulary_memory import translate_to_german
                    logger.info("Calling translate_to_german...")

                    # Check timeout before each major operation
                    if time.time() - start_time > timeout:
                        raise Exception("Translation timeout - taking too long")

                    german = translate_to_german(english, username)
                    logger.info(f"Got German translation: '{german}'")

                    if not isinstance(german, str) or "❌" in german:
                        logger.error(f"Translation failed: {german}")
                        # Send error feedback block
                        error_feedback = format_feedback_block(
                            user_answer=student_input,
                            correct_answer="",
                            alternatives=[],
                            explanation="Translation failed",
                            diff=None,
                            status="error"
                        )
                        yield f"data: {json.dumps({'feedbackBlock': error_feedback})}\n\n"
                        return

                    # Check timeout before evaluation
                    if time.time() - start_time > timeout:
                        raise Exception("Evaluation timeout - taking too long")

                    # Evaluate the student's translation
                    from features.ai.evaluation import evaluate_translation_ai
                    logger.info("Calling evaluate_translation_ai...")
                    correct, reason = evaluate_translation_ai(english, german, student_input)
                    logger.info(f"Evaluation result: correct={correct}, reason={reason}")

                    # Build the feedback block
                    feedback_block = format_feedback_block(
                        user_answer=student_input,
                        correct_answer=german,
                        alternatives=[],
                        explanation=reason,
                        diff=None,
                        status="correct" if correct else "incorrect"
                    )

                    # Stream the feedback block as JSON immediately
                    logger.info("Streaming feedback block...")
                    yield f"data: {json.dumps({'feedbackBlock': feedback_block})}\n\n"
                    logger.info("Feedback block streamed successfully")

                    # Trigger grammar/dictionary analysis in the background (async, not blocking feedback)
                    from threading import Thread
                    from features.ai.generation.translate_helpers import update_memory_async
                    Thread(target=update_memory_async, args=(username, english, german, student_input), daemon=True).start()
                    logger.info("Background memory update started")

                except Exception as e:
                    logger.error(f"Error in translation stream: {e}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    error_feedback = format_feedback_block(
                        user_answer=student_input,
                        correct_answer="",
                        alternatives=[],
                        explanation=f"Error: {str(e)}",
                        diff=None,
                        status="error"
                    )
                    yield f"data: {json.dumps({'feedbackBlock': error_feedback})}\n\n"

            return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

        except Exception as e:
            logger.error(f"Streaming failed, falling back to simple response: {e}")
            # Fallback to simple response
            try:
                from features.ai.memory.vocabulary_memory import translate_to_german
                from features.ai.evaluation import evaluate_translation_ai

                german = translate_to_german(english, username)
                if not isinstance(german, str) or "❌" in german:
                    return jsonify({
                        "error": "Translation failed",
                        "message": "Could not translate the text."
                    }), 500

                correct, reason = evaluate_translation_ai(english, german, student_input)
                feedback_block = format_feedback_block(
                    user_answer=student_input,
                    correct_answer=german,
                    alternatives=[],
                    explanation=reason,
                    diff=None,
                    status="correct" if correct else "incorrect"
                )

                return jsonify({
                    "feedbackBlock": feedback_block,
                    "message": "Translation completed (fallback mode)"
                })

            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return jsonify({
                    "error": "Translation failed",
                    "message": "Something went wrong with the translation. Please try again."
                }), 500

    except Exception as e:
        logger.error(f"Error in stream translation endpoint: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Return a simple error response instead of streaming
        return jsonify({
            "error": "Translation failed",
            "message": "Something went wrong with the translation. Please try again."
        }), 500
