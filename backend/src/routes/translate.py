"""Simple translation exercise endpoints."""

from utils.imports.imports import *
from utils.ai.translation_utils import evaluate_topic_qualities_ai
from utils.helpers.helper import run_in_background

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

    def _background_save():
        qualities = evaluate_topic_qualities_ai(english, german, student_input)
        update_topic_memory_translation(username, german, qualities)

    run_in_background(_background_save)
    prefix = "✅" if correct else "❌"
    feedback = f"{prefix} {reason}"

    return jsonify({"german": german, "feedback": feedback})
