"""Helper functions for exercise routes."""

import json
import random
import logging
import traceback
from threading import Thread
from datetime import datetime
from flask import current_app, jsonify # add jsonify import
from database import insert_row, select_rows, fetch_one, select_one
from utils.spaced_repetition.level_utils import check_auto_level_up
from utils.helpers.helper import require_user
from .. import EXERCISE_TEMPLATE
from .helpers import (
    _adjust_gapfill_results,
    fetch_topic_memory,
    _create_ai_block,
    store_user_ai_data,
    _ensure_schema
)
from .ai_evaluation_helpers import evaluate_answers_with_ai, process_ai_answers # ensure process_ai_answers is imported
import datetime
from utils.data.json_utils import extract_json
from utils.ai.prompt_utils import make_prompt, SYSTEM_PROMPT
from utils.ai.prompts import exercise_generation_prompt
from utils.ai.ai_api import send_request
from .. import (
    EXERCISE_TEMPLATE,
    CEFR_LEVELS,
)

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


def _strip_final_punct(s):
    s = s.strip()
    if s and s[-1] in ".?":
        return s[:-1].strip()
    return s


def _normalize_umlauts(s):
    # Accept ae == ä, oe == ö, ue == ü (and vice versa)
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    s = s.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    return s


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
        if user_ans == correct_ans:
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
) -> None:
    """Save exercise submission and update spaced repetition in a thread. Also update exercise history and prefetch next block."""
    log_exercise_event("submission_start", username, {
        "block_id": block_id,
        "answers_count": len(answers),
        "exercises_count": len(exercises),
        "answers": answers
    })

    from flask import current_app
    app = current_app._get_current_object()
    def run():
        with app.app_context():
            try:
                # logger.info(f"Processing AI answers for user {username}, block {block_id}")
                process_ai_answers(
                    username,
                    str(block_id),
                    answers,
                    {"exercises": exercises},
                )
                # logger.info(f"Checking auto level up for user {username}")
                check_auto_level_up(username)

                # logger.info(f"Inserting exercise submission for user {username}, block {block_id}")
                insert_row(
                    "exercise_submissions",
                    {
                        "username": username,
                        "block_id": str(block_id),
                        "answers": json.dumps(answers),
                    },
                )

                # Update exercise history with new questions
                new_questions = [ex.get("question") for ex in exercises if ex.get("question")]
                # logger.info(f"Updating exercise history for user {username} with {len(new_questions)} new questions")
                update_exercise_history(username, new_questions)

                # Prefetch next block with updated history
                # logger.info(f"Prefetching next exercises for user {username}")
                prefetch_next_exercises(username)

                log_exercise_event("submission_complete", username, {
                    "block_id": block_id,
                    "new_questions_count": len(new_questions)
                })

            except Exception as e:
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

    # logger.info(f"Fetching vocab data for user {username}")
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
    # logger.info(f"Found {len(vocab_data)} vocab entries for user {username}")

    # logger.info(f"Fetching topic memory for user {username}")
    topic_memory = fetch_topic_memory(username) or []
    # logger.info(f"Found {len(topic_memory)} topic memory entries for user {username}")

    # logger.info(f"Fetching user level for user {username}")
    level = get_user_level(username)
    # logger.info(f"User {username} has skill level {level}")

    # logger.info(f"Getting recent exercise questions for user {username}")
    recent_questions = get_recent_exercise_questions(username)
    # logger.info(f"Found {len(recent_questions) if recent_questions else 0} recent questions for user {username}")

    # logger.info(f"Generating new exercises for user {username} with level {level}")
    ai_block = generate_new_exercises(
        vocabular=vocab_data,
        topic_memory=topic_memory,
        example_exercise_block=example_block,
        level=level,
        recent_questions=recent_questions,
    )
    # logger.info(f"Generated AI block for user {username}: {ai_block is not None}")

    if not ai_block or not ai_block.get("exercises"):
        error_msg = f"No exercises generated for user {username}"
        logger.error(error_msg)
        log_exercise_event("exercise_generation_empty", username, {})
        return jsonify({"error": "Mistral error"}), 500

    # logger.info(f"Filtering exercises for user {username} to avoid recent questions")
    filtered = [ex for ex in ai_block["exercises"] if ex.get("question") not in recent_questions]
    # logger.info(f"After filtering: {len(filtered)} exercises for user {username}")

    tries = 0
    while len(filtered) < 3 and tries < 3:
        # logger.info(f"Retry {tries + 1} for user {username} - need more exercises")
        ai_block = generate_new_exercises(
            vocab_data or [],
            topic_memory or [],
            example_block or {},
            level=level,
            recent_questions=recent_questions or []
        )
        if not ai_block or not ai_block.get("exercises"):
            break
        filtered = [ex for ex in ai_block["exercises"] if ex.get("question") not in recent_questions]
        tries += 1

    random.shuffle(filtered)
    ai_block["exercises"] = filtered[:3]

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    log_exercise_event("exercise_request_complete", username, {
        "exercises_count": len(ai_block.get("exercises", [])),
        "user_level": level,
        "vocab_count": len(vocab_data),
        "topic_memory_count": len(topic_memory)
    })

    # logger.info(f"Returning {len(ai_block.get('exercises', []))} exercises for user {username}")
    return jsonify(ai_block)


