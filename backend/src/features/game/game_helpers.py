"""
Game Helper Functions

This module contains helper functions for game operations that are used
by the game routes but should not be in the route files themselves.

Author: XplorED Team
Date: 2025
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple, List

from core.services.import_service import *
from core.utils.html_helpers import ansi_to_html
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection
from features.game.sentence_order import evaluate_order, get_scrambled_sentence, generate_ai_sentence, LEVELS, save_result
from features.ai.memory.vocabulary_memory import save_vocab
from features.ai.memory.vocabulary_memory import extract_words


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
    Create a new game round with sentence and scrambled version.

    Args:
        username: The username
        level: Optional specific level request

    Returns:
        Dictionary containing level, sentence, and scrambled sentence

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        # Get appropriate level
        game_level = get_user_game_level(username, level)

        # Generate sentence
        sentence = generate_game_sentence(username, game_level)

        # Create scrambled version
        scrambled = get_scrambled_sentence(sentence)

        game_data = {
            "level": game_level,
            "sentence": sentence,
            "scrambled": scrambled
        }

        logger.info(f"Created game round for user {username} at level {game_level}")
        return game_data

    except ValueError as e:
        logger.error(f"Validation error creating game round: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating game round for user {username}: {e}")
        raise


def evaluate_game_answer(username: str, level: int, sentence: str, user_answer: str) -> Dict[str, Any]:
    """
    Evaluate a user's game answer and return results.

    Args:
        username: The username
        level: The game level
        sentence: The correct sentence
        user_answer: The user's answer

    Returns:
        Dictionary containing evaluation results

    Raises:
        ValueError: If required parameters are missing
    """
    try:
        if not username or not sentence or user_answer is None:
            raise ValueError("Username, sentence, and user_answer are required")

        level = int(level)
        user_answer = user_answer.strip()

        # Evaluate the answer
        correct, feedback = evaluate_order(user_answer, sentence)

        # Save the result
        save_result(username, level, correct, user_answer)

        # Save vocabulary if correct
        if correct:
            _save_game_vocabulary(username, sentence, level)

        # Prepare response
        result = {
            "correct": correct,
            "feedback": ansi_to_html(feedback),
            "correct_sentence": _get_correct_sentence_display(sentence)
        }

        logger.info(f"Evaluated game answer for user {username}: correct={correct}")
        return result

    except ValueError as e:
        logger.error(f"Validation error evaluating game answer: {e}")
        raise
    except Exception as e:
        logger.error(f"Error evaluating game answer for user {username}: {e}")
        raise


def _save_game_vocabulary(username: str, sentence: str, level: int) -> None:
    """
    Save vocabulary words from a game sentence.

    Args:
        username: The username
        sentence: The sentence to extract words from
        level: The game level
    """
    try:
        for word, art in extract_words(sentence):
            save_vocab(
                username,
                word,
                context=sentence,
                exercise=f"game_level_{level}",
                article=art,
            )

        logger.debug(f"Saved vocabulary from game sentence for user {username}")

    except Exception as e:
        logger.error(f"Error saving game vocabulary for user {username}: {e}")


def _get_correct_sentence_display(sentence: str) -> Optional[str]:
    """
    Get the correct sentence for display based on environment.

    Args:
        sentence: The correct sentence

    Returns:
        The sentence to display or None if in production
    """
    try:
        # Only show correct sentence in non-production environments
        if os.getenv("FLASK_ENV") != "production":
            return sentence
        return None

    except Exception as e:
        logger.error(f"Error determining sentence display: {e}")
        return None


def get_game_statistics(username: str) -> Dict[str, Any]:
    """
    Get game statistics for a user.

    Args:
        username: The username

    Returns:
        Dictionary containing game statistics

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        # Get recent game results
        rows = select_rows(
            "results",
            columns="level, correct, timestamp",
            where="username = ? AND exercise_type = 'game'",
            params=(username,),
            order_by="timestamp DESC",
            limit=20
        )

        if not rows:
            return {
                "total_games": 0,
                "correct_games": 0,
                "accuracy": 0.0,
                "highest_level": 0,
                "recent_results": []
            }

        total_games = len(rows)
        correct_games = sum(1 for row in rows if row["correct"])
        accuracy = (correct_games / total_games) * 100 if total_games > 0 else 0
        highest_level = max(row["level"] for row in rows) if rows else 0

        recent_results = [
            {
                "level": row["level"],
                "correct": bool(row["correct"]),
                "timestamp": row["timestamp"]
            }
            for row in rows[:10]  # Last 10 games
        ]

        stats = {
            "total_games": total_games,
            "correct_games": correct_games,
            "accuracy": round(accuracy, 1),
            "highest_level": highest_level,
            "recent_results": recent_results
        }

        logger.info(f"Retrieved game statistics for user {username}")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting game statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting game statistics for user {username}: {e}")
        return {
            "total_games": 0,
            "correct_games": 0,
            "accuracy": 0.0,
            "highest_level": 0,
            "recent_results": []
        }


def create_game_session(session_data: Dict[str, Any]) -> str:
    """
    Create a new game session.

    Args:
        session_data: Dictionary containing session information

    Returns:
        Session ID string
    """
    import uuid
    session_id = str(uuid.uuid4())
    # TODO: Implement actual session creation logic
    logger.info(f"Created game session {session_id}")
    return session_id


def update_game_progress(session_id: str, progress_data: Dict[str, Any]) -> bool:
    """
    Update game progress for a session.

    Args:
        session_id: The session ID
        progress_data: Dictionary containing progress information

    Returns:
        True if update was successful, False otherwise
    """
    # TODO: Implement actual progress update logic
    logger.info(f"Updated progress for session {session_id}")
    return True


def calculate_game_score(session_id: str, answers: List[Dict[str, Any]],
                        time_taken: int, difficulty: str) -> Dict[str, Any]:
    """
    Calculate the final score for a game session.

    Args:
        session_id: The session ID
        answers: List of answer dictionaries
        time_taken: Time taken in seconds
        difficulty: Game difficulty level

    Returns:
        Dictionary containing score and performance metrics
    """
    # TODO: Implement actual score calculation logic
    correct_answers = sum(1 for answer in answers if answer.get("correct", False))
    total_questions = len(answers)
    score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    return {
        "session_id": session_id,
        "score": score_percentage,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "time_taken": time_taken,
        "difficulty": difficulty
    }
