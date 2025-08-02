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
