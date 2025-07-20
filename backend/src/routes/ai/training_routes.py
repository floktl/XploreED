"""Training exercise endpoints."""

import json
import datetime
import logging
from flask import request, jsonify  # type: ignore

from . import ai_bp
from .helpers.helpers import (
    store_user_ai_data,
)
from .helpers.exercise_helpers import (
    generate_training_exercises,
    prefetch_next_exercises,
)
from database import select_one
from utils.helpers.helper import run_in_background, require_user

logger = logging.getLogger(__name__)


@ai_bp.route("/training-exercises", methods=["POST"])
def get_training_exercises():
    """Return AI-generated exercises and prefetch the next block."""
    username = require_user()
    logger.info(f"Training exercises request from user: {username}")
    # print("Training request from user:", username, flush=True)

    data = request.get_json() or {}
    answers = data.get("answers", {})
    logger.info(f"Training request data for user {username}: answers_count={len(answers)}")
    # print("Training answers received:", answers, flush=True)

    if answers:
        logger.info(f"User {username} has answers, checking cached next exercises")
        cached = select_one(
            "ai_user_data",
            columns="next_exercises",
            where="username = ?",
            params=(username,),
        )
        if cached and cached.get("next_exercises"):
            logger.info(f"Found cached next exercises for user {username}")
            try:
                ai_block = json.loads(cached["next_exercises"])
                logger.info(f"Successfully loaded cached next exercises for user {username}")
            except Exception as e:
                logger.error(f"Failed to parse cached next exercises for user {username}: {e}")
                ai_block = generate_training_exercises(username)
        else:
            logger.info(f"No cached next exercises for user {username}, generating new ones")
            ai_block = generate_training_exercises(username)

        if not ai_block:
            logger.error(f"Failed to generate training exercises for user {username}")
            return jsonify({"error": "Mistral error"}), 500

        logger.info(f"Storing exercises for user {username}")
        store_user_ai_data(
            username,
            {
                "exercises": json.dumps(ai_block),
                "exercises_updated_at": datetime.datetime.now().isoformat(),
            },
        )
        logger.info(f"Running prefetch next exercises for user {username}")
        run_in_background(prefetch_next_exercises, username)
        # print("Returned preloaded training exercises", flush=True)
        logger.info(f"Returning preloaded training exercises for user {username}")
        return jsonify(ai_block)

    logger.info(f"User {username} has no answers, checking cached exercises")
    cached = select_one(
        "ai_user_data",
        columns=["exercises", "next_exercises"],
        where="username = ?",
        params=(username,),
    )
    if cached and cached.get("exercises"):
        logger.info(f"Found cached exercises for user {username}")
        if not cached.get("next_exercises"):
            logger.info(f"No cached next exercises for user {username}, prefetching")
            run_in_background(prefetch_next_exercises, username)
        try:
            logger.info(f"Returning cached exercises for user {username}")
            return jsonify(json.loads(cached["exercises"]))
        except Exception as e:
            logger.error(f"Failed to parse cached exercises for user {username}: {e}")
            pass

    logger.info(f"Generating new training exercises for user {username}")
    ai_block = generate_training_exercises(username)
    if not ai_block:
        logger.error(f"Failed to generate training exercises for user {username}")
        return jsonify({"error": "Mistral error"}), 500
    # print("Returning new training exercises", flush=True)
    logger.info(f"Returning new training exercises for user {username}")
    return jsonify(ai_block)


