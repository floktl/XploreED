from flask import request, jsonify
from utils.session.session_manager import session_manager
from utils.blueprint import translate_bp
from game.german_sentence_game import translate_to_german, get_feedback
from utils.gemini_translator import get_feedback_with_gemini

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

    try:
        # Try to use Gemini AI for feedback
        _, feedback = get_feedback_with_gemini(german, student_input)
    except Exception as e:
        print(f"❌ Error using Gemini for feedback: {e}")
        # Fallback to traditional feedback
        _, feedback = get_feedback(german, student_input)
        # Format the feedback with HTML spans
        feedback = feedback.replace("\x1b[31m", '<span style="color:red;">')\
                          .replace("\x1b[32m", '<span style="color:green;">')\
                          .replace("\x1b[33m", '<span style="color:orange;">')\
                          .replace("\x1b[0m", '</span>')

    return jsonify({"german": german, "feedback": feedback})
