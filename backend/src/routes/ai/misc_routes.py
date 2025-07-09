"""Miscellaneous AI endpoints."""

import json
from flask import request, jsonify, Response, current_app

from . import ai_bp
from utils.helpers.helper import session_manager
from utils.ai.ai_api import send_prompt


@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():
    """Forward a single question to Mistral and return the answer."""
    username = require_user()

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            {"role": "user", "content": question},
            temperature=0.3,
        )
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"].strip()
            return jsonify({"answer": answer})
    except Exception as e:
        print("[ask_ai] Error:", e, flush=True)

    return jsonify({"error": "AI error"}), 500


@ai_bp.route("/ask-ai-stream", methods=["POST"])
def ask_ai_stream():
    """Stream a long AI answer back to the client."""
    username = require_user()

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    def generate():
        try:
            with send_prompt(
                "You are a helpful German teacher.",
                {"role": "user", "content": question},
                temperature=0.3,
                stream=True,
            ) as resp:
                buffer = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        if line.strip() == "data: [DONE]":
                            break
                        if line.startswith("data:"):
                            line = line[len("data:"):].strip()
                        data = json.loads(line)
                        chunk = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if chunk:
                            buffer += chunk

                            # ✨ Simple Markdown: Convert "**text**" to bold
                            buffer = buffer.replace("**", "")

                            # ✨ Flush as paragraph on sentence end
                            if buffer.endswith((".", "!", "?")):
                                structured = {
                                    "type": "paragraph",
                                    "text": buffer.strip()
                                }
                                yield f"data: {json.dumps(structured, ensure_ascii=False)}\n\n"
                                buffer = ""
                    except Exception:
                        continue
                if buffer.strip():
                    yield f"data: {json.dumps({ 'type': 'paragraph', 'text': buffer.strip() }, ensure_ascii=False)}\n\n"
        except Exception as e:
            current_app.logger.error("Streaming error: %s", e)
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


@ai_bp.route("/reading-exercise", methods=["POST"])
def reading_exercise():
    """Proxy to the lesson reading exercise generator."""
    from .lesson_routes import ai_reading_exercise

    return ai_reading_exercise()

