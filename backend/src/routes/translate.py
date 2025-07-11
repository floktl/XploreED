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
            print(f"[translate_async] Starting job {job_id} for user {username}", flush=True)
            german = translate_to_german(english, username)
            print(f"[translate_async] German result: {german}", flush=True)
            if not isinstance(german, str) or "❌" in german:
                result = {"german": german, "feedback": "❌ Translation failed."}
                redis_client.set(f"translation_job:{job_id}", json.dumps({"status": "done", "result": result}))
                return
            correct, reason = evaluate_translation_ai(english, german, student_input)
            print(f"[translate_async] Feedback: {correct}, {reason}", flush=True)
            update_memory_async(username, english, german, student_input)
            prefix = "✅" if correct else "❌"
            feedback = f"{prefix} {reason}"
            result = {"german": german, "feedback": feedback}
            redis_client.set(f"translation_job:{job_id}", json.dumps({"status": "done", "result": result}))
        except Exception as e:
            print("[translate_async] Background job error:", e, flush=True)
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

    def event_stream():
        buffer = ""
        try:
            resp = send_prompt(
                "You are a helpful German teacher.",
                {"role": "user", "content": f"Translate and evaluate: {english} | Student: {student_input}"},
                temperature=0.3,
                stream=True,
            )
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if line.strip() == "data: [DONE]":
                    break
                if line.startswith("data:"):
                    line = line[len("data:"):].strip()
                try:
                    data_json = json.loads(line)
                    chunk = (
                        data_json.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if chunk:
                        buffer += chunk
                        yield f"data: {chunk}\n\n"
                except Exception:
                    continue
        except Exception as e:
            yield f"data: [ERROR] {e}\n\n"
        # After streaming, save vocab/topic memory in background
        if buffer.strip():
            Thread(target=update_memory_async, args=(username, english, buffer.strip(), student_input), daemon=True).start()

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")
