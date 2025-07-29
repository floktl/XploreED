"""
German Class Tool - Mistral AI Integration

This module provides integration with Mistral AI's language processing API,
following clean architecture principles as outlined in the documentation.

Components:
- client: HTTP client for Mistral AI API requests
- Configuration: API endpoints and model settings

For detailed architecture information, see: docs/backend_structure.md
"""

from .client import build_payload, send_request, send_prompt

__all__ = [
    "build_payload",
    "send_request",
    "send_prompt",
]
