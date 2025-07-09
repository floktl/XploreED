"""Training exercise endpoints."""

import json
import datetime
from flask import request, jsonify

from . import ai_bp
from .helpers import (
    generate_training_exercises,
    prefetch_next_exercises,
    store_user_ai_data,
)
from database import fetch_one_custom
from utils.helpers.helper import run_in_background, session_manager


@ai_bp.route("/training-exercises", methods=["POST"])
def get_training_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    print("Training request from user:", username, flush=True)

    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    answers = data.get("answers", {})
    # print("Training answers received:", answers, flush=True)

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
        # print("Returned preloaded training exercises", flush=True)
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
    # print("Returning new training exercises", flush=True)
    return jsonify(ai_block)


