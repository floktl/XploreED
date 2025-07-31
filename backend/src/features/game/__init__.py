"""
Game Feature Module

This module contains game mechanics and interactive learning functionality.

Author: XplorED Team
Date: 2025
"""

from .game_helpers import (
    get_user_game_level,
    generate_game_sentence,
    create_game_round,
    evaluate_game_answer,
    get_game_statistics,
    create_game_session,
    update_game_progress,
    calculate_game_score
)

from .sentence_order import (
    generate_ai_sentence,
    get_scrambled_sentence,
    evaluate_order,
    get_feedback,
    save_result,
    get_all_results
)

__all__ = [
    # Game Helpers
    'get_user_game_level',
    'generate_game_sentence',
    'create_game_round',
    'evaluate_game_answer',
    'get_game_statistics',
    'create_game_session',
    'update_game_progress',
    'calculate_game_score',

    # Sentence Order Game
    'generate_ai_sentence',
    'get_scrambled_sentence',
    'evaluate_order',
    'get_feedback',
    'save_result',
    'get_all_results'
]
