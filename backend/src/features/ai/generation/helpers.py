"""Helper functions used by AI routes."""

import random
from difflib import SequenceMatcher

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection, fetch_topic_memory
from features.ai.prompts.utils import make_prompt, FEEDBACK_SYSTEM_PROMPT
from features.ai.prompts import (
    feedback_generation_prompt,
    exercise_generation_prompt,
)
from features.ai.evaluation.translation_evaluation import _normalize_umlauts, _strip_final_punct
from external.mistral.client import send_request
from .. import (
    EXERCISE_TEMPLATE,
)


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
    print(f"🔍 [TITLE DEBUG] 🔍 Title: '{title}'", flush=True)
    print(f"🔍 [TOPIC DEBUG] 🔍 Has topic field: {'topic' in exercise_block}", flush=True)
    if 'topic' in exercise_block:
        print(f"🔍 [TOPIC DEBUG] 🔍 Current topic: '{exercise_block.get('topic')}'", flush=True)
    # print(f"\033[34m[AI-HELPERS] Entering: [_ensure_schema] title={repr(title)}\033[0m", flush=True)

    # Extract topic from title if not already present
    if title and "topic" not in exercise_block:
        import re
        match = re.search(r'in the context of (\w+)', title, re.IGNORECASE)
        if match:
            extracted_topic = match.group(1).lower()
            exercise_block["topic"] = extracted_topic
            print(f"🔍 [TOPIC EXTRACTION] 🔍 Extracted topic '{extracted_topic}' from title: '{title}'", flush=True)
        else:
            exercise_block["topic"] = "general"
            print(f"🔍 [TOPIC EXTRACTION] 🔍 No topic found in title: '{title}', using 'general'", flush=True)
    elif title and "topic" in exercise_block:
        print(f"🔍 [TOPIC DEBUG] 🔍 Topic already exists, skipping extraction", flush=True)

    if "exercises" in exercise_block:
        exercise_block["exercises"] = [
            _fix_exercise(ex, i) for i, ex in enumerate(exercise_block["exercises"])
        ]

    return exercise_block


# generate_feedback_prompt moved to feedback_helpers.py


def print_db_exercise_blocks(username, context, parent_function=None):
    # Debug print removed to avoid DB lock issues
    from core.database.connection import fetch_one
    row = fetch_one("ai_user_data", "WHERE username = ?", (username,))
    parent_str = f"[{parent_function}] " if parent_function else ""
    if not row:
        print(f"\033[91m{parent_str}[{context}] No ai_user_data row for user {username}\033[0m", flush=True)
        return
    try:
        exercises = row.get("exercises")
        next_exercises = row.get("next_exercises")
        print(f"\033[95m{parent_str}[{context}] DB: Current block id:\033[0m", flush=True)
        if exercises:
            import json as _json
            block = _json.loads(exercises) if isinstance(exercises, str) else exercises
            block_id = block.get("block_id") if isinstance(block, dict) else None
            print(f"{block_id if block_id else '(none)'}", flush=True)
        else:
            print("(none)", flush=True)
        print(f"\033[95m{parent_str}[{context}] DB: Next block id:\033[0m", flush=True)
        if next_exercises:
            block = _json.loads(next_exercises) if isinstance(next_exercises, str) else next_exercises
            block_id = block.get("block_id") if isinstance(block, dict) else None
            print(f"{block_id if block_id else '(none)'}", flush=True)
        else:
            print("(none)", flush=True)
    except Exception as e:
        print(f"\033[91m{parent_str}[{context}] Error printing DB blocks: {e}\033[0m", flush=True)


def store_user_ai_data(username: str, data: dict, parent_function=None):
    """Insert or update cached AI data for a user."""
    # Debug print removed to avoid DB lock issues
    title = data.get('title') if isinstance(data, dict) else None
    # print(f"\033[34m[AI-HELPERS] Entering: [store_user_ai_data], parent_function={repr(parent_function)}\033[0m", flush=True)
    exists = select_one(
        "ai_user_data",
        columns="username",
        where="username = ?",
        params=(username,),
    )
    if exists:
        update_row("ai_user_data", data, "username = ?", (username,))
        # print_db_exercise_blocks(username, "store_user_ai_data: update_row", parent_function)
    else:
        data_with_user = {"username": username, **data}
        insert_row("ai_user_data", data_with_user)
        # print_db_exercise_blocks(username, "store_user_ai_data: insert_row", parent_function)


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
            "ef",
            "repetitions",
            "last_review",
        ],
        where="username = ?",
        params=(username,),
    )
    vocab_data = [
        {
            "type": "string",
            "word": row["vocab"],
            "translation": row.get("translation"),
            "sm2_interval": row.get("interval_days"),
            "sm2_due_date": row.get("next_review"),
            "sm2_ease": row.get("ef"),
            "repetitions": row.get("repetitions"),
            "sm2_last_review": row.get("last_review"),
            "quality": 0,
        }
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

    # Get recent questions to avoid duplicates
    try:
        from .exercise_creation import get_recent_exercise_questions
        recent_questions = get_recent_exercise_questions(username)
        # logger.info(f"_create_ai_block: Got {len(recent_questions)} recent questions for user {username}")
    except Exception as e:
        logger.error(f"_create_ai_block: Failed to get recent questions for user {username}: {e}")
        recent_questions = []

    try:
        from .exercise_creation import generate_new_exercises

        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level, recent_questions=recent_questions, username=username
        )
    except ValueError as e:
        logger.error(f"_create_ai_block: Failed to generate exercises for user {username}: {e}")
        print("[_create_ai_block]", e, flush=True)
        return None

    if not ai_block or not ai_block.get("exercises"):
        logger.error(f"_create_ai_block: No exercises generated for user {username}")
        return None

    # Ensure we have at least 3 exercises, retry if needed
    if len(ai_block.get("exercises", [])) < 3:
        # logger.wa
        # Try to generate more exercises
        for attempt in range(2):  # Try up to 2 more times
            try:
                additional_block = generate_new_exercises(
                    vocab_data, topic_memory, example_block, level=level, recent_questions=recent_questions, username=username
                )
                if additional_block and additional_block.get("exercises"):
                    additional_exercises = additional_block.get("exercises", [])
                    # Add unique exercises
                    existing_questions = {ex.get("question") for ex in ai_block.get("exercises", [])}
                    for ex in additional_exercises:
                        if ex.get("question") not in existing_questions and len(ai_block.get("exercises", [])) < 3:
                            ai_block["exercises"].append(ex)
                            existing_questions.add(ex.get("question"))
                    # logger.info(f"_create_ai_block: Added {len(exercises)} total exercises for user {username}")
                    if len(ai_block.get("exercises", [])) >= 3:
                        break
            except Exception as e:
                logger.error(f"_create_ai_block: Failed to generate additional exercises for user {username}: {e}")

    ai_block["exercises"] = ai_block["exercises"][:3]  # Take exactly 3 exercises

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    # logger.info(f"_create_ai_block: Final block has {len(ai_block.get('exercises', []))} exercises for user {username}")
    return ai_block


# _adjust_gapfill_results moved to feedback_helpers.py


# format_feedback_block moved to feedback_helpers.py

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
