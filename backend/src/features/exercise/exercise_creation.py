"""
XplorED - Exercise Creation Module

This module provides exercise creation and management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Creation Components:
- Exercise Block Creation: Create new exercise blocks for users
- Exercise Block Retrieval: Get exercise blocks and user exercise data
- Exercise Block Management: Update and delete exercise blocks

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
import datetime
import uuid
from typing import Optional, List

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows
from shared.exceptions import DatabaseError
from shared.types import ExerciseList, BlockResult, ExerciseBlockList

logger = logging.getLogger(__name__)


def create_exercise_block(username: str, exercises: ExerciseList, block_type: str = "ai_generated") -> Optional[str]:
    """
    Create a new exercise block for a user.

    Args:
        username: The username to create exercise block for
        exercises: List of exercise dictionaries
        block_type: Type of exercise block (ai_generated, training, etc.)

    Returns:
        Block ID if creation was successful, None otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not exercises:
            raise ValueError("Exercises list is required")

        logger.info(f"Creating exercise block for user '{username}' with {len(exercises)} exercises")

        # Generate unique block ID
        block_id = str(uuid.uuid4())

        # Create exercise block data
        block_data = {
            "username": username,
            "block_id": block_id,
            "block_type": block_type,
            "exercises": json.dumps(exercises),
            "created_at": datetime.datetime.now().isoformat(),
            "status": "active"
        }

        # Insert into database
        success = insert_row("exercise_blocks", block_data)

        if success:
            logger.info(f"Successfully created exercise block {block_id} for user '{username}'")
            return block_id
        else:
            logger.error(f"Failed to create exercise block for user '{username}'")
            return None

    except ValueError as e:
        logger.error(f"Validation error creating exercise block: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating exercise block: {e}")
        raise DatabaseError(f"Error creating exercise block: {str(e)}")


def get_exercise_block(block_id: str) -> BlockResult:
    """
    Get an exercise block by ID.

    Args:
        block_id: The exercise block ID

    Returns:
        Exercise block data or None if not found

    Raises:
        ValueError: If block_id is invalid
    """
    try:
        if not block_id:
            raise ValueError("Block ID is required")

        logger.info(f"Getting exercise block {block_id}")

        block = select_one("exercise_blocks", where="block_id = ?", params=(block_id,))

        if block:
            # Parse exercises JSON
            try:
                exercises = json.loads(block["exercises"]) if isinstance(block["exercises"], str) else block["exercises"]
                block["exercises"] = exercises
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing exercises JSON for block {block_id}: {e}")
                block["exercises"] = []

            logger.info(f"Retrieved exercise block {block_id}")
            return block
        else:
            logger.warning(f"Exercise block {block_id} not found")
            return None

    except ValueError as e:
        logger.error(f"Validation error getting exercise block: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting exercise by ID {block_id}: {e}")
        raise DatabaseError(f"Error getting exercise by ID {block_id}: {str(e)}")


def get_user_exercise_blocks(username: str, limit: int = 10) -> ExerciseBlockList:
    """
    Get exercise blocks for a specific user.

    Args:
        username: The username to get exercise blocks for
        limit: Maximum number of blocks to return

    Returns:
        List of exercise blocks for the user

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting exercise blocks for user '{username}' (limit: {limit})")

        blocks = select_rows(
            "exercise_blocks",
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=limit
        )

        # Parse exercises JSON for each block
        for block in blocks:
            try:
                exercises = json.loads(block["exercises"]) if isinstance(block["exercises"], str) else block["exercises"]
                block["exercises"] = exercises
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing exercises JSON for block {block['block_id']}: {e}")
                block["exercises"] = []

        logger.info(f"Retrieved {len(blocks)} exercise blocks for user '{username}'")
        return blocks

    except ValueError as e:
        logger.error(f"Validation error getting user exercise blocks: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting user exercise blocks: {e}")
        raise DatabaseError(f"Error getting user exercise blocks: {str(e)}")


def delete_exercise_block(username: str, block_id: str) -> bool:
    """
    Delete an exercise block.

    Args:
        username: The username who owns the block
        block_id: The exercise block ID to delete

    Returns:
        True if deletion was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not block_id:
            raise ValueError("Block ID is required")

        logger.info(f"Deleting exercise block {block_id} for user '{username}'")

        # Delete the exercise block
        success = delete_rows("exercise_blocks", "WHERE block_id = ? AND username = ?", (block_id, username))

        if success:
            logger.info(f"Successfully deleted exercise block {block_id} for user '{username}'")
            return True
        else:
            logger.warning(f"Exercise block {block_id} not found or already deleted for user '{username}'")
            return False

    except ValueError as e:
        logger.error(f"Validation error deleting exercise block: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting exercise {block_id} for user '{username}': {e}")
        raise DatabaseError(f"Error deleting exercise {block_id} for user '{username}': {str(e)}")


def update_exercise_block_status(username: str, block_id: str, status: str) -> bool:
    """
    Update the status of an exercise block.

    Args:
        username: The username who owns the block
        block_id: The exercise block ID to update
        status: The new status (active, completed, archived, etc.)

    Returns:
        True if update was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not block_id:
            raise ValueError("Block ID is required")

        if not status:
            raise ValueError("Status is required")

        logger.info(f"Updating exercise block {block_id} status to '{status}' for user '{username}'")

        # Update the exercise block status
        success = update_row(
            "exercise_blocks",
            {"status": status},
            "WHERE block_id = ? AND username = ?",
            (block_id, username)
        )

        if success:
            logger.info(f"Successfully updated exercise block {block_id} status to '{status}' for user '{username}'")
            return True
        else:
            logger.warning(f"Exercise block {block_id} not found for user '{username}'")
            return False

    except ValueError as e:
        logger.error(f"Validation error updating exercise block status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating exercise {block_id} status for user '{username}': {e}")
        raise DatabaseError(f"Error updating exercise {block_id} status for user '{username}': {str(e)}")