def generate_new_exercises(
    vocabular=None,
    topic_memory=None,
    example_exercise_block=None,
    level=None,
    recent_questions=None,
) -> dict | None:
    """Request a new exercise block from Mistral, passing recent questions to avoid repeats."""
    # logger.info(f"Starting generate_new_exercises with level={level}, vocab_count={len(vocabular) if vocabular else 0}, topic_count={len(topic_memory) if topic_memory else 0}")

    if recent_questions is None:
        recent_questions = []

    # logger.info(f"Processing topic memory for exercise generation")
    try:
        upcoming = sorted(
            (entry for entry in topic_memory if "next_repeat" in entry),
            key=lambda x: datetime.datetime.fromisoformat(x["next_repeat"]),
        )[:10]  # Increased from 5 to 10
        filtered_topic_memory = [
            {
                "grammar": entry.get("grammar"),
                "topic": entry.get("topic"),
                "skill_type": entry.get("skill_type"),
            }
            for entry in upcoming
        ]
        # logger.info(f"Filtered topic memory: {len(filtered_topic_memory)} entries")
    except Exception as e:
        logger.error(f"Failed to filter topic_memory: {e}")
        return None

    # logger.info(f"Processing vocabulary for exercise generation")
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
        ][:10]  # Limit to 10 vocab entries to keep API calls shorter
        # logger.info(f"Filtered vocabulary: {len(vocabular)} entries")
    except Exception as e:
        logger.error(f"Error stripping vocabulary fields: {e}")
        return None

    level_val = int(level or 0)
    level_val = max(0, min(level_val, 10))
    cefr_level = CEFR_LEVELS[level_val]
    example_exercise_block["level"] = cefr_level

    # logger.info(f"Preparing prompt with level={level_val}, cefr_level={cefr_level}, recent_questions_count={len(recent_questions)}")

    # Add recent questions to the prompt
    recent_str = "\n".join(recent_questions)
    user_prompt = exercise_generation_prompt(
        level_val,
        cefr_level,
        example_exercise_block,
        vocabular,
        filtered_topic_memory,
        recent_str,
    )

    # logger.info(f"Sending request to Mistral API")
    messages = make_prompt(user_prompt["content"], SYSTEM_PROMPT)
    response = send_request(messages)

    if response.status_code == 200:
        # logger.info(f"Mistral API response successful")
        content = response.json()["choices"][0]["message"]["content"]
        # logger.info(f"Raw API response length: {len(content)} characters")

        parsed = extract_json(content)
        if parsed is not None:
            # logger.info(f"Successfully parsed JSON response")
            parsed = _ensure_schema(parsed)
            parsed["level"] = cefr_level
            # logger.info(f"Exercise generation successful, returning {len(parsed.get('exercises', []))} exercises")
            return parsed
        else:
            logger.error(f"Failed to parse JSON from Mistral response")
            return None
    else:
        logger.error(f"Mistral API request failed: {response.status_code} - {response.text}")
        return None


