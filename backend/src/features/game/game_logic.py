"""
XplorED - Game Logic Module

This module provides core game logic and sentence generation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Game Logic Components:
- Level Management: Get and manage user game levels
- Sentence Generation: Generate sentences for games
- Game Rounds: Create and manage game rounds
- Answer Evaluation: Evaluate game answers and provide feedback

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import random
from typing import Dict, Any, Optional
import datetime

from core.database.connection import fetch_one
from features.game.sentence_order import generate_ai_sentence, LEVELS
from features.ai.memory.vocabulary_memory import save_vocab, extract_words

logger = logging.getLogger(__name__)


def get_user_game_level(username: str, requested_level: Optional[int] = None) -> int:
    """
    Get the appropriate game level for a user.

    Args:
        username: The username
        requested_level: Optional specific level request

    Returns:
        The game level to use

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if requested_level is not None:
            return int(requested_level)

        # Get user's skill level from database
        row = fetch_one("users", "WHERE username = ?", (username,))
        level = row.get("skill_level", 0) if row else 0

        logger.info(f"Using game level {level} for user {username}")
        return int(level)

    except ValueError as e:
        logger.error(f"Validation error getting game level: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting game level for user {username}: {e}")
        return 0


def generate_game_sentence(username: str, level: int) -> str:
    """
    Generate a sentence for the game at the specified level.

    Args:
        username: The username
        level: The game level

    Returns:
        The sentence to use for the game

    Raises:
        ValueError: If username or level is invalid
    """
    try:
        if not username or level is None:
            raise ValueError("Username and level are required")

        level = int(level)

        # Try to generate AI sentence first
        sentence = generate_ai_sentence(username)

        if not sentence:
            # Fallback to predefined levels
            sentence = LEVELS[level % len(LEVELS)]
            logger.info(f"Using fallback sentence for level {level}")
        else:
            logger.info(f"Generated AI sentence for user {username} at level {level}")

        return sentence

    except ValueError as e:
        logger.error(f"Validation error generating game sentence: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating game sentence for user {username}: {e}")
        return LEVELS[level % len(LEVELS)] if level is not None else LEVELS[0]


def create_game_round(username: str, level: Optional[int] = None) -> Dict[str, Any]:
    """
    Create a new game round for a user.

    Args:
        username: The username
        level: Optional specific level for the round

    Returns:
        Dictionary containing game round data

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        # Get appropriate level
        game_level = get_user_game_level(username, level)

        # Generate sentence for the round
        sentence = generate_game_sentence(username, game_level)

        # Create round data
        round_data = {
            "username": username,
            "level": game_level,
            "sentence": sentence,
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active"
        }

        # Save vocabulary from sentence
        _save_game_vocabulary(username, sentence, game_level)

        logger.info(f"Created game round for user {username} at level {game_level}")
        return round_data

    except ValueError as e:
        logger.error(f"Validation error creating game round: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating game round for user {username}: {e}")
        return {
            "username": username,
            "level": 0,
            "sentence": LEVELS[0],
            "error": str(e)
        }


def evaluate_game_answer(username: str, level: int, sentence: str, user_answer: str) -> Dict[str, Any]:
    """
    Evaluate a game answer and provide feedback.

    Args:
        username: The username
        level: The game level
        sentence: The correct sentence
        user_answer: The user's answer

    Returns:
        Dictionary containing evaluation results

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not username or not sentence or not user_answer:
            raise ValueError("Username, sentence, and user_answer are required")

        # Normalize answers for comparison
        correct_sentence = sentence.strip().lower()
        user_sentence = user_answer.strip().lower()

        # Check if answer is correct
        is_correct = correct_sentence == user_sentence

        # Generate feedback
        if is_correct:
            feedback = "Excellent! Your answer is correct."
        else:
            feedback = f"Not quite right. The correct answer is: {sentence}"

        # Create evaluation result
        result = {
            "username": username,
            "level": level,
            "correct_sentence": sentence,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "feedback": feedback,
            "evaluated_at": datetime.datetime.now().isoformat()
        }

        logger.info(f"Evaluated game answer for user {username}: {'correct' if is_correct else 'incorrect'}")
        return result

    except ValueError as e:
        logger.error(f"Validation error evaluating game answer: {e}")
        raise
    except Exception as e:
        logger.error(f"Error evaluating game answer for user {username}: {e}")
        return {
            "username": username,
            "level": level,
            "error": str(e),
            "is_correct": False
        }


def _save_game_vocabulary(username: str, sentence: str, level: int) -> None:
    """
    Save vocabulary from game sentence to user's vocabulary.

    Args:
        username: The username
        sentence: The sentence to extract vocabulary from
        level: The game level
    """
    try:
        # Extract words from sentence
        words = extract_words(sentence)

        # Save each word to vocabulary
        for word, article in words:
            if word and len(word) > 2:  # Only save meaningful words
                save_vocab(
                    username=username,
                    german_word=word,
                    context=f"Game level {level}",
                    exercise="sentence_order_game",
                    article=article
                )

        logger.debug(f"Saved vocabulary from game sentence for user {username}")

    except Exception as e:
        logger.error(f"Error saving game vocabulary for user {username}: {e}")


def _get_correct_sentence_display(sentence: str) -> Optional[str]:
    """
    Get a formatted display version of the correct sentence.

    Args:
        sentence: The sentence to format

    Returns:
        Formatted sentence or None if invalid
    """
    try:
        if not sentence:
            return None

        # Basic formatting: capitalize first letter, add period if missing
        formatted = sentence.strip()
        if formatted and not formatted[0].isupper():
            formatted = formatted[0].upper() + formatted[1:]

        if formatted and not formatted.endswith(('.', '!', '?')):
            formatted += '.'

        return formatted

    except Exception as e:
        logger.error(f"Error formatting sentence display: {e}")
        return sentence
