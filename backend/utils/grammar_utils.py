import os
import re
import json
import requests

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}

def _extract_json(text: str):
    print("[_extract_json] Raw input:", text, flush=True)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                print("[_extract_json] Failed to parse matched JSON.", flush=True)
                pass
    print("[_extract_json] Returning None.", flush=True)
    return None



def detect_language_topics(text: str) -> list[str]:
    # print("[detect_language_topics] 🔍 Input:", text, flush=True)

    user_prompt = {
        "role": "user",
        "content": f"""
You are a helpful German teacher. Identify grammar topics used in the following sentence:

"{text}"

Return only a JSON list of strings such as:
["modal verb", "pronoun", "subordinating conjunction"]
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
        # print("[detect_language_topics] ✅ Mistral response received.", flush=True)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # print("[detect_language_topics] 📦 Raw Mistral output:", content, flush=True)
            topics = _extract_json(content)
            if isinstance(topics, list):
                cleaned = [t.strip().lower() for t in topics if isinstance(t, str)]
                # print("[detect_language_topics] ✅ Parsed grammar topics:", cleaned, flush=True)
                return sorted(set(cleaned))
    except Exception as e:
        print("[detect_language_topics] ⚠️ Mistral topic detection failed:", e, flush=True)

    return []

__all__ = ["detect_language_topics"]
