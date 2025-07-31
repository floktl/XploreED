"""
AI Prompts Module

This module contains AI prompt templates and utilities for generating
consistent and effective AI interactions.

Author: XplorED Team
Date: 2025
"""

from .exercise_prompts import (
    exercise_generation_prompt,
    feedback_generation_prompt,
    analyze_word_prompt,
    translate_sentence_prompt,
    translate_word_prompt,
    evaluate_translation_prompt,
    quality_evaluation_prompt,
    answers_evaluation_prompt,
    reading_exercise_prompt,
    game_sentence_prompt,
    weakness_lesson_prompt,
    detect_topics_prompt
)

from .utils import (
    make_prompt,
    SYSTEM_PROMPT,
    FEEDBACK_SYSTEM_PROMPT
)

__all__ = [
    # Exercise Prompts
    'exercise_generation_prompt',
    'feedback_generation_prompt',
    'analyze_word_prompt',
    'translate_sentence_prompt',
    'translate_word_prompt',
    'evaluate_translation_prompt',
    'quality_evaluation_prompt',
    'answers_evaluation_prompt',
    'reading_exercise_prompt',
    'game_sentence_prompt',
    'weakness_lesson_prompt',
    'detect_topics_prompt',

    # Prompt Utilities
    'make_prompt',
    'SYSTEM_PROMPT',
    'FEEDBACK_SYSTEM_PROMPT'
]
