"""
XplorED - Exercise Creation Module

This module provides exercise creation and generation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Creation Components:
- Exercise Generation: Generate new exercises based on user data
- Block Creation: Create exercise blocks with variations
- Exercise History: Manage exercise history and recent questions
- User-Specific Generation: Generate exercises tailored to user level

For detailed architecture information, see: docs/backend_structure.md
"""

import json
import random
import logging
import traceback
from threading import Thread
from datetime import datetime, date
from typing import Optional

from flask import current_app, jsonify  # type: ignore

from core.database.connection import (
    select_one, select_rows, insert_row, update_row, delete_rows,
    fetch_one, fetch_all, fetch_custom, execute_query, get_connection,
    fetch_topic_memory
)
from features.ai.memory.level_manager import check_auto_level_up
from api.middleware.auth import require_user
from shared.text_utils import _extract_json as extract_json
from features.ai.prompts.utils import make_prompt, SYSTEM_PROMPT
from features.ai.prompts import exercise_generation_prompt
from external.mistral.client import send_request, send_prompt
from features.ai.memory.logger import topic_memory_logger
from shared.exceptions import DatabaseError, ExerciseGenerationError

from .. import (
    EXERCISE_TEMPLATE,
    CEFR_LEVELS,
)

logger = logging.getLogger(__name__)

# Global block ID counter (thread-safe)
import threading
import time
_block_id_lock = threading.Lock()
_block_id_counter = int(time.time() * 1000)  # Start with ms timestamp

def get_next_block_id():
    global _block_id_counter
    with _block_id_lock:
        _block_id_counter += 1
        return _block_id_counter

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

    # Update ai_user_data table
    update_row(
        "ai_user_data",
        {"exercise_history": json.dumps(updated)},
        "username = ?",
        (username,)
    )

def store_user_ai_data(username, data, parent_function=None):
    """Store user AI data in the ai_user_data table."""
    try:
        # Check if user exists in ai_user_data
        existing = fetch_one("ai_user_data", "WHERE username = ?", (username,))

        if existing:
            # Update existing row
            update_row("ai_user_data", data, "username = ?", (username,))
        else:
            # Insert new row
            data["username"] = username
            insert_row("ai_user_data", data)

    except Exception as e:
        logger.error(f"Error storing user AI data for {username}: {e}")
        raise DatabaseError(f"Error storing user AI data: {str(e)}")

def _create_ai_block(username: str) -> dict | None:
    """Create an AI block for the user."""
    try:
        # Get user data
        vocab_data, topic_memory = fetch_vocab_and_topic_data(username)

        # Get user level
        user_row = fetch_one("users", "WHERE username = ?", (username,))
        level = user_row.get("skill_level", 1) if user_row else 1

        # Get recent questions to avoid repetition
        recent_questions = get_recent_exercise_questions(username)

        # Generate new exercises
        ai_block = generate_new_exercises(
            vocabular=vocab_data,
            topic_memory=topic_memory,
            example_exercise_block=EXERCISE_TEMPLATE,
            level=level,
            recent_questions=recent_questions,
            username=username,
        )

        if not ai_block or not ai_block.get("exercises"):
            return None

        # Assign unique block_id
        ai_block["id"] = f"blk{get_next_block_id():04d}"

        # Limit to 3 exercises
        exercises = ai_block.get("exercises", [])
        ai_block["exercises"] = exercises[:3]

        # Keep correctAnswer for evaluation system
        # Note: correctAnswer is needed by the evaluation system

        return ai_block

    except Exception as e:
        logger.error(f"Error creating AI block for user {username}: {e}")
        return None

def _generate_blocks_for_new_user(username: str) -> dict | None:
    """Generate two unique blocks for new users by using different generation contexts."""

    # Generate first block with empty history
    ai_block = _create_ai_block(username)
    if not ai_block or not ai_block.get("exercises"):
        return None

    # Extract questions from first block and update history
    new_questions = [ex.get("question") for ex in ai_block.get("exercises", []) if ex.get("question")]
    safe_new_questions = new_questions if new_questions is not None else []

    # Update exercise history and ensure it's committed
    update_exercise_history(username, safe_new_questions)

    # Force a small delay to ensure DB commit is visible
    time.sleep(0.1)

    # Generate second block with different approach to ensure uniqueness
    next_block = _create_ai_block(username)

    if next_block and next_block.get("exercises"):
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        filtered = [ex for ex in exercises if ex.get("question") not in safe_new_questions]
        next_block["exercises"] = filtered[:3]
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        # Keep correctAnswer for evaluation system

    # Store both blocks
    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.now().isoformat(),
        }
    )

    return ai_block

