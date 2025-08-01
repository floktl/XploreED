import json
import re
import datetime
from utils.grammar.grammar_utils import detect_language_topics
from database import insert_row, update_row, select_one
from utils.spaced_repetition.level_utils import check_auto_level_up
from features.spaced_repetition import sm2
from utils.spaced_repetition.vocab_utils import translate_to_german
from utils.ai.ai_api import send_prompt
from utils.ai.prompts import (
    evaluate_translation_prompt,
    quality_evaluation_prompt,
)
from utils.spaced_repetition.vocab_utils import _extract_json
from utils.ai.topic_memory_logger import topic_memory_logger

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
    # print(f"\033[92m[MISTRAL CALL] evaluate_translation_ai\033[0m", flush=True)

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

    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Evaluating topics: {topics}", flush=True)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 English: '{english}'", flush=True)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Reference: '{reference}'", flush=True)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Student: '{student}'", flush=True)

    user_prompt = quality_evaluation_prompt(english, reference, student, topics)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Sending prompt to AI for topic evaluation", flush=True)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 PROMPT SENT TO AI:", flush=True)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 {user_prompt['content']}", flush=True)
    print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 END OF PROMPT", flush=True)


    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 API call completed, status code: {resp.status_code}", flush=True)

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 AI Response: '{content}'", flush=True)
            print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 JSON RESPONSE ONLY:", flush=True)
            print(f"{content}", flush=True)
            print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 END JSON", flush=True)

            data = _extract_json(content)
            if isinstance(data, dict):
                sanitized = {
                    k.replace("_", " ").strip(): int(v)
                    for k, v in data.items()
                }
                result = {t: sanitized.get(t, 0) for t in topics}
                print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Final topic qualities: {result}", flush=True)
                return result
            else:
                print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Failed to parse JSON from AI response", flush=True)
        else:
            print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 API call failed with status code: {resp.status_code}", flush=True)
    except Exception as e:
        print(f"🔍 [TOPIC QUALITY DEBUG] 🔍 Exception during AI call: {e}", flush=True)
        print("[evaluate_topic_qualities_ai] AI topic quality evaluation failed:", e, flush=True)

    return compare_topic_qualities(reference, student)

