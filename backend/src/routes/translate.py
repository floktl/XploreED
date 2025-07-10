"""Simple translation exercise endpoints."""

from app.imports.imports import *
from .translate_helpers import update_memory_async

@translate_bp.route("/translate", methods=["POST"])
def translate():
    """Translate English text and score the student's attempt."""
    username = require_user()

    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")

    german = translate_to_german(english, username)
    if not isinstance(german, str) or "❌" in german:
        return jsonify({"german": german, "feedback": "❌ Translation failed."})

    correct, reason = evaluate_translation_ai(english, german, student_input)

    update_memory_async(username, english, german, student_input)
    prefix = "✅" if correct else "❌"
    feedback = f"{prefix} {reason}"

    return jsonify({"german": german, "feedback": feedback})
