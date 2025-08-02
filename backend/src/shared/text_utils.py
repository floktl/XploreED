"""
XplorED - Shared Text Utilities Module

This module provides shared text processing utilities for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Text Utilities Components:
- JSON Extraction: Extract JSON from text responses
- Text Normalization: Normalize text for comparison
- Punctuation Handling: Handle punctuation in text processing

For detailed architecture information, see: docs/backend_structure.md
"""

import json
import logging
import re
from typing import Optional, Any

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> Optional[Any]:
    """
    Extract JSON from text that may contain other content.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON object or None if extraction fails
    """
    try:
        # Look for JSON-like patterns
        json_patterns = [
            r'\{.*\}',  # Object pattern
            r'\[.*\]',  # Array pattern
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        # If no JSON found in patterns, try parsing the entire text
        return json.loads(text.strip())

    except json.JSONDecodeError as e:
        logger.debug(f"Failed to extract JSON from text: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting JSON from text: {e}")
        return None


def _normalize_umlauts(text: str) -> str:
    """
    Normalize German umlauts for comparison.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized umlauts
    """
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss'
    }
    for umlaut, replacement in umlaut_map.items():
        text = text.replace(umlaut, replacement)
    return text


def _strip_final_punct(text: str) -> str:
    """
    Strip final punctuation from text.

    Args:
        text: Text to process

    Returns:
        Text with final punctuation removed
    """
    return text.rstrip(".,!?;:")
