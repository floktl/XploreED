"""
AI Memory Module

This module contains spaced repetition and memory management functionality for
optimizing learning retention and vocabulary acquisition.

Author: XplorED Team
Date: 2025
"""

from .vocabulary_memory import (
    normalize_word,
    vocab_exists,
    save_vocab,
    analyze_word_ai,
    extract_words,
    translate_to_german,
    review_vocab_word
)

from .level_manager import (
    initialize_topic_memory_for_level,
    calculate_level_progress,
    check_auto_level_up
)

from .logger import (
    topic_memory_logger
)

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
