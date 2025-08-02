"""
XplorED - Vocabulary Service

This module provides core vocabulary business logic services,
following clean architecture principles as outlined in the documentation.

Vocabulary Service Components:
- Vocabulary lookup and search
- Vocabulary CRUD operations
- Vocabulary analytics and statistics
- Learning progress tracking

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple
from core.database.connection import select_one, select_rows, fetch_custom, insert_row, update_row, delete_rows
from core.authentication import user_exists
from shared.text_utils import _extract_json as extract_json
from external.mistral.client import send_prompt
from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


class VocabularyService:
    """Core vocabulary business logic service."""

    # Vocabulary columns for consistent queries
    VOCAB_COLUMNS = "vocab, translation, article, word_type, details, created_at, next_review, context, exercise, repetitions, quality, last_review"

    @staticmethod
    def lookup_vocabulary_word(user: str, word: str) -> Optional[Dict[str, Any]]:
        """
        Lookup a vocabulary word for a user and return details if found.

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
                raise ValidationError("User and word are required")

            if not user_exists(user):
                raise ValidationError(f"User {user} does not exist")

            word = word.strip()
            if not word:
                return None

            logger.info(f"Looking up vocabulary word '{word}' for user '{user}'")

            # Normalize the word
            norm_word = VocabularyService._normalize_word(word)

            # Search strategies in order of preference
            search_strategies = [
                # Strategy 1: LIKE search on normalized word
                {
                    'query': f"SELECT {VocabularyService.VOCAB_COLUMNS} FROM vocab_log WHERE username = ? AND LOWER(vocab) LIKE ?",
                    'params': (user, f"%{norm_word.lower()}%")
                },
                # Strategy 2: Exact match on normalized word
                {
                    'query': f"SELECT {VocabularyService.VOCAB_COLUMNS} FROM vocab_log WHERE username = ? AND LOWER(vocab) = ?",
                    'params': (user, norm_word.lower())
                },
                # Strategy 3: Exact match on original word
                {
                    'query': f"SELECT {VocabularyService.VOCAB_COLUMNS} FROM vocab_log WHERE username = ? AND vocab = ?",
                    'params': (user, norm_word)
                },
                # Strategy 4: LIKE search on translation
                {
                    'query': f"SELECT {VocabularyService.VOCAB_COLUMNS} FROM vocab_log WHERE username = ? AND LOWER(translation) LIKE ?",
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
            return VocabularyService._create_vocabulary_entry(user, word, norm_word)

        except ValueError as e:
            logger.error(f"Validation error in vocabulary lookup: {e}")
            raise
        except Exception as e:
            logger.error(f"Error looking up vocabulary word '{word}' for user '{user}': {e}")
            return None

    @staticmethod
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
                raise ValidationError("User is required")

            if not user_exists(user):
                raise ValidationError(f"User {user} does not exist")

            logger.info(f"Getting vocabulary entries for user '{user}'")

            # Get vocabulary entries
            rows = select_rows(
                "vocab_log",
                columns=VocabularyService.VOCAB_COLUMNS,
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

        except ValidationError as e:
            logger.error(f"Validation error getting vocabulary entries: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting vocabulary entries for user '{user}': {e}")
            return []

    @staticmethod
    def get_vocabulary_statistics(user: str) -> Dict[str, Any]:
        """
        Get comprehensive vocabulary statistics for a user.

        Args:
            user: The username to get statistics for

        Returns:
            Dictionary containing vocabulary statistics

        Raises:
            ValueError: If user is invalid
        """
        try:
            if not user:
                raise ValidationError("User is required")

            if not user_exists(user):
                raise ValidationError(f"User {user} does not exist")

            logger.info(f"Getting vocabulary statistics for user '{user}'")

            # Get total vocabulary count
            total_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ?", params=(user,))
            total_vocabulary = total_result.get("count", 0) if total_result else 0

            # Get mastered vocabulary (repetitions > 0)
            mastered_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ? AND repetitions > 0", params=(user,))
            mastered_count = mastered_result.get("count", 0) if mastered_result else 0

            # Get due for review
            due_result = select_one("vocab_log", columns="COUNT(*) as count", where="username = ? AND datetime(next_review) <= datetime('now')", params=(user,))
            due_for_review = due_result.get("count", 0) if due_result else 0

            # Get average quality score
            quality_result = select_one("vocab_log", columns="AVG(quality) as avg_quality", where="username = ? AND quality IS NOT NULL", params=(user,))
            average_quality = quality_result.get("avg_quality", 0.0) if quality_result else 0.0

            # Calculate retention rate
            retention_rate = (mastered_count / total_vocabulary * 100) if total_vocabulary > 0 else 0.0

            statistics = {
                "total_vocabulary": total_vocabulary,
                "mastered_count": mastered_count,
                "due_for_review": due_for_review,
                "average_quality": round(average_quality, 2),
                "retention_rate": round(retention_rate, 2),
                "learning_progress": round((mastered_count / total_vocabulary * 100) if total_vocabulary > 0 else 0, 2)
            }

            logger.info(f"Retrieved vocabulary statistics for user '{user}': {total_vocabulary} total, {mastered_count} mastered")
            return statistics

        except ValidationError as e:
            logger.error(f"Validation error getting vocabulary statistics: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting vocabulary statistics for user '{user}': {e}")
            return {
                "total_vocabulary": 0,
                "mastered_count": 0,
                "due_for_review": 0,
                "average_quality": 0.0,
                "retention_rate": 0.0,
                "learning_progress": 0.0
            }

    @staticmethod
    def get_vocabulary_learning_progress(user: str, days: int = 30) -> Dict[str, Any]:
        """
        Get vocabulary learning progress over time.

        Args:
            user: The username to get progress for
            days: Number of days to look back

        Returns:
            Dictionary containing learning progress data

        Raises:
            ValueError: If user is invalid
        """
        try:
            if not user:
                raise ValueError("User is required")

            if not user_exists(user):
                raise ValueError(f"User {user} does not exist")

            if days <= 0:
                days = 30

            logger.info(f"Getting vocabulary learning progress for user '{user}' over {days} days")

            # Get vocabulary added per day
            daily_additions = fetch_custom("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as new_words
                FROM vocab_log
                WHERE username = ?
                    AND created_at >= date('now', '-{} days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """.format(days), (user,))

            # Get vocabulary reviewed per day
            daily_reviews = fetch_custom("""
                SELECT
                    DATE(last_review) as date,
                    COUNT(*) as reviews
                FROM vocab_log
                WHERE username = ?
                    AND repetitions > 0
                    AND last_review >= date('now', '-{} days')
                GROUP BY DATE(last_review)
                ORDER BY date
            """.format(days), (user,))

            # Get statistics
            stats = VocabularyService.get_vocabulary_statistics(user)

            progress = {
                "total_vocabulary": stats["total_vocabulary"],
                "retention_rate": stats["retention_rate"],
                "daily_additions": {row["date"]: row["new_words"] for row in daily_additions},
                "daily_reviews": {row["date"]: row["reviews"] for row in daily_reviews},
                "period_days": days
            }

            logger.info(f"Retrieved vocabulary progress for user '{user}': {stats['total_vocabulary']} total words, {stats['retention_rate']:.1f}% retention")
            return progress

        except ValueError as e:
            logger.error(f"Validation error getting vocabulary progress: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting vocabulary progress for user '{user}': {e}")
            return {"total_vocabulary": 0, "retention_rate": 0, "daily_additions": {}, "daily_reviews": {}, "period_days": days}

    @staticmethod
    def select_vocab_word_due_for_review(user: str) -> Optional[Dict[str, Any]]:
        """
        Select a vocabulary word due for review.

        Args:
            user: The username to get word for

        Returns:
            Dictionary containing vocabulary word or None if none due

        Raises:
            ValueError: If user is invalid
        """
        try:
            if not user:
                raise ValueError("User is required")

            if not user_exists(user):
                raise ValueError(f"User {user} does not exist")

            logger.info(f"Selecting vocabulary word due for review for user '{user}'")

            # Get word due for review
            row = select_one(
                "vocab_log",
                columns=VocabularyService.VOCAB_COLUMNS,
                where="username = ? AND datetime(next_review) <= datetime('now')",
                params=(user,),
                order_by="datetime(next_review) ASC"
            )

            if row:
                result = dict(row)
                logger.info(f"Selected vocabulary word '{result.get('vocab')}' for review")
                return result
            else:
                logger.info(f"No vocabulary words due for review for user '{user}'")
                return None

        except ValueError as e:
            logger.error(f"Validation error selecting vocabulary word: {e}")
            raise
        except Exception as e:
            logger.error(f"Error selecting vocabulary word for user '{user}': {e}")
            return None

    @staticmethod
    def update_vocab_after_review(vocab_id: int, user: str, quality: int) -> bool:
        """
        Update vocabulary after review using SM2 algorithm.

        Args:
            vocab_id: The vocabulary ID to update
            user: The username
            quality: Quality score (0-5)

        Returns:
            True if update was successful

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not vocab_id or not user or quality is None:
                raise ValueError("Vocab ID, user, and quality are required")

            if not user_exists(user):
                raise ValueError(f"User {user} does not exist")

            if not 0 <= quality <= 5:
                raise ValueError("Quality must be between 0 and 5")

            logger.info(f"Updating vocabulary {vocab_id} for user '{user}' with quality {quality}")

            # Get current vocabulary data
            vocab_data = select_one("vocab_log", columns="*", where="rowid = ? AND username = ?", params=(vocab_id, user))
            if not vocab_data:
                logger.error(f"Vocabulary {vocab_id} not found for user '{user}'")
                return False

            # Apply SM2 algorithm
            repetitions = vocab_data.get("repetitions", 0)
            quality_score = vocab_data.get("quality", 0)
            next_review = vocab_data.get("next_review")

            # Calculate new values
            new_repetitions, new_quality, new_next_review = VocabularyService._apply_sm2_algorithm(
                repetitions, quality_score, quality, next_review
            )

            # Update vocabulary
            update_data = {
                "repetitions": new_repetitions,
                "quality": new_quality,
                "next_review": new_next_review,
                "last_review": datetime.datetime.now().isoformat()
            }

            success = update_row("vocab_log", update_data, "WHERE rowid = ? AND username = ?", (vocab_id, user))

            if success:
                logger.info(f"Successfully updated vocabulary {vocab_id} for user '{user}'")
            else:
                logger.error(f"Failed to update vocabulary {vocab_id} for user '{user}'")

            return success

        except ValueError as e:
            logger.error(f"Validation error updating vocabulary: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating vocabulary {vocab_id} for user '{user}': {e}")
            return False

    @staticmethod
    def _normalize_word(word: str) -> str:
        """Normalize a word for searching."""
        try:
            return word.strip().lower()
        except Exception as e:
            logger.error(f"Error normalizing word: {e}")
            return word.strip() if word else ""

    @staticmethod
    def _create_vocabulary_entry(user: str, word: str, norm_word: str) -> Optional[Dict[str, Any]]:
        """Create a new vocabulary entry using AI."""
        try:
            # TODO: Implement AI vocabulary creation
            # For now, return None to indicate word not found
            logger.debug(f"Would create AI vocabulary entry for word '{word}'")
            return None
        except Exception as e:
            logger.error(f"Error creating vocabulary entry: {e}")
            return None

    @staticmethod
    def _apply_sm2_algorithm(repetitions: int, quality: int, new_quality: int, next_review: str) -> Tuple[int, int, str]:
        """Apply SuperMemo 2 algorithm to calculate new values."""
        try:
            # SM2 algorithm implementation
            if new_quality < 3:
                # Failed - reset repetitions
                new_repetitions = 0
                new_quality = new_quality
                # Next review in 1 day
                next_review_date = datetime.datetime.now() + datetime.timedelta(days=1)
            else:
                # Passed - increment repetitions
                new_repetitions = repetitions + 1
                new_quality = new_quality

                # Calculate interval based on repetitions
                if new_repetitions == 1:
                    interval = 1  # 1 day
                elif new_repetitions == 2:
                    interval = 6  # 6 days
                else:
                    # Use SM2 formula: interval = interval * EF
                    # For simplicity, use a basic progression
                    interval = 6 * (2 ** (new_repetitions - 2))

                next_review_date = datetime.datetime.now() + datetime.timedelta(days=interval)

            return new_repetitions, new_quality, next_review_date.isoformat()

        except Exception as e:
            logger.error(f"Error applying SM2 algorithm: {e}")
            # Fallback to basic values
            return repetitions, new_quality, (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
