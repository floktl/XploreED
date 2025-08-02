"""
XplorED - AI Generation Package

This package provides AI-powered content generation functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

AI Generation Components:
- Exercise Generation: Generate AI-powered exercises and training content
- Reading Generation: Generate reading comprehension exercises
- Lesson Generation: Generate lesson content and materials
- Translation Generation: Generate translation exercises and content
- Feedback Generation: Generate AI-powered feedback and explanations
- Misc Generation: Generate miscellaneous AI content and responses

For detailed architecture information, see: docs/backend_structure.md
"""

# Import exercise creation functions
from .exercise_creation import (
    generate_new_exercises,
    _create_ai_block_with_variation,
    _generate_blocks_for_new_user,
    _generate_blocks_for_existing_user,
    generate_training_exercises,
    get_next_block_id,
    ensure_unique_block_title,
    get_recent_exercise_questions,
    update_exercise_history,
    prefetch_next_exercises,
    log_generated_sentences,
    print_exercise_block_sentences
)

# Import exercise processing functions
from .exercise_processing import (
    save_exercise_submission_async,
    evaluate_exercises,
    parse_ai_submission_data,
    compile_score_summary,
    log_exercise_event,
    log_ai_user_data,
    log_vocab_log,
    fetch_vocab_and_topic_data,
    get_ai_exercises,
    print_db_exercise_blocks
)

# Import exercise utilities
from .exercise_utilities import (
    format_exercise_block,
    validate_exercise_data,
    sanitize_exercise_text,
    extract_exercise_keywords,
    calculate_exercise_difficulty
)

# Import feedback helpers
from .feedback_helpers import (
    generate_feedback_prompt,
    format_feedback_block,
    _adjust_gapfill_results,
    get_recent_exercise_topics,
    create_feedback_summary
)

# Import existing helper functions
from .helpers import (
    _fix_exercise,
    _ensure_schema,
    store_user_ai_data,
    _create_ai_block
)

# Import reading generation functions
from .reading_helpers import (
    generate_reading_exercise,
    ai_reading_exercise
)

# Import lesson generation functions
from .lesson_generator import (
    update_reading_memory_async
)

# Import translation generation functions
from .translate_helpers import (
    update_memory_async
)

# Import misc generation functions
from .misc_helpers import (
    stream_ai_answer
)

# Re-export all AI generation functions for backward compatibility
__all__ = [
    # Exercise Creation
    'generate_new_exercises',
    '_create_ai_block_with_variation',
    '_generate_blocks_for_new_user',
    '_generate_blocks_for_existing_user',
    'generate_training_exercises',
    'get_next_block_id',
    'ensure_unique_block_title',
    'get_recent_exercise_questions',
    'update_exercise_history',
    'prefetch_next_exercises',
    'log_generated_sentences',
    'print_exercise_block_sentences',

    # Exercise Processing
    'save_exercise_submission_async',
    'evaluate_exercises',
    'parse_ai_submission_data',
    'compile_score_summary',
    'log_exercise_event',
    'log_ai_user_data',
    'log_vocab_log',
    'fetch_vocab_and_topic_data',
    'get_ai_exercises',
    'print_db_exercise_blocks',

    # Exercise Utilities
    'format_exercise_block',
    'validate_exercise_data',
    'sanitize_exercise_text',
    'extract_exercise_keywords',
    'calculate_exercise_difficulty',

    # Feedback Helpers
    'generate_feedback_prompt',
    'format_feedback_block',
    '_adjust_gapfill_results',
    'get_recent_exercise_topics',
    'create_feedback_summary',

    # Existing Helpers
    '_fix_exercise',
    '_ensure_schema',
    'store_user_ai_data',
    '_create_ai_block',

    # Reading Generation
    'generate_reading_exercise',
    'ai_reading_exercise',

    # Lesson Generation
    'update_reading_memory_async',

    # Translation Generation
    'update_memory_async',

    # Misc Generation
    'stream_ai_answer'
]
