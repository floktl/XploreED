"""
Translation Exercise Routes

This module contains API routes for translation exercises and feedback.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
import json  # type: ignore
from flask import Response, stream_with_context  # type: ignore

from core.services.import_service import *
from features.translation.translation_helpers import (
    create_translation_job,
    process_translation_job,
    get_translation_job_status,
    stream_translation_feedback
)


logger = logging.getLogger(__name__)


@translate_bp.route("/translate", methods=["POST"])
def translate_async():
    """
    Create an asynchronous translation job.

    This endpoint creates a translation job and processes it in the background,
    returning a job ID that can be used to check the status.

    Returns:
        JSON response with job ID and initial status
    """
    try:
        username = require_user()
        data = request.get_json() or {}
        english = data.get("english", "").strip()
        student_input = data.get("student_input", "").strip()

        if not english:
            return jsonify({"msg": "English text is required"}), 400

        # Create translation job
        job_id = create_translation_job(english, student_input, str(username))  # type: ignore

        # Process job in background
        from threading import Thread
        Thread(
            target=process_translation_job,
            args=(job_id, english, student_input, str(username)),  # type: ignore
            daemon=True
        ).start()

        return jsonify({
            "job_id": job_id,
            "status": "processing"
        })

    except ValueError as e:
        logger.error(f"Validation error in async translation: {e}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating translation job: {e}")
        return jsonify({"msg": "Failed to create translation job"}), 500


@translate_bp.route("/translate/status/<job_id>", methods=["GET"])
def translate_status(job_id: str):
    """
    Check the status of a translation job.

    Args:
        job_id: The job ID to check

    Returns:
        JSON response with job status and result
    """
    try:
        if not job_id:
            return jsonify({"msg": "Job ID is required"}), 400

        job_data = get_translation_job_status(job_id)

        if not job_data:
            return jsonify({"status": "not_found"}), 404

        return jsonify(job_data)

    except ValueError as e:
        logger.error(f"Validation error checking job status: {e}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        logger.error(f"Error checking job status for {job_id}: {e}")
        return jsonify({"msg": "Failed to check job status"}), 500


@translate_bp.route("/translate/stream", methods=["POST"])
def translate_stream():
    """
    Stream translation feedback in real-time.

    This endpoint provides immediate feedback for translation exercises
    using Server-Sent Events (SSE).

    Returns:
        Server-Sent Events stream with translation feedback
    """
    try:
        username = require_user()
        data = request.get_json() or {}
        english = data.get("english", "").strip()
        student_input = data.get("student_input", "").strip()

        if not english:
            return jsonify({"msg": "English text is required"}), 400

        def event_stream():
            """Generate streaming events for translation feedback."""
            try:
                # Generate feedback using helper function
                feedback_json = stream_translation_feedback(english, student_input, str(username))  # type: ignore

                # Stream the feedback as JSON
                yield f"data: {feedback_json}\n\n"

            except Exception as e:
                logger.error(f"Error in translation stream: {e}")
                error_feedback = {
                    "feedbackBlock": {
                        "user_answer": student_input,
                        "correct_answer": "",
                        "explanation": f"Error: {str(e)}",
                        "status": "error"
                    }
                }
                yield f"data: {json.dumps(error_feedback)}\n\n"

        return Response(
            stream_with_context(event_stream()),
            mimetype="text/event-stream"
        )

    except ValueError as e:
        logger.error(f"Validation error in translation stream: {e}")
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in translation stream: {e}")
        return jsonify({"msg": "Failed to start translation stream"}), 500
