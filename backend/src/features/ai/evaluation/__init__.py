"""
XplorED - AI Evaluation Package

This package provides AI-powered evaluation and assessment functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

AI Evaluation Components:
- Exercise Evaluation: AI-powered assessment of exercise responses
- Translation Evaluation: Evaluate translation accuracy and quality
- Topic Evaluation: Evaluate grammar topic quality and performance
- Topic Memory: Update and manage topic memory based on evaluations

For detailed architecture information, see: docs/backend_structure.md
"""

# Import exercise evaluation functions
from .exercise_evaluation import (
    evaluate_answers_with_ai,
    generate_alternative_answers,
    generate_explanation
)

# Import exercise processing functions
from .exercise_processing import (
    process_ai_answers
)

# Import exercise helper functions
from .gap_fill_check import (
    check_gap_fill_correctness
)

# Import translation evaluation functions
from .translation_evaluation import (
    evaluate_translation_ai,
    compare_translations
)

# Import topic evaluation functions
from .topic_evaluation import (
    evaluate_topic_qualities_ai,
    compare_topic_qualities,
    analyze_topic_performance
)

# Import topic memory functions
from .topic_memory import (
    update_topic_memory_translation,
    update_topic_memory_reading,
    get_topic_memory_summary
)

# Re-export all AI evaluation functions for backward compatibility
__all__ = [
    # Exercise Evaluation
    'evaluate_answers_with_ai',
    'generate_alternative_answers',
    'generate_explanation',

    # Exercise Processing
    'process_ai_answers',

    # Exercise Helpers
    'check_gap_fill_correctness',

    # Translation Evaluation
    'evaluate_translation_ai',
    'compare_translations',

    # Topic Evaluation
    'evaluate_topic_qualities_ai',
    'compare_topic_qualities',
    'analyze_topic_performance',

    # Topic Memory
    'update_topic_memory_translation',
    'update_topic_memory_reading',
    'get_topic_memory_summary'
]
