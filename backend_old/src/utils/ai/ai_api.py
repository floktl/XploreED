"""Shared Mistral API helpers."""

import os
import requests  # type: ignore
import traceback
import logging
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
    try:
        payload = build_payload(messages, temperature, stream)
        # logging.info("Sending request to Mistral API: %s", MISTRAL_API_URL)
        # logging.debug("Request payload: %s", payload)

        response = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=60, stream=stream)

        if response.status_code != 200:
            # logging.error("=== MISTRAL API ERROR ===")
            # logging.error("Status code: %s", response.status_code)
            # logging.error("Response text: %s", response.text)
            # logging.error("Request payload: %s", payload)
            # logging.error("Headers: %s", HEADERS)
            pass

        return response
    except requests.exceptions.Timeout as e:
        # logging.error("=== MISTRAL API TIMEOUT ===")
        # logging.error("Timeout after 60 seconds")
        # logging.error("Request payload: %s", payload)
        # logging.error("Full stack trace:\n%s", traceback.format_exc())
        raise
    except requests.exceptions.RequestException as e:
        # logging.error("=== MISTRAL API REQUEST ERROR ===")
        # logging.error("Error type: %s", type(e).__name__)
        # logging.error("Error message: %s", str(e))
        # logging.error("Request payload: %s", payload)
        # logging.error("Full stack trace:\n%s", traceback.format_exc())
        raise
    except Exception as e:
        # logging.error("=== MISTRAL API UNEXPECTED ERROR ===")
        # logging.error("Error type: %s", type(e).__name__)
        # logging.error("Error message: %s", str(e))
        # logging.error("Request payload: %s", payload)
        # logging.error("Full stack trace:\n%s", traceback.format_exc())
        raise


def send_prompt(system_message: str, user_prompt: dict, temperature: float = 0.7, stream: bool = False) -> requests.Response:
    """Convenience wrapper for a system and user prompt."""
    # For chat/feedback endpoints, encourage Markdown output for tables/lists
    if "chat" in system_message.lower() or "teacher" in system_message.lower():
        system_message += " Always use Markdown for tables, lists, and formatting."
    messages = [
        {"role": "system", "content": system_message},
        user_prompt,
    ]
    return send_request(messages, temperature, stream)

