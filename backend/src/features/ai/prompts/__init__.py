"""
XplorED - AI Prompts Package

This package provides organized prompt templates for AI interactions,
following clean architecture principles as outlined in the documentation.

Prompt Modules:
- exercise_generation_prompts: Exercise creation and feedback
- evaluation_prompts: Assessment and evaluation
- translation_prompts: Translation and language analysis
- ai_assistance_prompts: AI assistance and streaming
- reading_prompts: Reading exercises and games

For detailed architecture information, see: docs/backend_structure.md
"""

from .exercise_generation_prompts import (
    exercise_generation_prompt,
    feedback_generation_prompt,
    weakness_lesson_prompt,
)

from .evaluation_prompts import (
    detect_topics_prompt,
    evaluate_translation_prompt,
    quality_evaluation_prompt,
    answers_evaluation_prompt,
    alternative_answers_prompt,
    explanation_prompt,
)

from .translation_prompts import (
    translate_sentence_prompt,
    translate_word_prompt,
    analyze_word_prompt,
)

from .ai_assistance_prompts import (
    ai_context_prompt,
    ai_question_prompt,
    streaming_prompt,
)

from .reading_prompts import (
    reading_exercise_prompt,
    reading_explanation_prompt,
    game_sentence_prompt,
)

# Re-export all prompt functions for backward compatibility
__all__ = [
    # Exercise generation
    "exercise_generation_prompt",
    "feedback_generation_prompt",
    "weakness_lesson_prompt",

    # Evaluation
    "detect_topics_prompt",
    "evaluate_translation_prompt",
    "quality_evaluation_prompt",
    "answers_evaluation_prompt",
    "alternative_answers_prompt",
    "explanation_prompt",

    # Translation
    "translate_sentence_prompt",
    "translate_word_prompt",
    "analyze_word_prompt",

    # AI assistance
    "ai_context_prompt",
    "ai_question_prompt",
    "streaming_prompt",

    # Reading
    "reading_exercise_prompt",
    "reading_explanation_prompt",
    "game_sentence_prompt",
]
