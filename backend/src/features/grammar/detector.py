import re
import json
from features.ai.prompts.exercise_prompts import detect_topics_prompt
from external.mistral.client import send_prompt


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
    # print("\033[95m🔍 [TOPIC MEMORY FLOW] 🔍 Starting detect_language_topics for text: '{}'\033[0m".format(text[:50] + "..." if len(text) > 50 else text), flush=True)

    user_prompt = detect_topics_prompt(text)
    # print("\033[96m🤖 [TOPIC MEMORY FLOW] 🤖 Calling Mistral AI for topic detection\033[0m", flush=True)
    print(f"\033[92m[MISTRAL CALL] detect_language_topics\033[0m", flush=True)
    print(user_prompt)
    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            print("\033[93m📄 [TOPIC MEMORY FLOW] 📄 Received AI response: '{}'\033[0m".format(content[:100] + "..." if len(content) > 100 else content), flush=True)

            topics = _extract_json(content)
            if isinstance(topics, list):
                cleaned = [t.strip().lower() for t in topics if isinstance(t, str)]
                result = sorted(set(cleaned))
                # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully detected topics: {}\033[0m".format(result), flush=True)
                return result
            else:
                print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Failed to parse topics from AI response\033[0m", flush=True)
        else:
            print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ AI API returned status code: {}\033[0m".format(resp.status_code), flush=True)
    except Exception as e:
        print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Mistral topic detection failed: {}\033[0m".format(e), flush=True)
        print("[detect_language_topics] ⚠️ Mistral topic detection failed:", e, flush=True)

    print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Returning empty topic list due to error\033[0m", flush=True)
    return []

__all__ = ["detect_language_topics"]
