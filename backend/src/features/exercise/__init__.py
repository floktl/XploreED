"""
Exercise Feature Module

This module contains exercise management and evaluation functionality.

Author: XplorED Team
Date: 2025
"""

from .exercise_manager import (
    create_exercise_block,
    get_exercise_block,
    get_user_exercise_blocks,
    submit_exercise_answers,
    get_exercise_results,
    delete_exercise_block,
    update_exercise_block_status,
    get_exercise_statistics
)

from .exercise_evaluator import (
    check_gap_fill_correctness,
    parse_submission_data,
    evaluate_first_exercise,
    create_immediate_results,
    evaluate_remaining_exercises_async,
    argue_exercise_evaluation,
    get_topic_memory_status
)

__all__ = [
    # Exercise Management
    'create_exercise_block',
    'get_exercise_block',
    'get_user_exercise_blocks',
    'submit_exercise_answers',
    'get_exercise_results',
    'delete_exercise_block',
    'update_exercise_block_status',
    'get_exercise_statistics',

    # Exercise Evaluation
    'check_gap_fill_correctness',
    'parse_submission_data',
    'evaluate_first_exercise',
    'create_immediate_results',
    'evaluate_remaining_exercises_async',
    'argue_exercise_evaluation',
    'get_topic_memory_status'
]
