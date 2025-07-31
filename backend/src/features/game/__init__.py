"""
XplorED - Game Package

This package provides game functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Game Modules:
- game_management: Game session and progress management
- game_logic: Core game logic and sentence generation
- game_statistics: Game statistics and analysis
- sentence_order: Sentence ordering game functionality

For detailed architecture information, see: docs/backend_structure.md
"""

from .game_management import (
    create_game_session,
    update_game_progress,
    calculate_game_score,
)

from .game_logic import (
    get_user_game_level,
    generate_game_sentence,
    create_game_round,
    evaluate_game_answer,
)

from .game_statistics import (
    get_game_statistics,
    get_user_game_level_progress,
    get_game_achievements,
)

from .sentence_order import (
    generate_ai_sentence,
    get_scrambled_sentence,
    evaluate_order,
    get_feedback,
    save_result,
    get_all_results,
)

# Re-export all game functions for backward compatibility
__all__ = [
    # Game management
    "create_game_session",
    "update_game_progress",
    "calculate_game_score",

    # Game logic
    "get_user_game_level",
    "generate_game_sentence",
    "create_game_round",
    "evaluate_game_answer",

    # Game statistics
    "get_game_statistics",
    "get_user_game_level_progress",
    "get_game_achievements",

    # Sentence order game
    "generate_ai_sentence",
    "get_scrambled_sentence",
    "evaluate_order",
    "get_feedback",
    "save_result",
    "get_all_results",
]