def _update_single_topic(username: str, grammar: str, skill: str, context: str, quality: int, topic: str = None) -> None:
    """Insert or update one topic memory row based on ``quality``."""
    # print("\033[95m💾 [TOPIC MEMORY FLOW] 💾 Starting _update_single_topic for user: {} grammar: {} skill: {} quality: {}\033[0m".format(username, grammar, skill, quality), flush=True)

    # 🔥 IMPROVED SM2 LOGIC 🔥
    # SM2 uses quality 0-5, where 3+ is considered "correct" for spaced repetition
    # Quality 5 = Perfect, 4 = Correct with hesitation, 3 = Correct with difficulty
    # Quality 2 = Incorrect but easy to recall, 1 = Incorrect but remembered, 0 = Complete blackout
    correct = quality >= 3
    # print("\033[94m📊 [TOPIC MEMORY FLOW] 📊 Quality {} translates to correct: {} (SM2 threshold: 3+)\033[0m".format(quality, correct), flush=True)

    # print("\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Checking for existing topic memory entry\033[0m", flush=True)
    existing = select_one(
        "topic_memory",
        columns=["id", "topic", "ease_factor", "intervall", "repetitions"],
        where="username = ? AND grammar = ? AND skill_type = ?",
        params=(username, grammar, skill),
    )

    if existing:
        # print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Found existing topic memory entry, updating...\033[0m", flush=True)
        # print("\033[94m📊 [TOPIC MEMORY FLOW] 📊 Current values - EF: {} Reps: {} Interval: {}\033[0m".format(
        #     existing.get("ease_factor"), existing.get("repetitions"), existing.get("intervall")), flush=True)

        ef, reps, interval = sm2(
            quality,
            existing.get("ease_factor") or 2.5,
            existing.get("repetitions") or 0,
            existing.get("intervall") or 1,
        )
        # print("\033[92m📈 [TOPIC MEMORY FLOW] 📈 SM2 calculated new values - EF: {} Reps: {} Interval: {}\033[0m".format(ef, reps, interval), flush=True)

        update_data = {
            "ease_factor": ef,
            "repetitions": reps,
            "intervall": interval,
            "next_repeat": (datetime.datetime.now() + datetime.timedelta(days=interval)).isoformat(),
            "last_review": datetime.datetime.now().isoformat(),
            "correct": int(correct),
            "quality": quality,
            "context": context,
        }
        # print("\033[96m💾 [TOPIC MEMORY FLOW] 💾 Updating existing topic memory row with ID: {}\033[0m".format(existing["id"]), flush=True)
        update_row("topic_memory", update_data, "id = ?", (existing["id"],))
        # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully updated existing topic memory entry\033[0m", flush=True)

        # 🔥 ADD THIS: Log the update with debug info
        # print(f"🔧 [LOGGER DEBUG] 🔧 About to call topic_memory_logger.log_topic_update", flush=True)
        topic_memory_logger.log_topic_update(
            username=username,
            grammar=grammar,
            skill=skill,
            quality=quality,
            is_new=False,
            old_values={
                "ease_factor": existing.get("ease_factor"),
                "repetitions": existing.get("repetitions"),
                "intervall": existing.get("intervall"),
                "topic": existing.get("topic")
            },
            new_values=update_data,
            row_id=existing["id"]
        )
        # print(f"🔧 [LOGGER DEBUG] 🔧 Called topic_memory_logger.log_topic_update successfully", flush=True)
    else:
        # print("\033[93m🆕 [TOPIC MEMORY FLOW] 🆕 No existing entry found, creating new topic memory entry\033[0m", flush=True)
        ef, reps, interval = sm2(quality)
        # print("\033[92m📈 [TOPIC MEMORY FLOW] 📈 SM2 calculated initial values - EF: {} Reps: {} Interval: {}\033[0m".format(ef, reps, interval), flush=True)

        new_entry = {
            "username": username,
            "grammar": grammar,
            "topic": topic,
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
        }

        # print("\033[96m💾 [TOPIC MEMORY FLOW] 💾 Inserting new topic memory entry\033[0m", flush=True)
        insert_row("topic_memory", new_entry)
        # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully created new topic memory entry\033[0m", flush=True)

        # 🔥 ADD THIS: Log the new entry with debug info
        # print(f"🔧 [LOGGER DEBUG] 🔧 About to call topic_memory_logger.log_topic_update for new entry", flush=True)
        topic_memory_logger.log_topic_update(
            username=username,
            grammar=grammar,
            skill=skill,
            quality=quality,
            is_new=True,
            new_values=new_entry
        )
        # print(f"🔧 [LOGGER DEBUG] 🔧 Called topic_memory_logger.log_topic_update for new entry successfully", flush=True)

    # check for automatic level advancement
    # print("\033[96m📈 [TOPIC MEMORY FLOW] 📈 Checking for automatic level advancement\033[0m", flush=True)
    check_auto_level_up(username)
    # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Level advancement check completed\033[0m", flush=True)

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
        if feat in ref_features and feat in student_features:
            # Topic detected in both - likely correct usage
            qualities[feat] = 4  # Good but not perfect
        elif feat in ref_features and feat not in student_features:
            # Topic in reference but missing in student - likely incorrect
            qualities[feat] = 1  # Some knowledge but incorrect
        elif feat not in ref_features and feat in student_features:
            # Topic in student but not in reference - likely incorrect
            qualities[feat] = 1  # Some knowledge but incorrect
        else:
            # Fallback case
            qualities[feat] = 3  # Neutral/unknown

    return qualities

__all__ = [
    "translate_to_german",
    "evaluate_translation_ai",
    "evaluate_topic_qualities_ai",
    "update_topic_memory_translation",
    "update_topic_memory_reading",
    "compare_topic_qualities",
]
