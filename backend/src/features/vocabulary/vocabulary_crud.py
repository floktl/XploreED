"""
XplorED - Vocabulary CRUD Module

This module provides vocabulary CRUD (Create, Read, Update, Delete) operations for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Vocabulary CRUD Components:
- Vocabulary Retrieval: Get user vocabulary entries and statistics
- Vocabulary Updates: Update vocabulary entries and details
- Vocabulary Deletion: Delete vocabulary entries and user data
- Data Management: Manage vocabulary data integrity

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Optional, Any, List

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query
from core.services import VocabularyService
# Vocabulary helper constants
VOCAB_COLUMNS = [
    "rowid as id",
    "vocab",
    "translation",
    "word_type",
    "article",
    "details",
    "next_review",
    "last_review",
    "context",
    "exercise",
]

logger = logging.getLogger(__name__)


def get_user_vocabulary_entries(
    user: str,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get vocabulary entries for a user with filtering and pagination.

    Args:
        user: The username to get vocabulary for
        limit: Maximum number of entries to return
        offset: Number of entries to skip for pagination
        status: Filter by status (learning, reviewing, mastered)
        search: Search term for filtering words

    Returns:
        Dictionary containing vocabulary entries and metadata

    Raises:
        ValueError: If user is invalid
    """
    try:
        # Get all vocabulary entries first
        all_entries = VocabularyService.get_user_vocabulary_entries(user)

        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            all_entries = [
                entry for entry in all_entries
                if search_lower in entry.get('vocab', '').lower()
                or search_lower in entry.get('translation', '').lower()
            ]

        # Apply status filter if provided
        if status:
            # Simple status filtering based on review count and next_review
            if status == 'learning':
                all_entries = [entry for entry in all_entries if entry.get('repetitions', 0) < 3]
            elif status == 'reviewing':
                all_entries = [entry for entry in all_entries if 3 <= entry.get('repetitions', 0) < 10]
            elif status == 'mastered':
                all_entries = [entry for entry in all_entries if entry.get('repetitions', 0) >= 10]

        # Calculate total before pagination
        total = len(all_entries)

        # Apply pagination
        paginated_entries = all_entries[offset:offset + limit]

        # Calculate statistics
        total_words = len(all_entries)
        learning_words = len([e for e in all_entries if e.get('repetitions', 0) < 3])
        reviewing_words = len([e for e in all_entries if 3 <= e.get('repetitions', 0) < 10])
        mastered_words = len([e for e in all_entries if e.get('repetitions', 0) >= 10])

        # Calculate average mastery (simplified)
        if total_words > 0:
            avg_mastery = sum(min(e.get('repetitions', 0) / 10.0, 1.0) for e in all_entries) / total_words
        else:
            avg_mastery = 0.0

        # Count words due for review (simplified)
        words_due_review = len([e for e in all_entries if e.get('next_review')])

        return {
            "vocabulary": paginated_entries,
            "statistics": {
                "total_words": total_words,
                "learning_words": learning_words,
                "reviewing_words": reviewing_words,
                "mastered_words": mastered_words,
                "average_mastery": round(avg_mastery, 2),
                "words_due_review": words_due_review
            },
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error getting vocabulary entries for user {user}: {e}")
        return {
            "vocabulary": [],
            "statistics": {
                "total_words": 0,
                "learning_words": 0,
                "reviewing_words": 0,
                "mastered_words": 0,
                "average_mastery": 0.0,
                "words_due_review": 0
            },
            "total": 0,
            "limit": limit,
            "offset": offset
        }


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

        # Get count before deletion
        count_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ?", params=(user,))
        initial_count = count_result.get("count", 0) if count_result else 0

        # Delete all vocabulary entries
        success = delete_rows("vocab_log", "WHERE username = ?", (user,))

        if success:
            logger.info(f"Successfully deleted {initial_count} vocabulary entries for user '{user}'")
            return True
        else:
            logger.error(f"Failed to delete vocabulary entries for user '{user}'")
            return False

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
        user: The username to delete vocabulary for
        vocab_id: The ID of the vocabulary entry to delete

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        ValueError: If user or vocab_id is invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        if not vocab_id or vocab_id <= 0:
            raise ValueError("Valid vocab_id is required")

        logger.info(f"Deleting vocabulary entry {vocab_id} for user '{user}'")

        # Verify the vocabulary entry exists and belongs to the user
        existing = select_one("vocab_log", where="id = ? AND username = ?", params=(vocab_id, user))
        if not existing:
            logger.warning(f"Vocabulary entry {vocab_id} not found for user '{user}'")
            return False

        # Delete the specific vocabulary entry
        success = delete_rows("vocab_log", "WHERE id = ? AND username = ?", (vocab_id, user))

        if success:
            logger.info(f"Successfully deleted vocabulary entry {vocab_id} for user '{user}'")
            return True
        else:
            logger.error(f"Failed to delete vocabulary entry {vocab_id} for user '{user}'")
            return False

    except ValueError as e:
        logger.error(f"Validation error deleting specific vocabulary: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting vocabulary entry {vocab_id} for user '{user}': {e}")
        return False


def update_vocabulary_entry(user: str, vocab_id: int, updates: Dict[str, Any]) -> bool:
    """
    Update a vocabulary entry for a user.

    Args:
        user: The username to update vocabulary for
        vocab_id: The ID of the vocabulary entry to update
        updates: Dictionary containing fields to update

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    try:
        if not user:
            raise ValueError("User is required")

        if not vocab_id or vocab_id <= 0:
            raise ValueError("Valid vocab_id is required")

        if not updates or not isinstance(updates, dict):
            raise ValueError("Updates dictionary is required")

        logger.info(f"Updating vocabulary entry {vocab_id} for user '{user}'")

        # Verify the vocabulary entry exists and belongs to the user
        existing = select_one("vocab_log", where="id = ? AND username = ?", params=(vocab_id, user))
        if not existing:
            logger.warning(f"Vocabulary entry {vocab_id} not found for user '{user}'")
            return False

        # Filter out invalid fields
        valid_fields = {
            "vocab", "translation", "article", "word_type", "details",
            "context", "exercise", "next_review", "repetitions"
        }

        filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not filtered_updates:
            logger.warning(f"No valid fields to update for vocabulary entry {vocab_id}")
            return False

        # Update the vocabulary entry
        success = update_row("vocab_log", filtered_updates, "id = ? AND username = ?", (vocab_id, user))

        if success:
            logger.info(f"Successfully updated vocabulary entry {vocab_id} for user '{user}'")
            return True
        else:
            logger.error(f"Failed to update vocabulary entry {vocab_id} for user '{user}'")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating vocabulary: {e}")
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
    return VocabularyService.get_vocabulary_statistics(user)


def update_vocab_after_review(rowid: int, user: str, quality: int) -> bool:
    """
    Update spaced repetition values after a vocabulary review.

    Args:
        rowid: The ID of the vocabulary entry to update
        user: The username
        quality: The quality rating (0-5) for the review

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If required parameters are invalid
    """
    return VocabularyService.update_vocab_after_review(rowid, user, quality)
