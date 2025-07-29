"""
Vocabulary Helper Functions

This module contains helper functions for vocabulary operations that are used
by the user routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Optional, Any

from core.services.import_service import *
from features.ai.memory.vocabulary_memory import normalize_word, vocab_exists, save_vocab
from features.ai.generation.user_helpers import fetch_vocab_entries


logger = logging.getLogger(__name__)


def lookup_vocabulary_word(user: str, word: str) -> Optional[Dict[str, Any]]:
    """
    Lookup a vocabulary word for a user and return details if found.

    This function searches for a word in the user's vocabulary using multiple
    search strategies and creates a new entry using AI if not found.

    Args:
        user: The username to search for
        word: The word to lookup

    Returns:
        Dict containing vocabulary details or None if not found

    Raises:
        ValueError: If user or word is invalid
    """
    try:
        if not user or not word:
            raise ValueError("User and word are required")

        word = word.strip()
        if not word:
            return None

        logger.info(f"Looking up vocabulary word '{word}' for user '{user}'")

        # Normalize the word
        norm_word, _, _ = normalize_word(word)

        # Search strategies in order of preference
        search_strategies = [
            # Strategy 1: LIKE search on normalized word
            {
                'query': f"SELECT vocab, translation, article, word_type, details, created_at, next_review, context, exercise FROM vocab_log WHERE username = ? AND LOWER(vocab) LIKE ?",
                'params': (user, f"%{norm_word.lower()}%")
            },
            # Strategy 2: Exact match on normalized word
            {
                'query': "SELECT vocab, translation, article, word_type, details, created_at, next_review, context, exercise FROM vocab_log WHERE username = ? AND LOWER(vocab) = ?",
                'params': (user, norm_word.lower())
            },
            # Strategy 3: Exact match on original word
            {
                'query': "SELECT vocab, translation, article, word_type, details, created_at, next_review, context, exercise FROM vocab_log WHERE username = ? AND vocab = ?",
                'params': (user, norm_word)
            },
            # Strategy 4: LIKE search on translation
            {
                'query': "SELECT vocab, translation, article, word_type, details, created_at, next_review, context, exercise FROM vocab_log WHERE username = ? AND LOWER(translation) LIKE ?",
                'params': (user, f"%{word.lower()}%")
            }
        ]

        # Try each search strategy
        for strategy in search_strategies:
            rows = fetch_custom(strategy['query'], strategy['params'])
            if rows:
                row = rows[0]
                result = dict(row)
                result["is_new"] = False
                logger.info(f"Found existing vocabulary entry for '{word}'")
                return result

        # If not found, create new entry using AI
        return _create_vocabulary_entry(user, word, norm_word)

    except ValueError as e:
        logger.error(f"Validation error in vocabulary lookup: {e}")
        raise
    except Exception as e:
        logger.error(f"Error looking up vocabulary word '{word}' for user '{user}': {e}")
        return None


def _create_vocabulary_entry(user: str, word: str, norm_word: str) -> Optional[Dict[str, Any]]:
    """
    Create a new vocabulary entry using AI.

    Args:
        user: The username
        word: The original word
        norm_word: The normalized word

    Returns:
        Dict containing the new vocabulary entry or None if creation failed
    """
    try:
        logger.info(f"Creating new vocabulary entry for '{word}' using AI")

        # Check if word already exists before creating
        original_exists = vocab_exists(user, word)

        # Save the word using AI
        saved_word = save_vocab(user, word, context="AI lookup", exercise="ai")

        if not saved_word:
            logger.error(f"Failed to save vocabulary word '{word}' using AI")
            return None

        # Fetch the newly created entry
        row = fetch_one(
            "vocab_log",
            where_clause="username = ? AND LOWER(vocab) = ?",
            params=(user, saved_word.lower()),
            columns="vocab, translation, article, word_type, details, created_at, next_review, context, exercise",
        )

        if row:
            result = dict(row)
            # Mark as new if it didn't exist before and the saved word is different
            result["is_new"] = not original_exists and saved_word != word
            logger.info(f"Successfully created new vocabulary entry for '{word}'")
            return result
        else:
            logger.error(f"Failed to fetch newly created vocabulary entry for '{word}'")
            return None

    except Exception as e:
        logger.error(f"Error creating vocabulary entry for '{word}': {e}")
        return None


def search_vocabulary_with_ai(user: str, word: str) -> Optional[Dict[str, Any]]:
    """
    Search for a vocabulary word using AI and save it to the user's vocabulary.

    Args:
        user: The username
        word: The word to search for

    Returns:
        Dict containing vocabulary details or None if search failed

    Raises:
        ValueError: If user or word is invalid
    """
    try:
        if not user or not word:
            raise ValueError("User and word are required")

        word = word.strip()
        if not word:
            return None

        logger.info(f"Searching AI for vocabulary word '{word}' for user '{user}'")

        # Check if word already exists
        if vocab_exists(user, word):
            logger.info(f"Word '{word}' already exists, fetching existing entry")
            row = fetch_one(
                "vocab_log",
                where_clause="username = ? AND vocab = ?",
                params=(user, word),
                columns="vocab, translation, article, word_type, details, created_at, next_review, context, exercise",
            )
            if row:
                return dict(row)

        # Use AI to analyze and save the word
        saved_word = save_vocab(user, word, context="AI search", exercise="ai")

        if not saved_word:
            logger.error(f"Failed to save word '{word}' using AI")
            return None

        # Fetch the newly saved entry
        row = fetch_one(
            "vocab_log",
            where_clause="username = ? AND vocab = ?",
            params=(user, saved_word),
            columns="vocab, translation, article, word_type, details, created_at, next_review, context, exercise",
        )

        if row:
            logger.info(f"Successfully created vocabulary entry for '{word}' using AI")
            return dict(row)
        else:
            logger.error(f"Failed to fetch newly saved vocabulary entry for '{word}'")
            return None

    except ValueError as e:
        logger.error(f"Validation error in AI vocabulary search: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching vocabulary with AI for '{word}': {e}")
        return None


def get_user_vocabulary_entries(user: str) -> list:
    """
    Get all vocabulary entries for a user.

    Args:
        user: The username

    Returns:
        List of vocabulary entries

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Fetching vocabulary entries for user '{user}'")

        entries = fetch_vocab_entries(user)
        return entries or []

    except ValueError as e:
        logger.error(f"Validation error fetching vocabulary entries: {e}")
        raise
    except Exception as e:
        logger.error(f"Error fetching vocabulary entries for user '{user}': {e}")
        return []


def delete_user_vocabulary(user: str) -> bool:
    """
    Delete all vocabulary entries for a user.

    Args:
        user: The username

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Deleting all vocabulary entries for user '{user}'")

        delete_rows("vocab_log", "WHERE username = ?", (user,))
        return True

    except ValueError as e:
        logger.error(f"Validation error deleting vocabulary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting vocabulary for user '{user}': {e}")
        return False


def delete_specific_vocabulary(user: str, vocab_id: int) -> bool:
    """
    Delete a specific vocabulary entry for a user.

    Args:
        user: The username
        vocab_id: The vocabulary entry ID

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If user or vocab_id is invalid
    """
    try:
        if not user or not vocab_id:
            raise ValueError("User and vocab_id are required")

        logger.info(f"Deleting vocabulary entry {vocab_id} for user '{user}'")

        delete_rows("vocab_log", "WHERE username = ? AND id = ?", (user, vocab_id))
        return True

    except ValueError as e:
        logger.error(f"Validation error deleting vocabulary entry: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting vocabulary entry {vocab_id} for user '{user}': {e}")
        return False
