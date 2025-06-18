"""Combined progress test endpoints."""

from utils.imports.imports import *
from game.german_sentence_game import generate_ai_sentence, get_scrambled_sentence, evaluate_order, LEVELS
from routes.ai import generate_training_exercises, evaluate_answers_with_ai, generate_reading_exercise
from utils.translation_utils import translate_to_german, evaluate_translation_ai
from utils.db_utils import fetch_one, update_row
import random

ENGLISH_SENTENCES = [
    "I am hungry.",
    "We are going to the park.",
    "They like to read books.",
    "Tomorrow I will visit my friend.",
]

progress_test_bp = Blueprint("progress_test", __name__, url_prefix="/api")

@progress_test_bp.route("/progress-test", methods=["GET"])
def get_progress_test():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    sentence = generate_ai_sentence(username) or LEVELS[level % len(LEVELS)]
    scrambled = get_scrambled_sentence(sentence)

    exercise_block = generate_training_exercises(username)
    for ex in exercise_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    reading = generate_reading_exercise("story", level)
    for q in reading.get("questions", []):
        q.pop("correctAnswer", None)

    english = random.choice(ENGLISH_SENTENCES)

    return jsonify({
        "sentence": sentence,
        "scrambled": scrambled,
        "exercise_block": exercise_block,
        "reading": reading,
        "english": english,
    })


@progress_test_bp.route("/progress-test/submit", methods=["POST"])
def submit_progress_test():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    answers = data.get("answers", {})

    sentence = data.get("sentence", "")
    order_answer = answers.get("order", "")
    correct_order, _ = evaluate_order(order_answer, sentence)

    ex_pass = bool(answers.get("ai_pass"))

    english = data.get("english", "")
    translation_answer = answers.get("translation", "")
    german = translate_to_german(english, username)
    trans_correct, _ = evaluate_translation_ai(english, german, translation_answer)

    reading_block = data.get("reading") or {}
    reading_answers = answers.get("reading", {})
    reading_correct = 0
    questions = reading_block.get("questions", [])
    for q in questions:
        qid = str(q.get("id"))
        if str(reading_answers.get(qid, "")).strip().lower() == str(q.get("correctAnswer", "")).strip().lower():
            reading_correct += 1
    reading_pass = questions and reading_correct == len(questions)

    total = sum([
        int(correct_order),
        int(ex_pass),
        int(trans_correct),
        int(reading_pass),
    ])

    passed = total >= 3

    if passed:
        row = fetch_one("users", "WHERE username = ?", (username,))
        level = row.get("skill_level", 0) if row else 0
        update_row("users", {"skill_level": level + 1}, "username = ?", (username,))

    return jsonify({"passed": passed, "score": total})

