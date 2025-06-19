import os
import json
import re
import requests
import datetime
from utils.grammar_utils import detect_language_topics
from utils.db_utils import insert_row, update_row, fetch_one_custom
from utils.algorithm import sm2
from utils.vocab_utils import translate_to_german

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}


def _extract_json(text: str):
    print("Extracting JSON...", flush=True)
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
    print("Evaluating translation using Mistral...", flush=True)

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
        print("Mistral response received.", flush=True)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            print("Raw response content:", content, flush=True)
            data = _extract_json(content)
            if isinstance(data, dict):
                print("Parsed JSON result:", data, flush=True)
                return bool(data.get("correct")), str(data.get("reason", ""))
    except Exception as e:
        print("AI translation evaluation failed:", e, flush=True)

    return False, "Could not evaluate translation."


def evaluate_topic_qualities_ai(
    english: str, reference: str, student: str
) -> dict[str, int]:
    """Return quality scores 0-5 for grammar topics using the Mistral API."""

    print("🧠 evaluate_translation_ai called with:", flush=True)
    print("  English:", english, flush=True)
    print("  Reference:", reference, flush=True)
    print("  Student:", student, flush=True)
    print("Evaluating topic qualities using Mistral...", flush=True)

    topics = sorted(
        set(detect_language_topics(reference) or ["unknown"]) |
        set(detect_language_topics(student) or ["unknown"])
    )

    print("Detected topics:", topics, flush=True)

    if not topics:
        print("No topics found.", flush=True)
        return {}

    user_prompt = {
        "role": "user",
        "content": (
            "You are a helpful German teacher grading a student's translation.\n\n"
            f"English sentence: '{english}'\n"
            f"Reference translation: '{reference}'\n"
            f"Student translation: '{student}'\n\n"
            "Provide JSON mapping each listed language topic to an integer quality"
            " score from 0 to 5. Topics: " + ", ".join(topics)
        ),
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
        print("Mistral response received for topic quality.", flush=True)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            print("Raw quality response content:", content, flush=True)
            data = _extract_json(content)
            if isinstance(data, dict):
                print("Parsed topic quality result:", data, flush=True)
                return {t: int(data.get(t, 0)) for t in topics}
    except Exception as e:
        print("AI topic quality evaluation failed:", e, flush=True)

    return compare_topic_qualities(reference, student)


def _update_single_topic(
    username: str,
    topic: str,
    skill: str,
    context: str,
    quality: int,
) -> None:
    """Insert or update a single topic_memory entry."""
    print(f"Updating single topic: {username=}, {topic=}, {skill=}, {quality=}", flush=True)
    correct = quality == 5

    existing = fetch_one_custom(
        "SELECT id, ease_factor, intervall, repetitions FROM topic_memory "
        "WHERE username = ? AND topic = ? AND skill_type = ?",
        (username, topic, skill),
    )
    print("Existing topic entry:", existing, flush=True)

    if existing:
        ef, reps, interval = sm2(
            quality,
            existing.get("ease_factor") or 2.5,
            existing.get("repetitions") or 0,
            existing.get("intervall") or 1,
        )
        print(f"Updated EF: {ef}, reps: {reps}, interval: {interval}", flush=True)
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
                "quality": quality,
            },
            "id = ?",
            (existing["id"],),
        )
        print("Topic memory row updated.", flush=True)
    else:
        ef, reps, interval = sm2(quality)
        print(f"New EF: {ef}, reps: {reps}, interval: {interval}", flush=True)
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
                "quality": quality,
            },
        )
        print("New topic memory row inserted.", flush=True)


def update_topic_memory_translation(
    username: str,
    german: str,
    qualities: dict[str, int] | None = None,
) -> None:
    """Update spaced repetition entries for each detected topic."""
    print(f"Updating translation memory for user '{username}'...", flush=True)
    features = detect_language_topics(german) or ["unknown"]
    print("Detected translation features:", features, flush=True)
    for feature in features:
        quality = qualities.get(feature)
        print(f"Updating feature '{feature}' with quality {quality}", flush=True)
        _update_single_topic(username, feature, "translation", german, quality)


def update_topic_memory_reading(
    username: str,
    text: str,
    qualities: dict[str, int] | None = None,
) -> None:
    """Update spaced repetition entries for reading comprehension."""
    print(f"Updating reading memory for user '{username}'...", flush=True)
    features = detect_language_topics(text) or ["unknown"]
    print("Detected reading features:", features, flush=True)
    for feature in features:
        quality = qualities.get(feature)
        print(f"Updating feature '{feature}' with quality {quality}", flush=True)
        _update_single_topic(username, feature, "reading", text, quality)


def compare_topic_qualities(reference: str, student: str) -> dict[str, int]:
    """Return quality scores for each detected topic comparing two sentences."""
    print("Comparing topic qualities heuristically...", flush=True)
    ref_features = set(detect_language_topics(reference) or ["unknown"])
    student_features = set(detect_language_topics(student) or ["unknown"])
    print("Reference features:", ref_features, flush=True)
    print("Student features:", student_features, flush=True)
    qualities: dict[str, int] = {}
    for feat in ref_features | student_features:
        qualities[feat] = 5 if feat in ref_features and feat in student_features else 2
        print(f"Topic '{feat}': assigned quality {qualities[feat]}", flush=True)
    return qualities

__all__ = [
    "translate_to_german",
    "evaluate_translation_ai",
    "evaluate_topic_qualities_ai",
    "update_topic_memory_translation",
    "update_topic_memory_reading",
    "compare_topic_qualities",
]
