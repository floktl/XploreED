# backend/routes/translate.py
from flask import Blueprint, jsonify, request
from session_manager import session_manager
from german_sentence_game import translate_to_german, get_feedback

translate_bp = Blueprint("translate", __name__, url_prefix="/api")

@translate_bp.route("/translate", methods=["POST"])
def translate():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")

    german = translate_to_german(english, username)
    if not isinstance(german, str) or "❌" in german:
        return jsonify({"german": german, "feedback": "❌ Translation failed."})

    correct, feedback = get_feedback(german, student_input)
    feedback = feedback.replace("\x1b[31m", '<span style="color:red;">')\
                       .replace("\x1b[32m", '<span style="color:green;">')\
                       .replace("\x1b[33m", '<span style="color:orange;">')\
                       .replace("\x1b[0m", '</span>')

    return jsonify({"german": german, "feedback": feedback})
