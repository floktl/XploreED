"""Routes that provide AI generated exercises and text-to-speech."""

from utils.imports.imports import *
import json
import random
import datetime
from pathlib import Path
from difflib import SequenceMatcher
from utils.vocab_utils import split_and_clean, save_vocab, review_vocab_word, extract_words
from mock_data.script import (
    generate_new_exercises,
    generate_feedback_prompt,
    _extract_json,
)
from utils.grammar_utils import detect_language_topics
from utils.translation_utils import _update_single_topic, update_topic_memory_reading
from utils.helper import run_in_background
from flask import request, Response
from elevenlabs.client import ElevenLabs
import os
import requests

DEFAULT_TOPICS = [
    "dogs",
    "living",
    "family",
    "work",
    "shopping",
    "travel",
    "sports",
    "food",
    "hobbies",
    "weather",
]


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
    "vocabHelp": [],
}

READING_TEMPLATE = {
    "lessonId": "ai-reading",
    "style": "story",
    "text": "Guten Morgen!",
    "questions": [],
    "feedbackPrompt": "",
    "vocabHelp": [],
}

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}

CEFR_LEVELS = [
    "A1",
    "A1",
    "A2",
    "A2",
    "B1",
    "B1",
    "B2",
    "B2",
    "C1",
    "C1",
    "C2",
]


def store_user_ai_data(username: str, data: dict):
    """Insert or update cached AI data for a user."""
    exists = fetch_one_custom(
        "SELECT username FROM ai_user_data WHERE username = ?",
        (username,),
    )
    if exists:
        update_row("ai_user_data", data, "username = ?", (username,))
    else:
        data_with_user = {"username": username, **data}
        insert_row("ai_user_data", data_with_user)


def _create_ai_block(username: str) -> dict | None:
    """Create a single AI exercise block for the user.

    Returns ``None`` if the Mistral API did not return a valid block.
    """
    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = fetch_custom(
        "SELECT vocab, translation, interval_days, next_review, ef, repetitions, last_review "
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
            "sm2_last_review": row.get("last_review"),
            "quality": 0,
        }
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    try:
        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level
        )
    except ValueError as e:
        print("[_create_ai_block]", e, flush=True)
        return None
    if not ai_block or not ai_block.get("exercises"):
        return None

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    return ai_block


def generate_training_exercises(username: str) -> dict | None:
    """Generate current and next exercise blocks and store them.

    Returns ``None`` if a valid exercise block could not be generated.
    """

    ai_block = _create_ai_block(username)
    if not ai_block:
        return None
    next_block = _create_ai_block(username)

    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.datetime.now().isoformat(),
        },
    )

    return ai_block


def prefetch_next_exercises(username: str) -> None:
    """Generate and store a new next exercise block asynchronously."""
    next_block = _create_ai_block(username)
    if not next_block:
        return
    store_user_ai_data(
        username,
        {
            "next_exercises": json.dumps(next_block),
        },
    )


def evaluate_answers_with_ai(
    exercises: list, answers: dict, mode: str = "strict"
) -> dict | None:
    """Ask Mistral to evaluate student answers and return JSON results."""
    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]

    instructions = (
        "Evaluate these answers for a German exercise. "
        "Return JSON with 'pass' (true/false) and a 'results' list. "
        "Each result must include 'id' and 'correct_answer'. "
        "Mark pass true only if all answers are fully correct."
    )
    if mode == "argue":
        instructions = (
            "Reevaluate the student's answers carefully. "
            "Consider possible alternative correct solutions. "
            + instructions
        )

    user_prompt = {
        "role": "user",
        "content": instructions + "\n" + json.dumps(formatted, ensure_ascii=False),
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher."
                ),
            },
            user_prompt,
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=10)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = _extract_json(content)
            return parsed
    except Exception as e:
        current_app.logger.error("AI evaluation failed: %s", e)

    return None


