import re
import json
from utils.ai.prompts import detect_topics_prompt
from utils.ai.ai_api import send_prompt


def _extract_json(text: str):
    """Parse a JSON list from ``text`` if possible."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None



def detect_language_topics(text: str) -> list[str]:
    """Use Mistral to detect grammar topics present in ``text``."""

    user_prompt = detect_topics_prompt(text)

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            topics = _extract_json(content)
            if isinstance(topics, list):
                cleaned = [t.strip().lower() for t in topics if isinstance(t, str)]
                return sorted(set(cleaned))
    except Exception as e:
        print("[detect_language_topics] ⚠️ Mistral topic detection failed:", e, flush=True)

    return []

__all__ = ["detect_language_topics"]
