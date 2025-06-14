import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = "WPu0KpNOAUFviCzNgnbWQuRbz7Zpwyde"
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

def generate_new_exercises(vocabular, topic_memory, example_exercise_block):
    user_prompt = {
        "role": "user",
        "content": f"""
Given the following vocabulary memory:
{json.dumps(vocabular, indent=2)}

And topic memory:
{json.dumps(topic_memory, indent=2)}

Use the following exercise block as an example:
{json.dumps(example_exercise_block, indent=2)}

Now create a new exercise block that adapts to the student's vocabulary and grammar weaknesses. Output only a JSON object with the same structure.
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
        try:
            parsed_json = json.loads(content)
            return parsed_json
        except json.JSONDecodeError:
            print("Error parsing JSON from model response. Raw output:")
            print(content)
            return None
    else:
        print(f"API request failed: {response.status_code} - {response.text}")
        return None

# === EXAMPLE USAGE ===
if __name__ == "__main__":
    example_block = {
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

    vocab_data = [
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

    topic_memory_data = [
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

    new_exercise = generate_new_exercises(vocab_data, topic_memory_data, example_block)
    if new_exercise:
        print(json.dumps(new_exercise, indent=2, ensure_ascii=False))
