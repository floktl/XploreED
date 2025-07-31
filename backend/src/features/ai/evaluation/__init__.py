"""
AI Evaluation Module

This module contains AI-powered evaluation and assessment functionality for
user responses, exercises, and translations.

Author: XplorED Team
Date: 2025
"""

from .exercise_evaluator import (
    evaluate_answers_with_ai,
    generate_alternative_answers,
    generate_explanation
)

from .translation_evaluator import (
    evaluate_translation_ai,
    evaluate_topic_qualities_ai,
    update_topic_memory_translation,
    update_topic_memory_reading,
    compare_topic_qualities
)

__all__ = [
    # Exercise Evaluation
    'evaluate_answers_with_ai',
    'generate_alternative_answers',
    'generate_explanation',

    # Translation Evaluation
    'evaluate_translation_ai',
    'evaluate_topic_qualities_ai',
    'update_topic_memory_translation',
    'update_topic_memory_reading',
    'compare_topic_qualities'
]
