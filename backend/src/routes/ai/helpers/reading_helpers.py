"""Lesson and reading exercise routes."""

import datetime
from flask import request, jsonify, current_app  # type: ignore
from .. import ai_bp
from .helpers import fetch_topic_memory
from database import fetch_one, select_rows
from utils.spaced_repetition.vocab_utils import extract_words, save_vocab
from utils.helpers.helper import require_user
from .lesson_helpers import update_reading_memory_async
from utils.spaced_repetition.vocab_utils import save_vocab, extract_words
from utils.data.json_utils import extract_json
from utils.ai.prompts import (
    reading_exercise_prompt,
)
from utils.ai.ai_api import send_prompt

from .. import (
    EXERCISE_TEMPLATE,
    READING_TEMPLATE,
    CEFR_LEVELS,
    FEEDBACK_FILE,
)

def generate_reading_exercise(
    style: str,
    level: int,
    vocab: list | None = None,
    topic_memory: list | None = None,
) -> dict:
    """Create a short reading text with questions using Mistral.

    The text should reuse known vocabulary and explicitly train the learner's
    weak grammar topics provided via ``topic_memory``.
    """
    example = READING_TEMPLATE.copy()
    cefr_level = CEFR_LEVELS[max(0, min(level, 10))]
    example["level"] = cefr_level
    example["style"] = style

    extra = ""
    if vocab:
        words = ", ".join(v.get("word") for v in vocab[:10])
        extra += f"Use these vocabulary words: {words}. "
    if topic_memory:
        topics = {
            row.get("grammar") or row.get("topic")
            for row in topic_memory
            if row.get("grammar") or row.get("topic")
        }
        if topics:
            topics_str = ", ".join(list(topics)[:5])
            extra += (
                f"Focus on these weak topics: {topics_str}. "
                "Questions should explicitly train these weaknesses. "
            )

    user_prompt = reading_exercise_prompt(style, cefr_level, extra)

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.7,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extract_json(content)
            if parsed:
                return parsed
    except Exception as e:
        current_app.logger.error("Failed to generate reading exercise: %s", e)

    return example


def ai_reading_exercise():
    """Return a short reading exercise based on the user's level."""
    username = require_user()

    data = request.get_json() or {}
    style = data.get("style", "story")

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    vocab_rows = select_rows(
        "vocab_log",
        columns=["vocab", "translation"],
        where="username = ?",
        params=(username,),
    )
    vocab_data = [
        {"word": row["vocab"], "translation": row.get("translation")}
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    block = generate_reading_exercise(style, level, vocab_data, topic_memory)
    if not block or not block.get("text") or not block.get("questions"):
        return jsonify({"error": "Mistral error"}), 500
    for q in block.get("questions", []):
        q.pop("correctAnswer", None)
    return jsonify(block)


@ai_bp.route("/reading-exercise/submit", methods=["POST"])
def submit_reading_exercise():
    """Evaluate reading answers and update memory."""
    username = require_user()

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

    update_reading_memory_async(username, text)

    return jsonify({"summary": summary, "results": results})