def generate_training_exercises(username: str) -> dict | None:
    """Generate current and next exercise blocks and store them. Ensures next block is unique."""
    # logger.info(f"Starting generate_training_exercises for user {username}")

    # Check if this is a new user (no exercise history)
    recent_questions = get_recent_exercise_questions(username)
    is_new_user = len(recent_questions) == 0

    if is_new_user:
        # logger.info(f"Detected new user {username}, generating two unique blocks with different contexts")
        return _generate_blocks_for_new_user(username)
    else:
        # logger.info(f"Existing user {username} with {len(recent_questions)} recent questions")
        return _generate_blocks_for_existing_user(username)


def _generate_blocks_for_new_user(username: str) -> dict | None:
    """Generate two unique blocks for new users by using different generation contexts."""
    # logger.info(f"Generating blocks for new user {username}")

    # Generate first block with empty history
    # logger.info(f"Generating first block for new user {username}")
    ai_block = _create_ai_block(username)
    if not ai_block or not ai_block.get("exercises"):
        # logger.error(f"Failed to generate first block for new user {username}")
        return None

    # logger.info(f"Generated first block for new user {username} with {len(ai_block.get('exercises', []))} exercises")

    # Extract questions from first block and update history
    new_questions = [ex.get("question") for ex in ai_block.get("exercises", []) if ex.get("question")]
    # logger.info(f"Extracted {len(new_questions)} questions from first block for new user {username}")

    # Update exercise history and ensure it's committed
    update_exercise_history(username, new_questions)
    log_ai_user_data(username, "after updating exercise history")

    # Force a small delay to ensure DB commit is visible
    import time
    time.sleep(0.1)

    # Generate second block with different approach to ensure uniqueness
    # logger.info(f"Generating second block for new user {username} with different context")
    next_block = _create_ai_block_with_variation(username, new_questions)

    if next_block and next_block.get("exercises"):
        # logger.info(f"Generated second block for new user {username} with {len(next_block.get('exercises', []))} exercises")

        # Filter out questions that are already in recent history
        filtered = [ex for ex in next_block["exercises"] if ex.get("question") not in new_questions]
        # logger.info(f"After filtering duplicates for new user {username}: {len(filtered)} exercises remain")

        tries = 0
        while len(filtered) < 3 and tries < 3:
            # logger.info(f"Retry {tries + 1} for new user {username} - need more unique exercises")
            next_block = _create_ai_block_with_variation(username, new_questions)
            if not next_block or not next_block.get("exercises"):
                break
            filtered = [ex for ex in next_block["exercises"] if ex.get("question") not in new_questions]
            tries += 1

        random.shuffle(filtered)
        next_block["exercises"] = filtered[:3]
        # logger.info(f"Final second block for new user {username}: {len(next_block.get('exercises', []))} exercises")
    else:
        # logger.warning(f"Failed to generate second block for new user {username}")
        pass

    # Store both blocks
    # logger.info(f"Storing exercise blocks for new user {username}")
    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.datetime.now().isoformat(),
        },
    )
    log_ai_user_data(username, "after storing both blocks")

    # logger.info(f"Successfully completed generate_training_exercises for new user {username}")
    return ai_block


