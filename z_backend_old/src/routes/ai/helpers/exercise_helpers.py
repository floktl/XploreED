"""Helper functions for exercise routes."""

import json
import random
import logging
import traceback
from threading import Thread
from datetime import datetime
from flask import current_app, jsonify
from database import insert_row, select_rows, fetch_one, select_one
from utils.spaced_repetition.level_utils import check_auto_level_up
from utils.helpers.helper import require_user
from .helpers import (
    _adjust_gapfill_results,
    fetch_topic_memory,
    _create_ai_block,
    store_user_ai_data,
    _ensure_schema,
    print_db_exercise_blocks
)
from utils.ai.translation_utils import _normalize_umlauts, _strip_final_punct
from .ai_evaluation_helpers import evaluate_answers_with_ai, process_ai_answers
import datetime
from utils.data.json_utils import extract_json
from utils.ai.prompt_utils import make_prompt, SYSTEM_PROMPT
from utils.ai.prompts import exercise_generation_prompt
from utils.ai.ai_api import send_request
from .. import (
    EXERCISE_TEMPLATE,
    CEFR_LEVELS,
)
import time
import threading
import re

# Configure logging to write to log.txt
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress werkzeug info logs except for errors
# import logging
# logging.getLogger('werkzeug').setLevel(logging.ERROR)

def log_exercise_event(event_type: str, username: str, details: dict = None):
    """Log exercise-related events with timestamp and user context."""
    log_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event_type": event_type,
        "username": username,
        "details": details or {}
    }
    # logger.info(f"EXERCISE_EVENT: {json.dumps(log_data, indent=2)}")

def log_ai_user_data(username: str, context: str):
    """Log the current ai_user_data row for the user with context info."""
    import logging
    logger = logging.getLogger(__name__)
    row = select_one(
        "ai_user_data",
        columns="*",
        where="username = ?",
        params=(username,),
    )
    # logger.info(f"[DB] ai_user_data for {username} after {context}: {json.dumps(row, indent=2, ensure_ascii=False)}")

def log_vocab_log(username: str, context: str):
    import logging
    logger = logging.getLogger(__name__)
    rows = select_rows(
        "vocab_log",
        columns="*",
        where="username = ?",
        params=(username,),
    )
    # logger.info(f"[DB] vocab_log for {username} after {context}: {json.dumps(rows, indent=2, ensure_ascii=False)}")

def fetch_vocab_and_topic_data(username: str) -> tuple[list, list]:
    """Return vocab and topic memory data for the given user."""
    vocab_rows = select_rows(
        "vocab_log",
        columns="vocab,translation",
        where="username = ?",
        params=(username,),
    ) or []
    vocab_data = [
        {"word": row["vocab"], "translation": row.get("translation")}
        for row in vocab_rows
    ]
    topic_rows = fetch_topic_memory(username) or []
    topic_data = [dict(row) for row in topic_rows]
    return vocab_data, topic_data



def compile_score_summary(exercises: list, answers: dict, id_map: dict) -> dict:
    """Return score summary for the evaluated answers."""
    mistakes = []
    correct = 0
    for ex in exercises:
        cid = str(ex.get("id"))
        user_ans = answers.get(cid, "")
        correct_ans = id_map.get(cid, "")
        # Ignore final . or ? for all exercise types
        user_ans = _strip_final_punct(user_ans)
        correct_ans = _strip_final_punct(correct_ans)
        # Normalize umlauts for both answers
        user_ans = _normalize_umlauts(user_ans)
        correct_ans = _normalize_umlauts(correct_ans)

        # 🔥 IMPROVED GRADING LOGIC 🔥
        is_correct = False
        if user_ans == correct_ans:
            is_correct = True
        else:
            # For gap-fill exercises, check if the answer makes grammatical sense
            exercise_type = ex.get("type", "")
            if exercise_type == "gap-fill":
                # Import the function from exercise_routes
                from ..exercise_routes import _check_gap_fill_correctness
                is_correct = _check_gap_fill_correctness(ex, user_ans, correct_ans)
            else:
                # For other exercise types, use exact match
                is_correct = user_ans == correct_ans

        if is_correct:
            correct += 1
        else:
            mistakes.append({
                "question": ex.get("question"),
                "your_answer": user_ans,
                "correct_answer": correct_ans,
            })
    return {"correct": correct, "total": len(exercises), "mistakes": mistakes}


