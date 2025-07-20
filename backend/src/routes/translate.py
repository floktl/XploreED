"""Simple translation exercise endpoints."""

from app.imports.imports import *
from .ai.helpers.translate_helpers import update_memory_async
from threading import Thread
import uuid
import time
import redis
import json
import os
from flask import Response, stream_with_context
from .ai.helpers.helpers import format_feedback_block

# Connect to Redis (host from env, default 'localhost')
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

@translate_bp.route("/translate", methods=["POST"])
def translate_async():
    """Async translation: create job, return job_id, process in background."""
    username = require_user()
    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")

    job_id = str(uuid.uuid4())
    redis_client.set(f"translation_job:{job_id}", json.dumps({"status": "processing", "result": None}))

    def process():
        try:
            german = translate_to_german(english, username)
            if not isinstance(german, str) or "❌" in german:
                result = {"german": german, "feedback": "❌ Translation failed."}
                redis_client.set(f"translation_job:{job_id}", json.dumps({"status": "done", "result": result}))
                return
            correct, reason = evaluate_translation_ai(english, german, student_input)
            update_memory_async(username, english, german, student_input)
            prefix = "✅" if correct else "❌"
            # Build feedback block
            feedbackBlock = format_feedback_block(
                user_answer=student_input,
                correct_answer=german,
                alternatives=[],
                explanation=reason,
                diff=None,
                status="correct" if correct else "incorrect"
            )
            result = {"german": german, "feedbackBlock": feedbackBlock}
            redis_client.set(f"translation_job:{job_id}", json.dumps({"status": "done", "result": result}))
        except Exception as e:
            redis_client.set(f"translation_job:{job_id}", json.dumps({
                "status": "done",
                "result": {"german": "", "feedback": f"❌ Internal error: {e}"}
            }))

    Thread(target=process, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "processing"})

@translate_bp.route("/translate/status/<job_id>", methods=["GET"])
def translate_status(job_id):
    """Check translation job status/result from Redis."""
    job_json = redis_client.get(f"translation_job:{job_id}")
    if not job_json:
        return jsonify({"status": "not_found"}), 404
    job = json.loads(job_json)
    return jsonify(job)

@translate_bp.route("/translate/stream", methods=["POST"])
def translate_stream():
    """Stream AI translation feedback as it arrives, then save vocab/topic memory after full answer."""
    username = require_user()
    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")

    # print(f"[translate_stream] Starting for user {username}, english={english}, student_input={student_input}", flush=True)

    def event_stream():
        buffer = ""
        try:
            # First, get the German translation
            german = translate_to_german(english, username)
            # print(f"[translate_stream] German translation: {german}", flush=True)

            if not isinstance(german, str) or "❌" in german:
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

            # Evaluate the student's translation (single main API call)
            correct, reason = evaluate_translation_ai(english, german, student_input)
            # print(f"[translate_stream] Evaluation: correct={correct}, reason={reason}", flush=True)

            # Build the feedback block
            feedback_block = format_feedback_block(
                user_answer=student_input,
                correct_answer=german,
                alternatives=[],
                explanation=reason,
                diff=None,
                status="correct" if correct else "incorrect"
            )
            # print(f"[translate_stream] Feedback block: {json.dumps(feedback_block, ensure_ascii=False)}", flush=True)

            # Stream the feedback block as JSON immediately
            yield f"data: {json.dumps({'feedbackBlock': feedback_block})}\n\n"

            # Optionally, trigger grammar/dictionary analysis in the background (async, not blocking feedback)
            Thread(target=update_memory_async, args=(username, english, german, student_input), daemon=True).start()
            # If you want to add more async enrichment, do it here (e.g., grammar/dictionary info)

        except Exception as e:
            # print(f"[translate_stream] Error: {e}", flush=True)
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