def _adjust_gapfill_results(exercises: list, answers: dict, evaluation: dict | None) -> dict | None:
    """Ensure AI evaluation for gap-fill exercises matches provided options."""
    if not evaluation or "results" not in evaluation:
        return evaluation

    id_map = {str(r.get("id")): r.get("correct_answer", "") for r in evaluation.get("results", [])}

    for ex in exercises:
        if ex.get("type") != "gap-fill":
            continue
        cid = str(ex.get("id"))
        correct = id_map.get(cid, "")
        options = ex.get("options") or []
        if correct not in options and options:
            norm_corr = str(correct).strip().lower()
            best = options[0]
            best_score = -1.0
            for opt in options:
                opt_norm = opt.lower()
                score = SequenceMatcher(None, norm_corr, opt_norm).ratio()
                if score > best_score:
                    best = opt
                    best_score = score
                if opt_norm in norm_corr or norm_corr in opt_norm:
                    best = opt
                    break
            id_map[cid] = best

    evaluation["results"] = [{"id": k, "correct_answer": v} for k, v in id_map.items()]

    pass_val = True
    for ex in exercises:
        cid = str(ex.get("id"))
        ans = str(answers.get(cid, "")).strip().lower()
        corr = str(id_map.get(cid, "")).strip().lower()
        if ans != corr:
            pass_val = False
    evaluation["pass"] = pass_val
    return evaluation


def generate_reading_exercise(style: str, level: int) -> dict:
    """Create a short reading text with questions using Mistral."""
    example = READING_TEMPLATE.copy()
    cefr_level = CEFR_LEVELS[max(0, min(level, 10))]
    example["level"] = cefr_level
    example["style"] = style

    user_prompt = {
        "role": "user",
        "content": (
            "Create a short "
            f"{style} in German for level {cefr_level}. "
            "Return JSON with keys 'text', 'questions' (each with id, question, options, correctAnswer)."
        ),
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German teacher."},
            user_prompt,
        ],
        "temperature": 0.7,
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=20)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = _extract_json(content)
            if parsed:
                return parsed
    except Exception as e:
        current_app.logger.error("Failed to generate reading exercise: %s", e)

    return example


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


def fetch_topic_memory(username: str, include_correct: bool = False) -> list:
    """Retrieve topic memory rows for a user.

    If ``include_correct`` is ``False`` (default), only entries that were
    answered incorrectly are returned.
    """
    query = (
        "SELECT grammar, topic, skill_type, context, lesson_content_id, ease_factor, "
        "intervall, next_repeat, repetitions, last_review, correct, quality "
        "FROM topic_memory WHERE username = ?"
    )
    params = [username]
    if not include_correct:
        query += " AND (correct IS NULL OR correct = 0)"
    try:
        rows = fetch_custom(query, tuple(params))
        return rows if rows else []
    except Exception:
        # Table might not exist yet
        return []

def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    if not exercise_block:
        print("❌ Missing exercise block for processing", flush=True)
        return

    all_exercises = exercise_block.get("exercises", [])
    exercise_map = {str(e.get("id")): e for e in all_exercises}

    results = []
    reviewed: set[str] = set()
    for ex_id, user_ans in answers.items():
        ex = exercise_map.get(str(ex_id))
        if not ex:
            continue
        correct_ans = str(ex.get("correctAnswer", "")).strip().lower()
        user_ans = str(user_ans).strip().lower()
        is_correct = int(user_ans == correct_ans)
        quality = 5 if is_correct else 2
        features = detect_language_topics(
            f"{ex.get('question', '')} {correct_ans}"
        ) or ["unknown"]
        skill = ex.get("type", "")

        for feature in features:
            _update_single_topic(
                username,
                feature,
                skill,
                ex.get("question", ""),
                quality,
            )

            results.append(
                {
                    "topic_memory": {
                        "grammar": feature,
                        "skill_type": skill,
                        "quality": quality,
                        "correct": is_correct,
                    }
                }
            )

        words = set(
            [w for w, _ in extract_words(ex.get("question", ""))]
            + [w for w, _ in extract_words(correct_ans)]
        )
        for vocab in words:
            review_vocab_word(username, vocab, quality, seen=reviewed)

    # print("AI submission results (HJSON):\n", json.dumps(results, indent=2), flush=True)


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
        "SELECT vocab, translation, interval_days, next_review, ef, repetitions, last_review "
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
            "sm2_last_review": row.get("last_review"),
            "quality": 0,
        }
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    try:
        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level
        )
    except ValueError as e:
        print("[ai-exercise]", e, flush=True)
        return jsonify({"error": "Mistral error"}), 500
    if not ai_block or not ai_block.get("exercises"):
        return jsonify({"error": "Mistral error"}), 500

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]

    # remove solutions before sending to client
    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    return jsonify(ai_block)


