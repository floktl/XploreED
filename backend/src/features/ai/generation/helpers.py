"""Helper functions used by AI routes."""

import random
from difflib import SequenceMatcher

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection, fetch_topic_memory
from features.ai.prompts.utils import make_prompt, FEEDBACK_SYSTEM_PROMPT
from features.ai.prompts import (
    feedback_generation_prompt,
    exercise_generation_prompt,
)
from shared.text_utils import _normalize_umlauts, _strip_final_punct
from external.mistral.client import send_request
from .exercise_creation import generate_new_exercises, get_recent_exercise_questions
from .. import (
    EXERCISE_TEMPLATE,
)
from shared.exceptions import DatabaseError


def _fix_exercise(ex: dict, idx: int) -> dict:
    """Normalize a single exercise dict."""
    # print(f"\033[34m[AI-HELPERS] Entering: [_fix_exercise] ex={repr(ex)}, idx={repr(idx)}\033[0m", flush=True)
    fixed = {
        "id": ex.get("id", f"ex{idx+1}"),
        "type": ex.get("type"),
        "question": ex.get("question") or ex.get("sentence") or "Missing question",
        "explanation": ex.get("explanation") or ex.get("hint") or "No explanation.",
    }
    if fixed["type"] == "gap-fill":
        fixed["options"] = ex.get("options", ["bin", "bist", "ist", "sind"])
    return fixed


def _ensure_schema(exercise_block: dict) -> dict:
    """Return exercise block with guaranteed keys."""
    title = exercise_block.get('title') if isinstance(exercise_block, dict) else None


    # Extract topic from title if not already present
    if title and "topic" not in exercise_block:
        import re
        match = re.search(r'in the context of (\w+)', title, re.IGNORECASE)
        if match:
            extracted_topic = match.group(1).lower()
            exercise_block["topic"] = extracted_topic
            pass
        else:
            exercise_block["topic"] = "general"
    elif title and "topic" in exercise_block:
        pass

    if "exercises" in exercise_block:
        exercise_block["exercises"] = [
            _fix_exercise(ex, i) for i, ex in enumerate(exercise_block["exercises"])
        ]

    return exercise_block


def store_user_ai_data(username: str, data: dict, parent_function=None):
    """Insert or update cached AI data for a user."""
    import logging
    logger = logging.getLogger(__name__)

    # Debug print removed to avoid DB lock issues
    title = data.get('title') if isinstance(data, dict) else None
    logger.info(f"Storing AI data for user {username}, data keys: {list(data.keys())}")

    try:
        exists = select_one(
            "ai_user_data",
            columns="username",
            where="username = ?",
            params=(username,),
        )
        logger.info(f"User {username} exists in ai_user_data: {exists is not None}")

        if exists:
            logger.info(f"Updating existing row for user {username}")
            update_row("ai_user_data", data, "username = ?", (username,))
            # print_db_exercise_blocks(username, "store_user_ai_data: update_row", parent_function)
        else:
            logger.info(f"Inserting new row for user {username}")
            data_with_user = {"username": username, **data}
            insert_row("ai_user_data", data_with_user)
            # print_db_exercise_blocks(username, "store_user_ai_data: insert_row", parent_function)

        logger.info(f"Successfully stored AI data for user {username}")
    except Exception as e:
        logger.error(f"Error storing user AI data for {username}: {e}")
        raise DatabaseError(f"Error storing user AI data: {str(e)}")


def _create_ai_block(username: str) -> dict | None:
    """Create a single AI exercise block for the user.

    Returns ``None`` if the Mistral API did not return a valid block.
    """
    # Debug print removed to avoid DB lock issues
    import logging
    logger = logging.getLogger(__name__)

    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = select_rows(
        "vocab_log",
        columns=[
            "vocab",
            "translation",
            "interval_days",
            "next_review",
            "level"
        ],
        where="username = ? AND level > 0",
        params=(username,),
        order_by="level DESC, next_review ASC",
        limit=10
    )

    topic_memory_rows = fetch_topic_memory(username)

    recent_questions = get_recent_exercise_questions(username, limit=20)

    # Generate new exercises
    ai_block = generate_new_exercises(
        vocabular=vocab_rows,
        topic_memory=topic_memory_rows,
        example_exercise_block=example_block,
        level=5,  # Default level
        recent_questions=recent_questions,
        username=username
    )

    if not ai_block:
        logger.error(f"Failed to generate AI block for user {username}")
        return None

    # Ensure proper schema
    ai_block = _ensure_schema(ai_block)

    return ai_block


def print_ai_user_data_titles(username):
    """Print only the block_id for current and next block for the given user to the backend logs, colorized and on two lines."""
    from core.database.connection import fetch_one
    row = fetch_one("ai_user_data", "WHERE username = ?", (username,))
    if not row:
        print(f"\033[91m| [DEBUG] No ai_user_data row for user {username}\033[0m", flush=True)
        return
    try:
        import json as _json
        exercises = row.get("exercises")
        next_exercises = row.get("next_exercises")
        current_id = None
        next_id = None
        if exercises:
            block = _json.loads(exercises) if isinstance(exercises, str) else exercises
            current_id = block.get("block_id") if isinstance(block, dict) else None
        if next_exercises:
            block = _json.loads(next_exercises) if isinstance(next_exercises, str) else next_exercises
            next_id = block.get("block_id") if isinstance(block, dict) else None
        print(f"\033[92m| [DEBUG] Current block id: {current_id if current_id else '(none)'}\033[0m", flush=True)
        print(f"\033[96m| [DEBUG] Next block id: {next_id if next_id else '(none)'}\033[0m", flush=True)
    except Exception as e:
        print(f"\033[91m| [DEBUG] Error printing ai_user_data block ids for user {username}: {e}\033[0m", flush=True)


# get_recent_exercise_topics moved to feedback_helpers.py
