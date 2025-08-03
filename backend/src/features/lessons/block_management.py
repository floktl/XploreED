"""
XplorED - Lesson Block Management

This module provides lesson block management business logic,
following clean architecture principles as outlined in the documentation.

Block Management Components:
- Lesson block database operations
- Block ID tracking and management
- Lesson-specific block business logic

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Set
from bs4 import BeautifulSoup  # type: ignore
from core.database.connection import get_connection
from shared.exceptions import DatabaseError
# Function moved from core.processing to avoid circular import

logger = logging.getLogger(__name__)


def extract_lesson_block_ids_from_html(html: str) -> Set[str]:
    """
    Extract all data-block-id values from HTML content.

    Args:
        html: HTML content containing data-block-id attributes

    Returns:
        Set[str]: Set of block IDs found in the HTML
    """
    soup = BeautifulSoup(html, "html.parser")
    block_ids: Set[str] = set()

    # Extract all data-block-id values
    for block in soup.select('[data-block-id]'):
        block_id = block.get("data-block-id")
        if block_id:
            block_ids.add(str(block_id))

    return block_ids


def update_lesson_blocks_from_html(lesson_id: int, html: str) -> None:
    """
    Store all data-block-id values for lesson_id in the database.

    This function parses HTML content to extract block IDs and updates
    the lesson_blocks table to maintain the relationship between
    lessons and their interactive blocks.

    Args:
        lesson_id: ID of the lesson to update blocks for
        html: HTML content containing data-block-id attributes
    """
    try:
        block_ids = extract_lesson_block_ids_from_html(html)

        # Update database with block IDs
        with get_connection() as conn:
            cursor = conn.cursor()

            # Remove existing blocks for this lesson
            cursor.execute("DELETE FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,))

            # Insert new block IDs
            for block_id in block_ids:
                cursor.execute(
                    "INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id) VALUES (?, ?)",
                    (lesson_id, block_id)
                )

            conn.commit()

        logger.info(f"Updated {len(block_ids)} blocks for lesson {lesson_id}")

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error updating lesson blocks from HTML: {e}")
        raise DatabaseError(f"Error updating lesson blocks from HTML: {str(e)}")


def get_lesson_block_ids(lesson_id: int) -> Set[str]:
    """
    Get all block IDs associated with a lesson.

    Args:
        lesson_id: ID of the lesson to get blocks for

    Returns:
        Set[str]: Set of block IDs for the lesson
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT block_id FROM lesson_blocks WHERE lesson_id = ?",
                (lesson_id,)
            )
            results = cursor.fetchall()
            return {row[0] for row in results}
    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson block IDs: {e}")
        raise DatabaseError(f"Error getting lesson block IDs: {str(e)}")


def delete_lesson_blocks(lesson_id: int) -> None:
    """
    Delete all blocks associated with a lesson.

    Args:
        lesson_id: ID of the lesson to delete blocks for
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,))
            conn.commit()

        logger.info(f"Deleted all blocks for lesson {lesson_id}")

    except DatabaseError:
        raise
    except Exception as e:
        logger.error(f"Error deleting lesson blocks: {e}")
        raise DatabaseError(f"Error deleting lesson blocks: {str(e)}")


__all__ = [
    "extract_block_ids_from_html",
    "update_lesson_blocks_from_html",
    "get_lesson_block_ids",
    "delete_lesson_blocks",
]
