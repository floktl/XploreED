from flask import request, jsonify
from utils.session.session_manager import session_manager
from utils.blueprint import translate_bp
from game.german_sentence_game import get_feedback
from utils.gemini_translator import get_feedback_with_gemini, translate_with_gemini

@translate_bp.route("/translate", methods=["POST"])
def translate():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")

    # Get translation with confidence score
    translation_result = translate_with_gemini(english, username)

    # Handle different return types (backward compatibility)
    if isinstance(translation_result, dict):
        german = translation_result.get("text", "")
        translation_confidence = translation_result.get("confidence", 75)
    else:
        german = translation_result
        translation_confidence = 75  # Default confidence

    if not isinstance(german, str) or "❌" in german:
        return jsonify({
            "german": german,
            "feedback": "❌ Translation failed.",
            "translation_confidence": 0,
            "feedback_confidence": 0
        })

    try:
        # Try to use Gemini AI for feedback with confidence score
        _, feedback, feedback_confidence = get_feedback_with_gemini(german, student_input)
    except Exception as e:
        print(f"❌ Error using Gemini for feedback: {e}")
        # Fallback to traditional feedback
        _, feedback = get_feedback(german, student_input)
        # Format the feedback with HTML spans
        feedback = feedback.replace("\x1b[31m", '<span style="color:red;">')\
                          .replace("\x1b[32m", '<span style="color:green;">')\
                          .replace("\x1b[33m", '<span style="color:orange;">')\
                          .replace("\x1b[0m", '</span>')
        feedback_confidence = 50  # Medium confidence for fallback

    return jsonify({
        "german": german,
        "feedback": feedback,
        "translation_confidence": translation_confidence,
        "feedback_confidence": feedback_confidence
    })
