import os
import json
import re
import requests

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
