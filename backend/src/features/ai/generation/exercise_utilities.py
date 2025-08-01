"""
XplorED - Exercise Utilities Module

This module provides utility functions for exercise generation and processing in the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Utilities Components:
- Text Processing: Normalize and process text for exercises
- Gap Fill Validation: Check gap-fill exercise correctness
- Exercise Formatting: Format and structure exercise data
- Debug Utilities: Debug and logging utilities for exercises

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _normalize_umlauts(text: str) -> str:
    """
    Normalize German umlauts for comparison.

    Args:
        text: Text to normalize

    Returns:
        Text with normalized umlauts
    """
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss'
    }
    for umlaut, replacement in umlaut_map.items():
        text = text.replace(umlaut, replacement)
    return text


def _strip_final_punct(text: str) -> str:
    """
    Strip final punctuation from text.

    Args:
        text: Text to process

    Returns:
        Text with final punctuation removed
    """
    return text.rstrip(".,!?;:")


def check_gap_fill_correctness(exercise: dict, user_answer: str, correct_answer: str) -> bool:
    """
    Check if a gap-fill answer is correct based on grammatical context.

    Args:
        exercise: The exercise dictionary containing question and type
        user_answer: The user's submitted answer
        correct_answer: The correct answer for comparison

    Returns:
        True if the answer is correct, False otherwise
    """
    try:
        # Get the question text to understand the context
        question = exercise.get("question", "").lower()
        user_ans = user_answer.lower().strip()
        correct_ans = correct_answer.lower().strip()

        logger.debug(f"Checking gap-fill: question='{question}', user='{user_ans}', correct='{correct_ans}'")

        # First try exact match
        if user_ans == correct_ans:
            logger.debug("Exact match found")
            return True

        # Check for common German grammar patterns
        # Pattern 1: Personal pronouns with verb conjugation
        if "habe" in question or "habe " in question:
            # "____ habe einen Hund" - should be "Ich" (1st person singular)
            if user_ans in ["ich", "i"] and correct_ans in ["ich", "i"]:
                logger.debug("Correct 1st person singular with 'habe'")
                return True
            elif user_ans in ["du", "d"] and correct_ans in ["ich", "i"]:
                logger.debug("Wrong: 'du' with 'habe' should be 'ich'")
                return False

        if "bist" in question or "bist " in question:
            # "____ bist glücklich" - should be "Du" (2nd person singular)
            if user_ans in ["du", "d"] and correct_ans in ["du", "d"]:
                logger.debug("Correct 2nd person singular with 'bist'")
                return True
            elif user_ans in ["ich", "i"] and correct_ans in ["du", "d"]:
                logger.debug("Wrong: 'ich' with 'bist' should be 'du'")
                return False

        if "ist" in question or "ist " in question:
            # "____ ist ein Student" - could be "Er", "Sie", "Es" (3rd person singular)
            if user_ans in ["er", "sie", "es"] and correct_ans in ["er", "sie", "es"]:
                logger.debug("Correct 3rd person singular with 'ist'")
                return True

        if "sind" in question or "sind " in question:
            # "____ sind Studenten" - should be "Sie" (3rd person plural) or "Wir" (1st person plural)
            if user_ans in ["sie", "wir"] and correct_ans in ["sie", "wir"]:
                logger.debug("Correct plural with 'sind'")
                return True

        # Pattern 2: Articles with nouns
        if any(article in question for article in ["der", "die", "das", "den", "dem", "des"]):
            # Check if user provided the correct article
            if user_ans in ["der", "die", "das", "den", "dem", "des"]:
                if user_ans == correct_ans:
                    logger.debug("Correct article provided")
                    return True

        # Pattern 3: Prepositions
        prepositions = ["in", "auf", "unter", "über", "neben", "zwischen", "hinter", "vor"]
        if any(prep in question for prep in prepositions):
            if user_ans in prepositions and user_ans == correct_ans:
                logger.debug("Correct preposition provided")
                return True

        # Pattern 4: Verb forms
        if any(verb in question for verb in ["gehe", "gehst", "geht", "gehen"]):
            if user_ans in ["gehe", "gehst", "geht", "gehen"] and user_ans == correct_ans:
                logger.debug("Correct verb form provided")
                return True

        # Pattern 5: Adjective endings
        if any(ending in question for ending in ["e", "er", "es", "en", "em"]):
            if user_ans in ["e", "er", "es", "en", "em"] and user_ans == correct_ans:
                logger.debug("Correct adjective ending provided")
                return True

        # If no specific pattern matches, check for close similarity
        # Normalize umlauts for comparison
        user_normalized = _normalize_umlauts(user_ans)
        correct_normalized = _normalize_umlauts(correct_ans)

        if user_normalized == correct_normalized:
            logger.debug("Normalized match found")
            return True

        # Check for common abbreviations or variations
        if user_ans in ["d", "du"] and correct_ans in ["du", "d"]:
            logger.debug("Correct abbreviation for 'du'")
            return True
        if user_ans in ["i", "ich"] and correct_ans in ["ich", "i"]:
            logger.debug("Correct abbreviation for 'ich'")
            return True

        logger.debug("No match found, answer is incorrect")
        return False

    except Exception as e:
        logger.error(f"Error checking gap-fill correctness: {e}")
        return False


def format_exercise_block(block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format an exercise block for consistent structure.

    Args:
        block: The exercise block to format

    Returns:
        Formatted exercise block
    """
    try:
        if not block or not isinstance(block, dict):
            return block

        # Ensure required fields
        formatted_block = {
            "id": block.get("id", ""),
            "title": block.get("title", "Exercise Block"),
            "topic": block.get("topic", "general"),
            "level": block.get("level", "A1"),
            "exercises": []
        }

        # Format exercises
        exercises = block.get("exercises", [])
        for i, exercise in enumerate(exercises):
            if isinstance(exercise, dict):
                formatted_exercise = {
                    "id": exercise.get("id", f"ex{i+1}"),
                    "type": exercise.get("type", "gap-fill"),
                    "question": exercise.get("question", ""),
                    "correctAnswer": exercise.get("correctAnswer", ""),
                    "explanation": exercise.get("explanation", ""),
                    "options": exercise.get("options", [])
                }
                formatted_block["exercises"].append(formatted_exercise)

        logger.debug(f"Formatted exercise block with {len(formatted_block['exercises'])} exercises")
        return formatted_block

    except Exception as e:
        logger.error(f"Error formatting exercise block: {e}")
        return block