def save_exercise_submission_async(
    username: str,
    block_id: str,
    answers: dict,
    exercises: list,
    exercise_block: dict = None,
) -> None:
    """Save exercise submission and update spaced repetition in a thread. Also update exercise history."""
    # print("\033[95m🔄 [TOPIC MEMORY FLOW] 🔄 Starting save_exercise_submission_async for user: {} block: {}\033[0m".format(username, block_id), flush=True)
    # print("\033[94m📊 [TOPIC MEMORY FLOW] Processing {} exercises with {} answers\033[0m".format(len(exercises), len(answers)), flush=True)

    log_exercise_event("submission_start", username, {
        "block_id": block_id,
        "answers_count": len(answers),
        "exercises_count": len(exercises),
        "answers": answers
    })

    from flask import current_app
    app = current_app._get_current_object()
    def run():
        # print("\033[93m⚡ [TOPIC MEMORY FLOW] ⚡ Background thread started for topic memory processing\033[0m", flush=True)
        with app.app_context():
            exercises_list = exercises if isinstance(exercises, list) else []

            # Create exercise block with topic if available
            if exercise_block and isinstance(exercise_block, dict):
                block_for_processing = {
                    "exercises": exercises_list,
                    "topic": exercise_block.get("topic", "general")
                }
                # print(f"🔍 [TOPIC MEMORY FLOW] 🔍 Using topic from exercise block: '{exercise_block.get('topic')}'", flush=True)
            else:
                block_for_processing = {"exercises": exercises_list}
                # print(f"🔍 [TOPIC MEMORY FLOW] 🔍 No exercise block provided, using default topic", flush=True)

            try:
                # print("\033[96m🧠 [TOPIC MEMORY FLOW] 🧠 Calling process_ai_answers to update topic memory and vocabulary\033[0m", flush=True)
                process_ai_answers(
                    username,
                    str(block_id),
                    answers,
                    block_for_processing,
                )
                # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ process_ai_answers completed successfully\033[0m", flush=True)

                # print("\033[96m📈 [TOPIC MEMORY FLOW] 📈 Checking for automatic level advancement\033[0m", flush=True)
                check_auto_level_up(username)
                # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Level advancement check completed\033[0m", flush=True)

                # print("\033[96m📚 [TOPIC MEMORY FLOW] 📚 Updating exercise history\033[0m", flush=True)
                new_questions = []
                for ex in exercises_list:
                    if isinstance(ex, dict) and ex.get("question"):
                        new_questions.append(ex["question"])
                update_exercise_history(username, new_questions)
                # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Exercise history updated\033[0m", flush=True)

                # print("\033[96m🔄 [TOPIC MEMORY FLOW] 🔄 Prefetching next exercises\033[0m", flush=True)
                prefetch_next_exercises(username)
                # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Next exercises prefetched\033[0m", flush=True)

                # print("\033[95m🎉 [TOPIC MEMORY FLOW] 🎉 All topic memory and exercise processing completed successfully!\033[0m", flush=True)

                # Set completion flag for frontend polling (simple in-memory approach)
                try:
                    # Use a simple in-memory completion tracking
                    if not hasattr(current_app, 'topic_memory_completion'):
                        current_app.topic_memory_completion = {}

                    completion_key = f"{username}:{block_id}"
                    current_app.topic_memory_completion[completion_key] = True
                except Exception as e:
                    print(f"\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ Failed to set completion flag: {e}\033[0m", flush=True)

            except Exception as e:
                print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Error during topic memory processing: {}\033[0m".format(str(e)), flush=True)
                error_details = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "block_id": block_id
                }
                logger.error(f"Failed to save exercise submission for user {username}: {e}")
                log_exercise_event("submission_error", username, error_details)
                current_app.logger.error("Failed to save exercise submission: %s", e)
    Thread(target=run, daemon=True).start()


