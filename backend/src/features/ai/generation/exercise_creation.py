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


def generate_new_exercises(
    vocabular=None,
    topic_memory=None,
    example_exercise_block=None,
    level=None,
    recent_questions=None,
    username=None,
) -> dict | None:
    """
    Generate new exercises using AI.

    Args:
        vocabular: User vocabulary data
        topic_memory: User topic memory data
        example_exercise_block: Example exercise block
        level: User skill level
        recent_questions: Recent questions to avoid
        username: Username for logging

    Returns:
        Generated exercise block or None
    """
    try:
        logger.info(f"Generating new exercises for user: {username}")

        # Prepare vocabulary data
        vocab_text = ""
        if vocabular:
            vocab_words = [v.get("word", "") for v in vocabular[:10] if v.get("word")]
            vocab_text = f"Use these vocabulary words: {', '.join(vocab_words)}. "

        # Prepare topic memory data
        topic_text = ""
        if topic_memory:
            topics = {
                row.get("grammar") or row.get("topic")
                for row in topic_memory
                if row.get("grammar") or row.get("topic")
            }
            if topics:
                topics_list = list(topics)[:10]
                topic_text = f"Focus on these weak topics: {', '.join(topics_list)}. "

        # Prepare recent questions to avoid
        recent_text = ""
        if recent_questions:
            recent_text = f"Avoid these recent questions: {', '.join(recent_questions[:5])}. "

        # Determine CEFR level
        cefr_level = CEFR_LEVELS[max(0, min(level or 0, 10))]
        level_val = level or 0

        # Create example exercise block (placeholder)
        example_exercise_block = {
            "lessonId": "example",
            "title": "Example Exercise",
            "level": level_val,
            "topic": "general",
            "exercises": [
                {
                    "id": "ex1",
                    "type": "gap-fill",
                    "question": "Ich _____ Deutsch.",
                    "options": ["spreche", "sprechen", "spricht", "sprechst"],
                    "correctAnswer": "spreche"
                }
            ],
            "feedbackPrompt": "Great job!"
        }

        # Create prompt
        user_prompt = exercise_generation_prompt(
            level_val=level_val,
            cefr_level=cefr_level,
            example_exercise_block=example_exercise_block,
            vocabular=vocabular or [],
            filtered_topic_memory=topic_memory or [],
            recent_questions=", ".join(recent_questions[:5]) if recent_questions else ""
        )

        logger.debug(f"Sending exercise generation prompt to AI")
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.7,
        )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extract_json(content)

            if parsed and isinstance(parsed, dict):
                # Ensure proper schema
                if "exercises" in parsed:
                    for i, ex in enumerate(parsed["exercises"]):
                        ex["id"] = ex.get("id", f"ex{i+1}")

                logger.info(f"Successfully generated exercise block for user: {username}")
                return parsed
            else:
                logger.warning(f"Failed to parse AI response for user: {username}")
                raise ExerciseGenerationError("Failed to parse AI response")
        else:
            logger.error(f"AI request failed with status {resp.status_code} for user: {username}")
            raise ExerciseGenerationError(f"AI request failed with status {resp.status_code}")

    except ExerciseGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error generating new exercises for user {username}: {e}")
        logger.error(traceback.format_exc())
        raise ExerciseGenerationError(f"Error generating new exercises: {str(e)}")


def _create_ai_block_with_variation(username: str, exclude_questions: list) -> dict | None:
    """
    Create an AI exercise block with variation to avoid repetition.

    Args:
        username: The username
        exclude_questions: Questions to exclude

    Returns:
        Exercise block or None
    """
    try:
        logger.info(f"Creating AI block with variation for user: {username}")

        # Get user data
        user_row = fetch_one("users", "WHERE username = ?", (username,))
        level = user_row.get("skill_level", 0) if user_row else 0

        # Get vocabulary and topic memory
        vocab_rows = select_rows(
            "vocab_log",
            columns=["vocab", "translation"],
            where="username = ?",
            params=(username,),
        )
        vocab_data = [
            {"word": row["vocab"], "translation": row.get("translation")}
            for row in vocab_rows
        ] if vocab_rows else []

        topic_rows = fetch_topic_memory(username)
        topic_memory = [dict(row) for row in topic_rows] if isinstance(topic_rows, list) else []

        # Get recent questions
        recent_questions = get_recent_exercise_questions(username, limit=10)

        # Generate new exercises
        block = generate_new_exercises(
            vocabular=vocab_data,
            topic_memory=topic_memory,
            level=level,
            recent_questions=recent_questions,
            username=username
        )

        if block:
            # Store the block
            block_id = get_next_block_id()
            block["id"] = block_id
            block["username"] = username
            block["created_at"] = datetime.now().isoformat()

            insert_row("ai_exercise_blocks", block)
            logger.info(f"Created AI block {block_id} for user: {username}")

            # Update exercise history
            new_questions = [ex.get("question", "") for ex in block.get("exercises", [])]
            update_exercise_history(username, new_questions)

            return block
        else:
            logger.warning(f"Failed to generate exercise block for user: {username}")
            return None

    except ExerciseGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error creating AI block for user {username}: {e}")
        raise ExerciseGenerationError(f"Error creating AI block with variation: {str(e)}")