def validate_exercise_data(exercise_data: Dict[str, Any]) -> bool:
    """
    Validate exercise data structure.

    Args:
        exercise_data: Exercise data to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        if not exercise_data or not isinstance(exercise_data, dict):
            logger.warning("Exercise data is not a valid dictionary")
            return False

        # Check required fields
        required_fields = ["title", "exercises"]
        for field in required_fields:
            if field not in exercise_data:
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate exercises
        exercises = exercise_data.get("exercises", [])
        if not isinstance(exercises, list):
            logger.warning("Exercises field is not a list")
            return False

        for i, exercise in enumerate(exercises):
            if not isinstance(exercise, dict):
                logger.warning(f"Exercise {i} is not a dictionary")
                return False

            # Check exercise required fields
            exercise_required = ["type", "question", "correctAnswer"]
            for field in exercise_required:
                if field not in exercise:
                    logger.warning(f"Exercise {i} missing required field: {field}")
                    return False

        logger.debug(f"Exercise data validation passed for {len(exercises)} exercises")
        return True

    except Exception as e:
        logger.error(f"Error validating exercise data: {e}")
        return False


def sanitize_exercise_text(text: str) -> str:
    """
    Sanitize exercise text for safe display.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    try:
        if not text:
            return ""

        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&']
        sanitized = text

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."

        logger.debug(f"Sanitized exercise text (length: {len(sanitized)})")
        return sanitized

    except Exception as e:
        logger.error(f"Error sanitizing exercise text: {e}")
        return text or ""


def extract_exercise_keywords(text: str) -> list:
    """
    Extract keywords from exercise text.

    Args:
        text: Text to extract keywords from

    Returns:
        List of keywords
    """
    try:
        if not text:
            return []

        # Simple keyword extraction
        words = text.lower().split()

        # Filter out common words
        common_words = {
            'der', 'die', 'das', 'den', 'dem', 'des',
            'ein', 'eine', 'einen', 'einem', 'eines',
            'und', 'oder', 'aber', 'dass', 'wenn',
            'ist', 'sind', 'war', 'waren', 'habe', 'hat',
            'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr'
        }

        keywords = [word for word in words if word not in common_words and len(word) > 2]

        # Remove duplicates and limit
        unique_keywords = list(set(keywords))[:10]

        logger.debug(f"Extracted {len(unique_keywords)} keywords from exercise text")
        return unique_keywords

    except Exception as e:
        logger.error(f"Error extracting exercise keywords: {e}")
        return []


def calculate_exercise_difficulty(exercise: Dict[str, Any]) -> str:
    """
    Calculate the difficulty level of an exercise.

    Args:
        exercise: Exercise to analyze

    Returns:
        Difficulty level (easy, medium, hard)
    """
    try:
        if not exercise or not isinstance(exercise, dict):
            return "medium"

        question = exercise.get("question", "")
        exercise_type = exercise.get("type", "gap-fill")

        # Simple difficulty calculation based on text length and type
        text_length = len(question)

        if exercise_type == "gap-fill":
            if text_length < 50:
                return "easy"
            elif text_length < 100:
                return "medium"
            else:
                return "hard"
        else:
            # For other exercise types
            if text_length < 30:
                return "easy"
            elif text_length < 80:
                return "medium"
            else:
                return "hard"

    except Exception as e:
        logger.error(f"Error calculating exercise difficulty: {e}")
        return "medium"