def _generate_blocks_for_existing_user(username: str) -> dict | None:
    """Generate blocks for existing users with proper history management."""
    # logger.info(f"Generating blocks for existing user {username}")

    # Generate first block
    ai_block = _create_ai_block(username)
    if not ai_block or not ai_block.get("exercises"):
        # logger.error(f"Failed to generate first block for existing user {username}")
        return None

    # logger.info(f"Generated first block for existing user {username} with {len(ai_block.get('exercises', []))} exercises")

    # Extract questions from first block and update history
    new_questions = [ex.get("question") for ex in ai_block.get("exercises", []) if ex.get("question")]
    # logger.info(f"Extracted {len(new_questions)} questions from first block for existing user {username}")

    # Update exercise history and ensure it's committed
    update_exercise_history(username, new_questions)
    log_ai_user_data(username, "after updating exercise history")

    # Force a small delay to ensure DB commit is visible
    import time
    time.sleep(0.1)

    # Get the updated recent questions to ensure uniqueness
    recent_questions = get_recent_exercise_questions(username)
    # logger.info(f"Updated recent questions for existing user {username}: {len(recent_questions)} questions")

    # Generate next block with updated history
    # logger.info(f"Generating next block for existing user {username} with updated history")
    next_block = _create_ai_block(username)

    if next_block and next_block.get("exercises"):
        # logger.info(f"Generated next block for existing user {username} with {len(next_block.get('exercises', []))} exercises")

        # Filter out questions that are already in recent history
        filtered = [ex for ex in next_block["exercises"] if ex.get("question") not in recent_questions]
        # logger.info(f"After filtering duplicates for existing user {username}: {len(filtered)} exercises remain")

        tries = 0
        while len(filtered) < 3 and tries < 3:
            # logger.info(f"Retry {tries + 1} for existing user {username} - need more unique exercises")
            next_block = _create_ai_block(username)
            if not next_block or not next_block.get("exercises"):
                break
            filtered = [ex for ex in next_block["exercises"] if ex.get("question") not in recent_questions]
            tries += 1

        random.shuffle(filtered)
        next_block["exercises"] = filtered[:3]
        # logger.info(f"Final next block for existing user {username}: {len(next_block.get('exercises', []))} exercises")
    else:
        # logger.warning(f"Failed to generate next block for existing user {username}")
        pass

    # Store both blocks
    # logger.info(f"Storing exercise blocks for existing user {username}")
    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.datetime.now().isoformat(),
        },
    )
    log_ai_user_data(username, "after storing both blocks")

    # logger.info(f"Successfully completed generate_training_exercises for existing user {username}")
    return ai_block


def _create_ai_block_with_variation(username: str, exclude_questions: list) -> dict | None:
    """Create an AI block with variation to ensure uniqueness for new users."""
    # logger.info(f"Creating AI block with variation for new user {username} with {len(exclude_questions)} exclude questions")

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
    # logger.info(f"Using {len(recent_questions)} exclude questions as recent questions for variation")

    try:
        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level, recent_questions=recent_questions
        )
    except ValueError as e:
        logger.error(f"Failed to generate AI block with variation for new user {username}: {e}")
        return None

    if not ai_block or not ai_block.get("exercises"):
        # logger.error(f"No exercises generated in variation block for new user {username}")
        return None

    exercises = ai_block.get("exercises", [])
    # logger.info(f"Generated {len(exercises)} exercises in variation block for new user {username}")

    # Ensure we have at least 3 exercises, retry if needed
    if len(exercises) < 3:
        # logger.warning(f"Only {len(exercises)} exercises in variation block for new user {username}, retrying...")
        # Try to generate more exercises
        for attempt in range(2):  # Try up to 2 more times
            try:
                additional_block = generate_new_exercises(
                    vocab_data, topic_memory, example_block, level=level, recent_questions=recent_questions
                )
                if additional_block and additional_block.get("exercises"):
                    additional_exercises = additional_block.get("exercises", [])
                    # Add unique exercises
                    existing_questions = {ex.get("question") for ex in exercises}
                    for ex in additional_exercises:
                        if ex.get("question") not in existing_questions and len(exercises) < 3:
                            exercises.append(ex)
                            existing_questions.add(ex.get("question"))
                    # logger.info(f"Added {len(exercises)} total exercises in variation block for new user {username}")
                    if len(exercises) >= 3:
                        break
            except Exception as e:
                logger.error(f"Failed to generate additional exercises in variation block for new user {username}: {e}")

    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]  # Take exactly 3 exercises

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    # logger.info(f"Successfully created AI block with variation for new user {username}: {len(ai_block.get('exercises', []))} exercises")
    return ai_block


