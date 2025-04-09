# backend/routes/game.py
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from session_manager import session_manager
import os
from german_sentence_game import LEVELS, get_scrambled_sentence, evaluate_order, save_result

limiter = Limiter(get_remote_address)
game_bp = Blueprint("game", __name__, url_prefix="/api")

@game_bp.route("/level", methods=["POST"])
@limiter.limit("10/minute")
def level_game():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    level = int(data.get("level", 0))
    sentence = LEVELS[level]
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
    user_answer = data.get("answer", "").strip()

    correct, feedback = evaluate_order(user_answer, LEVELS[level])
    save_result(username, level, correct, user_answer)

    def ansi_to_html(text):
        return text.replace("\x1b[31m", '<span style="color:red;">')\
                .replace("\x1b[32m", '<span style="color:green;">')\
                .replace("\x1b[33m", '<span style="color:orange;">')\
                .replace("\x1b[0m", '</span>')

    return jsonify({
        "correct": correct,
        "feedback": ansi_to_html(feedback),
        "correct_sentence": LEVELS[level] if os.getenv("FLASK_ENV") != "production" else None
    })
