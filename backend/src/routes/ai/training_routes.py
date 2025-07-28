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
    # print("\033[92m[ENTER] get_training_exercises\033[0m", flush=True)
    """Get training exercises for the user."""
    username = require_user()
    # logger.info(f"Training exercises request from user: {username}")

    data = request.get_json()
    answers = data.get("answers", {})
    # logger.info(f"Training request data for user {username}: answers_count={len(answers)}")

    if answers:
        # logger.info(f"User {username} has answers, checking cached next exercises")
        # Check if we have cached next exercises
        row = select_one(
            "ai_user_data",
            columns="exercises, next_exercises",
            where="username = ?",
            params=(username,),
        )
        if row and row.get("next_exercises"):
            try:
                cached_next = json.loads(row["next_exercises"])
                if cached_next and cached_next.get("exercises"):
                    # logger.info(f"Found cached next exercises for user {username}")
                    # logger.info(f"Successfully loaded cached next exercises for user {username}")
                    # print(f"🔍 [TRAINING DEBUG] 🔍 Retrieved exercise block with topic: '{cached_next.get('topic')}'", flush=True)
                    # print(f"🔍 [TRAINING DEBUG] 🔍 Retrieved exercise block keys: {list(cached_next.keys())}", flush=True)
                    block_id = cached_next.get('block_id') if cached_next and isinstance(cached_next, dict) else None
                    # print(f"\033[91m[EXIT] get_training_exercises block_id={block_id if block_id else '(no block_id)'}\033[0m", flush=True)
                    return jsonify(cached_next)
            except Exception as e:
                logger.error(f"Failed to parse cached next exercises for user {username}: {e}")

        # logger.info(f"No cached next exercises for user {username}, generating new ones")
        try:
            ai_block = generate_training_exercises(username)
            if ai_block and ai_block.get("exercises"):
                # logger.info(f"Storing exercises for user {username}")
                # print(f"🔍 [TRAINING DEBUG] 🔍 Storing exercise block with topic: '{ai_block.get('topic')}'", flush=True)
                # print(f"🔍 [TRAINING DEBUG] 🔍 Exercise block keys: {list(ai_block.keys())}", flush=True)
                store_user_ai_data(
                    username,
                    {
                        "current_exercises": json.dumps(ai_block),
                        "next_exercises": json.dumps(ai_block),  # For now, store same as next
                    },
                )
                # logger.info(f"Running prefetch next exercises for user {username}")
                run_in_background(prefetch_next_exercises, username)
                # logger.info(f"Returning preloaded training exercises for user {username}")
                block_id = ai_block.get('block_id') if ai_block and isinstance(ai_block, dict) else None
                # print(f"\033[91m[EXIT] get_training_exercises block_id={block_id if block_id else '(no block_id)'}\033[0m", flush=True)
                return jsonify(ai_block)
        except Exception as e:
            logger.error(f"Failed to generate training exercises for user {username}")
            # print("\033[91m[EXIT] get_training_exercises\033[0m", flush=True)
            return jsonify({"error": "Failed to generate exercises"}), 500
    else:
        # logger.info(f"User {username} has no answers, checking cached exercises")
        # Check if we have cached current exercises
        row = select_one(
            "ai_user_data",
            columns="exercises, next_exercises",
            where="username = ?",
            params=(username,),
        )
        if row and row.get("exercises"):
            try:
                cached_current = json.loads(row["exercises"])
                if cached_current and cached_current.get("exercises"):
                    # logger.info(f"Found cached exercises for user {username}")
                    # print(f"🔍 [TRAINING DEBUG] 🔍 Retrieved current exercise block with topic: '{cached_current.get('topic')}'", flush=True)
                    # print(f"🔍 [TRAINING DEBUG] 🔍 Retrieved current exercise block keys: {list(cached_current.keys())}", flush=True)
                    block_id = cached_current.get('block_id') if cached_current and isinstance(cached_current, dict) else None
                    # print(f"\033[91m[EXIT] get_training_exercises block_id={block_id if block_id else '(no block_id)'}\033[0m", flush=True)
                    return jsonify(cached_current)
            except Exception as e:
                logger.error(f"Failed to parse cached exercises for user {username}: {e}")

        # logger.info(f"No cached next exercises for user {username}, prefetching")
        try:
            ai_block = generate_training_exercises(username)
            if ai_block and ai_block.get("exercises"):
                # logger.info(f"Returning cached exercises for user {username}")
                # print("\033[91m[EXIT] get_training_exercises\033[0m", flush=True)
                return jsonify(ai_block)
        except Exception as e:
            logger.error(f"Failed to generate training exercises for user {username}")
            # print("\033[91m[EXIT] get_training_exercises\033[0m", flush=True)
            return jsonify({"error": "Failed to generate exercises"}), 500

    # logger.info(f"Generating new training exercises for user {username}")
    try:
        ai_block = generate_training_exercises(username)
        if ai_block and ai_block.get("exercises"):
            # logger.info(f"Returning new training exercises for user {username}")
            # print("\033[91m[EXIT] get_training_exercises\033[0m", flush=True)
            return jsonify(ai_block)
        else:
            # print("\033[91m[EXIT] get_training_exercises\033[0m", flush=True)
            return jsonify({"error": "No exercises generated"}), 500
    except Exception as e:
        logger.error(f"Failed to generate training exercises for user {username}")
        # print("\033[91m[EXIT] get_training_exercises\033[0m", flush=True)
        return jsonify({"error": "Failed to generate exercises"}), 500


