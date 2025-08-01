"""
XplorED - Topic Memory Module

This module provides topic memory update functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Topic Memory Components:
- Topic Memory Updates: Update topic memory based on evaluation results
- Memory Integration: Integrate topic memory with evaluation systems
- Spaced Repetition: Apply spaced repetition to topic memory
- Memory Analytics: Track and analyze topic memory performance

For detailed architecture information, see: docs/backend_structure.md
"""

import datetime
from typing import Dict, Optional

from core.database.connection import insert_row, update_row, select_one
from features.ai.memory.level_manager import check_auto_level_up
from features.spaced_repetition import sm2
from features.ai.memory.logger import topic_memory_logger

import logging
logger = logging.getLogger(__name__)


def _update_single_topic(username: str, grammar: str, skill: str, context: str, quality: int, topic: Optional[str] = None) -> None:
    """
    Update a single topic in the topic memory system.

    Args:
        username: The user's username
        grammar: The grammar topic to update
        skill: The skill type
        context: The context of the update
        quality: The quality score (0-5)
        topic: Optional topic category
    """
    try:
        logger.debug(f"Updating topic memory for user {username}, grammar: {grammar}, quality: {quality}")

        # Check if topic already exists for this user
        existing = select_one(
            "topic_memory",
            columns="*",
            where="username = ? AND grammar = ?",
            params=(username, grammar)
        )

        now = datetime.datetime.now().isoformat()

        if existing:
            # Update existing topic
            old_ef = existing.get("ease_factor", 2.5)
            old_reps = existing.get("repetitions", 0)
            old_interval = existing.get("intervall", 1)

            # Apply SM2 algorithm
            new_ef, new_reps, new_interval = sm2(quality, old_ef, old_reps, old_interval)

            # Calculate next review date
            next_review = (datetime.datetime.now() + datetime.timedelta(days=new_interval)).isoformat()

            # Update the topic
            update_row(
                "topic_memory",
                {
                    "ease_factor": new_ef,
                    "repetitions": new_reps,
                    "intervall": new_interval,
                    "next_repeat": next_review,
                    "last_review": now,
                    "correct": existing.get("correct", 0) + (1 if quality >= 3 else 0),
                    "quality": quality
                },
                "username = ? AND grammar = ?",
                (username, grammar)
            )

            # Log the update
            topic_memory_logger.log_topic_update(
                username=username,
                grammar=grammar,
                skill=skill,
                quality=quality,
                is_new=False,
                old_values={
                    "ease_factor": old_ef,
                    "repetitions": old_reps,
                    "intervall": old_interval
                },
                new_values={
                    "ease_factor": new_ef,
                    "repetitions": new_reps,
                    "intervall": new_interval,
                    "topic": topic or "general"
                },
                row_id=existing.get("id")
            )

            logger.debug(f"Updated existing topic: {grammar} - EF: {old_ef:.2f}->{new_ef:.2f}, Reps: {old_reps}->{new_reps}")

        else:
            # Create new topic entry
            new_ef, new_reps, new_interval = sm2(quality, 2.5, 0, 1)
            next_review = (datetime.datetime.now() + datetime.timedelta(days=new_interval)).isoformat()

            insert_row(
                "topic_memory",
                {
                    "username": username,
                    "grammar": grammar,
                    "skill_type": skill,
                    "context": context,
                    "lesson_content_id": None,
                    "ease_factor": new_ef,
                    "intervall": new_interval,
                    "next_repeat": next_review,
                    "repetitions": new_reps,
                    "last_review": now,
                    "correct": 1 if quality >= 3 else 0,
                    "quality": quality
                }
            )

            # Log the new entry
            topic_memory_logger.log_topic_update(
                username=username,
                grammar=grammar,
                skill=skill,
                quality=quality,
                is_new=True,
                new_values={
                    "ease_factor": new_ef,
                    "repetitions": new_reps,
                    "intervall": new_interval,
                    "topic": topic or "general",
                    "context": context
                }
            )

            logger.debug(f"Created new topic: {grammar} - EF: {new_ef:.2f}, Reps: {new_reps}")

    except Exception as e:
        logger.error(f"Error updating topic memory for user {username}, grammar {grammar}: {e}")


