"""
XplorED - Exercise Package

This package provides exercise functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Modules:
- exercise_creation: Exercise block creation and management
- exercise_evaluation: Exercise evaluation and processing
- exercise_results: Exercise results and statistics

For detailed architecture information, see: docs/backend_structure.md
"""

from .exercise_creation import (
    create_exercise_block,
    get_exercise_block,
    get_user_exercise_blocks,
    delete_exercise_block,
    update_exercise_block_status,
)

from .exercise_evaluation import (
    parse_submission_data,
    evaluate_first_exercise,
    create_immediate_results,
    evaluate_remaining_exercises_async,
)

from .exercise_results import (
    submit_exercise_answers,
    get_exercise_results,
    get_exercise_statistics,
    argue_exercise_evaluation,
    get_topic_memory_status,
)

# Import from AI evaluation to avoid circular imports
from features.ai.evaluation.exercise_evaluator import check_gap_fill_correctness

# Re-export all exercise functions for backward compatibility
__all__ = [
    # Exercise creation
    "create_exercise_block",
    "get_exercise_block",
    "get_user_exercise_blocks",
    "delete_exercise_block",
    "update_exercise_block_status",

    # Exercise evaluation
    "check_gap_fill_correctness",
    "parse_submission_data",
    "evaluate_first_exercise",
    "create_immediate_results",
    "evaluate_remaining_exercises_async",

    # Exercise results
    "submit_exercise_answers",
    "get_exercise_results",
    "get_exercise_statistics",
    "argue_exercise_evaluation",
    "get_topic_memory_status",
]
