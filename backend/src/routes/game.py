"""Endpoints for the sentence ordering game."""

from flask import request, jsonify
import os
from utils.session.session_manager import session_manager
from app.blueprint import game_bp
from utils.spaced_repetition.vocab_utils import save_vocab, extract_words
from game.german_sentence_game import (
    LEVELS,
    get_scrambled_sentence,
    evaluate_order,
    save_result,
    generate_ai_sentence,
)
from app.extensions import limiter
from utils.data.db_utils import fetch_one

@game_bp.route("/level", methods=["POST"])
@limiter.limit("10/minute")
def level_game():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    level = data.get("level")
    if level is None:
        row = fetch_one("users", "WHERE username = ?", (username,))
        level = row.get("skill_level", 0) if row else 0
    level = int(level)
    sentence = generate_ai_sentence(username)
    if not sentence:
        sentence = LEVELS[level % len(LEVELS)]
    scrambled = get_scrambled_sentence(sentence)
    return jsonify({"level": level, "sentence": sentence, "scrambled": scrambled})


@game_bp.route("/level/submit", methods=["POST"])
@limiter.limit("20/minute")
def submit_level():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    level = int(data.get("level", 0))
    sentence = data.get("sentence") or LEVELS[level % len(LEVELS)]
    user_answer = data.get("answer", "").strip()

    correct, feedback = evaluate_order(user_answer, sentence)
    save_result(username, level, correct, user_answer)

    if correct:
        for word, art in extract_words(sentence):
            save_vocab(
                username,
                word,
                context=sentence,
                exercise=f"game_level_{level}",
                article=art,
            )

    def ansi_to_html(text):
        return (
            text.replace("\x1b[31m", '<span style="color:red;">')
            .replace("\x1b[32m", '<span style="color:green;">')
            .replace("\x1b[33m", '<span style="color:orange;">')
            .replace("\x1b[0m", "</span>")
        )

    return jsonify(
        {
            "correct": correct,
            "feedback": ansi_to_html(feedback),
            "correct_sentence": (
                sentence if os.getenv("FLASK_ENV") != "production" else None
            ),
        }
    )
