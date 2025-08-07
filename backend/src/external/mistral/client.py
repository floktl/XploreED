"""
XplorED - Mistral AI Client

This module provides the external integration with Mistral AI's API for
advanced language processing capabilities, following clean architecture principles.

Features:
- Request payload building with configurable parameters
- HTTP request handling with comprehensive error management
- Streaming support for real-time responses
- Automatic Markdown formatting for structured outputs

For detailed architecture information, see: docs/backend_structure.md
"""

import os
import requests  # type: ignore
import traceback
import logging
from typing import List, Optional
from shared.constants import MISTRAL_API_URL, MISTRAL_MODEL
from shared.exceptions import AIEvaluationError

logger = logging.getLogger(__name__)

# === Configuration ===
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}


# === Request Building ===
def build_payload(
    messages: list[dict],
    temperature: float = 0.7,
    stream: bool = False
) -> dict:
    """
    Build request payload for the Mistral API.

    Args:
        messages: List of message dictionaries with role and content
        temperature: Controls response randomness (0.0-1.0)
        stream: Enable streaming responses

    Returns:
        dict: Formatted payload for Mistral API
    """
    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    if stream:
        payload["stream"] = True

    return payload


# === Request Handling ===
def send_request(
    messages: list[dict],
    temperature: float = 0.7,
    stream: bool = False
) -> requests.Response:
    """
    Send a request to the Mistral API and return the raw response.

    Args:
        messages: List of message dictionaries with role and content
        temperature: Controls response randomness (0.0-1.0)
        stream: Enable streaming responses

    Returns:
        requests.Response: Raw API response

    Raises:
        AIEvaluationError: When API request fails
    """
    try:
        payload = build_payload(messages, temperature, stream)

        # Send request to Mistral API
        response = requests.post(
            MISTRAL_API_URL,
            headers=HEADERS,
            json=payload,
            timeout=60,
            stream=stream
        )

        # Handle non-200 responses
        if response.status_code != 200:
            error_msg = f"Mistral API error: {response.status_code} - {response.text}"
            raise AIEvaluationError(error_msg)

        return response

    except requests.exceptions.Timeout:
        raise AIEvaluationError("Mistral API request timed out after 60 seconds")
    except requests.exceptions.RequestException as e:
        raise AIEvaluationError(f"Mistral API request failed: {str(e)}")
    except Exception as e:
        error_msg = f"Mistral API error: {str(e)}"
        logger.error(error_msg)
        raise AIEvaluationError(error_msg)


# === Convenience Functions ===
def send_prompt(
    system_message: str,
    user_prompt: dict,
    temperature: float = 0.7,
    stream: bool = False
) -> requests.Response:
    """
    Convenience wrapper for sending system and user prompts.

    Automatically enhances system messages for chat/feedback endpoints
    with Markdown formatting instructions.

    Args:
        system_message: System prompt defining AI behavior
        user_prompt: User message dictionary with role and content
        temperature: Controls response randomness (0.0-1.0)
        stream: Enable streaming responses

    Returns:
        requests.Response: Raw API response
    """
    # Enhance system message for chat/feedback endpoints
    if "chat" in system_message.lower() or "teacher" in system_message.lower():
        system_message += " Always use Markdown for tables, lists, and formatting."

    messages = [
        {"role": "system", "content": system_message},
        user_prompt,
    ]

    return send_request(messages, temperature, stream)


# === Export Configuration ===
__all__ = [
    "build_payload",
    "send_request",
    "send_prompt",
]

