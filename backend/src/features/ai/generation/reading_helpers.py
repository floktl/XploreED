"""Lesson and reading exercise routes."""

from flask import request, jsonify, current_app  # type: ignore
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection, fetch_topic_memory
from api.middleware.auth import require_user
from shared.text_utils import _extract_json as extract_json
from features.ai.prompts import reading_exercise_prompt
from external.mistral.client import send_prompt
import uuid
from shared.exceptions import DatabaseError

from .. import (
    READING_TEMPLATE,
    CEFR_LEVELS,
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
            topics_str = ", ".join(list(topics)[:10])  # Increased from 5 to 10
            extra += (
                f"Focus on these weak topics: {topics_str}. "
                "Questions should explicitly train these weaknesses. "
            )

    user_prompt = reading_exercise_prompt(style, cefr_level, extra)
    # print(f"\033[92m[MISTRAL CALL] generate_reading_exercise\033[0m", flush=True)
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
        raise DatabaseError(f"Failed to generate reading exercise: {str(e)}")

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
    topic_memory = [dict(row) for row in topic_rows] if isinstance(topic_rows, list) else []

    block = generate_reading_exercise(style, level, vocab_data, topic_memory)
    if not block or not block.get("text") or not block.get("questions"):
        return jsonify({"error": "Mistral error"}), 500

    # --- Secure server-side storage of correct answers ---
    exercise_id = str(uuid.uuid4())
    # Store the full block (with correct answers) in a cache
    cache = current_app.config.setdefault("READING_EXERCISE_CACHE", {})
    cache[exercise_id] = block

    # Remove correctAnswer before sending to frontend (work on a copy)
    import copy
    block_to_send = copy.deepcopy(block)
    for q in block_to_send.get("questions", []):
        q.pop("correctAnswer", None)
    block_to_send["exercise_id"] = exercise_id
    return jsonify(block_to_send)
