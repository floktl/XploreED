from utils.imports.imports import *
import json
import random
from pathlib import Path
from game.german_sentence_game import split_and_clean, save_vocab

EXERCISE_FILE = (
    Path(__file__).resolve().parent.parent / "mock_data" / "ai_exercises.json"
)
FEEDBACK_FILE = (
    Path(__file__).resolve().parent.parent / "mock_data" / "ai_feedback.json"
)


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


@ai_bp.route("/ai-feedback", methods=["POST"])
def generate_ai_feedback():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    _ = data.get("answers", {})  # currently unused but reserved for future use

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    feedback = random.choice(feedback_data) if feedback_data else {}
    return jsonify(feedback)


@ai_bp.route("/training-exercises", methods=["POST"])
def get_training_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    answers = data.get("answers", {})

    with open(EXERCISE_FILE, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    # Save vocab for correctly answered questions
    all_exercises = base_data.get("exercises", []) + base_data.get("nextExercises", [])
    answer_map = {str(k): str(v) for k, v in answers.items()}
    for ex in all_exercises:
        ex_id = str(ex.get("id"))
        if ex_id in answer_map:
            user_ans = answer_map[ex_id].strip().lower()
            correct_ans = str(ex.get("correctAnswer", "")).strip().lower()
            if user_ans == correct_ans:
                for word in split_and_clean(correct_ans):
                    save_vocab(
                        username,
                        word,
                        context=correct_ans,
                        exercise=ex_id,
                    )

    # Provide a random new set of exercises
    pool = list(all_exercises)
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
