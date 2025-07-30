"""
Exercise Feature Module

This module contains exercise management functionality.

Author: German Class Tool Team
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

__all__ = [
    # Exercise Manager
    'create_exercise_block',
    'get_exercise_block',
    'get_user_exercise_blocks',
    'submit_exercise_answers',
    'get_exercise_results',
    'delete_exercise_block',
    'update_exercise_block_status',
    'get_exercise_statistics'
]