@ai_bp.route("/ai-exercise/<block_id>/submit", methods=["POST"])
def submit_ai_exercise(block_id):
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Session ID:", session_id, "Username:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    # print("Received submission data (HJSON):\n", json.dumps(data, indent=2), flush=True)

    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block") or {}
    exercises = exercise_block.get("exercises", [])

    evaluation = evaluate_answers_with_ai(exercises, answers)
    evaluation = _adjust_gapfill_results(exercises, answers, evaluation)
    if not evaluation:
        return jsonify({"msg": "Evaluation failed"}), 500

    id_map = {str(r.get("id")): r.get("correct_answer") for r in evaluation.get("results", [])}
    for ex in exercises:
        cid = str(ex.get("id"))
        if cid in id_map:
            ex["correctAnswer"] = id_map[cid]

    mistakes = []
    correct = 0
    for ex in exercises:
        cid = str(ex.get("id"))
        user_ans = answers.get(cid, "")
        correct_ans = id_map.get(cid, "")
        if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
            correct += 1
        else:
            mistakes.append({
                "question": ex.get("question"),
                "your_answer": user_ans,
                "correct_answer": correct_ans,
            })

    summary = {"correct": correct, "total": len(exercises), "mistakes": mistakes}

    vocab_rows = fetch_custom(
        "SELECT vocab, translation FROM vocab_log WHERE username = ?",
        (username,),
    )
    vocab_data = [
        {"word": row["vocab"], "translation": row.get("translation")}
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_data = [dict(row) for row in topic_rows] if topic_rows else []

    feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

    def _background_save():
        try:
            process_ai_answers(
                username,
                str(block_id),
                answers,
                {"exercises": exercises},
            )
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

    run_in_background(_background_save)

    passed = bool(evaluation.get("pass"))
    run_in_background(prefetch_next_exercises, username)

    return jsonify({
        "feedbackPrompt": feedback_prompt,
        "pass": passed,
        "summary": summary,
        "results": evaluation.get("results", []),
    })


@ai_bp.route("/ai-exercise/<block_id>/argue", methods=["POST"])
def argue_ai_exercise(block_id):
    """Reevaluate answers when the student wants to argue with the AI."""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_block = data.get("exercise_block") or {}
    exercises = exercise_block.get("exercises", [])

    evaluation = evaluate_answers_with_ai(exercises, answers, mode="argue")
    evaluation = _adjust_gapfill_results(exercises, answers, evaluation)
    if not evaluation:
        return jsonify({"msg": "Evaluation failed"}), 500

    # Update topic memory asynchronously with the reevaluated results
    run_in_background(
        process_ai_answers,
        username,
        str(block_id),
        answers,
        {"exercises": exercises},
    )

    return jsonify(evaluation)


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
        all_exercises = exercise_block.get("exercises", [])
        evaluation = evaluate_answers_with_ai(all_exercises, answers)
        evaluation = _adjust_gapfill_results(all_exercises, answers, evaluation)
        id_map = {
            str(r.get("id")): r.get("correct_answer")
            for r in evaluation.get("results", [])
        } if evaluation else {}

        summary = {"correct": 0, "total": len(all_exercises), "mistakes": []}
        for ex in all_exercises:
            cid = str(ex.get("id"))
            user_ans = answers.get(cid, "")
            correct_ans = id_map.get(cid, "")
            if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
                summary["correct"] += 1
            else:
                summary["mistakes"].append(
                    {
                        "question": ex.get("question"),
                        "your_answer": user_ans,
                        "correct_answer": correct_ans,
                    }
                )

        vocab_rows = fetch_custom(
            "SELECT vocab, translation, interval_days, next_review, ef, repetitions, last_review "
            "FROM vocab_log WHERE username = ?",
            (username,),
        )
        vocab_data = [
            {
                "word": row["vocab"],
                "translation": row.get("translation"),
            }
            for row in vocab_rows
        ] if vocab_rows else []

        topic_rows = fetch_topic_memory(username)
        topic_data = [dict(row) for row in topic_rows] if topic_rows else []

        feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

        # Update topic memory asynchronously with the final evaluation results
        run_in_background(
            process_ai_answers,
            username,
            str(exercise_block.get("lessonId", "feedback")),
            answers,
            {"exercises": all_exercises},
        )

        return jsonify({
            "feedbackPrompt": feedback_prompt,
            "summary": summary,
            "results": evaluation.get("results", []),
        })

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

    if answers:
        cached = fetch_one_custom(
            "SELECT next_exercises FROM ai_user_data WHERE username = ?",
            (username,),
        )
        if cached and cached.get("next_exercises"):
            try:
                ai_block = json.loads(cached["next_exercises"])
            except Exception:
                ai_block = generate_training_exercises(username)
        else:
            ai_block = generate_training_exercises(username)

        if not ai_block:
            return jsonify({"error": "Mistral error"}), 500

        store_user_ai_data(
            username,
            {
                "exercises": json.dumps(ai_block),
                "exercises_updated_at": datetime.datetime.now().isoformat(),
            },
        )
        run_in_background(prefetch_next_exercises, username)
        print("Returned preloaded training exercises", flush=True)
        return jsonify(ai_block)

    cached = fetch_one_custom(
        "SELECT exercises, next_exercises FROM ai_user_data WHERE username = ?",
        (username,),
    )
    if cached and cached.get("exercises"):
        if not cached.get("next_exercises"):
            run_in_background(prefetch_next_exercises, username)
        try:
            return jsonify(json.loads(cached["exercises"]))
        except Exception:
            pass

    ai_block = generate_training_exercises(username)
    if not ai_block:
        return jsonify({"error": "Mistral error"}), 500
    print("Returning new training exercises", flush=True)
    return jsonify(ai_block)


@ai_bp.route("/ai-lesson", methods=["GET"])
def create_ai_lesson():
    """Return a mock HTML lesson based on the user's topic memory."""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    topic_rows = fetch_topic_memory(username)
    topics = [row.get("grammar") for row in topic_rows if row.get("grammar")] if topic_rows else []

    if topics:
        items = "".join(f"<li>{t}</li>" for t in topics[:5])
        html = (
            "<h2>AI Review Lesson</h2>"
            "<p>Let's review these topics:</p>"
            f"<ul>{items}</ul>"
        )
    else:
        html = """
    <h2>AI Review Lesson: Modalverben (Modal Verbs)</h2>
    <p>Modalverben sind Hilfsverben, die ein anderes Verb im Infinitiv begleiten. Sie drücken Notwendigkeit, Möglichkeit, Erlaubnis oder Wunsch aus.</p>

    <h3>🧠 Die wichtigsten Modalverben:</h3>
    <ul>
    <li><strong>müssen</strong> – to have to, must</li>
    <li><strong>können</strong> – to be able to, can</li>
    <li><strong>wollen</strong> – to want</li>
    <li><strong>sollen</strong> – should, ought to</li>
    <li><strong>dürfen</strong> – may, to be allowed to</li>
    <li><strong>mögen</strong> – to like</li>
    </ul>

    <h3>🔧 Satzbau (Word Order):</h3>
    <p>Im Präsens steht das Modalverb an zweiter Stelle, das Hauptverb am Ende des Satzes im Infinitiv:</p>
    <ul>
    <li>Ich <strong>muss</strong> heute <strong>lernen</strong>.</li>
    <li>Wir <strong>dürfen</strong> hier nicht <strong>parken</strong>.</li>
    </ul>

    <h3>🗣 Konjugation von <code>müssen</code> im Präsens:</h3>
    <table border="1" cellpadding="5">
    <tr><th>Person</th><th>Form</th></tr>
    <tr><td>ich</td><td>muss</td></tr>
    <tr><td>du</td><td>musst</td></tr>
    <tr><td>er/sie/es</td><td>muss</td></tr>
    <tr><td>wir</td><td>müssen</td></tr>
    <tr><td>ihr</td><td>müsst</td></tr>
    <tr><td>sie/Sie</td><td>müssen</td></tr>
    </table>

    <h3>🎯 Beispiele mit verschiedenen Modalverben:</h3>
    <ul>
    <li>Ich <strong>kann</strong> gut schwimmen. (I can swim well.)</li>
    <li>Du <strong>musst</strong> deine Hausaufgaben machen. (You must do your homework.)</li>
    <li>Er <strong>will</strong> Arzt werden. (He wants to become a doctor.)</li>
    <li>Wir <strong>sollen</strong> pünktlich sein. (We should be on time.)</li>
    <li>Ihr <strong>dürft</strong> nicht laut sprechen. (You are not allowed to speak loudly.)</li>
    </ul>

    <h3>📝 Übung:</h3>
    <p>Setze das passende Modalverb ein:</p>
    <ol>
    <li>Ich _______ ins Kino gehen. (Permission)</li>
    <li>Wir _______ jeden Tag Deutsch lernen. (Obligation)</li>
    <li>Du _______ deine Eltern anrufen. (Advice)</li>
    </ol>

    <h3>📌 Merke:</h3>
    <p>Modalverben helfen dir, deine Meinung, Absichten oder Pflichten auszudrücken. Übe sie regelmäßig in verschiedenen Kontexten!</p>
    """


    return Response(html, mimetype="text/html")


@ai_bp.route("/weakness-lesson", methods=["GET"])
def ai_weakness_lesson():
    """Return a short HTML lesson focused on the user's weakest topic."""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    row = fetch_one_custom(
        "SELECT grammar, skill_type FROM topic_memory WHERE username = ? "
        "ORDER BY ease_factor ASC, repetitions DESC LIMIT 1",
        (username,),
    )

    grammar = row.get("grammar") if row else None
    skill = row.get("skill_type") if row else None
    if not grammar:
        grammar = "Modalverben"
        skill = "grammar"

    user_prompt = {
        "role": "user",
        "content": (
            "Create a short HTML lesson in English for a German learner. "
            f"Explain the topic '{grammar}' ({skill}) and give three training tips."
            "Return only valid HTML."
        ),
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German teacher."},
            user_prompt,
        ],
        "temperature": 0.7,
    }

    cached = fetch_one_custom(
        "SELECT weakness_lesson, weakness_topic FROM ai_user_data WHERE username = ?",
        (username,),
    )
    if cached and cached.get("weakness_lesson") and cached.get("weakness_topic") == grammar:
        return Response(cached["weakness_lesson"], mimetype="text/html")

    try:
        resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=20)
        if resp.status_code == 200:
            html = resp.json()["choices"][0]["message"]["content"].strip()
            store_user_ai_data(
                username,
                {
                    "weakness_lesson": html,
                    "weakness_topic": grammar,
                    "lesson_updated_at": datetime.datetime.now().isoformat(),
                },
            )
            return Response(html, mimetype="text/html")
    except Exception as e:
        current_app.logger.error("Failed to generate weakness lesson: %s", e)
    return jsonify({"error": "Mistral error"}), 500