def _generate_blocks_for_new_user(username: str) -> dict | None:
    """
    Generate exercise blocks for a new user.

    Args:
        username: The username

    Returns:
        Exercise block or None
    """
    try:
        logger.info(f"Generating blocks for new user: {username}")

        # Create initial blocks for new user
        block = _create_ai_block_with_variation(username, [])

        if block:
            # Prefetch next exercises
            prefetch_next_exercises(username)

            logger.info(f"Successfully generated initial blocks for new user: {username}")
            return block
        else:
            logger.warning(f"Failed to generate initial blocks for new user: {username}")
            return None

    except ExerciseGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error generating blocks for new user {username}: {e}")
        raise ExerciseGenerationError(f"Error generating blocks for new user: {str(e)}")


def _generate_blocks_for_existing_user(username: str) -> dict | None:
    """
    Generate exercise blocks for an existing user.

    Args:
        username: The username

    Returns:
        Exercise block or None
    """
    try:
        logger.info(f"Generating blocks for existing user: {username}")

        # Get recent questions to avoid repetition
        recent_questions = get_recent_exercise_questions(username, limit=20)

        # Create new block with variation
        block = _create_ai_block_with_variation(username, recent_questions)

        if block:
            # Prefetch next exercises
            prefetch_next_exercises(username)

            logger.info(f"Successfully generated blocks for existing user: {username}")
            return block
        else:
            logger.warning(f"Failed to generate blocks for existing user: {username}")
            return None

    except ExerciseGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error generating blocks for existing user {username}: {e}")
        raise ExerciseGenerationError(f"Error generating blocks for existing user: {str(e)}")


def generate_training_exercises(username: str) -> dict | None:
    """
    Generate training exercises for a user.

    Args:
        username: The username

    Returns:
        Exercise block or None
    """
    try:
        logger.info(f"Generating training exercises for user: {username}")

        # Check if user is new or existing
        user_row = fetch_one("users", "WHERE username = ?", (username,))

        if user_row:
            # Existing user
            return _generate_blocks_for_existing_user(username)
        else:
            # New user
            return _generate_blocks_for_new_user(username)

    except ExerciseGenerationError:
        raise
    except Exception as e:
        logger.error(f"Error generating training exercises for user {username}: {e}")
        raise ExerciseGenerationError(f"Error generating training exercises: {str(e)}")


def get_next_block_id() -> str:
    """
    Get the next available block ID.

    Returns:
        Next block ID
    """
    try:
        # Get the highest existing block ID
        result = fetch_custom(
            "SELECT MAX(CAST(SUBSTR(id, 4) AS INTEGER)) as max_id FROM ai_exercise_blocks WHERE id LIKE 'blk%'"
        )

        if result and result[0] and result[0].get("max_id"):
            next_id = result[0]["max_id"] + 1
        else:
            next_id = 1

        return f"blk{next_id:04d}"

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting next block ID: {e}")
        raise DatabaseError(f"Error getting next block ID: {str(e)}")


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


def get_recent_exercise_questions(username, limit=20):
    """
    Get recent exercise questions for a user.

    Args:
        username: The username
        limit: Maximum number of questions to return

    Returns:
        List of recent questions
    """
    try:
        # Get recent questions from exercise history
        recent_rows = select_rows(
            "exercise_history",
            columns=["question"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=limit
        )

        if recent_rows:
            return [row.get("question", "") for row in recent_rows if row.get("question")]
        else:
            return []

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting recent exercise questions for user {username}: {e}")
        raise DatabaseError(f"Error getting recent exercise questions: {str(e)}")


def update_exercise_history(username, new_questions, limit=20):
    """
    Update exercise history for a user.

    Args:
        username: The username
        new_questions: New questions to add
        limit: Maximum number of questions to keep
    """
    try:
        # Add new questions to history
        for question in new_questions:
            if question.strip():
                insert_row("exercise_history", {
                    "username": username,
                    "question": question,
                    "created_at": datetime.now().isoformat()
                })

        # Keep only the most recent questions
        # Get the IDs of questions to keep
        recent_rows = select_rows(
            "exercise_history",
            columns=["id"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=limit
        )

        if recent_rows:
            keep_ids = [row["id"] for row in recent_rows]
            # Delete older questions
            delete_rows(
                "exercise_history",
                "username = ? AND id NOT IN (" + ",".join(["?"] * len(keep_ids)) + ")",
                (username,) + tuple(keep_ids)
            )

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error updating exercise history for user {username}: {e}")
        raise DatabaseError(f"Error updating exercise history: {str(e)}")


def prefetch_next_exercises(username: str) -> None:
    """
    Prefetch next exercises for a user in the background.

    Args:
        username: The username
    """
    def run():
        try:
            logger.info(f"Prefetching next exercises for user: {username}")

            # Create next block in background
            _create_ai_block_with_variation(username, [])

            logger.info(f"Successfully prefetched exercises for user: {username}")

        except Exception as e:
            logger.error(f"Error prefetching exercises for user {username}: {e}")
            # Don't raise here as this runs in background thread

    # Run in background thread
    thread = Thread(target=run, daemon=True)
    thread.start()


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