def evaluate_exercises(exercises: list, answers: dict) -> tuple[dict | None, dict]:
    """Return evaluation result and id map after updating exercises."""
    evaluation = evaluate_answers_with_ai(exercises, answers)
    evaluation = _adjust_gapfill_results(exercises, answers, evaluation)
    if not evaluation:
        return None, {}

    id_map = {str(r.get("id")): r.get("correct_answer") for r in evaluation.get("results", [])}
    for ex in exercises:
        cid = str(ex.get("id"))
        if cid in id_map:
            ex["correctAnswer"] = id_map[cid]
    return evaluation, id_map


def parse_submission_data(data: dict) -> tuple[list, dict, str | None]:
    """Validate and extract exercises and answers from submission."""
    answers = data.get("answers", {})
    block = data.get("exercise_block")
    if not isinstance(block, dict):
        return [], {}, "Invalid or missing exercise block."
    exercises = block.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        return [], {}, "No exercises found to evaluate."
    return exercises, answers, None


def get_ai_exercises():
    """Return a new AI-generated exercise block for the user."""
    username = require_user()
    log_exercise_event("exercise_request_start", username, {})

    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = select_rows(
        "vocab_log",
        columns="vocab,translation,interval_days,next_review,ef,repetitions,last_review",
        where="username = ?",
        params=(username,),
    ) or []
    vocab_data = [
        {
            "word": row["vocab"],
            "translation": row.get("translation"),
            "interval_days": row.get("interval_days"),
            "next_review": row.get("next_review"),
            "ef": row.get("ef"),
            "repetitions": row.get("repetitions"),
            "last_review": row.get("last_review"),
        }
        for row in vocab_rows
    ]

    topic_memory = fetch_topic_memory(username) or []

    # Replace get_user_level with safe fallback
    row_user = fetch_one("users", "WHERE username = ?", (username,))
    level = row_user.get("skill_level", 0) if row_user is not None else 0

    recent_questions = get_recent_exercise_questions(username)

    ai_block = generate_new_exercises(
        vocabular=vocab_data,
        topic_memory=topic_memory,
        example_exercise_block=example_block,
        level=level,
        recent_questions=recent_questions,
        username=username,
    )

    if not ai_block or not ai_block.get("exercises"):
        error_msg = f"No exercises generated for user {username}"
        logger.error(error_msg)
        log_exercise_event("exercise_generation_empty", str(username), {})
        return jsonify({"error": "Mistral error"}), 500

    exercises = ai_block.get("exercises") if ai_block and isinstance(ai_block.get("exercises"), list) else []
    safe_recent_questions = recent_questions if recent_questions is not None else []
    filtered = [ex for ex in exercises if ex.get("question") not in safe_recent_questions]

    if ai_block is not None:
        ai_block["exercises"] = filtered[:3]
        exercises = ai_block["exercises"] if ai_block and isinstance(ai_block.get("exercises"), list) else []
        for ex in exercises:
            ex.pop("correctAnswer", None)

    log_exercise_event("exercise_request_complete", str(username), {
        "exercises_count": len(ai_block["exercises"]) if ai_block is not None and isinstance(ai_block.get("exercises"), list) else 0,
        "user_level": level,
        "vocab_count": len(vocab_data),
        "topic_memory_count": len(topic_memory)
    })

    return jsonify(ai_block)


# Global block ID counter (thread-safe)
_block_id_lock = threading.Lock()
_block_id_counter = int(time.time() * 1000)  # Start with ms timestamp

