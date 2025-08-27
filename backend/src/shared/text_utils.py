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
from shared.exceptions import ValidationError

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
        if not isinstance(text, str):
            return None

        cleaned = text.strip()

        # 1) Strip Markdown code fences like ```json ... ``` or ``` ... ```
        #    Remove leading/trailing triple backticks blocks if present
        cleaned = re.sub(r"^```[a-zA-Z0-9_\-]*\s*\n", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned, flags=re.MULTILINE)

        # 2) Remove JavaScript-style comments which are invalid in strict JSON
        #    - Line comments: // ... end-of-line
        #    - Block comments: /* ... */
        cleaned = re.sub(r"(?m)//.*$", "", cleaned)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

        # 3) Remove trailing commas before closing brackets/braces
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        # 4) Try direct parse of the whole cleaned text first
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass

        # 5) Fallback: extract the first JSON-looking object/array from the text
        json_patterns = [
            r"\{[^\0]*?\}",   # Non-greedy object
            r"\[[^\0]*?\]",   # Non-greedy array
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned, re.DOTALL)
            for match in matches:
                candidate = re.sub(r",\s*([}\]])", r"\1", match)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        # 6) Final attempt on the original text (in case it was already valid)
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
