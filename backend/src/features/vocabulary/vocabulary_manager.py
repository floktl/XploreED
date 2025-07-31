"""
Vocabulary Manager

This module contains core vocabulary management functions for CRUD operations
on vocabulary entries.

Author: XplorED Team
Date: 2025
"""

import logging
from typing import Dict, Optional, Any, List

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query
from features.ai.memory.vocabulary_memory import normalize_word, vocab_exists, save_vocab
from features.vocabulary.vocab_helpers import fetch_vocab_entries

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
        Dict containing vocabulary details or None if creation failed
    """
    try:
        logger.info(f"Creating new vocabulary entry for '{word}' for user '{user}'")

        # Check if word already exists
        if vocab_exists(user, norm_word):
            logger.info(f"Vocabulary word '{word}' already exists for user '{user}'")
            return lookup_vocabulary_word(user, word)

        # Create new entry using AI
        vocab_data = {
            "username": user,
            "vocab": norm_word,
            "translation": "",  # Will be filled by AI
            "word_type": "",
            "article": "",
            "details": "",
            "context": f"User looked up: {word}",
            "exercise": ""
        }

        # Save the entry
        success = save_vocab(vocab_data)
        if not success:
            logger.error(f"Failed to save vocabulary entry for '{word}'")
            return None

        # Return the created entry
        result = vocab_data.copy()
        result["is_new"] = True
        logger.info(f"Created new vocabulary entry for '{word}'")
        return result

    except Exception as e:
        logger.error(f"Error creating vocabulary entry for '{word}' for user '{user}': {e}")
        return None


def get_user_vocabulary_entries(user: str) -> List[Dict[str, Any]]:
    """
    Get all vocabulary entries for a user.

    Args:
        user: The username to get vocabulary for

    Returns:
        List of vocabulary entries

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Getting vocabulary entries for user '{user}'")

        # Get vocabulary entries due for review
        vocab_entries = fetch_vocab_entries(user)

        logger.info(f"Retrieved {len(vocab_entries)} vocabulary entries for user '{user}'")
        return vocab_entries

    except ValueError as e:
        logger.error(f"Validation error getting vocabulary entries: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting vocabulary entries for user '{user}': {e}")
        return []


def delete_user_vocabulary(user: str) -> bool:
    """
    Delete all vocabulary entries for a user.

    Args:
        user: The username to delete vocabulary for

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Deleting all vocabulary entries for user '{user}'")

        success = delete_rows("vocab_log", "WHERE username = ?", (user,))

        if success:
            logger.info(f"Successfully deleted all vocabulary entries for user '{user}'")
        else:
            logger.error(f"Failed to delete vocabulary entries for user '{user}'")

        return success

    except ValueError as e:
        logger.error(f"Validation error deleting vocabulary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting vocabulary for user '{user}': {e}")
        return False


def delete_specific_vocabulary(user: str, vocab_id: int) -> bool:
    """
    Delete a specific vocabulary entry.

    Args:
        user: The username
        vocab_id: The vocabulary entry ID to delete

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        if not vocab_id or vocab_id <= 0:
            raise ValueError("Valid vocabulary ID is required")

        logger.info(f"Deleting vocabulary entry {vocab_id} for user '{user}'")

        success = delete_rows("vocab_log", "WHERE username = ? AND rowid = ?", (user, vocab_id))

        if success:
            logger.info(f"Successfully deleted vocabulary entry {vocab_id} for user '{user}'")
        else:
            logger.error(f"Failed to delete vocabulary entry {vocab_id} for user '{user}'")

        return success

    except ValueError as e:
        logger.error(f"Validation error deleting vocabulary entry: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting vocabulary entry {vocab_id} for user '{user}': {e}")
        return False


def search_vocabulary_with_ai(user: str, word: str) -> Optional[Dict[str, Any]]:
    """
    Search for vocabulary using AI assistance.

    Args:
        user: The username to search for
        word: The word to search for

    Returns:
        Dict containing vocabulary details or None if not found

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not user or not word:
            raise ValueError("User and word are required")

        word = word.strip()
        if not word:
            return None

        logger.info(f"Searching vocabulary with AI for '{word}' for user '{user}'")

        # Use the lookup function which includes AI creation
        result = lookup_vocabulary_word(user, word)

        if result:
            logger.info(f"Found vocabulary entry for '{word}' via AI search")
        else:
            logger.warning(f"No vocabulary entry found for '{word}' via AI search")

        return result

    except ValueError as e:
        logger.error(f"Validation error in AI vocabulary search: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching vocabulary with AI for '{word}' for user '{user}': {e}")
        return None


def update_vocabulary_entry(user: str, vocab_id: int, updates: Dict[str, Any]) -> bool:
    """
    Update a vocabulary entry.

    Args:
        user: The username
        vocab_id: The vocabulary entry ID to update
        updates: Dictionary of fields to update

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        if not vocab_id or vocab_id <= 0:
            raise ValueError("Valid vocabulary ID is required")

        if not updates:
            raise ValueError("Updates dictionary is required")

        logger.info(f"Updating vocabulary entry {vocab_id} for user '{user}'")

        # Remove any invalid fields
        valid_fields = ['translation', 'article', 'word_type', 'details', 'context', 'exercise']
        filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not filtered_updates:
            logger.warning(f"No valid fields to update for vocabulary entry {vocab_id}")
            return False

        success = update_row("vocab_log", filtered_updates, "WHERE username = ? AND rowid = ?", (user, vocab_id))

        if success:
            logger.info(f"Successfully updated vocabulary entry {vocab_id} for user '{user}'")
        else:
            logger.error(f"Failed to update vocabulary entry {vocab_id} for user '{user}'")

        return success

    except ValueError as e:
        logger.error(f"Validation error updating vocabulary entry: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating vocabulary entry {vocab_id} for user '{user}': {e}")
        return False


def get_vocabulary_statistics(user: str) -> Dict[str, Any]:
    """
    Get vocabulary statistics for a user.

    Args:
        user: The username to get statistics for

    Returns:
        Dictionary containing vocabulary statistics

    Raises:
        ValueError: If user is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Getting vocabulary statistics for user '{user}'")

        # Get total vocabulary count
        total_count = select_one("vocab_log", columns="COUNT(*) as count", where="username = ?", params=(user,))
        total = total_count.get("count", 0) if total_count else 0

        # Get vocabulary due for review
        due_count = select_one("vocab_log", columns="COUNT(*) as count", where="username = ? AND next_review <= datetime('now')", params=(user,))
        due = due_count.get("count", 0) if due_count else 0

        # Get vocabulary by word type
        word_types = fetch_custom("""
            SELECT word_type, COUNT(*) as count
            FROM vocab_log
            WHERE username = ? AND word_type IS NOT NULL AND word_type != ''
            GROUP BY word_type
        """, (user,))

        # Get vocabulary by article
        articles = fetch_custom("""
            SELECT article, COUNT(*) as count
            FROM vocab_log
            WHERE username = ? AND article IS NOT NULL AND article != ''
            GROUP BY article
        """, (user,))

        stats = {
            "total_vocabulary": total,
            "due_for_review": due,
            "word_types": {row["word_type"]: row["count"] for row in word_types},
            "articles": {row["article"]: row["count"] for row in articles}
        }

        logger.info(f"Retrieved vocabulary statistics for user '{user}': {total} total, {due} due for review")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting vocabulary statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting vocabulary statistics for user '{user}': {e}")
        return {"total_vocabulary": 0, "due_for_review": 0, "word_types": {}, "articles": {}}