def get_next_block_id():
    global _block_id_counter
    with _block_id_lock:
        _block_id_counter += 1
        return _block_id_counter

# --- PATCH: Ensure block title is unique and numbered (must be after generate_new_exercises is defined) ---

def ensure_unique_block_title(block):
    if not block or not isinstance(block, dict):
        return block
    block_id = get_next_block_id()
    base_title = block.get("title", "(no title)")
    # Remove any existing [Block #...] suffix
    import re
    base_title = re.sub(r"\s*\[Block #\d+\]$", "", base_title)
    block["title"] = f"{base_title} [Block #{block_id}]"
    block["block_id"] = block_id
    return block


def generate_new_exercises(
    vocabular=None,
    topic_memory=None,
    example_exercise_block=None,
    level=None,
    recent_questions=None,
    username=None,
) -> dict | None:
    """Request a new exercise block from Mistral, passing recent questions to avoid repeats."""

    if recent_questions is None:
        recent_questions = []

    # Get recent topics to avoid repetition
    recent_topics = []
    if username:
        try:
            from .helpers import get_recent_exercise_topics
            recent_topics = get_recent_exercise_topics(username, limit=3)
        except Exception as e:
            logger.error(f"Failed to get recent topics: {e}")

    try:
        upcoming = sorted(
            (entry for entry in topic_memory if "next_repeat" in entry),
            key=lambda x: datetime.datetime.fromisoformat(x["next_repeat"]),
        )[:10]
        filtered_topic_memory = [
            {
                "grammar": entry.get("grammar"),
                "topic": entry.get("topic"),
                "skill_type": entry.get("skill_type"),
            }
            for entry in upcoming
        ]
    except Exception as e:
        logger.error(f"Failed to filter topic_memory: {e}")
        return None

    try:
        vocabular = [
            {
                "word": entry.get("word") or entry.get("vocab"),
                "translation": entry.get("translation"),
            }
            for entry in vocabular
            if (
                (entry.get("sm2_due_date") or entry.get("next_review"))
                and datetime.datetime.fromisoformat(
                    entry.get("sm2_due_date") or entry.get("next_review")
                ).date()
                <= datetime.date.today()
            )
        ][:10]
    except Exception as e:
        logger.error(f"Error stripping vocabulary fields: {e}")
        return None

    level_val = int(level or 0)
    level_val = max(0, min(level_val, 10))
    cefr_level = CEFR_LEVELS[level_val]
    example_exercise_block["level"] = cefr_level

    user_prompt = exercise_generation_prompt(
        level_val,
        cefr_level,
        example_exercise_block,
        vocabular,
        filtered_topic_memory,
        "\n".join(recent_questions),
        recent_topics,
    )

    # print(f"[DEBUG] Exercise generation prompt for user level {level_val} ({cefr_level}):", flush=True)
    # §print(f"[DEBUG] Prompt content: {user_prompt['content']}", flush=True)

    messages = make_prompt(user_prompt["content"], SYSTEM_PROMPT)
    # print(f"\033[92m[MISTRAL CALL] generate_new_exercises\033[0m", flush=True)
    response = send_request(messages, temperature=0.7)

    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]

        parsed = extract_json(content)
        if parsed is not None:
            parsed = _ensure_schema(parsed)
            parsed["level"] = cefr_level
            return parsed
        else:
            logger.error(f"Failed to parse JSON from Mistral response")
            return None
    else:
        logger.error(f"Mistral API request failed: {response.status_code} - {response.text}")
        return None


def _create_ai_block_with_variation(username: str, exclude_questions: list) -> dict | None:
    """Create an AI block with variation to ensure uniqueness for new users."""

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

    # Use the exclude_questions as recent questions to ensure uniqueness
    recent_questions = exclude_questions

    try:
        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level, recent_questions=recent_questions, username=username
        )
    except ValueError as e:
        logger.error(f"Failed to generate AI block with variation for new user {username}: {e}")
        return None

    if not ai_block or not ai_block.get("exercises"):
        return None

    exercises = ai_block.get("exercises", [])

    ai_block["exercises"] = exercises[:3]

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    return ai_block


