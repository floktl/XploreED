"""
Debug Helper Functions

This module contains helper functions for debug operations that are used
by the debug routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
import json
import os
import redis
from typing import Dict, Any, List, Optional

from core.services.import_service import *
from features.ai.generation.helpers import print_ai_user_data_titles
from core.database.connection import get_connection, select_one, select_rows


logger = logging.getLogger(__name__)


def get_all_database_data() -> Dict[str, Any]:
    """
    Retrieve all data from all database tables for debugging purposes.

    Returns:
        Dictionary containing all table data with columns and rows

    Raises:
        Exception: If database operations fail
    """
    try:
        db_path = os.getenv("DB_FILE", "database/user_data.db")
        logger.info(f"Retrieving all database data from {db_path}")

        with get_connection() as conn:
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            result = {}

            for table in tables:
                try:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]

                    # Get all rows
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()

                    result[table] = {
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows)
                    }

                    logger.debug(f"Retrieved {len(rows)} rows from table {table}")

                except Exception as e:
                    logger.error(f"Error retrieving data from table {table}: {e}")
                    result[table] = {
                        "columns": [],
                        "rows": [],
                        "row_count": 0,
                        "error": str(e)
                    }

        logger.info(f"Successfully retrieved data from {len(result)} tables")
        return result

    except Exception as e:
        logger.error(f"Error retrieving database data: {e}")
        raise


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


def get_database_schema() -> Dict[str, Any]:
    """
    Get database schema information for debugging.

    Returns:
        Dictionary containing schema information for all tables
    """
    try:
        logger.info("Retrieving database schema information")

        with get_connection() as conn:
            cursor = conn.cursor()

            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            schema_info = {}

            for table in tables:
                try:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = []

                    for col in cursor.fetchall():
                        columns.append({
                            "name": col[1],
                            "type": col[2],
                            "not_null": bool(col[3]),
                            "default_value": col[4],
                            "primary_key": bool(col[5])
                        })

                    # Get table size
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]

                    schema_info[table] = {
                        "columns": columns,
                        "row_count": row_count
                    }

                except Exception as e:
                    logger.error(f"Error getting schema for table {table}: {e}")
                    schema_info[table] = {
                        "columns": [],
                        "row_count": 0,
                        "error": str(e)
                    }

        logger.info(f"Retrieved schema for {len(schema_info)} tables")
        return schema_info

    except Exception as e:
        logger.error(f"Error retrieving database schema: {e}")
        return {"error": str(e)}


def get_user_statistics(username: str) -> Dict[str, Any]:
    """
    Get comprehensive user statistics for debugging.

    Args:
        username: The username to get statistics for

    Returns:
        Dictionary containing user statistics

    Raises:
        ValueError: If username is invalid
    """
    try:
        if not username:
            raise ValueError("Username is required")

        logger.info(f"Getting statistics for user {username}")

        stats = {
            "username": username,
            "vocabulary": {},
            "results": {},
            "ai_data": {},
            "topic_memory": {}
        }

        # Vocabulary statistics
        vocab_count = select_rows(
            "vocab_log",
            columns=["COUNT(*) as count"],
            where="username = ?",
            params=(username,)
        )
        stats["vocabulary"]["total_words"] = vocab_count[0]["count"] if vocab_count else 0

        # Results statistics
        results_count = select_rows(
            "results",
            columns=["COUNT(*) as count, AVG(correct) as avg_correct"],
            where="username = ?",
            params=(username,)
        )
        if results_count:
            stats["results"]["total_exercises"] = results_count[0]["count"]
            stats["results"]["average_correct"] = float(results_count[0]["avg_correct"] or 0)
        else:
            stats["results"]["total_exercises"] = 0
            stats["results"]["average_correct"] = 0.0

        # AI data statistics
        ai_data = select_one(
            "ai_user_data",
            columns="exercises, next_exercises",
            where="username = ?",
            params=(username,)
        )
        stats["ai_data"]["has_exercises"] = bool(ai_data and ai_data.get("exercises"))
        stats["ai_data"]["has_next_exercises"] = bool(ai_data and ai_data.get("next_exercises"))

        # Topic memory statistics
        topic_count = select_rows(
            "topic_memory",
            columns=["COUNT(*) as count"],
            where="username = ?",
            params=(username,)
        )
        stats["topic_memory"]["total_topics"] = topic_count[0]["count"] if topic_count else 0

        logger.info(f"Retrieved statistics for user {username}")
        return stats

    except ValueError as e:
        logger.error(f"Validation error getting user statistics: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for user {username}: {e}")
        raise
