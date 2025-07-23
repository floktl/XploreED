import json
import re
import datetime
from utils.grammar.grammar_utils import detect_language_topics
from database import insert_row, update_row, select_one
from utils.spaced_repetition.level_utils import check_auto_level_up
from utils.spaced_repetition.algorithm import sm2
from utils.spaced_repetition.vocab_utils import translate_to_german
from utils.ai.ai_api import send_prompt
from utils.ai.prompts import (
    evaluate_translation_prompt,
    quality_evaluation_prompt,
)
import random

# Default conversation topics used when creating new topic memory rows
DEFAULT_TOPICS = [
    "dogs",
    "living",
    "family",
    "work",
    "shopping",
    "travel",
    "sports",
    "food",
    "hobbies",
    "weather",
]

def _extract_json(text: str):
    """Return a JSON object if ``text`` contains one."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None

def _normalize_umlauts(s: str) -> str:
    # Accept ae == ä, oe == ö, ue == ü (and vice versa)
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    s = s.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    return s

def _strip_final_punct(s: str) -> str:
    s = s.strip()
    if s and s[-1] in ".?":
        return s[:-1].strip()
    return s


def evaluate_translation_ai(english: str, reference: str, student: str):
    """Return ``(correct, reason)`` after scoring ``student`` against ``reference``. Ignores missing/extra . or ? at end."""
    # Ignore final . or ? for both student and reference
    reference = _strip_final_punct(reference)
    student = _strip_final_punct(student)
    # Normalize umlauts for both answers
    reference = _normalize_umlauts(reference)
    student = _normalize_umlauts(student)

    # Direct comparison with normalized strings
    if student.strip().lower() == reference.strip().lower():
        return True, "Your translation is correct!"

    # If direct comparison fails, use AI evaluation
    # print("[evaluate_translation_ai] Evaluating translation using Mistral...", flush=True)
    # print(f"[evaluate_translation_ai] Inputs: english='{english}', reference='{reference}', student='{student}'", flush=True)

    user_prompt = evaluate_translation_prompt(english, student)
    print(f"\033[92m[MISTRAL CALL] evaluate_translation_ai\033[0m", flush=True)

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            data = _extract_json(content)
            if isinstance(data, dict):
                return bool(data.get("correct")), str(data.get("reason", ""))
    except Exception as e:
        print("[evaluate_translation_ai] AI translation evaluation failed:", e, flush=True)

    return False, "Could not evaluate translation."

def evaluate_topic_qualities_ai(english: str, reference: str, student: str) -> dict[str, int]:
    """Return a mapping of grammar topics to quality scores."""

    topics = sorted(
        set(detect_language_topics(reference) or ["unknown"]) |
        set(detect_language_topics(student) or ["unknown"])
    )

    if not topics:
        return {}

    user_prompt = quality_evaluation_prompt(english, reference, student, topics)
    print(f"\033[92m[MISTRAL CALL] evaluate_topic_qualities_ai\033[0m", flush=True)


    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            data = _extract_json(content)
            if isinstance(data, dict):
                sanitized = {
                    k.replace("_", " ").strip(): int(v)
                    for k, v in data.items()
                }
                return {t: sanitized.get(t, 0) for t in topics}
    except Exception as e:
        print("[evaluate_topic_qualities_ai] AI topic quality evaluation failed:", e, flush=True)

    return compare_topic_qualities(reference, student)

def _update_single_topic(username: str, grammar: str, skill: str, context: str, quality: int) -> None:
    """Insert or update one topic memory row based on ``quality``."""
    correct = quality == 5

    existing = select_one(
        "topic_memory",
        columns=["id", "topic", "ease_factor", "intervall", "repetitions"],
        where="username = ? AND grammar = ? AND skill_type = ?",
        params=(username, grammar, skill),
    )

    if existing:
        ef, reps, interval = sm2(
            quality,
            existing.get("ease_factor") or 2.5,
            existing.get("repetitions") or 0,
            existing.get("intervall") or 1,
        )
        update_data = {
            "ease_factor": ef,
            "repetitions": reps,
            "intervall": interval,
            "next_repeat": (datetime.datetime.now() + datetime.timedelta(days=interval)).isoformat(),
            "last_review": datetime.datetime.now().isoformat(),
            "correct": int(correct),
            "quality": quality,
        }
        if not existing.get("topic"):
            update_data["topic"] = random.choice(DEFAULT_TOPICS)
        update_row("topic_memory", update_data, "id = ?", (existing["id"],))
    else:
        ef, reps, interval = sm2(quality)
        insert_row(
            "topic_memory",
            {
                "username": username,
                "grammar": grammar,
                "topic": random.choice(DEFAULT_TOPICS),
                "skill_type": skill,
                "context": context,
                "lesson_content_id": "translation_practice",
                "ease_factor": ef,
                "intervall": 0,
                "next_repeat": (datetime.datetime.now() + datetime.timedelta(days=0)).isoformat(),
                "repetitions": reps,
                "last_review": datetime.datetime.now().isoformat(),
                "correct": int(correct),
                "quality": quality,
            },
        )

    # check for automatic level advancement
    check_auto_level_up(username)

def update_topic_memory_translation(username: str, german: str, qualities: dict[str, int] | None = None) -> None:
    """Update translation topic memory using ``qualities`` if provided."""
    if qualities:
        sanitized = {k.replace("_", " ").strip(): v for k, v in qualities.items()}
        features = list(sanitized.keys())
    else:
        sanitized = {}
        features = detect_language_topics(german) or ["unknown"]
    for feature in features:
        quality = sanitized.get(feature, 3)
        _update_single_topic(username, feature, "translation", german, quality)

def update_topic_memory_reading(username: str, text: str, qualities: dict[str, int] | None = None) -> None:
    """Update reading topic memory using ``qualities`` or detected topics."""
    if qualities:
        sanitized = {k.replace("_", " ").strip(): v for k, v in qualities.items()}
        features = list(sanitized.keys())
    else:
        sanitized = {}
        features = detect_language_topics(text) or ["unknown"]
    for feature in features:
        quality = sanitized.get(feature, 3)
        _update_single_topic(username, feature, "reading", text, quality)

def compare_topic_qualities(reference: str, student: str) -> dict[str, int]:
    """Return best-guess topic quality comparison for fallback use."""
    ref_features = set(detect_language_topics(reference) or ["unknown"])
    student_features = set(detect_language_topics(student) or ["unknown"])
    qualities: dict[str, int] = {}
    for feat in ref_features | student_features:
        qualities[feat] = 5 if feat in ref_features and feat in student_features else 2
    return qualities

__all__ = [
    "translate_to_german",
    "evaluate_translation_ai",
    "evaluate_topic_qualities_ai",
    "update_topic_memory_translation",
    "update_topic_memory_reading",
    "compare_topic_qualities",
]