def update_topic_memory_translation(username: str, german: str, qualities: Optional[Dict[str, int]] = None) -> None:
    """
    Update topic memory based on translation results.

    Args:
        username: The user's username
        german: The German text that was translated
        qualities: Optional dictionary of topic quality scores
    """
    try:
        logger.debug(f"Updating topic memory for translation: user={username}, text='{german[:50]}...'")

        if qualities:
            # Update each topic with its quality score
            for topic, quality in qualities.items():
                if topic != "unknown":
                    _update_single_topic(
                        username=username,
                        grammar=topic,
                        skill="translation",
                        context="translation-exercise",
                        quality=quality,
                        topic="translation"
                    )
        else:
            # Fallback: detect topics and give default quality
            from features.grammar import detect_language_topics
            topics = detect_language_topics(german) or []

            for topic in topics:
                if topic != "unknown":
                    _update_single_topic(
                        username=username,
                        grammar=topic,
                        skill="translation",
                        context="translation-exercise",
                        quality=3,  # Default quality
                        topic="translation"
                    )

    except Exception as e:
        logger.error(f"Error updating topic memory for translation: {e}")


def update_topic_memory_reading(username: str, text: str, qualities: Optional[Dict[str, int]] = None) -> None:
    """
    Update topic memory based on reading comprehension results.

    Args:
        username: The user's username
        text: The text that was read
        qualities: Optional dictionary of topic quality scores
    """
    try:
        logger.debug(f"Updating topic memory for reading: user={username}, text='{text[:50]}...'")

        if qualities:
            # Update each topic with its quality score
            for topic, quality in qualities.items():
                if topic != "unknown":
                    _update_single_topic(
                        username=username,
                        grammar=topic,
                        skill="reading",
                        context="reading-exercise",
                        quality=quality,
                        topic="reading"
                    )
        else:
            # Fallback: detect topics and give default quality
            from features.grammar import detect_language_topics
            topics = detect_language_topics(text) or []

            for topic in topics:
                if topic != "unknown":
                    _update_single_topic(
                        username=username,
                        grammar=topic,
                        skill="reading",
                        context="reading-exercise",
                        quality=3,  # Default quality
                        topic="reading"
                    )

    except Exception as e:
        logger.error(f"Error updating topic memory for reading: {e}")


def get_topic_memory_summary(username: str) -> Dict:
    """
    Get a summary of the user's topic memory.

    Args:
        username: The user's username

    Returns:
        Dictionary containing topic memory summary
    """
    try:
        from core.database.connection import select_rows

        # Get all topic memory entries for the user
        topics = select_rows(
            "topic_memory",
            columns=["grammar", "ease_factor", "repetitions", "quality", "correct"],
            where="username = ?",
            params=(username,)
        )

        if not topics:
            return {
                "total_topics": 0,
                "average_ease_factor": 0,
                "total_repetitions": 0,
                "strong_topics": [],
                "weak_topics": []
            }

        # Calculate statistics
        total_topics = len(topics)
        ease_factors = [t.get("ease_factor", 2.5) for t in topics]
        average_ef = sum(ease_factors) / len(ease_factors) if ease_factors else 0
        total_repetitions = sum(t.get("repetitions", 0) for t in topics)

        # Categorize topics
        strong_topics = [t["grammar"] for t in topics if t.get("ease_factor", 2.5) >= 3.0]
        weak_topics = [t["grammar"] for t in topics if t.get("ease_factor", 2.5) < 2.0]

        return {
            "total_topics": total_topics,
            "average_ease_factor": round(average_ef, 2),
            "total_repetitions": total_repetitions,
            "strong_topics": strong_topics,
            "weak_topics": weak_topics
        }

    except Exception as e:
        logger.error(f"Error getting topic memory summary for user {username}: {e}")
        return {
            "total_topics": 0,
            "average_ease_factor": 0,
            "total_repetitions": 0,
            "strong_topics": [],
            "weak_topics": []
        }
