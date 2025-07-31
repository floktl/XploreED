"""
AI Generation Module

This module contains AI-powered content generation functionality for exercises,
lessons, translations, and other learning materials.

Author: XplorED Team
Date: 2025
"""

from .exercise_generator import (
    generate_training_exercises,
    evaluate_exercises,
    prefetch_next_exercises
)

from .reading_helpers import (
    generate_reading_exercise
)

from .lesson_generator import (
    update_reading_memory_async
)

from .misc_helpers import (
    stream_ai_answer
)

from .translate_helpers import (
    update_memory_async
)



from .helpers import (
    _adjust_gapfill_results
)

__all__ = [
    # Exercise Generation
    'generate_training_exercises',
    'evaluate_exercises',
    'prefetch_next_exercises',

    # Reading Generation
    'generate_reading_exercise',

    # Lesson Generation
    'update_reading_memory_async',

    # Misc Generation
    'stream_ai_answer',

    # Translation Generation
    'update_memory_async',



    # Helper Functions
    '_adjust_gapfill_results'
]