def prefetch_next_exercises(username: str) -> None:
    """Generate and store a new next exercise block asynchronously, ensuring uniqueness."""
    from routes.ai.helpers.helpers import print_ai_user_data_titles
    # print_ai_user_data_titles(username)
    def run():
        try:
            # print(f"\033[95m[DEBUG] prefetch_next_exercises: username={repr(username)}\033[0m", flush=True)
            # Get recent questions first to ensure we have the latest
            recent_questions = get_recent_exercise_questions(username)
            # print(f"\033[94m[DEBUG] recent_questions={repr(recent_questions)}\033[0m", flush=True)

            # Create AI block for user {username}
            next_block = _create_ai_block(username)
            if next_block is not None:
                next_block["block_id"] = get_next_block_id()
            # Log the block_id instead of the title
            # print(f"[prefetch_next_exercises: next_block] Generated block id: {next_block.get('block_id', '(none)')}", flush=True)
            # log_generated_sentences(next_block, parent_function="prefetch_next_exercises: next_block")

            if next_block and isinstance(next_block, dict) and "exercises" in next_block:
                exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
                # print(f"\033[92m[DEBUG] exercises (before filtering)={repr(exercises)}\033[0m", flush=True)
                filtered = [ex for ex in exercises if ex.get("question") not in (recent_questions if recent_questions is not None else [])]
                # print(f"\033[93m[DEBUG] filtered exercises={repr(filtered)}\033[0m", flush=True)

                # Debug print right before changing the next block
                # print_ai_user_data_titles(username)
                # Print current block id in DB (not exercises)
                from database import fetch_one
                row = fetch_one("ai_user_data", "WHERE username = ?", (username,))
                current_id = None
                if row and row.get("exercises"):
                    import json as _json
                    block = _json.loads(row["exercises"]) if isinstance(row["exercises"], str) else row["exercises"]
                    current_id = block.get("block_id") if isinstance(block, dict) else None
                # print(f"\033[35m[DEBUG] Current block id in DB: {current_id if current_id else '(none)'}\033[0m", flush=True)
                # print(f"\033[91m[DEBUG] filtered (after shuffle)={repr(filtered)}\033[0m", flush=True)
                next_block["exercises"] = filtered[:3]
                # print(f"\033[96m[DEBUG] next_block (after filtering)={repr(next_block)}\033[0m", flush=True)
            else:
                print("\033[91m[prefetch_next_exercises] WARNING: next_block is None or invalid, skipping DB update.\033[0m", flush=True)
                next_block = None

            # Store next exercises for user {username}
            if next_block:
                # Promote previous next block to current block before updating next block
                from database import fetch_one
                row = fetch_one("ai_user_data", "WHERE username = ?", (username,))
                prev_next_block = None
                if row and row.get("next_exercises"):
                    import json as _json
                    prev_next_block = _json.loads(row["next_exercises"]) if isinstance(row["next_exercises"], str) else row["next_exercises"]
                if prev_next_block:
                    store_user_ai_data(
                        username,
                        {
                            "exercises": json.dumps(prev_next_block),
                        },
                        parent_function="prefetch_next_exercises"
                    )
                # print(f"\033[95m[DEBUG] Storing next_block for user {username}: {repr(next_block)}\033[0m", flush=True)
                store_user_ai_data(
                    username,
                    {
                        "next_exercises": json.dumps(next_block or {}),
                    },
                    parent_function="prefetch_next_exercises"
                )
                # print_db_exercise_blocks(username, "prefetch_next_exercises", parent_function="prefetch_next_exercises")

        except Exception as e:
            print(f"\033[91m[DEBUG] Error in prefetch_next_exercises for user {username}: {e}\033[0m", flush=True)
            logger.error(f"Error in prefetch_next_exercises for user {username}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    import threading
    threading.Thread(target=run, daemon=True).start()


def get_recent_exercise_questions(username, limit=20):
    row = fetch_one("ai_user_data", "WHERE username = ?", (username,), columns="exercise_history")
    if row and row.get("exercise_history"):
        try:
            history = json.loads(row["exercise_history"])[:limit]
            return history
        except Exception as e:
            logger.error(f"Failed to parse exercise history for user {username}: {e}")
            return []
    else:
        return []

def update_exercise_history(username, new_questions, limit=20):
    history = get_recent_exercise_questions(username, limit)
    updated = (new_questions + history)[:limit]
    store_user_ai_data(username, {"exercise_history": json.dumps(updated)})

    # Force database commit to ensure the update is visible immediately
    try:
        from database import get_connection
        with get_connection() as conn:
            conn.commit()
    except Exception as e:
        logger.error(f"Database commit failed for user {username}: {e}")


def print_exercise_block_sentences(block, context, color="\033[94m"):  # Default blue
    if not block:
        print(f"{color}[{context}] No exercise block to print.\033[0m", flush=True)
        return
    try:
        import json as _json
        if isinstance(block, str):
            block = _json.loads(block)
        title = block.get("title", "(no title)") if isinstance(block, dict) else "(no title)"
        print(f"{color}[{context}] Exercise block title: {title}\033[0m", flush=True)
    except Exception as e:
        print(f"\033[91m[{context}] Error printing exercise block: {e}\033[0m", flush=True)


def log_generated_sentences(block, parent_function=None):
    parent_str = f"[{parent_function}] " if parent_function else ""
    if not block or not isinstance(block, dict):
        print(f"{parent_str}No valid block to log generated title.", flush=True)
        return
    title = block.get("title", "(no title)")
    print(f"{parent_str}Generated block title: {title}", flush=True)


def _generate_blocks_for_new_user(username: str) -> dict | None:
    """Generate two unique blocks for new users by using different generation contexts."""

    # Generate first block with empty history
    ai_block = _create_ai_block(username)
    log_generated_sentences(ai_block, parent_function="_generate_blocks_for_new_user: current_block")
    if not ai_block or not ai_block.get("exercises"):
        return None

    # Assign unique block_id
    ai_block["block_id"] = get_next_block_id()

    # Extract questions from first block and update history
    new_questions = [ex.get("question") for ex in ai_block.get("exercises", []) if ex.get("question")]
    safe_new_questions = new_questions if new_questions is not None else []

    # Update exercise history and ensure it's committed
    update_exercise_history(username, safe_new_questions)
    log_ai_user_data(username, "after updating exercise history")

    # Force a small delay to ensure DB commit is visible
    import time
    time.sleep(0.1)

    # Generate second block with different approach to ensure uniqueness
    next_block = _create_ai_block_with_variation(username, safe_new_questions)
    log_generated_sentences(next_block, parent_function="_generate_blocks_for_new_user: next_block")

    if next_block and next_block.get("exercises"):
        # Assign unique block_id
        next_block["block_id"] = get_next_block_id()
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        filtered = [ex for ex in exercises if ex.get("question") not in safe_new_questions]
        next_block["exercises"] = filtered[:3]
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        for ex in exercises:
            ex.pop("correctAnswer", None)

    # Store both blocks
    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.datetime.now().isoformat(),
        },
        parent_function="_generate_blocks_for_new_user"
    )
    # print_db_exercise_blocks(username, "_generate_blocks_for_new_user", parent_function="_generate_blocks_for_new_user")
    # print_exercise_block_sentences(ai_block, "_generate_blocks_for_new_user: current_block", color="\033[92m")  # Green
    # print_exercise_block_sentences(next_block, "_generate_blocks_for_new_user: next_block", color="\033[96m")    # Cyan
    # log_ai_user_data(username, "after storing both blocks")

    return ai_block

