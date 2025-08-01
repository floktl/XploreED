"""
XplorED - Vocabulary Lookup Module

This module provides vocabulary lookup and creation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Vocabulary Lookup Components:
- Word Lookup: Search for vocabulary words using multiple strategies
- AI Integration: Create new vocabulary entries using AI
- Word Normalization: Normalize words for consistent searching
- Search Strategies: Multiple search approaches for finding vocabulary

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Optional, Any, List

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query
from features.ai.memory.vocabulary_memory import normalize_word, vocab_exists, save_vocab
# Import removed - function moved to vocabulary_crud.py

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
        user: The username to create entry for
        word: The original word
        norm_word: The normalized word

    Returns:
        Dict containing new vocabulary entry or None if creation fails
    """
    try:
        logger.info(f"Creating new vocabulary entry for '{word}' using AI")

        # Check if word already exists in user's vocabulary
        if vocab_exists(user, norm_word):
            logger.info(f"Vocabulary entry already exists for '{word}'")
            return lookup_vocabulary_word(user, word)

        # Create new entry using AI
        vocab_data = save_vocab(user, word)
        if vocab_data:
            vocab_data["is_new"] = True
            logger.info(f"Successfully created new vocabulary entry for '{word}'")
            return vocab_data
        else:
            logger.error(f"Failed to create vocabulary entry for '{word}'")
            return None

    except Exception as e:
        logger.error(f"Error creating vocabulary entry for '{word}': {e}")
        return None


def search_vocabulary_with_ai(user: str, word: str) -> Optional[Dict[str, Any]]:
    """
    Search for vocabulary using AI assistance.

    Args:
        user: The username to search for
        word: The word to search

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

        logger.info(f"Searching vocabulary with AI for '{word}' for user '{user}'")

        # First try normal lookup
        result = lookup_vocabulary_word(user, word)
        if result:
            return result

        # If not found, force AI creation
        norm_word, _, _ = normalize_word(word)
        vocab_data = save_vocab(user, word)

        if vocab_data:
            vocab_data["is_new"] = True
            logger.info(f"Successfully created vocabulary entry with AI for '{word}'")
            return vocab_data
        else:
            logger.error(f"Failed to create vocabulary entry with AI for '{word}'")
            return None

    except ValueError as e:
        logger.error(f"Validation error in AI vocabulary search: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching vocabulary with AI for '{word}' for user '{user}': {e}")
        return None


def select_vocab_word_due_for_review(user: str) -> Optional[Dict[str, Any]]:
    """
    Get the next vocabulary word the user should review.

    Args:
        user: The username to get review word for

    Returns:
        Dictionary containing vocabulary word details or None if no words due for review

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Getting vocabulary word due for review for user '{user}'")

        # Training columns for review
        train_columns = ["rowid as id", "vocab", "translation", "word_type", "article"]

        # Get the next word due for review
        word = select_one(
            "vocab_log",
            columns=train_columns,
            where="username = ? AND datetime(next_review) <= datetime('now')",
            params=(user,),
            order_by="next_review ASC",
        )

        if word:
            logger.info(f"Found vocabulary word due for review for user '{user}': {word.get('vocab', 'unknown')}")
            return dict(word)
        else:
            logger.info(f"No vocabulary words due for review for user '{user}'")
            return None

    except ValueError as e:
        logger.error(f"Validation error getting vocabulary word for review: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting vocabulary word for review for user '{user}': {e}")
        return None