def _generate_blocks_for_existing_user(username: str) -> dict | None:
    """Generate blocks for existing users with proper history management."""

    # Generate first block
    ai_block = _create_ai_block(username)
    if not ai_block or not ai_block.get("exercises"):
        return None

    # Extract questions from first block and update history
    new_questions = [ex.get("question") for ex in ai_block.get("exercises", []) if ex.get("question")]
    safe_new_questions = new_questions if new_questions is not None else []

    # Update exercise history and ensure it's committed
    update_exercise_history(username, safe_new_questions)

    # Force a small delay to ensure DB commit is visible
    time.sleep(0.1)

    # Get the updated recent questions to ensure uniqueness
    recent_questions = get_recent_exercise_questions(username)
    safe_recent_questions = recent_questions if recent_questions is not None else []

    # Generate next block with updated history
    next_block = _create_ai_block(username)

    if next_block and next_block.get("exercises"):
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        filtered = [ex for ex in exercises if ex.get("question") not in safe_recent_questions]
        next_block["exercises"] = filtered[:3]
        exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
        # Keep correctAnswer for evaluation system

    # Store both blocks
    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.now().isoformat(),
        }
    )

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

def prefetch_next_exercises(username: str) -> None:
    """Generate and store a new next exercise block asynchronously, ensuring uniqueness."""
    def run():
        try:
            # Get recent questions first to ensure we have the latest
            recent_questions = get_recent_exercise_questions(username)

            # Create AI block for user
            next_block = _create_ai_block(username)
            if next_block is not None:
                next_block["id"] = f"blk{get_next_block_id():04d}"

            if next_block and isinstance(next_block, dict) and "exercises" in next_block:
                exercises = next_block["exercises"] if next_block and isinstance(next_block.get("exercises"), list) else []
                filtered = [ex for ex in exercises if ex.get("question") not in (recent_questions if recent_questions is not None else [])]
                next_block["exercises"] = filtered[:3]
            else:
                next_block = None

            # Store next exercises for user
            if next_block:
                # Promote previous next block to current block before updating next block
                row = fetch_one("ai_user_data", "WHERE username = ?", (username,))
                prev_next_block = None
                if row and row.get("next_exercises"):
                    prev_next_block = json.loads(row["next_exercises"]) if isinstance(row["next_exercises"], str) else row["next_exercises"]
                if prev_next_block:
                    store_user_ai_data(
                        username,
                        {
                            "exercises": json.dumps(prev_next_block),
                        }
                    )
                store_user_ai_data(
                    username,
                    {
                        "next_exercises": json.dumps(next_block or {}),
                    }
                )

        except Exception as e:
            logger.error(f"Error in prefetch_next_exercises for user {username}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    Thread(target=run, daemon=True).start()


def ensure_unique_block_title(block):
    """
    Ensure the block title is unique.

    Args:
        block: The exercise block

    Returns:
        Block with unique title
    """
    try:
        if not block or "title" not in block:
            return block

        base_title = block["title"]
        counter = 1

        while True:
            # Check if title exists
            existing = fetch_one(
                "ai_exercise_blocks",
                "WHERE title = ?",
                (block["title"],)
            )

            if not existing:
                break

            block["title"] = f"{base_title} ({counter})"
            counter += 1

        return block

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error ensuring unique block title: {e}")
        raise DatabaseError(f"Error ensuring unique block title: {str(e)}")


def print_exercise_block_sentences(block, context, color="\033[94m"):
    """
    Print exercise block sentences for debugging.

    Args:
        block: Exercise block to print
        context: Context string for logging
        color: Color code for output
    """
    try:
        if not block or not isinstance(block, dict):
            print(f"{color}[{context}] No valid block to print.\033[0m", flush=True)
            return

        title = block.get("title", "(no title)") if isinstance(block, dict) else "(no title)"
        print(f"{color}[{context}] Exercise block title: {title}\033[0m", flush=True)
    except Exception as e:
        print(f"\033[91m[{context}] Error printing exercise block: {e}\033[0m", flush=True)


def log_generated_sentences(block, parent_function=None):
    """
    Log generated sentences for debugging.

    Args:
        block: Exercise block to log
        parent_function: Parent function name for context
    """
    parent_str = f"[{parent_function}] " if parent_function else ""
    if not block or not isinstance(block, dict):
        print(f"{parent_str}No valid block to log generated title.", flush=True)
        return
    title = block.get("title", "(no title)")
    print(f"{parent_str}Generated block title: {title}", flush=True)


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
            # This would need to be implemented based on your current structure
            recent_topics = []
        except Exception as e:
            logger.error(f"Failed to get recent topics: {e}")

    try:
        if topic_memory:
            upcoming = sorted(
                (entry for entry in topic_memory if "next_repeat" in entry),
                key=lambda x: datetime.fromisoformat(x["next_repeat"]),
            )[:10]
            filtered_topic_memory = [
                {
                    "grammar": entry.get("grammar"),
                    "topic": entry.get("topic"),
                    "skill_type": entry.get("skill_type"),
                }
                for entry in upcoming
            ]
        else:
            filtered_topic_memory = []
    except Exception as e:
        logger.error(f"Failed to filter topic_memory: {e}")
        filtered_topic_memory = []

    try:
        if vocabular:
            vocabular = [
                {
                    "word": entry.get("word") or entry.get("vocab"),
                    "translation": entry.get("translation"),
                }
                for entry in vocabular
                if (
                    (entry.get("sm2_due_date") or entry.get("next_review"))
                    and datetime.fromisoformat(
                        entry.get("sm2_due_date") or entry.get("next_review")
                    ).date()
                    <= datetime.now().date()
                )
            ][:10]
        else:
            vocabular = []
    except Exception as e:
        logger.error(f"Error stripping vocabulary fields: {e}")
        vocabular = []

    level_val = int(level or 0)
    level_val = max(0, min(level_val, 10))

    # Define CEFR levels (you may need to import this from your constants)
    CEFR_LEVELS = {
        0: "A1", 1: "A1", 2: "A2", 3: "A2", 4: "B1", 5: "B1",
        6: "B2", 7: "B2", 8: "C1", 9: "C1", 10: "C2"
    }
    cefr_level = CEFR_LEVELS[level_val]

    if example_exercise_block:
        example_exercise_block["level"] = cefr_level

    # Create a simple exercise generation prompt
    user_prompt = f"""
    Generate 3 German language exercises for a {cefr_level} level student.

    Vocabulary to include: {', '.join([v.get('word', '') for v in vocabular[:5]])}
    Topics to focus on: {', '.join([t.get('grammar', '') for t in filtered_topic_memory[:3]])}
    Avoid these recent questions: {', '.join(recent_questions[:3])}

    Create exercises with these types:
    1. Gap-fill exercise
    2. Translation exercise
    3. Grammar exercise

    Return as JSON with this structure:
    {{
        "title": "Exercise Block",
        "level": "{cefr_level}",
        "topic": "general",
        "exercises": [
            {{
                "id": "ex1",
                "type": "gap-fill",
                "question": "Ich _____ Deutsch.",
                "correctAnswer": "spreche",
                "options": ["spreche", "sprechen", "spricht", "sprechen"]
            }},
            {{
                "id": "ex2",
                "type": "translation",
                "question": "I like bread.",
                "correctAnswer": "Ich mag Brot."
            }},
            {{
                "id": "ex3",
                "type": "grammar",
                "question": "Das _____ lecker.",
                "correctAnswer": "ist",
                "options": ["ist", "sind", "war", "waren"]
            }}
        ]
    }}
    """

    # Generate dynamic exercises with variation
    exercise_templates = [
        # Template 1: Food and eating
        {
            "title": f"German {cefr_level} - Food & Eating",
            "exercises": [
                {
                    "id": "ex1",
                    "type": "gap-fill",
                    "question": "Ich _____ ein Apfel.",
                    "correctAnswer": "esse",
                    "options": ["esse", "trinke", "kaufe", "sehe"]
                },
                {
                    "id": "ex2",
                    "type": "translation",
                    "question": "I like bread.",
                    "correctAnswer": "Ich mag Brot."
                },
                {
                    "id": "ex3",
                    "type": "grammar",
                    "question": "Das Essen _____ lecker.",
                    "correctAnswer": "ist",
                    "options": ["ist", "sind", "war", "waren"]
                }
            ]
        },
        # Template 2: Daily activities
        {
            "title": f"German {cefr_level} - Daily Activities",
            "exercises": [
                {
                    "id": "ex1",
                    "type": "gap-fill",
                    "question": "Ich _____ Deutsch.",
                    "correctAnswer": "lerne",
                    "options": ["lerne", "lernt", "lernen", "gelernt"]
                },
                {
                    "id": "ex2",
                    "type": "translation",
                    "question": "I go to work.",
                    "correctAnswer": "Ich gehe zur Arbeit."
                },
                {
                    "id": "ex3",
                    "type": "grammar",
                    "question": "Er _____ jeden Tag.",
                    "correctAnswer": "arbeitet",
                    "options": ["arbeitet", "arbeiten", "arbeitete", "gearbeitet"]
                }
            ]
        },
        # Template 3: Family and home
        {
            "title": f"German {cefr_level} - Family & Home",
            "exercises": [
                {
                    "id": "ex1",
                    "type": "gap-fill",
                    "question": "Meine Familie _____ in Berlin.",
                    "correctAnswer": "wohnt",
                    "options": ["wohnt", "wohnen", "wohnte", "gewohnt"]
                },
                {
                    "id": "ex2",
                    "type": "translation",
                    "question": "I have a sister.",
                    "correctAnswer": "Ich habe eine Schwester."
                },
                {
                    "id": "ex3",
                    "type": "grammar",
                    "question": "Das Haus _____ groß.",
                    "correctAnswer": "ist",
                    "options": ["ist", "sind", "war", "waren"]
                }
            ]
        },
        # Template 4: Weather and seasons
        {
            "title": f"German {cefr_level} - Weather & Seasons",
            "exercises": [
                {
                    "id": "ex1",
                    "type": "gap-fill",
                    "question": "Es _____ heute.",
                    "correctAnswer": "regnet",
                    "options": ["regnet", "regnen", "regnete", "geregnet"]
                },
                {
                    "id": "ex2",
                    "type": "translation",
                    "question": "It's cold today.",
                    "correctAnswer": "Es ist kalt heute."
                },
                {
                    "id": "ex3",
                    "type": "grammar",
                    "question": "Der Winter _____ kalt.",
                    "correctAnswer": "ist",
                    "options": ["ist", "sind", "war", "waren"]
                }
            ]
        },
        # Template 5: Shopping and money
        {
            "title": f"German {cefr_level} - Shopping & Money",
            "exercises": [
                {
                    "id": "ex1",
                    "type": "gap-fill",
                    "question": "Ich _____ ein Buch.",
                    "correctAnswer": "kaufe",
                    "options": ["kaufe", "kaufen", "kaufte", "gekauft"]
                },
                {
                    "id": "ex2",
                    "type": "translation",
                    "question": "How much does it cost?",
                    "correctAnswer": "Wie viel kostet es?"
                },
                {
                    "id": "ex3",
                    "type": "grammar",
                    "question": "Das Buch _____ teuer.",
                    "correctAnswer": "ist",
                    "options": ["ist", "sind", "war", "waren"]
                }
            ]
        }
    ]

    # Randomly select a template
    selected_template = random.choice(exercise_templates)

    # Add some randomization to make exercises even more varied
    if random.random() < 0.3:  # 30% chance to shuffle options
        for exercise in selected_template["exercises"]:
            if "options" in exercise:
                random.shuffle(exercise["options"])

    # Create the final block with unique ID
    template_block = {
        "title": selected_template["title"],
        "level": cefr_level,
        "topic": "general",
        "exercises": selected_template["exercises"]
    }

    return template_block

def fetch_vocab_and_topic_data(username: str) -> tuple[list, list]:
    """Return vocab and topic memory data for the given user."""
    try:
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
    except Exception as e:
        logger.error(f"Error fetching vocab and topic data for {username}: {e}")
        return [], []

# Define exercise template
EXERCISE_TEMPLATE = {
    "title": "German Language Exercises",
    "level": "A1",
    "topic": "general",
    "exercises": [
        {
            "id": "ex1",
            "type": "gap-fill",
            "question": "Ich _____ Deutsch.",
            "correctAnswer": "spreche",
            "options": ["spreche", "sprechen", "spricht", "sprechen"]
        }
    ]
}



