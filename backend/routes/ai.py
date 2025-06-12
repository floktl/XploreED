from utils.imports.imports import *
import json
from pathlib import Path

EXERCISE_FILE = Path(__file__).resolve().parent.parent / "mock_data" / "ai_exercises.json"
FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "mock_data" / "ai_feedback.json"

@ai_bp.route("/ai-exercises", methods=["POST"])
def get_ai_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    with open(EXERCISE_FILE, "r") as f:
        mock_data = json.load(f)

    return jsonify(mock_data)

@ai_bp.route("/ai-feedback", methods=["GET"])
def get_ai_feedback():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    return jsonify(feedback_data)

