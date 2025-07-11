"""Miscellaneous AI endpoints."""

from flask import request, jsonify

from . import ai_bp
from utils.helpers.helper import require_user
from utils.ai.ai_api import send_prompt
from .helpers.misc_helpers import stream_ai_answer


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

    return stream_ai_answer(question)
