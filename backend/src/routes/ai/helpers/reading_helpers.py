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
    feedback_generation_prompt,
)
from utils.ai.ai_api import send_prompt
import uuid
from .helpers import format_feedback_block

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
            topics_str = ", ".join(list(topics)[:10])  # Increased from 5 to 10
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


@ai_bp.route("/reading-exercise/submit", methods=["POST"])
def submit_reading_exercise():
    """Evaluate reading answers and update memory."""
    username = require_user()

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_id = data.get("exercise_id")
    cache = current_app.config.get("READING_EXERCISE_CACHE", {})
    exercise = cache.get(exercise_id)
    if not exercise:
        return jsonify({"error": "Exercise not found or expired"}), 400
    text = exercise.get("text", "")
    questions = exercise.get("questions", [])

    # Debug: log questions and their fields
    import logging
    logger = logging.getLogger("reading_debug")
    # for q in questions:
    #     logger.info(f"Q: {q}")
    #     logger.info(f"id: {q.get('id')}, question: {q.get('question')}, correctAnswer: {q.get('correctAnswer')}")

    correct = 0
    results = []
    feedback_blocks = []
    mistakes = []
    from utils.ai.ai_api import send_prompt
    def _normalize_umlauts(s):
        # Accept ae == ä, oe == ö, ue == ü (and vice versa)
        s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
        s = s.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
        return s

    def _strip_final_punct(s):
        s = s.strip()
        if s and s[-1] in ".?":
            return s[:-1].strip()
        return s

    for q in questions:
        qid = str(q.get("id"))
        sol = str(q.get("correctAnswer", "")).strip().lower()
        ans = str(answers.get(qid, "")).strip().lower()
        # Ignore final . or ? for all exercise types
        sol = _strip_final_punct(sol)
        ans = _strip_final_punct(ans)
        # Normalize umlauts for both answers
        sol = _normalize_umlauts(sol)
        ans = _normalize_umlauts(ans)
        status = "correct" if ans == sol else "incorrect"
        explanation = ""
        if status == "incorrect":
            # Generate a very short explanation using AI
            prompt = f"Explain in one short sentence (no more than 12 words) why the answer '{answers.get(qid, '')}' is incorrect for the question: {q.get('question')} (correct answer: {q.get('correctAnswer')})"
            try:
                resp = send_prompt(
                    "You are a helpful German teacher.",
                    {"role": "user", "content": prompt},
                    temperature=0.3
                )
                # current_app.logger.info(f"AI explanation response: {resp.status_code} {resp.text}")
                if resp.status_code == 200:
                    explanation = resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                current_app.logger.error(f"Failed to generate per-question explanation: {e}")
                explanation = ""
        block = format_feedback_block(
            user_answer=answers.get(qid, ""),
            correct_answer=q.get("correctAnswer"),
            alternatives=[],
            explanation=explanation,
            diff=None,
            status=status
        )
        feedback_blocks.append(block)
        if ans == sol:
            correct += 1
        else:
            mistakes.append({
                "question": q.get("question"),
                "your_answer": answers.get(qid, ""),
                "correct_answer": q.get("correctAnswer"),
            })
        results.append({"id": qid, "correct_answer": q.get("correctAnswer")})

    summary = {"correct": correct, "total": len(questions), "mistakes": mistakes}

    # Generate feedbackPrompt using Mistral
    feedbackPrompt = None
    try:
        from utils.ai.ai_api import send_prompt
        mistakes_text = "\n".join([
            f"Q: {m['question']}\nYour answer: {m['your_answer']}\nCorrect: {m['correct_answer']}" for m in mistakes
        ])
        prompt = feedback_generation_prompt(correct, len(questions), mistakes_text, "", "")
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.5,
        )
        if resp.status_code == 200:
            feedbackPrompt = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        current_app.logger.error("Failed to generate feedbackPrompt: %s", e)
        feedbackPrompt = None

    # Save vocab and update topic memory in background threads
    import threading
    def save_vocab_bg():
        for word, art in extract_words(text):
            save_vocab(username, word, context=text, exercise="reading", article=art)
    threading.Thread(target=save_vocab_bg, daemon=True).start()
    threading.Thread(target=update_reading_memory_async, args=(username, text), daemon=True).start()

    return jsonify({"summary": summary, "results": results, "feedbackPrompt": feedbackPrompt, "feedbackBlocks": feedback_blocks})
