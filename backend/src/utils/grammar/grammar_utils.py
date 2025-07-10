import re
import json
from utils.ai.prompts import detect_topics_prompt
from utils.ai.ai_api import send_prompt


def _extract_json(text: str):
    """Parse a JSON list from ``text`` if possible."""
    # print("[_extract_json] Raw input:", text, flush=True)
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
    """Use Mistral to detect grammar topics present in ``text``."""
    # print("[detect_language_topics] 🔍 Input:", text, flush=True)

    user_prompt = detect_topics_prompt(text)

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
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
