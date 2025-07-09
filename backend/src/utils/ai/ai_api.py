"""Shared Mistral API helpers."""

import os
import requests
from typing import List, Dict

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}


def build_payload(messages: list[dict], temperature: float = 0.7, stream: bool = False) -> dict:
    """Return request payload for the Mistral API."""
    payload = {
        "model": "mistral-medium",
        "messages": messages,
        "temperature": temperature,
    }
    if stream:
        payload["stream"] = True
    return payload


def send_request(messages: list[dict], temperature: float = 0.7, stream: bool = False) -> requests.Response:
    """Send a request to the Mistral API and return the raw response."""
    payload = build_payload(messages, temperature, stream)
    return requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=20, stream=stream)


def send_prompt(system_message: str, user_prompt: dict, temperature: float = 0.7, stream: bool = False) -> requests.Response:
    """Convenience wrapper for a system and user prompt."""
    messages = [
        {"role": "system", "content": system_message},
        user_prompt,
    ]
    return send_request(messages, temperature, stream)