def _generate_blocks_for_existing_user(username: str) -> dict | None:
    """Generate blocks for existing users with proper history management."""

    # Generate first block
    ai_block = _create_ai_block(username)
    log_generated_sentences(ai_block, parent_function="_generate_blocks_for_existing_user: current_block")
    if not ai_block or not ai_block.get("exercises"):
        return None

    # Assign unique block_id
    ai_block["block_id"] = get_next_block_id()

    # Extract questions from first block and update history
    new_questions = [ex.get("question") for ex in ai_block.get("exercises", []) if ex.get("question")]
    safe_new_questions = new_questions if new_questions is not None else []

    # Update exercise history and ensure it's committed
    update_exercise_history(username, safe_new_questions)
    log_ai_user_data(username, "after updating exercise history")

    # Force a small delay to ensure DB commit is visible
    import time
    time.sleep(0.1)

    # Get the updated recent questions to ensure uniqueness
    recent_questions = get_recent_exercise_questions(username)
    safe_recent_questions = recent_questions if recent_questions is not None else []

    # Generate next block with updated history
    next_block = _create_ai_block(username)
    log_generated_sentences(next_block, parent_function="_generate_blocks_for_existing_user: next_block")

    if next_block and next_block.get("exercises"):
        # Assign unique block_id
        next_block["block_id"] = get_next_block_id()
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        filtered = [ex for ex in exercises if ex.get("question") not in safe_recent_questions]
        next_block["exercises"] = filtered[:3]
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        for ex in exercises:
            ex.pop("correctAnswer", None)

    # Store both blocks
    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.datetime.now().isoformat(),
        },
        parent_function="_generate_blocks_for_existing_user"
    )
    # print_db_exercise_blocks(username, "_generate_blocks_for_existing_user", parent_function="_generate_blocks_for_existing_user")
    # print_exercise_block_sentences(ai_block, "_generate_blocks_for_existing_user: current_block", color="\033[92m")  # Green
    # print_exercise_block_sentences(next_block, "_generate_blocks_for_existing_user: next_block", color="\033[96m")    # Cyan
    # log_ai_user_data(username, "after storing both blocks")

    return ai_block


