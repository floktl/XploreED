# === mistral_exercise_generator.py ===

import os
import json
import re
from datetime import datetime, date
import requests
from dotenv import load_dotenv
from utils.prompt_utils import make_prompt, SYSTEM_PROMPT, FEEDBACK_SYSTEM_PROMPT
from utils.prompts import exercise_generation_prompt, feedback_generation_prompt
from utils.ai_api import send_request
from utils.json_utils import extract_json

load_dotenv()

SYSTEM_PROMPT = """
Your task is to generate new exercises in JSON format.
Use provided memory data to tailor difficulty.
Use the example structure.
"""

# Mapping from numeric level (0-10) to CEFR code
CEFR_LEVELS = [
    "A1", "A1", "A2", "A2", "B1",
    "B1", "B2", "B2", "C1", "C1", "C2"
]

# === NO FALLBACK DATA ===

# === UTILS ===

def _ensure_schema(exercise_block: dict) -> dict:
    def fix_exercise(ex, idx):
        fixed = {
            "id": ex.get("id", f"ex{idx+1}"),
            "type": ex.get("type"),
            "question": ex.get("question") or ex.get("sentence") or "Missing question",
            "explanation": ex.get("explanation") or ex.get("hint") or "No explanation."
        }
        if fixed["type"] == "gap-fill":
            fixed["options"] = ex.get("options", ["bin", "bist", "ist", "sind"])
        return fixed

    if "exercises" in exercise_block:
        exercise_block["exercises"] = [
            fix_exercise(ex, i) for i, ex in enumerate(exercise_block["exercises"])
        ]

    return exercise_block

# === MAIN FUNCTION ===

from datetime import datetime, date

def generate_new_exercises(
    vocabular=None,
    topic_memory=None,
    example_exercise_block=None,
    level=None,
):
    # print('Generate new exercises!!!!!!!!', flush=True)

    try:
        upcoming = sorted(
            (entry for entry in topic_memory if "next_repeat" in entry),
            key=lambda x: datetime.fromisoformat(x["next_repeat"])
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
                (entry.get("sm2_due_date") or entry.get("next_review")) and
                datetime.fromisoformat(entry.get("sm2_due_date") or entry.get("next_review")).date() <= date.today()
            )
        ]
    except Exception as e:
        print("❌ Error stripping vocabulary fields:", e, flush=True)

    level_val = int(level or 0)
    level_val = max(0, min(level_val, 10))
    cefr_level = CEFR_LEVELS[level_val]

    example_exercise_block["level"] = cefr_level

    # print("🧠 Sending request to Mistral AI...", flush=True)

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
            # print("✅ Successfully parsed exercise block from AI./n/n", flush=True)
            parsed = _ensure_schema(parsed)
            parsed["level"] = cefr_level
            # print(json.dumps(parsed, indent=2), flush=True)
            return parsed
        print("❌ Failed to parse JSON. Raw content:", flush=True)
        print(content, flush=True)
        return None
    else:
        print(f"❌ API request failed: {response.status_code} - {response.text}", flush=True)
        return None

# === Generate Feedback Prompt using Mistral ===

def generate_feedback_prompt(
    summary: dict,
    vocab: list | None = None,
    topic_memory: list | None = None,
) -> str:
    """Return concise feedback (1–2 sentences) summarizing student performance."""

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

    topic_counts = {}
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

    messages = make_prompt(
        user_prompt["content"], FEEDBACK_SYSTEM_PROMPT
    )
    try:
        resp = send_request(messages, temperature=0.3)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("[generate_feedback_prompt] Error:", e, flush=True)

    return "Great effort! We'll generate custom exercises to help you improve further."
