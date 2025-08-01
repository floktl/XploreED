"""
XplorED - AI Memory Package

This package provides spaced repetition and memory management functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

AI Memory Components:
- Vocabulary Memory: Spaced repetition for vocabulary learning and retention
- Level Management: User level progression and topic memory management
- Memory Logging: Topic memory logging and analytics
- Learning Optimization: Optimize learning intervals and memory retention

For detailed architecture information, see: docs/backend_structure.md
"""

# Import vocabulary memory functions
from .vocabulary_memory import (
    normalize_word,
    vocab_exists,
    save_vocab,
    analyze_word_ai,
    extract_words,
    translate_to_german,
    review_vocab_word
)

# Import level management functions
from .level_manager import (
    initialize_topic_memory_for_level,
    calculate_level_progress,
    check_auto_level_up
)

# Import memory logging functions
from .logger import (
    topic_memory_logger
)

# Re-export all AI memory functions for backward compatibility
__all__ = [
    # Vocabulary Memory
    'normalize_word',
    'vocab_exists',
    'save_vocab',
    'analyze_word_ai',
    'extract_words',
    'translate_to_german',
    'review_vocab_word',

    # Level Management
    'initialize_topic_memory_for_level',
    'calculate_level_progress',
    'check_auto_level_up',

    # Memory Logging
    'topic_memory_logger'
]
