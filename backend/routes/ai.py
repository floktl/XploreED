from utils.imports.imports import *
import json
import random
import datetime
from pathlib import Path
from game.german_sentence_game import split_and_clean, save_vocab
from mock_data.script import generate_new_exercises, generate_feedback_prompt
from flask import request, Response
from elevenlabs.client import ElevenLabs
import os


FEEDBACK_FILE = (
    Path(__file__).resolve().parent.parent / "mock_data" / "ai_feedback.json"
)

EXERCISE_TEMPLATE = {
    "lessonId": "dynamic-ai-lesson",
    "title": "AI Generated Exercises",
    "instructions": "Fill in the blanks or translate the sentences.",
    "level": "A1",
    "exercises": [],
    "feedbackPrompt": "",
    "nextInstructions": "",
    "nextExercises": [],
    "nextFeedbackPrompt": "",
    "vocabHelp": [],
}


@ai_bp.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text", "")
    voice_id = data.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
    model_id = data.get("model_id", "eleven_multilingual_v2")

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not set"}), 500

    client = ElevenLabs(api_key=api_key)
    try:
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128",
        )
        return Response(audio, mimetype="audio/mpeg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def fetch_topic_memory(username: str) -> list:
    """Retrieve topic memory rows for a user if the table exists."""
    try:
        rows = fetch_custom(
            "SELECT topic, skill_type, lesson_content_id, ease_factor, intervall, next_repeat, repetitions, last_review FROM topic_memory WHERE username = ?",
            (username,),
        )
        return rows if rows else []
    except Exception:
        # Table might not exist yet
        return []

def fetch_topic_memory(username: str) -> list:
    """Retrieve topic memory rows for a user if the table exists."""
    try:
        rows = fetch_custom(
            "SELECT topic, skill_type, lesson_content_id, ease_factor, intervall, next_repeat, repetitions, last_review FROM topic_memory WHERE username = ?",
            (username,),
        )
        return rows if rows else []
    except Exception:
        # Table might not exist yet
        return []



def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    if not exercise_block:
        print("❌ Missing exercise block for processing", flush=True)
        return

    all_exercises = exercise_block.get("exercises", []) + exercise_block.get("nextExercises", [])
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
            try:
                insert_row(
                    "topic_memory",
                    {
                        "username": username,
                        **entry["topic_memory"],
                    },
                )
            except Exception as e:
                current_app.logger.error("Failed to insert topic memory: %s", e)

    print("AI submission results:", results, flush=True)


@ai_bp.route("/ai-exercises", methods=["POST"])
def get_ai_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Session ID:", session_id, flush=True)
    print("Username:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = fetch_custom(
        "SELECT vocab, translation, interval_days, next_review, ef, repetitions, created_at "
        "FROM vocab_log WHERE username = ?",
        (username,),
    )

    vocab_data = [
        {
            "type": "string",
            "word": row["vocab"],
            "translation": row.get("translation"),
            "sm2_interval": row.get("interval_days"),
            "sm2_due_date": row.get("next_review"),
            "sm2_ease": row.get("ef"),
            "repetitions": row.get("repetitions"),
            "sm2_last_review": row.get("created_at"),
            "quality": 0,
        }
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    ai_block = generate_new_exercises(vocab_data, topic_memory, example_block)
    if not ai_block:
        ai_block = example_block.copy()

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:5]

    return jsonify(ai_block)


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
    exercise_block = data.get("exercise_block")

    # Process answers with SM2 spaced repetition algorithm
    process_ai_answers(username, str(block_id), answers, exercise_block)

    #raw adata, not important for now
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
    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block")
    print("Feedback generation data:", data, flush=True)

    if exercise_block:
        all_exercises = exercise_block.get("exercises", []) + exercise_block.get(
            "nextExercises", []
        )
        ex_map = {str(e.get("id")): e for e in all_exercises}

        total = 0
        correct = 0
        for ex_id, ans in answers.items():
            ex = ex_map.get(str(ex_id))
            if not ex:
                continue
            total += 1
            if str(ans).strip().lower() == str(ex.get("correctAnswer", "")).strip().lower():
                correct += 1

        summary = {"correct": correct, "total": total}
        feedback_prompt = generate_feedback_prompt(summary)
        return jsonify({"feedbackPrompt": feedback_prompt})

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

    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = fetch_custom(
        "SELECT vocab, translation, interval_days, next_review, ef, repetitions, created_at "
        "FROM vocab_log WHERE username = ?",
        (username,),
    )
    vocab_data = [
        {
            "type": "string",
            "word": row["vocab"],
            "translation": row.get("translation"),
            "sm2_interval": row.get("interval_days"),
            "sm2_due_date": row.get("next_review"),
            "sm2_ease": row.get("ef"),
            "repetitions": row.get("repetitions"),
            "sm2_last_review": row.get("created_at"),
            "quality": 0,
        }
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    ai_block = generate_new_exercises(vocab_data, topic_memory, example_block)
    if not ai_block:
        ai_block = example_block.copy()

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:5]
    print("Returning new training exercises", flush=True)

    return jsonify(ai_block)
