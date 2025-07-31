"""
XplorED - AI Debug Module

This module provides AI-related debugging functions for development and troubleshooting,
following clean architecture principles as outlined in the documentation.

AI Debug Components:
- AI User Data: Debug AI user data and exercise information
- Evaluation Status: Check AI evaluation results and Redis cache status
- AI Performance: Analyze AI response times and accuracy

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
import os
import redis
from typing import Dict, Any

from core.database.connection import select_one
from features.ai.generation.helpers import print_ai_user_data_titles

logger = logging.getLogger(__name__)


def debug_user_ai_data(username: str) -> Dict[str, Any]:
    """
    Debug AI user data for a specific user.

    Args:
        username: The username to debug

    Returns:
        Dictionary containing debug information

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Debugging AI user data for user {username}")

        # Print AI user data titles
        print_ai_user_data_titles(username)

        # Get user's AI data
        row = select_one(
            "ai_user_data",
            columns="exercises, next_exercises",
            where="username = ?",
            params=(username,)
        )

        block_ids = []
        debug_info = {
            "username": username,
            "block_ids": [],
            "evaluation_status": {}
        }

        if row:
            # Extract block IDs from exercises
            if row.get("exercises"):
                try:
                    block = json.loads(row["exercises"]) if isinstance(row["exercises"], str) else row["exercises"]
                    if isinstance(block, dict) and block.get("block_id"):
                        block_ids.append(block["block_id"])
                except Exception as e:
                    logger.error(f"Error parsing exercises for user {username}: {e}")

            # Extract block IDs from next_exercises
            if row.get("next_exercises"):
                try:
                    block = json.loads(row["next_exercises"]) if isinstance(row["next_exercises"], str) else row["next_exercises"]
                    if isinstance(block, dict) and block.get("block_id"):
                        block_ids.append(block["block_id"])
                except Exception as e:
                    logger.error(f"Error parsing next_exercises for user {username}: {e}")

        debug_info["block_ids"] = block_ids

        # Check evaluation status for each block
        for block_id in block_ids:
            status = _get_evaluation_status(username, block_id)
            debug_info["evaluation_status"][block_id] = status

        logger.info(f"Completed debugging AI user data for user {username}")
        return debug_info

    except ValueError as e:
        logger.error(f"Validation error debugging AI user data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error debugging AI user data for user {username}: {e}")
        raise


def _get_evaluation_status(username: str, block_id: str) -> Dict[str, Any]:
    """
    Get evaluation status for a specific block ID.

    Args:
        username: The username
        block_id: The block ID to check

    Returns:
        Dictionary containing evaluation status
    """
    try:
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            redis_client = redis.from_url(redis_url, decode_responses=True)
        else:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

        result_key = f"exercise_result:{username}:{block_id}"
        result_json = redis_client.get(result_key)

        if not result_json:
            return {
                "status": "not_found",
                "message": "No evaluation result found"
            }

        try:
            result_data = json.loads(result_json)
            return {
                "status": "found",
                "data": result_data
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in result: {e}"
            }

    except Exception as e:
        logger.error(f"Error getting evaluation status for block {block_id}: {e}")
        return {
            "status": "error",
            "message": f"Error fetching evaluation status: {e}"
        }
