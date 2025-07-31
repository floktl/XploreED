"""
XplorED - JSON Processing Utilities

This module provides JSON parsing and extraction utilities,
following clean architecture principles as outlined in the documentation.

JSON Operations:
- Content Extraction: Extract JSON from mixed text content
- Error Handling: Robust parsing with fallback mechanisms
- Data Validation: Safe JSON object extraction and validation

For detailed architecture information, see: docs/backend_structure.md
"""

import json
import re
from typing import Any, Optional


# === JSON Content Extraction ===
def extract_json(text: str) -> Optional[Any]:
    """
    Extract and parse JSON object from a possibly messy string.

    This function attempts to extract valid JSON from text that may contain
    additional content, such as AI responses or log output. It uses multiple
    strategies to find and parse JSON content.

    Args:
        text: String that may contain JSON content

    Returns:
        Optional[Any]: Parsed JSON object if found, None otherwise

    Examples:
        >>> extract_json('Some text {"key": "value"} more text')
        {'key': 'value'}

        >>> extract_json('No JSON here')
        None
    """
    # First attempt: direct JSON parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Second attempt: find JSON object with regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


# === Export Configuration ===
__all__ = [
    "extract_json",
]

