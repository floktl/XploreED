"""Helper functions for exercise routes."""

import json
import random
from threading import Thread
from flask import current_app # type: ignore
from app.imports.imports import *
from database import insert_row, select_rows, fetch_one
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
from .ai_evaluation_helpers import evaluate_answers_with_ai
import datetime
from utils.data.json_utils import extract_json
from utils.ai.prompt_utils import make_prompt, SYSTEM_PROMPT
from utils.ai.prompts import exercise_generation_prompt
from utils.ai.ai_api import send_request
from .. import (
    EXERCISE_TEMPLATE,
    CEFR_LEVELS,
)

def fetch_vocab_and_topic_data(username: str) -> tuple[list, list]:
    """Return vocab and topic memory data for the given user."""
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
    topic_data = [dict(row) for row in topic_rows] if topic_rows else []
    return vocab_data, topic_data


def compile_score_summary(exercises: list, answers: dict, id_map: dict) -> dict:
    """Return score summary for the evaluated answers."""
    mistakes = []
    correct = 0
    for ex in exercises:
        cid = str(ex.get("id"))
        user_ans = answers.get(cid, "")
        correct_ans = id_map.get(cid, "")
        if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
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
    """Save exercise submission and update spaced repetition in a thread."""
    app = current_app._get_current_object()

    def run():
        with app.app_context():
            try:
                process_ai_answers(
                    username,
                    str(block_id),
                    answers,
                    {"exercises": exercises},
                )
                check_auto_level_up(username)
                insert_row(
                    "exercise_submissions",
                    {
                        "username": username,
                        "block_id": str(block_id),
                        "answers": json.dumps(answers),
                    },
                )
            except Exception as e:
                current_app.logger.error("Failed to save exercise submission: %s", e)

    Thread(target=run).start()


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
    # print("Session ID:", session_id, flush=True)
    # print("Username:", username, flush=True)

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

    try:
        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level
        )
    except ValueError as e:
        print("[ai-exercise]", e, flush=True)
        return jsonify({"error": "Mistral error"}), 500
    if not ai_block or not ai_block.get("exercises"):
        return jsonify({"error": "Mistral error"}), 500

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]

    # remove solutions before sending to client
    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    return jsonify(ai_block)


def generate_new_exercises(
    vocabular=None,
    topic_memory=None,
    example_exercise_block=None,
    level=None,
) -> dict | None:
    """Request a new exercise block from Mistral."""

    try:
        upcoming = sorted(
            (entry for entry in topic_memory if "next_repeat" in entry),
            key=lambda x: datetime.datetime.fromisoformat(x["next_repeat"]),
        )[:5]

        filtered_topic_memory = [
            {
                "grammar": entry.get("grammar"),
                "topic": entry.get("topic"),
                "skill_type": entry.get("skill_type"),
            }
            for entry in upcoming
        ]
    except Exception as e:
        print("❌ Failed to filter topic_memory:", e, flush=True)
        filtered_topic_memory = []

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
        ]
    except Exception as e:
        print("❌ Error stripping vocabulary fields:", e, flush=True)

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
    )

    messages = make_prompt(user_prompt["content"], SYSTEM_PROMPT)
    response = send_request(messages)
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        parsed = extract_json(content)
        if parsed is not None:
            parsed = _ensure_schema(parsed)
            parsed["level"] = cefr_level
            return parsed
        print("❌ Failed to parse JSON. Raw content:", flush=True)
        print(content, flush=True)
        return None
    else:
        print(f"❌ API request failed: {response.status_code} - {response.text}", flush=True)
        return None


def generate_training_exercises(username: str) -> dict | None:
    """Generate current and next exercise blocks and store them.

    Returns ``None`` if a valid exercise block could not be generated.
    """

    ai_block = _create_ai_block(username)
    if not ai_block:
        return None
    next_block = _create_ai_block(username)

    store_user_ai_data(
        username,
        {
            "exercises": json.dumps(ai_block),
            "next_exercises": json.dumps(next_block or {}),
            "exercises_updated_at": datetime.datetime.now().isoformat(),
        },
    )

    return ai_block


def prefetch_next_exercises(username: str) -> None:
    """Generate and store a new next exercise block asynchronously."""
    next_block = _create_ai_block(username)
    if not next_block:
        return
    store_user_ai_data(
        username,
        {
            "next_exercises": json.dumps(next_block),
        },
    )


