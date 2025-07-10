"""Training exercise endpoints."""

import json
import datetime
from flask import request, jsonify  # type: ignore

from . import ai_bp
from .helpers import (
    generate_training_exercises,
    prefetch_next_exercises,
    store_user_ai_data,
)
from database import select_one
from utils.helpers.helper import run_in_background, require_user


@ai_bp.route("/training-exercises", methods=["POST"])
def get_training_exercises():
    """Return AI-generated exercises and prefetch the next block."""
    username = require_user()
    print("Training request from user:", username, flush=True)

    data = request.get_json() or {}
    answers = data.get("answers", {})
    # print("Training answers received:", answers, flush=True)

    if answers:
        cached = select_one(
            "ai_user_data",
            columns="next_exercises",
            where="username = ?",
            params=(username,),
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

    cached = select_one(
        "ai_user_data",
        columns=["exercises", "next_exercises"],
        where="username = ?",
        params=(username,),
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


