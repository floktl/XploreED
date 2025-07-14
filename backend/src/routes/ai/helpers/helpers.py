"""Helper functions used by AI routes."""

import random
from difflib import SequenceMatcher

from database import *
from utils.ai.prompt_utils import make_prompt, FEEDBACK_SYSTEM_PROMPT
from utils.ai.prompts import (
    feedback_generation_prompt,
)
from utils.ai.ai_api import send_request
from .. import (
    EXERCISE_TEMPLATE,
)


def _fix_exercise(ex: dict, idx: int) -> dict:
    """Normalize a single exercise dict."""
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

    if "exercises" in exercise_block:
        exercise_block["exercises"] = [
            _fix_exercise(ex, i) for i, ex in enumerate(exercise_block["exercises"])
        ]

    return exercise_block


def generate_feedback_prompt(
    summary: dict,
    vocab: list | None = None,
    topic_memory: list | None = None,
) -> str:
    """Return short feedback summary for the user."""

    correct = summary.get("correct", 0)
    total = summary.get("total", 0)
    mistakes = summary.get("mistakes", [])

    if total == 0:
        return "No answers were submitted."

    top_mistakes = [
        f"Q: {m['question']} | Your: {m['your_answer']} | Correct: {m['correct_answer']}"
        for m in mistakes[:2]
    ]
    mistakes_text = "\n".join(top_mistakes)

    top_vocab = [
        f"{v.get('word')} – {v.get('translation')}" for v in (vocab or [])[:3]
        if v.get("word") and v.get("translation")
    ]
    examples_text = ", ".join(top_vocab)

    topic_counts: dict[str, int] = {}
    for entry in topic_memory or []:
        for topic in str(entry.get("topic", "")).split(","):
            t = topic.strip()
            if t:
                topic_counts[t] = topic_counts.get(t, 0) + 1
    repeated_topics = [t for t, c in topic_counts.items() if c > 1][:3]
    repeated_text = ", ".join(repeated_topics)

    user_prompt = feedback_generation_prompt(
        correct,
        total,
        mistakes_text,
        repeated_text,
        examples_text,
    )

    messages = make_prompt(user_prompt["content"], FEEDBACK_SYSTEM_PROMPT)
    try:
        resp = send_request(messages, temperature=0.3)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("[generate_feedback_prompt] Error:", e, flush=True)

    return "Great effort! We'll generate custom exercises to help you improve further."


def store_user_ai_data(username: str, data: dict):
    """Insert or update cached AI data for a user."""
    exists = select_one(
        "ai_user_data",
        columns="username",
        where="username = ?",
        params=(username,),
    )
    if exists:
        update_row("ai_user_data", data, "username = ?", (username,))
    else:
        data_with_user = {"username": username, **data}
        insert_row("ai_user_data", data_with_user)


def _create_ai_block(username: str) -> dict | None:
    """Create a single AI exercise block for the user.

    Returns ``None`` if the Mistral API did not return a valid block.
    """
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
        from .exercise_helpers import get_recent_exercise_questions
        recent_questions = get_recent_exercise_questions(username)
        logger.info(f"_create_ai_block: Got {len(recent_questions)} recent questions for user {username}")
    except Exception as e:
        logger.error(f"_create_ai_block: Failed to get recent questions for user {username}: {e}")
        recent_questions = []

    try:
        from .exercise_helpers import generate_new_exercises

        ai_block = generate_new_exercises(
            vocab_data, topic_memory, example_block, level=level, recent_questions=recent_questions
        )
    except ValueError as e:
        logger.error(f"_create_ai_block: Failed to generate exercises for user {username}: {e}")
        print("[_create_ai_block]", e, flush=True)
        return None

    if not ai_block or not ai_block.get("exercises"):
        logger.error(f"_create_ai_block: No exercises generated for user {username}")
        return None

    exercises = ai_block.get("exercises", [])
    logger.info(f"_create_ai_block: Generated {len(exercises)} exercises for user {username}")

    # Ensure we have at least 3 exercises, retry if needed
    if len(exercises) < 3:
        logger.warning(f"_create_ai_block: Only {len(exercises)} exercises generated for user {username}, retrying...")
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
                    logger.info(f"_create_ai_block: Added {len(exercises)} total exercises for user {username}")
                    if len(exercises) >= 3:
                        break
            except Exception as e:
                logger.error(f"_create_ai_block: Failed to generate additional exercises for user {username}: {e}")

    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]  # Take exactly 3 exercises

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    logger.info(f"_create_ai_block: Final block has {len(ai_block.get('exercises', []))} exercises for user {username}")
    return ai_block


def _adjust_gapfill_results(exercises: list, answers: dict, evaluation: dict | None) -> dict | None:
    """Ensure AI evaluation for gap-fill exercises matches provided options."""
    if not evaluation or "results" not in evaluation:
        return evaluation

    id_map = {str(r.get("id")): r.get("correct_answer", "") for r in evaluation.get("results", [])}

    for ex in exercises:
        if ex.get("type") != "gap-fill":
            continue
        cid = str(ex.get("id"))
        correct = id_map.get(cid, "")
        options = ex.get("options") or []
        if correct not in options and options:
            norm_corr = str(correct).strip().lower()
            best = options[0]
            best_score = -1.0
            for opt in options:
                opt_norm = opt.lower()
                score = SequenceMatcher(None, norm_corr, opt_norm).ratio()
                if score > best_score:
                    best = opt
                    best_score = score
                if opt_norm in norm_corr or norm_corr in opt_norm:
                    best = opt
                    break
            id_map[cid] = best

    evaluation["results"] = [{"id": k, "correct_answer": v} for k, v in id_map.items()]

    pass_val = True
    for ex in exercises:
        cid = str(ex.get("id"))
        ans = str(answers.get(cid, "")).strip().lower()
        corr = str(id_map.get(cid, "")).strip().lower()
        if ans != corr:
            pass_val = False
    evaluation["pass"] = pass_val
    return evaluation


def format_feedback_block(user_answer, correct_answer, alternatives=None, explanation=None, diff=None, status=None):
    """
    Return a standardized feedback dict for frontend rendering.
    """
    return {
        "status": status or ("correct" if str(user_answer).strip().lower() == str(correct_answer).strip().lower() else "incorrect"),
        "correct": correct_answer,
        "alternatives": alternatives or [],
        "explanation": explanation or "",
        "userAnswer": user_answer,
        "diff": diff,
    }
