"""Helper functions used by AI routes."""

import json
import random
import datetime
import requests
from difflib import SequenceMatcher
from flask import current_app

from utils.spaced_repetition.vocab_utils import split_and_clean, save_vocab, review_vocab_word, extract_words
from database import *
from utils.grammar.grammar_utils import detect_language_topics
from utils.ai.translation_utils import _update_single_topic, update_topic_memory_reading
from utils.spaced_repetition.level_utils import check_auto_level_up
from utils.helpers.helper import run_in_background
from utils.data.json_utils import extract_json
from utils.ai.prompt_utils import make_prompt, SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT
from utils.ai.prompts import (
    exercise_generation_prompt,
    feedback_generation_prompt,
    answers_evaluation_prompt,
    reading_exercise_prompt,
)
from utils.ai.ai_api import send_request, send_prompt
from datetime import date
from . import (
    EXERCISE_TEMPLATE,
    READING_TEMPLATE,
    CEFR_LEVELS,
    FEEDBACK_FILE,
)


def _ensure_schema(exercise_block: dict) -> dict:
    """Return exercise block with guaranteed keys."""

    def fix_exercise(ex, idx):
        fixed = {
            "id": ex.get("id", f"ex{idx+1}"),
            "type": ex.get("type"),
            "question": ex.get("question") or ex.get("sentence") or "Missing question",
            "explanation": ex.get("explanation") or ex.get("hint") or "No explanation.",
        }
        if fixed["type"] == "gap-fill":
            fixed["options"] = ex.get("options", ["bin", "bist", "ist", "sind"])
        return fixed

    if "exercises" in exercise_block:
        exercise_block["exercises"] = [
            fix_exercise(ex, i) for i, ex in enumerate(exercise_block["exercises"])
        ]

    return exercise_block


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
                <= date.today()
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
    exists = fetch_one_custom(
        "SELECT username FROM ai_user_data WHERE username = ?",
        (username,),
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
    example_block = EXERCISE_TEMPLATE.copy()

    vocab_rows = fetch_custom(
        "SELECT vocab, translation, interval_days, next_review, ef, repetitions, last_review "
        "FROM vocab_log WHERE username = ?",
        (username,),
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
        print("[_create_ai_block]", e, flush=True)
        return None
    if not ai_block or not ai_block.get("exercises"):
        return None

    exercises = ai_block.get("exercises", [])
    random.shuffle(exercises)
    ai_block["exercises"] = exercises[:3]

    for ex in ai_block.get("exercises", []):
        ex.pop("correctAnswer", None)

    return ai_block


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


def evaluate_answers_with_ai(
    exercises: list, answers: dict, mode: str = "strict"
) -> dict | None:
    """Ask Mistral to evaluate student answers and return JSON results."""
    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]

    instructions = (
        "Evaluate these answers for a German exercise. "
        "Return JSON with 'pass' (true/false) and a 'results' list. "
        "Each result must include 'id' and 'correct_answer'. "
        "Mark pass true only if all answers are fully correct."
    )
    if mode == "argue":
        instructions = (
            "Reevaluate the student's answers carefully. "
            "Consider possible alternative correct solutions. "
            + instructions
        )

    user_prompt = answers_evaluation_prompt(instructions, formatted)

    try:
        resp = send_prompt(
            "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extract_json(content)
            return parsed
    except Exception as e:
        current_app.logger.error("AI evaluation failed: %s", e)

    return None


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


def generate_reading_exercise(
    style: str,
    level: int,
    vocab: list | None = None,
    topic_memory: list | None = None,
) -> dict:
    """Create a short reading text with questions using Mistral.

    The text should reuse known vocabulary and explicitly train the learner's
    weak grammar topics provided via ``topic_memory``.
    """
    example = READING_TEMPLATE.copy()
    cefr_level = CEFR_LEVELS[max(0, min(level, 10))]
    example["level"] = cefr_level
    example["style"] = style

    extra = ""
    if vocab:
        words = ", ".join(v.get("word") for v in vocab[:10])
        extra += f"Use these vocabulary words: {words}. "
    if topic_memory:
        topics = {
            row.get("grammar") or row.get("topic")
            for row in topic_memory
            if row.get("grammar") or row.get("topic")
        }
        if topics:
            topics_str = ", ".join(list(topics)[:5])
            extra += (
                f"Focus on these weak topics: {topics_str}. "
                "Questions should explicitly train these weaknesses. "
            )

    user_prompt = reading_exercise_prompt(style, cefr_level, extra)

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.7,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extract_json(content)
            if parsed:
                return parsed
    except Exception as e:
        current_app.logger.error("Failed to generate reading exercise: %s", e)

    return example

def fetch_topic_memory(username: str, include_correct: bool = False) -> list:
    """Retrieve topic memory rows for a user.

    If ``include_correct`` is ``False`` (default), only entries that were
    answered incorrectly are returned.
    """
    query = (
        "SELECT grammar, topic, skill_type, context, lesson_content_id, ease_factor, "
        "intervall, next_repeat, repetitions, last_review, correct, quality "
        "FROM topic_memory WHERE username = ?"
    )
    params = [username]
    if not include_correct:
        query += " AND (correct IS NULL OR correct = 0)"
    try:
        rows = fetch_custom(query, tuple(params))
        return rows if rows else []
    except Exception:
        # Table might not exist yet
        return []

def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    if not exercise_block:
        print("❌ Missing exercise block for processing", flush=True)
        return

    all_exercises = exercise_block.get("exercises", [])
    exercise_map = {str(e.get("id")): e for e in all_exercises}

    results = []
    reviewed: set[str] = set()
    for ex_id, user_ans in answers.items():
        ex = exercise_map.get(str(ex_id))
        if not ex:
            continue
        correct_ans = str(ex.get("correctAnswer", "")).strip().lower()
        user_ans = str(user_ans).strip().lower()
        is_correct = int(user_ans == correct_ans)
        quality = 5 if is_correct else 2
        features = detect_language_topics(
            f"{ex.get('question', '')} {correct_ans}"
        ) or ["unknown"]
        skill = ex.get("type", "")

        for feature in features:
            _update_single_topic(
                username,
                feature,
                skill,
                ex.get("question", ""),
                quality,
            )

            results.append(
                {
                    "topic_memory": {
                        "grammar": feature,
                        "skill_type": skill,
                        "quality": quality,
                        "correct": is_correct,
                    }
                }
            )

        words = set(
            [w for w, _ in extract_words(ex.get("question", ""))]
            + [w for w, _ in extract_words(correct_ans)]
        )
        for vocab in words:
            review_vocab_word(username, vocab, quality, seen=reviewed)

    # print("AI submission results (HJSON):\n", json.dumps(results, indent=2), flush=True)



