# === mistral_exercise_generator.py ===

import requests
import os
import json
import re
from dotenv import load_dotenv
import datetime

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

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

# === FALLBACK DATA ===

FALLBACK_EXERCISE_BLOCK = {
  "lessonId": "mock-ai-lesson-001",
  "title": "Using 'sein' in the Present Tense",
  "instructions": "Fill in the blanks or translate the sentences.",
  "level": "A1",
  "exercises": [
    {
      "id": "ex1",
      "type": "gap-fill",
      "question": "Ich ___ müde.",
      "options": ["bist", "bin", "ist", "seid"],
      "explanation": "'Ich' uses 'bin' in present tense."
    }
  ],
  "feedbackPrompt": "Good start! You sometimes mix up plural forms. Remember 'wir sind' and 'sie sind'.",
  "vocabHelp": [
    {"word": "sein", "meaning": "to be"}
  ]
}

FALLBACK_VOCAB_DATA = [
    {
        "type": "string",
        "word": "sein",
        "translation": "to be",
        "sm2_interval": 3,
        "sm2_due_date": "2025-06-12",
        "sm2_ease": 2.3,
        "repetitions": 2,
        "sm2_last_review": "2025-06-10",
        "quality": 4
    }
]

FALLBACK_TOPIC_MEMORY = [
    {
        "topic": "gender",
        "skill_type": "gap-fill",
        "context": "This example is great",
        "lesson_content_id": "1.1",
        "ease_factor": 2.2,
        "intervall": 3,
        "next_repeat": "2025-06-13",
        "repetitions": 2,
        "last_review": "2025-06-10",
        "correct": 0
    }
]

# === UTILS ===

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

import json
import datetime
import requests