def generate_training_exercises(username: str) -> dict | None:
    """Generate current and next exercise blocks and store them. Ensures next block is unique."""
    # Check if this is a new user (no exercise history)
    recent_questions = get_recent_exercise_questions(username)
    if recent_questions is None:
        recent_questions = []
    is_new_user = len(recent_questions) == 0

    if is_new_user:
        return _generate_blocks_for_new_user(username)
    else:
        return _generate_blocks_for_existing_user(username)


def print_db_exercise_blocks(username, parent_str, parent_function=None):
    # Print block_id instead of title for current and next blocks
    row = fetch_one("ai_user_data", "WHERE username = ?", (username,))
    current_block = None
    next_block = None
    if row:
        if row.get("exercises"):
            try:
                current_block = json.loads(row["exercises"])
            except Exception:
                pass
        if row.get("next_exercises"):
            try:
                next_block = json.loads(row["next_exercises"])
            except Exception:
                pass
    if parent_function:
        parent_str = f"[{parent_function}] "
    else:
        parent_str = ""
    print(f"{parent_str}DB: Current block id:", flush=True)
    if current_block and isinstance(current_block, dict):
        print(f"  block_id: {current_block.get('block_id', '(none)')}", flush=True)
    else:
        print("  (none)", flush=True)
    print(f"{parent_str}DB: Next block id:", flush=True)
    if next_block and isinstance(next_block, dict):
        print(f"  block_id: {next_block.get('block_id', '(none)')}", flush=True)
    else:
        print("  (none)", flush=True)


