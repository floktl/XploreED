"""Centralised prompt helpers for Mistral API."""

SYSTEM_PROMPT = (
    "Your task is to generate new exercises in JSON format. "
    "Use provided memory data to tailor difficulty."
)

FEEDBACK_SYSTEM_PROMPT = (
    "You are a strict German teacher, answer in english only, "
    "and skip any small talk, focus on improvement only"
)


def make_prompt(content: str, system: str = SYSTEM_PROMPT) -> list[dict]:
    """Return a messages list for the Mistral API."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]