def generate_new_exercises(
    vocabular=None,
    topic_memory=None,
    example_exercise_block=None,
    level=None,
):
    print('Generate new exercises!!!!!!!!', flush=True)
    print(topic_memory, flush=True)

    if not vocabular:
        print("⚠️ No vocabulary data found. Using fallback vocab.", flush=True)
        vocabular = FALLBACK_VOCAB_DATA

    if not topic_memory:
        print("⚠️ No topic memory found. Using fallback topic.", flush=True)
        topic_memory = FALLBACK_TOPIC_MEMORY

    if not example_exercise_block:
        print("⚠️ No example block provided. Using fallback block.", flush=True)
        example_exercise_block = FALLBACK_EXERCISE_BLOCK

    try:
        upcoming = sorted(
            (entry for entry in topic_memory if "next_repeat" in entry),
            key=lambda x: datetime.datetime.fromisoformat(x["next_repeat"])
        )[:5]

        filtered_topic_memory = [
            {
                "grammar": entry.get("grammar"),
                "topic": entry.get("topic"),
                "skill_type": entry.get("skill_type"),
                "context": entry.get("context"),
                "next_repeat": entry.get("next_repeat"),
            }
            for entry in upcoming
        ]
    except Exception as e:
        print("❌ Failed to filter topic_memory:", e, flush=True)
        filtered_topic_memory = []

    # ✅ Keep only essential vocab fields
    try:
        vocabular = [
            {
                "word": entry.get("word") or entry.get("vocab"),
                "translation": entry.get("translation"),
                "sm2_due_date": entry.get("sm2_due_date")
                or entry.get("next_review"),
            }
            for entry in vocabular
        ]
    except Exception as e:
        print("❌ Error stripping vocabulary fields:", e, flush=True)

    level_val = int(level or 0)
    level_val = max(0, min(level_val, 10))
    cefr_level = CEFR_LEVELS[level_val]

    example_exercise_block["level"] = cefr_level

    print("🧠 Sending request to Mistral AI...", flush=True)

    user_prompt = {
        "role": "user",
        "content": f"""
You are generating structured grammar and translation exercises for a German learner.
The student's level is {level_val}/10 (CEFR {cefr_level}).
Adjust sentence complexity and vocabulary accordingly.

Here is the required JSON structure — you must follow it **exactly**:

1. Each exercise must include:
   - `id`: a unique ID like `"ex1"`
   - `type`: either `"gap-fill"` or `"translation"`
   - `question`: a string (either a full sentence with a blank depending on the students level, or a translation task with the same conditions, remember to always put a full sentence)
   - For "gap-fill":
     - `options`: list of 4 strings
     - `correctAnswer`: the correct string
   - For "translation":
     - `correctAnswer`: the correct German translation
   - `explanation`: one-line grammar explanation

 2. The overall JSON must contain:
   - `lessonId`, `title`, `instructions`, `level`
   - `exercises`: list of 2 total exercises (mix of both types)
   - `feedbackPrompt`
   - `vocabHelp`: list of vocab entries with:
       - `word`, `meaning`

⚠️ Do not change field names or format.
⚠️ Do not include other types like "sentenceCreation", "prompt", or "hint".
⚠️ All keys must match the example exactly.
⚠️ Do not repeat or reuse any example sentences from previous exercises or memory.
⚠️ Always generate new, unique sentences that were not seen in earlier exercises.

Here is an example structure for reference (do not reuse content!):
{json.dumps(example_exercise_block, indent=2)}

Here is the learner’s vocabulary list (prioritize vocab with next_repeat due soon, include one or two per sentence, try to teach the learner new words based):
{json.dumps(vocabular, indent=2)}

Here is the topic memory (prioritize these themes or test new related ones):
{json.dumps(filtered_topic_memory, indent=2)}
When you create new sentences, do never use the same sentences from the context in topic memory, use them only to see where the student has a weakness on what context.
Create new sentences with new words and topics.
Create a new exercise block using the **same structure** and **same field names**, but adapt the **content** to the learner’s weaknesses and level.
"""
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            user_prompt
        ],
        "temperature": 0.7
    }
    print(user_prompt, flush=True)
    response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        if parsed is not None:
            print("✅ Successfully parsed exercise block from AI.", flush=True)
            parsed = _ensure_schema(parsed)
            parsed["level"] = cefr_level
            print(json.dumps(parsed, indent=2), flush=True)
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
    """Return a short paragraph of feedback in English.

    The prompt uses the student's vocabulary list to build short example
    sentences and checks topic memory entries to highlight repeated errors.
    """
    correct = summary.get("correct", 0)
    total = summary.get("total", 0)
    mistakes = summary.get("mistakes", [])

    if total == 0:
        return "No answers were submitted."

    mistakes_text = "\n".join(
        f"- Question: {m['question']} | Your answer: {m['your_answer']} | Correct: {m['correct_answer']}"
        for m in mistakes[:3]
    )

    # Build short example sentences using the student's vocabulary
    examples = []
    if vocab:
        for item in vocab[:3]:
            word = item.get("word")
            if not word:
                continue
            translation = item.get("translation")
            if translation:
                examples.append(f"Example: {word} – {translation}.")
            else:
                examples.append(f"Example: {word}.")
    examples_text = "\n".join(examples)

    repeated_topics = []
    if topic_memory:
        topic_counts = {}
        for entry in topic_memory:
            topic = entry.get("topic")
            if not topic:
                continue
            for t in str(topic).split(','):
                t = t.strip()
                if not t:
                    continue
                topic_counts[t] = topic_counts.get(t, 0) + 1
        repeated_topics = [t for t, c in topic_counts.items() if c > 1]
    repeated_text = "\n".join(f"- {t}" for t in repeated_topics[:3])

    user_prompt = {
        "role": "user",
        "content": f"""
You are a friendly German teacher. Summarise this placement test result for the new student.

Correct answers: {correct} out of {total}

List each mistake in the following format:
{mistakes_text}

If a topic was answered incorrectly multiple times also mention it:
{repeated_text}

Use these vocabulary items in short example sentences:
{examples_text}

End with two short sentences explaining that this platform will generate custom exercises focusing on the student's weak areas so they can improve.
"""
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "Write a short ecouraging one line feedback in English. Mention what went well and what could be improved."},
            user_prompt
        ],
        "temperature": 0.5
    }

    response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return "Could not generate feedback."
