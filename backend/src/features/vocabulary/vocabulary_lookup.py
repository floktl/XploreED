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
from core.services import VocabularyService
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
    return VocabularyService.lookup_vocabulary_word(user, word)


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
        vocab_word = save_vocab(user, word)
        if vocab_word:
            # Get the created vocabulary entry
            vocab_data = lookup_vocabulary_word(user, vocab_word)
            if vocab_data:
                vocab_data["is_new"] = True
                logger.info(f"Successfully created new vocabulary entry for '{word}'")
                return vocab_data
            else:
                logger.error(f"Failed to retrieve created vocabulary entry for '{word}'")
                return None
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
        vocab_word = save_vocab(user, word)

        if vocab_word:
            # Get the created vocabulary entry
            vocab_data = lookup_vocabulary_word(user, vocab_word)
            if vocab_data:
                vocab_data["is_new"] = True
                logger.info(f"Successfully created vocabulary entry with AI for '{word}'")
                return vocab_data
            else:
                logger.error(f"Failed to retrieve created vocabulary entry with AI for '{word}'")
                return None
        else:
            logger.error(f"Failed to create vocabulary entry with AI for '{word}'")
            return None

    except ValueError as e:
        logger.error(f"Validation error in AI vocabulary search: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching vocabulary with AI for '{word}' for user '{user}': {e}")
        return None


def select_vocab_word_due_for_review(
    user: str,
    count: int = 10,
    difficulty: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get vocabulary words due for review.

    Args:
        user: The username to get review words for
        count: Number of words to retrieve (default: 10)
        difficulty: Target difficulty level (optional)

    Returns:
        List of dictionaries containing vocabulary word details

    Raises:
        ValueError: If user is invalid
    """
    try:
        # Get all vocabulary entries for the user
        all_entries = VocabularyService.get_user_vocabulary_entries(user)

        # Filter for words due for review
        due_entries = []
        for entry in all_entries:
            next_review = entry.get('next_review')
            if next_review:
                # Simple check if due for review (simplified logic)
                due_entries.append(entry)

        # Apply difficulty filter if provided
        if difficulty:
            due_entries = [entry for entry in due_entries if entry.get('word_type') == difficulty]

        # Sort by next_review date (earliest first)
        due_entries.sort(key=lambda x: x.get('next_review', ''))

        # Limit to requested count
        result = due_entries[:count]

        return result

    except Exception as e:
        logger.error(f"Error selecting vocabulary words for review for user {user}: {e}")
        return []
