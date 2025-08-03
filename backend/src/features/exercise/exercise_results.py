"""
XplorED - Exercise Results Module

This module provides exercise results and statistics functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Results Components:
- Results Retrieval: Get exercise results and evaluation status
- Statistics Analysis: Calculate exercise statistics and performance metrics
- Topic Memory Integration: Handle topic memory updates and status checks

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
import os
from typing import Optional, List
import datetime

from core.database.connection import select_one, select_rows, insert_row, update_row
from external.redis import redis_client
from shared.exceptions import DatabaseError
from shared.types import ExerciseAnswers, ExerciseList, AnalyticsData, StatisticsResult

logger = logging.getLogger(__name__)


def submit_exercise_answers(username: str, block_id: str, answers: ExerciseAnswers) -> bool:
    """
    Submit exercise answers for a specific block.

    Args:
        username: The username submitting answers
        block_id: The exercise block ID
        answers: Dictionary of exercise ID to answer mappings

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
            raise ValueError("Answers are required")

        logger.info(f"Submitting exercise answers for user '{username}' block {block_id}")

        # Store answers in database
        submission_data = {
            "username": username,
            "block_id": block_id,
            "answers": json.dumps(answers),
            "submitted_at": datetime.datetime.now().isoformat()
        }

        success = insert_row("exercise_submissions", submission_data)

        if success:
            logger.info(f"Successfully submitted exercise answers for user '{username}' block {block_id}")
            return True
        else:
            logger.error(f"Failed to submit exercise answers for user '{username}' block {block_id}")
            return False

    except ValueError as e:
        logger.error(f"Validation error submitting exercise answers: {e}")
        raise
    except Exception as e:
        logger.error(f"Error submitting exercise answers: {e}")
        raise DatabaseError(f"Error submitting exercise answers: {str(e)}")


def get_exercise_results(username: str, block_id: str) -> Optional[AnalyticsData]:
    """
    Get exercise results for a specific block.

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

        logger.info(f"Getting exercise results for user '{username}' block {block_id}")

        # First try to get results from Redis
        result_key = f"exercise_result:{username}:{block_id}"
        results = redis_client.get_json(result_key)

        if results:
            logger.info(f"Retrieved exercise results from Redis for user '{username}' block {block_id}")
            return results

        # Fallback to database
        block = select_one("exercise_blocks", where="block_id = ? AND username = ?", params=(block_id, username))

        if block and block.get("results"):
            try:
                results = json.loads(block["results"]) if isinstance(block["results"], str) else block["results"]
                logger.info(f"Retrieved exercise results from database for user '{username}' block {block_id}")
                return results
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing database results for user '{username}' block {block_id}: {e}")

        logger.warning(f"No exercise results found for user '{username}' block {block_id}")
        return None

    except ValueError as e:
        logger.error(f"Validation error getting exercise results: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting exercise results: {e}")
        raise DatabaseError(f"Error getting exercise results: {str(e)}")


def get_exercise_statistics(username: str) -> StatisticsResult:
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

        stats = {
            "username": username,
            "total_blocks": 0,
            "completed_blocks": 0,
            "total_exercises": 0,
            "correct_exercises": 0,
            "accuracy_rate": 0.0,
            "average_score": 0.0
        }

        # Get exercise blocks
        blocks = select_rows(
            "exercise_blocks",
            columns=["block_id", "status", "results"],
            where="username = ?",
            params=(username,)
        )

        stats["total_blocks"] = len(blocks)

        for block in blocks:
            if block.get("status") == "completed":
                stats["completed_blocks"] += 1

            # Parse results if available
            if block.get("results"):
                try:
                    results = json.loads(block["results"]) if isinstance(block["results"], str) else block["results"]

                    if isinstance(results, list):
                        stats["total_exercises"] += len(results)

                        for result in results:
                            if result.get("is_correct"):
                                stats["correct_exercises"] += 1

                    elif isinstance(results, dict) and results.get("exercises"):
                        exercises = results["exercises"]
                        if isinstance(exercises, list):
                            stats["total_exercises"] += len(exercises)

                            for exercise in exercises:
                                if exercise.get("is_correct"):
                                    stats["correct_exercises"] += 1

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing results for block {block['block_id']}: {e}")

        # Calculate rates
        if stats["total_exercises"] > 0:
            stats["accuracy_rate"] = round((stats["correct_exercises"] / stats["total_exercises"]) * 100, 2)
            stats["average_score"] = round(stats["correct_exercises"] / stats["total_exercises"], 2)

        logger.info(f"Retrieved exercise statistics for user '{username}': {stats['total_blocks']} blocks, {stats['accuracy_rate']}% accuracy")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting exercise statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting exercise statistics: {e}")
        raise DatabaseError(f"Error getting exercise statistics: {str(e)}")


def argue_exercise_evaluation(block_id: str, exercises: ExerciseList, answers: ExerciseAnswers,
                             exercise_block: Optional[AnalyticsData] = None) -> AnalyticsData:
    """
    Allow users to argue against exercise evaluation results.

    Args:
        block_id: The exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        exercise_block: Optional exercise block data

    Returns:
        Dictionary containing argument result
    """
    try:
        logger.info(f"Processing exercise evaluation argument for block {block_id}")

        # Create argument data
        argument_data = {
            "block_id": block_id,
            "exercises": exercises,
            "answers": answers,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Store argument in database
        success = insert_row("exercise_arguments", argument_data)

        if success:
            logger.info(f"Successfully stored exercise argument for block {block_id}")
            return {
                "status": "success",
                "message": "Your argument has been submitted for review",
                "argument_id": block_id
            }
        else:
            logger.error(f"Failed to store exercise argument for block {block_id}")
            return {
                "status": "error",
                "message": "Failed to submit argument"
            }

    except Exception as e:
        logger.error(f"Error arguing exercise evaluation: {e}")
        raise DatabaseError(f"Error arguing exercise evaluation: {str(e)}")


def get_topic_memory_status(username: str, block_id: str) -> StatisticsResult:
    """
    Get topic memory status for a user and exercise block.

    Args:
        username: The username
        block_id: The exercise block ID

    Returns:
        Dictionary containing topic memory status
    """
    try:
        logger.info(f"Getting topic memory status for user '{username}' block {block_id}")

        # Get topic memory data
        topic_data = select_rows(
            "topic_memory",
            columns=["topic", "level", "next_review", "strength"],
            where="username = ?",
            params=(username,)
        )

        # Get exercise block to extract topics
        block = select_one("exercise_blocks", where="block_id = ?", params=(block_id,))

        topics_in_block = []
        if block and block.get("exercises"):
            try:
                exercises = json.loads(block["exercises"]) if isinstance(block["exercises"], str) else block["exercises"]

                for exercise in exercises:
                    if isinstance(exercise, dict) and exercise.get("topic"):
                        topics_in_block.append(exercise["topic"])

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing exercises for topic extraction: {e}")

        # Create status response
        status = {
            "username": username,
            "block_id": block_id,
            "total_topics": len(topic_data),
            "topics_in_block": list(set(topics_in_block)),
            "topic_details": []
        }

        for topic in topic_data:
            status["topic_details"].append({
                "topic": topic["topic"],
                "level": topic["level"],
                "strength": topic["strength"],
                "next_review": topic["next_review"],
                "in_current_block": topic["topic"] in topics_in_block
            })

        logger.info(f"Retrieved topic memory status for user '{username}' block {block_id}: {len(topic_data)} topics")
        return status

    except Exception as e:
        logger.error(f"Error getting topic memory status: {e}")
        raise DatabaseError(f"Error getting topic memory status: {str(e)}")
