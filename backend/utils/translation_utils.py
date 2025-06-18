import os
import json
import re
import requests
import datetime
from utils.grammar_utils import detect_language_topics
from utils.db_utils import insert_row, update_row, fetch_one_custom
from utils.algorithm import sm2

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}


def _extract_json(text: str):
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


def evaluate_translation_ai(english: str, reference: str, student: str):
    """Check if student's translation conveys the same meaning using Mistral."""

    user_prompt = {
        "role": "user",
        "content": f"""
You are a helpful German teacher verifying a student's translation.

English sentence: "{english}"
DeepL reference: "{reference}"
Student translation: "{student}"

Answer in JSON with keys `correct` (true/false) and `reason` in one short English sentence.
""",
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German teacher."},
            user_prompt,
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=10)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            data = _extract_json(content)
            if isinstance(data, dict):
                return bool(data.get("correct")), str(data.get("reason", ""))
    except Exception as e:
        print("AI translation evaluation failed:", e)

    return False, "Could not evaluate translation."


def _update_single_topic(
    username: str,
    topic: str,
    skill: str,
    context: str,
    correct: bool,
) -> None:
    """Insert or update a single topic_memory entry."""
    quality = 5 if correct else 2

    existing = fetch_one_custom(
        "SELECT id, ease_factor, intervall, repetitions FROM topic_memory "
        "WHERE username = ? AND topic = ? AND skill_type = ?",
        (username, topic, skill),
    )

    if existing:
        ef, reps, interval = sm2(
            quality,
            existing.get("ease_factor") or 2.5,
            existing.get("repetitions") or 0,
            existing.get("intervall") or 1,
        )
        update_row(
            "topic_memory",
            {
                "ease_factor": ef,
                "repetitions": reps,
                "intervall": interval,
                "next_repeat": (
                    datetime.datetime.now()
                    + datetime.timedelta(days=interval)
                ).isoformat(),
                "last_review": datetime.datetime.now().isoformat(),
                "correct": int(correct),
            },
            "id = ?",
            (existing["id"],),
        )
    else:
        ef, reps, interval = sm2(quality)
        insert_row(
            "topic_memory",
            {
                "username": username,
                "topic": topic,
                "skill_type": skill,
                "context": context,
                "lesson_content_id": "translation_practice",
                "ease_factor": ef,
                "intervall": interval,
                "next_repeat": (
                    datetime.datetime.now()
                    + datetime.timedelta(days=interval)
                ).isoformat(),
                "repetitions": reps,
                "last_review": datetime.datetime.now().isoformat(),
                "correct": int(correct),
            },
        )


def update_topic_memory_translation(username: str, german: str, correct: bool) -> None:
    """Update spaced repetition entries for each detected topic."""
    features = detect_language_topics(german) or ["unknown"]
    for feature in features:
        _update_single_topic(username, feature, "translation", german, correct)


def update_topic_memory_reading(username: str, text: str, correct: bool) -> None:
    """Update spaced repetition entries for reading comprehension."""
    features = detect_language_topics(text) or ["unknown"]
    for feature in features:
        _update_single_topic(username, feature, "reading", text, correct)


__all__ = [
    "evaluate_translation_ai",
    "update_topic_memory_translation",
    "update_topic_memory_reading",
]
