from utils.imports.imports import *
import json
import random
import datetime
from pathlib import Path
from game.german_sentence_game import split_and_clean, save_vocab

EXERCISE_FILE = (
    Path(__file__).resolve().parent.parent / "mock_data" / "ai_exercises.json"
)
FEEDBACK_FILE = (
    Path(__file__).resolve().parent.parent / "mock_data" / "ai_feedback.json"
)


def process_ai_answers(username: str, block_id: str, answers: dict) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    try:
        with open(EXERCISE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("❌ Failed to load exercises for processing", flush=True)
        return

    all_exercises = data.get("exercises", []) + data.get("nextExercises", [])
    exercise_map = {str(e.get("id")): e for e in all_exercises}

    results = []
    for ex_id, user_ans in answers.items():
        ex = exercise_map.get(str(ex_id))
        if not ex:
            continue
        correct_ans = str(ex.get("correctAnswer", "")).strip().lower()
        user_ans = str(user_ans).strip().lower()
        quality = 5 if user_ans == correct_ans else 2
        ef, reps, interval = sm2(quality)
        if user_ans != correct_ans:
            entry = {
                "topic_memory": {
                    "topic": ex.get("question", ""),
                    "skill_type": ex.get("type", ""),
                    "lesson_content_id": block_id,
                    "ease_factor": ef,
                    "intervall": interval,
                    "next_repeat": (
                        datetime.datetime.now()
                        + datetime.timedelta(days=interval)
                    ).isoformat(),
                    "repetitions": reps,
                    "last_review": datetime.datetime.now().isoformat(),
                }
            }
            results.append(entry)

    print("AI submission results:", results, flush=True)

@ai_bp.route("/ai-exercises", methods=["POST"])
def get_ai_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Session ID:", session_id, flush=True)
    print("Username:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    with open(EXERCISE_FILE, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    pool = base_data.get("exercises", []) + base_data.get("nextExercises", [])
    random.shuffle(pool)
    selected = pool[:5]
    print("Selected exercises:", selected, flush=True)

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


@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id):
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Session ID:", session_id, "Username:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    print("Received submission data:", data, flush=True)
    answers = data.get("answers", {})

    # Process answers with SM2 spaced repetition algorithm
    process_ai_answers(username, str(block_id), answers)

    try:
        insert_row(
            "exercise_submissions",
            {
                "username": username,
                "block_id": str(block_id),
                "answers": json.dumps(answers),
            },
        )
        print("Successfully inserted submission", flush=True)
    except Exception as e:
        current_app.logger.error("Failed to save exercise submission: %s", e)
        return jsonify({"msg": "Error"}), 500

    return jsonify({"status": "ok"})


@ai_bp.route("/ai-feedback", methods=["GET"])
def get_ai_feedback():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Fetching AI feedback for:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    return jsonify(feedback_data)


@ai_bp.route("/ai-feedback/<feedback_id>", methods=["GET"])
def get_ai_feedback_item(feedback_id):
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print(f"User '{username}' requested feedback ID {feedback_id}", flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        feedback_data = []

    item = next((fb for fb in feedback_data if str(fb.get("id")) == str(feedback_id)), None)
    if not item:
        return jsonify({"msg": "Feedback not found"}), 404
    return jsonify(item)


@ai_bp.route("/ai-feedback", methods=["POST"])
def generate_ai_feedback():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Generating feedback for user:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    print("Feedback generation data (placeholder):", data, flush=True)

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
    print("Training request from user:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    answers = data.get("answers", {})
    print("Training answers received:", answers, flush=True)

    with open(EXERCISE_FILE, "r", encoding="utf-8") as f:
        base_data = json.load(f)

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

    pool = list(all_exercises)
    random.shuffle(pool)
    selected = pool[:5]
    print("Returning new training exercises", flush=True)

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
