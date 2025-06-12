from utils.imports.imports import *
import json
import random
from pathlib import Path

EXERCISE_FILE = Path(__file__).resolve().parent.parent / "mock_data" / "ai_exercises.json"
FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "mock_data" / "ai_feedback.json"

@ai_bp.route("/ai-exercises", methods=["POST"])
def get_ai_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    with open(EXERCISE_FILE, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    # Combine all available exercises and randomly pick five for this round
    pool = base_data.get("exercises", []) + base_data.get("nextExercises", [])
    random.shuffle(pool)
    selected = pool[:5]

    response = {
        "lessonId": base_data.get("lessonId"),
        "title": base_data.get("title"),
        "instructions": base_data.get("instructions"),
        "level": base_data.get("level"),
        "exercises": selected,
        "feedbackPrompt": base_data.get("feedbackPrompt"),
        "nextInstructions": base_data.get("nextInstructions"),
        "nextFeedbackPrompt": base_data.get("nextFeedbackPrompt"),
        "vocabHelp": base_data.get("vocabHelp", []),
    }

    return jsonify(response)

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

