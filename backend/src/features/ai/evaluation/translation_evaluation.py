"""
XplorED - Translation Evaluation Module

This module provides translation evaluation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Translation Evaluation Components:
- Translation Assessment: Evaluate translation accuracy and quality
- Text Processing: Process and normalize text for comparison
- Quality Scoring: Score translation quality using AI
- Evaluation Results: Process and format evaluation results

For detailed architecture information, see: docs/backend_structure.md
"""

import json
import re
from typing import Tuple, Optional

from shared.text_utils import _extract_json, _normalize_umlauts, _strip_final_punct
from features.ai.prompts import evaluate_translation_prompt
from external.mistral.client import send_prompt
from shared.exceptions import AIEvaluationError, ValidationError

import logging
logger = logging.getLogger(__name__)


def evaluate_translation_ai(english: str, reference: str, student: str) -> Tuple[bool, str]:
    """
    Evaluate translation accuracy using AI.

    Args:
        english: The original English text
        reference: The reference German translation
        student: The student's German translation

    Returns:
        Tuple of (is_correct, reason)
    """
    # Ignore final . or ? for both student and reference
    reference = _strip_final_punct(reference)
    student = _strip_final_punct(student)
    # Normalize umlauts for both answers
    reference = _normalize_umlauts(reference)
    student = _normalize_umlauts(student)

    # Direct comparison with normalized strings
    if student.strip().lower() == reference.strip().lower():
        return True, "Your translation is correct!"

    # If direct comparison fails, use AI evaluation
    logger.debug("Evaluating translation using Mistral...")
    logger.debug(f"Inputs: english='{english}', reference='{reference}', student='{student}'")

    user_prompt = evaluate_translation_prompt(english, student)

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            data = _extract_json(content)
            if isinstance(data, dict):
                return bool(data.get("correct")), str(data.get("reason", ""))
    except AIEvaluationError:
        raise
    except Exception as e:
        logger.error(f"Error evaluating translation with AI: {e}")
        raise AIEvaluationError(f"Error evaluating translation with AI: {str(e)}")

    return False, "Could not evaluate translation."


def compare_translations(reference: str, student: str) -> dict:
    """
    Compare two translations and return detailed analysis.

    Args:
        reference: The reference translation
        student: The student's translation

    Returns:
        Dictionary containing comparison analysis
    """
    try:
        # Normalize both translations
        ref_norm = _normalize_umlauts(_strip_final_punct(reference))
        stu_norm = _normalize_umlauts(_strip_final_punct(student))

        # Check for exact match
        if stu_norm.lower() == ref_norm.lower():
            return {
                "exact_match": True,
                "similarity": 1.0,
                "differences": [],
                "suggestions": []
            }

        # Calculate basic similarity
        ref_words = set(ref_norm.lower().split())
        stu_words = set(stu_norm.lower().split())

        if ref_words:
            similarity = len(ref_words.intersection(stu_words)) / len(ref_words)
        else:
            similarity = 0.0

        # Find differences
        missing_words = ref_words - stu_words
        extra_words = stu_words - ref_words

        return {
            "exact_match": False,
            "similarity": similarity,
            "differences": {
                "missing_words": list(missing_words),
                "extra_words": list(extra_words)
            },
            "suggestions": []
        }

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error comparing translations: {e}")
        raise AIEvaluationError(f"Error comparing translations: {str(e)}")