def prefetch_next_exercises(username: str) -> None:
    """Generate and store a new next exercise block asynchronously, ensuring uniqueness."""
    # logger.info(f"Starting prefetch_next_exercises for user {username}")

    def run():
        try:
            # Get recent questions first to ensure we have the latest
            recent_questions = get_recent_exercise_questions(username)
            # logger.info(f"Got {len(recent_questions) if recent_questions else 0} recent questions for user {username}")

            # logger.info(f"Creating AI block for user {username}")
            next_block = _create_ai_block(username)
            # logger.info(f"AI block created for user {username}: {next_block is not None}")

            if next_block and next_block.get("exercises"):
                # logger.info(f"Filtering exercises for user {username} to avoid duplicates")
                filtered = [ex for ex in next_block["exercises"] if ex.get("question") not in recent_questions]
                # logger.info(f"After filtering: {len(filtered)} exercises for user {username}")

                tries = 0
                while len(filtered) < 3 and tries < 3:
                    # logger.info(f"Retry {tries + 1} for user {username} - need more exercises")
                    next_block = _create_ai_block(username)
                    if not next_block or not next_block.get("exercises"):
                        break
                    filtered = [ex for ex in next_block["exercises"] if ex.get("question") not in recent_questions]
                    tries += 1

                random.shuffle(filtered)
                next_block["exercises"] = filtered[:3]
                # logger.info(f"Final next block for user {username}: {len(next_block.get('exercises', []))} exercises")
            else:
                # logger.warning(f"No exercises in next block for user {username}")
                pass

            # logger.info(f"Storing next exercises for user {username}")
            store_user_ai_data(
                username,
                {
                    "next_exercises": json.dumps(next_block or {}),
                },
            )
            # logger.info(f"Successfully stored next exercises for user {username}")

        except Exception as e:
            logger.error(f"Error in prefetch_next_exercises for user {username}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    Thread(target=run).start()


def get_recent_exercise_questions(username, limit=20):
    # logger.info(f"Getting recent exercise questions for user {username}, limit={limit}")
    row = fetch_one("ai_user_data", "WHERE username = ?", (username,), columns="exercise_history")
    if row and row.get("exercise_history"):
        try:
            history = json.loads(row["exercise_history"])[:limit]
            # logger.info(f"Found {len(history)} recent questions for user {username}")
            return history
        except Exception as e:
            logger.error(f"Failed to parse exercise history for user {username}: {e}")
            return []
    else:
        # logger.info(f"No exercise history found for user {username}")
        return []

def update_exercise_history(username, new_questions, limit=20):
    # logger.info(f"Updating exercise history for user {username} with {len(new_questions)} new questions, limit={limit}")
    history = get_recent_exercise_questions(username, limit)
    updated = (new_questions + history)[:limit]
    # logger.info(f"Updated history for user {username}: {len(updated)} total questions")
    store_user_ai_data(username, {"exercise_history": json.dumps(updated)})

    # Force database commit to ensure the update is visible immediately
    try:
        from database import get_connection
        with get_connection() as conn:
            conn.commit()
        # logger.info(f"Database commit successful for user {username}")
    except Exception as e:
        logger.error(f"Database commit failed for user {username}: {e}")

    # logger.info(f"Successfully stored updated exercise history for user {username}")