@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German teacher."},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=10)
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"].strip()
            return jsonify({"answer": answer})
    except Exception as e:
        print("[ask_ai] Error:", e, flush=True)

    return jsonify({"error": "AI error"}), 500


@ai_bp.route("/ask-ai-stream", methods=["POST"])
def ask_ai_stream():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German teacher."},
            {"role": "user", "content": question},
        ],
        "temperature": 0.3,
        "stream": True,
    }

    def generate():
        try:
            with requests.post(
                MISTRAL_API_URL,
                headers=HEADERS,
                json=payload,
                stream=True,
                timeout=20,
            ) as resp:
                buffer = ""
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        if line.strip() == "data: [DONE]":
                            break
                        if line.startswith("data:"):
                            line = line[len("data:"):].strip()
                        data = json.loads(line)
                        chunk = (
                            data.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if chunk:
                            buffer += chunk

                            # ✨ Simple Markdown: Convert "**text**" to bold
                            buffer = buffer.replace("**", "")

                            # ✨ Flush as paragraph on sentence end
                            if buffer.endswith((".", "!", "?")):
                                structured = {
                                    "type": "paragraph",
                                    "text": buffer.strip()
                                }
                                yield f"data: {json.dumps(structured, ensure_ascii=False)}\n\n"
                                buffer = ""
                    except Exception:
                        continue
                if buffer.strip():
                    yield f"data: {json.dumps({ 'type': 'paragraph', 'text': buffer.strip() }, ensure_ascii=False)}\n\n"
        except Exception as e:
            current_app.logger.error("Streaming error: %s", e)
        yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


@ai_bp.route("/reading-exercise", methods=["POST"])
def ai_reading_exercise():
    """Return a short reading exercise based on the user's level."""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    style = data.get("style", "story")

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    block = generate_reading_exercise(style, level)
    if not block or not block.get("text") or not block.get("questions"):
        return jsonify({"error": "Mistral error"}), 500
    for q in block.get("questions", []):
        q.pop("correctAnswer", None)
    return jsonify(block)


@ai_bp.route("/reading-exercise/submit", methods=["POST"])
def submit_reading_exercise():
    """Evaluate reading answers and update memory."""
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise = data.get("exercise") or {}
    text = exercise.get("text", "")
    questions = exercise.get("questions", [])

    correct = 0
    results = []
    for q in questions:
        qid = str(q.get("id"))
        sol = str(q.get("correctAnswer", "")).strip().lower()
        ans = str(answers.get(qid, "")).strip().lower()
        if ans == sol:
            correct += 1
        results.append({"id": qid, "correct_answer": q.get("correctAnswer")})

    summary = {"correct": correct, "total": len(questions), "mistakes": []}
    for q in questions:
        qid = str(q.get("id"))
        if str(answers.get(qid, "")).strip().lower() != str(q.get("correctAnswer", "")).strip().lower():
            summary["mistakes"].append(
                {
                    "question": q.get("question"),
                    "your_answer": answers.get(qid, ""),
                    "correct_answer": q.get("correctAnswer"),
                }
            )

    for word, art in extract_words(text):
        save_vocab(username, word, context=text, exercise="reading", article=art)

    def _background_save():
        features = detect_language_topics(text) or ["unknown"]
        qualities = {feat: 5 for feat in features}
        update_topic_memory_reading(username, text, qualities)
        for q in questions:
            is_correct = str(answers.get(str(q.get("id")), "")).strip().lower() == str(q.get("correctAnswer", "")).strip().lower()
            features = detect_language_topics(f"{q.get('question','')} {q.get('correctAnswer','')}") or ["unknown"]
            for feat in features:
                quality = 5 if is_correct else 2
                _update_single_topic(username, feat, "reading", q.get("question",""), quality)

    run_in_background(_background_save)

    vocab_rows = fetch_custom(
        "SELECT vocab, translation FROM vocab_log WHERE username = ?",
        (username,),
    )
    vocab_data = [
        {"word": row["vocab"], "translation": row.get("translation")}
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_data = [dict(row) for row in topic_rows] if topic_rows else []

    feedback_prompt = generate_feedback_prompt(summary, vocab_data, topic_data)

    return jsonify({
        "feedbackPrompt": feedback_prompt,
        "pass": correct == len(questions),
        "summary": summary,
        "results": results,
    })
