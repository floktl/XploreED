"""
Exercise Manager

This module contains core exercise management functions for CRUD operations
on exercises and exercise results.

Author: German Class Tool Team
Date: 2025
"""

import logging
import json
import datetime
from typing import Dict, Optional, Any, List, Tuple

from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query
from features.ai.exercise_helpers import check_gap_fill_correctness, parse_submission_data

logger = logging.getLogger(__name__)


def create_exercise_block(username: str, exercises: List[Dict], block_type: str = "ai_generated") -> Optional[str]:
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
        import uuid
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
        logger.error(f"Error creating exercise block for user '{username}': {e}")
        return None


def get_exercise_block(block_id: str) -> Optional[Dict[str, Any]]:
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
                block["exercises"] = json.loads(block["exercises"])
            except (json.JSONDecodeError, KeyError):
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
        logger.error(f"Error getting exercise block {block_id}: {e}")
        return None


def get_user_exercise_blocks(username: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent exercise blocks for a user.

    Args:
        username: The username to get blocks for
        limit: Maximum number of blocks to return

    Returns:
        List of exercise blocks

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting exercise blocks for user '{username}' (limit: {limit})")

        blocks = select_rows(
            "exercise_blocks",
            columns=["block_id", "block_type", "created_at", "status"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=limit
        )

        # Parse exercises for each block
        for block in blocks:
            try:
                full_block = get_exercise_block(block["block_id"])
                if full_block:
                    block["exercise_count"] = len(full_block.get("exercises", []))
                else:
                    block["exercise_count"] = 0
            except Exception:
                block["exercise_count"] = 0

        logger.info(f"Retrieved {len(blocks)} exercise blocks for user '{username}'")
        return blocks

    except ValueError as e:
        logger.error(f"Validation error getting exercise blocks: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting exercise blocks for user '{username}': {e}")
        return []


def submit_exercise_answers(username: str, block_id: str, answers: Dict[str, str]) -> bool:
    """
    Submit answers for an exercise block.

    Args:
        username: The username submitting answers
        block_id: The exercise block ID
        answers: Dictionary of exercise ID to answer mapping

    Returns:
        True if submission was successful, False otherwise

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not block_id:
            raise ValueError("Block ID is required")

        if not answers:
            raise ValueError("Answers dictionary is required")

        logger.info(f"Submitting exercise answers for user '{username}', block {block_id}")

        # Get the exercise block
        block = get_exercise_block(block_id)
        if not block:
            logger.error(f"Exercise block {block_id} not found")
            return False

        # Create submission data
        submission_data = {
            "username": username,
            "block_id": block_id,
            "answers": json.dumps(answers),
            "submitted_at": datetime.datetime.now().isoformat(),
            "status": "submitted"
        }

        # Insert submission
        success = insert_row("exercise_submissions", submission_data)

        if success:
            logger.info(f"Successfully submitted answers for block {block_id}")
        else:
            logger.error(f"Failed to submit answers for block {block_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error submitting exercise answers: {e}")
        raise
    except Exception as e:
        logger.error(f"Error submitting exercise answers for user '{username}', block {block_id}: {e}")
        return False


def get_exercise_results(username: str, block_id: str) -> Optional[Dict[str, Any]]:
    """
    Get results for an exercise block.

    Args:
        username: The username to get results for
        block_id: The exercise block ID

    Returns:
        Exercise results or None if not found

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        if not block_id:
            raise ValueError("Block ID is required")

        logger.info(f"Getting exercise results for user '{username}', block {block_id}")

        # Get submission
        submission = select_one("exercise_submissions", where="username = ? AND block_id = ?", params=(username, block_id))

        if not submission:
            logger.warning(f"No submission found for user '{username}', block {block_id}")
            return None

        # Get exercise block
        block = get_exercise_block(block_id)
        if not block:
            logger.error(f"Exercise block {block_id} not found")
            return None

        # Parse answers
        try:
            answers = json.loads(submission["answers"])
        except (json.JSONDecodeError, KeyError):
            answers = {}

        # Get results if they exist
        results = select_one("exercise_results", where="username = ? AND block_id = ?", params=(username, block_id))

        if results:
            try:
                results["evaluation"] = json.loads(results["evaluation"])
            except (json.JSONDecodeError, KeyError):
                results["evaluation"] = {}

        # Prepare response
        response = {
            "block_id": block_id,
            "username": username,
            "exercises": block["exercises"],
            "answers": answers,
            "submitted_at": submission["submitted_at"],
            "results": results,
            "status": submission["status"]
        }

        logger.info(f"Retrieved exercise results for user '{username}', block {block_id}")
        return response

    except ValueError as e:
        logger.error(f"Validation error getting exercise results: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting exercise results for user '{username}', block {block_id}: {e}")
        return None


def delete_exercise_block(username: str, block_id: str) -> bool:
    """
    Delete an exercise block and related data.

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

        # Delete related data first
        delete_rows("exercise_submissions", "WHERE block_id = ?", (block_id,))
        delete_rows("exercise_results", "WHERE block_id = ?", (block_id,))

        # Delete the block
        success = delete_rows("exercise_blocks", "WHERE username = ? AND block_id = ?", (username, block_id))

        if success:
            logger.info(f"Successfully deleted exercise block {block_id}")
        else:
            logger.error(f"Failed to delete exercise block {block_id}")

        return success

    except ValueError as e:
        logger.error(f"Validation error deleting exercise block: {e}")
        raise
    except Exception as e:
        logger.error(f"Error deleting exercise block {block_id} for user '{username}': {e}")
        return False


def update_exercise_block_status(username: str, block_id: str, status: str) -> bool:
    """
    Update the status of an exercise block.

    Args:
        username: The username who owns the block
        block_id: The exercise block ID
        status: New status (active, completed, archived, etc.)

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

        success = update_row(
            "exercise_blocks",
            {"status": status, "updated_at": datetime.datetime.now().isoformat()},
            "WHERE username = ? AND block_id = ?",
            (username, block_id)
        )

        if success:
            logger.info(f"Successfully updated exercise block {block_id} status to '{status}'")
        else:
            logger.error(f"Failed to update exercise block {block_id} status")

        return success

    except ValueError as e:
        logger.error(f"Validation error updating exercise block status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error updating exercise block {block_id} status for user '{username}': {e}")
        return False


def get_exercise_statistics(username: str) -> Dict[str, Any]:
    """
    Get exercise statistics for a user.

    Args:
        username: The username to get statistics for

    Returns:
        Dictionary containing exercise statistics

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting exercise statistics for user '{username}'")

        # Get total exercise blocks
        total_blocks = select_one("exercise_blocks", columns="COUNT(*) as count", where="username = ?", params=(username,))
        total = total_blocks.get("count", 0) if total_blocks else 0

        # Get completed blocks
        completed_blocks = select_one("exercise_blocks", columns="COUNT(*) as count", where="username = ? AND status = 'completed'", params=(username,))
        completed = completed_blocks.get("count", 0) if completed_blocks else 0

        # Get total submissions
        total_submissions = select_one("exercise_submissions", columns="COUNT(*) as count", where="username = ?", params=(username,))
        submissions = total_submissions.get("count", 0) if total_submissions else 0

        # Get average score (if results exist)
        avg_score_data = select_one("exercise_results", columns="AVG(score) as avg_score", where="username = ?", params=(username,))
        avg_score = round(avg_score_data.get("avg_score", 0), 2) if avg_score_data else 0

        # Get recent activity
        recent_blocks = select_rows(
            "exercise_blocks",
            columns=["block_type", "created_at"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=5
        )

        stats = {
            "total_exercise_blocks": total,
            "completed_blocks": completed,
            "completion_rate": round((completed / total * 100) if total > 0 else 0, 2),
            "total_submissions": submissions,
            "average_score": avg_score,
            "recent_activity": [
                {
                    "block_type": block["block_type"],
                    "created_at": block["created_at"]
                }
                for block in recent_blocks
            ]
        }

        logger.info(f"Retrieved exercise statistics for user '{username}': {total} blocks, {completed} completed")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting exercise statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting exercise statistics for user '{username}': {e}")
        return {"total_exercise_blocks": 0, "completed_blocks": 0, "completion_rate": 0, "total_submissions": 0, "average_score": 0, "recent_activity": []}
