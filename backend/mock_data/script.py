# === mistral_exercise_generator.py ===

import requests
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or "WPu0KpNOAUFviCzNgnbWQuRbz7Zpwyde"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json"
}

SYSTEM_PROMPT = """
You are an expert German language teacher AI.
Your task is to generate new grammar and vocabulary exercises in JSON format.
Use provided memory data to tailor difficulty and topic focus.
Use the example structure to maintain consistency.
"""

# === FALLBACK DATA ===

FALLBACK_EXERCISE_BLOCK = {
  "lessonId": "mock-ai-lesson-001",
  "title": "Using 'sein' in the Present Tense",
  "instructions": "Fill in the blanks or translate the sentences.",
  "level": "A1",
  "exercises": [
    {"id": "ex1", "type": "gap-fill", "question": "Ich ___ müde.", "options": ["bist", "bin", "ist", "seid"], "correctAnswer": "bin", "explanation": "'Ich' uses 'bin' in present tense."},
    {"id": "ex2", "type": "gap-fill", "question": "Du ___ mein Freund.", "options": ["bin", "bist", "ist", "seid"], "correctAnswer": "bist", "explanation": "'Du' requires 'bist'."},
    {"id": "ex3", "type": "translation", "question": "Translate to German: He is tired.", "correctAnswer": "Er ist müde.", "explanation": "Use 'er ist' for 'he is'."},
    {"id": "ex4", "type": "gap-fill", "question": "Wir ___ in Berlin.", "options": ["seid", "bin", "ist", "sind"], "correctAnswer": "sind", "explanation": "'Wir' uses 'sind' for the plural form."},
    {"id": "ex5", "type": "translation", "question": "Translate to German: They are students.", "correctAnswer": "Sie sind Studenten.", "explanation": "Use plural 'sie sind'."}
  ],
  "feedbackPrompt": "Good start! You sometimes mix up plural forms. Remember 'wir sind' and 'sie sind'.",
  "nextInstructions": "More practice with 'sein'. Fill or translate the following.",
  "nextExercises": [
    {"id": "ex6", "type": "gap-fill", "question": "Er ___ Student.", "options": ["ist", "sind", "bist", "seid"], "correctAnswer": "ist", "explanation": "'Er' pairs with 'ist'."},
    {"id": "ex7", "type": "gap-fill", "question": "Ihr ___ müde.", "options": ["ist", "bist", "seid", "sind"], "correctAnswer": "seid", "explanation": "'Ihr' uses 'seid'."},
    {"id": "ex8", "type": "translation", "question": "Translate to German: I am late.", "correctAnswer": "Ich bin spät.", "explanation": "Use 'bin' with 'ich'."},
    {"id": "ex9", "type": "translation", "question": "Translate to German: She is at home.", "correctAnswer": "Sie ist zu Hause.", "explanation": "Use 'sie ist' with 'zu Hause'."},
    {"id": "ex10", "type": "gap-fill", "question": "Sie (they) ___ Lehrer.", "options": ["bist", "ist", "seid", "sind"], "correctAnswer": "sind", "explanation": "Plural 'sie' uses 'sind'."}
  ],
  "nextFeedbackPrompt": "Great! Keep paying attention to pronouns and word order.",
  "vocabHelp": [
    {"word": "sein", "meaning": "to be"},
    {"word": "müde", "meaning": "tired"},
    {"word": "Student", "meaning": "student"}
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
        "topic": "sein",
        "skill_type": "grammar",
        "lesson_content_id": "1.1",
        "ease_factor": 2.2,
        "intervall": 3,
        "next_repeat": "2025-06-13",
        "repetitions": 2,
        "last_review": "2025-06-10"
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
            "correctAnswer": ex.get("correctAnswer") or ex.get("answer") or "Missing",
            "explanation": ex.get("explanation") or ex.get("hint") or "No explanation."
        }
        if fixed["type"] == "gap-fill":
            fixed["options"] = ex.get("options", ["bin", "bist", "ist", "sind"])
        return fixed

    for key in ["exercises", "nextExercises"]:
        if key in exercise_block:
            exercise_block[key] = [fix_exercise(ex, i) for i, ex in enumerate(exercise_block[key])]

    return exercise_block

# === MAIN FUNCTION ===

def generate_new_exercises(vocabular=None, topic_memory=None, example_exercise_block=None):
    if not vocabular:
        print("⚠️ No vocabulary data found. Using fallback vocab.", flush=True)
        vocabular = FALLBACK_VOCAB_DATA
    if not topic_memory:
        print("⚠️ No topic memory found. Using fallback topic.", flush=True)
        topic_memory = FALLBACK_TOPIC_MEMORY
    if not example_exercise_block:
        print("⚠️ No example block provided. Using fallback block.", flush=True)
        example_exercise_block = FALLBACK_EXERCISE_BLOCK

    print("🧠 Sending request to Mistral AI...", flush=True)

    user_prompt = {
        "role": "user",
        "content": f"""
You are generating structured grammar and translation exercises for a German learner.

Here is the required JSON structure — you must follow it **exactly**:

1. Each exercise must include:
   - `id`: a unique ID like `"ex1"`
   - `type`: either `"gap-fill"` or `"translation"`
   - `question`: a string (either a sentence with a blank, or a translation task)
   - For "gap-fill":
     - `options`: list of 4 strings
     - `correctAnswer`: the correct string
   - For "translation":
     - `correctAnswer`: the correct German translation
   - `explanation`: one-line grammar explanation

2. The overall JSON must contain:
   - `lessonId`, `title`, `instructions`, `level`
   - `exercises`: list of 5 total exercises (mix of both types)
   - `feedbackPrompt`
   - `nextInstructions`
   - `nextExercises`: list of 5 total, same format
   - `nextFeedbackPrompt`
   - `vocabHelp`: list of vocab entries with:
       - `word`, `meaning`

⚠️ Do not change field names or format.
⚠️ Do not include other types like "conjugation", "sentenceCreation", "prompt", or "hint".
⚠️ All keys must match the example exactly.

Here is an example:
{json.dumps(example_exercise_block, indent=2)}

Based on the following memory data:
Vocabulary:
{json.dumps(vocabular, indent=2)}

Topic Memory:
{json.dumps(topic_memory, indent=2)}

Create a new exercise block using the **same structure** and **same field names**, but adapt the **content** to the learner’s weaknesses.
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

    response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        if parsed is not None:
            print("✅ Successfully parsed exercise block from AI.", flush=True)
            parsed = _ensure_schema(parsed)
            print(json.dumps(parsed, indent=2), flush=True)
            return parsed
        print("❌ Failed to parse JSON. Raw content:", flush=True)
        print(content, flush=True)
        return None
    else:
        print(f"❌ API request failed: {response.status_code} - {response.text}", flush=True)
        return None
