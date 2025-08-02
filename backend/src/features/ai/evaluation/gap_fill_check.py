"""
XplorED - Exercise Evaluation Helpers Module

This module provides helper functions for exercise evaluation in the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Helpers Components:
- Text Processing: Normalize and process text for comparison
- Gap Fill Validation: Check gap-fill exercise correctness
- Answer Validation: Validate exercise answers and responses
- Utility Functions: Helper functions for exercise evaluation

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

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
