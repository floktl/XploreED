"""
German Class Tool - External Integrations Module

This module provides external service integrations used throughout the backend application,
following clean architecture principles as outlined in the documentation.

Integrations:
- mistral: AI language processing via Mistral AI API
- redis: Caching and session management
- tts: Text-to-speech functionality

For detailed architecture information, see: docs/backend_structure.md
"""

from . import mistral
from . import redis
from . import tts

# Re-export commonly used items for convenience
from .mistral.client import build_payload, send_request, send_prompt

__all__ = [
    # Module imports
    "mistral",
    "redis",
    "tts",

    # Mistral client functions
    "build_payload",
    "send_request",
    "send_prompt",
]
