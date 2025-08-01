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

        # Get vocabulary entries
        rows = select_rows(
            "vocab_log",
            columns=VOCAB_COLUMNS,
            where="username = ?",
            params=(user,),
            order_by="datetime(next_review) ASC",
        )
        entries = [dict(row) for row in rows] if rows else []

        if entries:
            logger.info(f"Retrieved {len(entries)} vocabulary entries for user '{user}'")
        else:
            logger.info(f"No vocabulary entries found for user '{user}'")

        return entries

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
    try:
        if not user:
            raise ValueError("User is required")

        logger.info(f"Getting vocabulary statistics for user '{user}'")

        # Get total vocabulary count
        total_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ?", params=(user,))
        total_vocabulary = total_result.get("count", 0) if total_result else 0

        # Get vocabulary by word type
        word_types_result = fetch_custom("""
            SELECT word_type, COUNT(*) as count
            FROM vocab_log
            WHERE username = ?
            GROUP BY word_type
            ORDER BY count DESC
        """, (user,))

        word_type_stats = {row["word_type"]: row["count"] for row in word_types_result} if word_types_result else {}

        # Get vocabulary with repetitions (learned words)
        learned_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ? AND repetitions > 0", params=(user,))
        learned_vocabulary = learned_result.get("count", 0) if learned_result else 0

        # Get vocabulary without repetitions (new words)
        new_vocabulary = total_vocabulary - learned_vocabulary

        # Get average repetitions
        avg_repetitions_result = select_one("vocab_log", columns="AVG(repetitions) as avg_repetitions", where="username = ?", params=(user,))
        avg_repetitions = round(avg_repetitions_result.get("avg_repetitions", 0), 2) if avg_repetitions_result else 0

        # Get vocabulary due for review
        due_review_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ? AND next_review <= datetime('now')", params=(user,))
        due_for_review = due_review_result.get("count", 0) if due_review_result else 0

        statistics = {
            "total_vocabulary": total_vocabulary,
            "learned_vocabulary": learned_vocabulary,
            "new_vocabulary": new_vocabulary,
            "average_repetitions": avg_repetitions,
            "due_for_review": due_for_review,
            "word_type_distribution": word_type_stats,
            "learning_progress": round((learned_vocabulary / total_vocabulary * 100), 2) if total_vocabulary > 0 else 0
        }

        logger.info(f"Retrieved vocabulary statistics for user '{user}': {total_vocabulary} total words, {learned_vocabulary} learned")
        return statistics

    except ValueError as e:
        logger.error(f"Validation error getting vocabulary statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting vocabulary statistics for user '{user}': {e}")
        return {
            "total_vocabulary": 0,
            "learned_vocabulary": 0,
            "new_vocabulary": 0,
            "average_repetitions": 0,
            "due_for_review": 0,
            "word_type_distribution": {},
            "learning_progress": 0
        }


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
    try:
        if not rowid or rowid <= 0:
            raise ValueError("Valid rowid is required")

        if not user:
            raise ValueError("User is required")

        if quality < 0 or quality > 5:
            raise ValueError("Quality must be between 0 and 5")

        logger.info(f"Updating vocabulary review for entry {rowid} for user '{user}' with quality {quality}")

        # Get current spaced repetition values
        row = select_one(
            "vocab_log",
            columns=["ef", "repetitions", "interval_days"],
            where="rowid = ? AND username = ?",
            params=(rowid, user),
        )

        if not row:
            logger.warning(f"Vocabulary entry {rowid} not found for user '{user}'")
            return False

        # Calculate new spaced repetition values
        ef = row.get("ef", 2.5)
        reps = row.get("repetitions", 0)
        interval = row.get("interval_days", 1)

        from features.spaced_repetition import sm2
        ef, reps, interval = sm2(quality, ef, reps, interval)

        # Calculate next review date
        import datetime
        next_review = (
            datetime.datetime.now() + datetime.timedelta(days=interval)
        ).isoformat()

        # Update the vocabulary entry
        success = update_row(
            "vocab_log",
            {
                "ef": ef,
                "repetitions": reps,
                "interval_days": interval,
                "next_review": next_review,
            },
            "rowid = ? AND username = ?",
            (rowid, user),
        )

        if success:
            logger.info(f"Successfully updated vocabulary review for entry {rowid}")
            return True
        else:
            logger.error(f"Failed to update vocabulary review for entry {rowid}")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating vocabulary review: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating vocabulary review for entry {rowid}: {e}")
        return False
