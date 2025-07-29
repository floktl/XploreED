"""
Debug Routes

This module contains API routes for debugging and development purposes.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
import datetime
import redis # type: ignore
from typing import Dict, Any

from core.services.import_service import *
from features.debug.debug_helpers import (
    get_all_database_data,
    debug_user_ai_data,
    get_database_schema,
    get_user_statistics
)


logger = logging.getLogger(__name__)


@debug_bp.route("/all-data", methods=["GET"])
def show_all_data():
    """
    Dump all database tables and rows for debugging.

    This endpoint retrieves all data from all database tables and returns
    it in a structured format for debugging purposes.

    Returns:
        JSON response with all database data or error details
    """
    try:
        logger.info("Request to dump all database data")

        data = get_all_database_data()
        return jsonify(data)

    except Exception as e:
        logger.error(f"Error dumping database data: {e}")
        return jsonify({"error": str(e)}), 500


@debug_bp.route("/ai-user-titles", methods=["POST"])
def debug_ai_user_titles():
    """
    Debug AI user data for the current user.

    This endpoint triggers debugging of AI user data including exercise
    blocks and evaluation status.

    Returns:
        JSON response with debug information or error details
    """
    try:
        username = require_user()

        logger.info(f"Debugging AI user data for user {username}")

        debug_info = debug_user_ai_data(str(username))
        return jsonify(debug_info)

    except ValueError as e:
        logger.error(f"Validation error debugging AI user data: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error debugging AI user data: {e}")
        return jsonify({"error": str(e)}), 500


@debug_bp.route("/schema", methods=["GET"])
def show_database_schema():
    """
    Get database schema information for debugging.

    This endpoint retrieves schema information for all database tables
    including column definitions and row counts.

    Returns:
        JSON response with database schema or error details
    """
    try:
        logger.info("Request to get database schema")

        schema = get_database_schema()
        return jsonify(schema)

    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        return jsonify({"error": str(e)}), 500


@debug_bp.route("/user-stats", methods=["GET"])
def show_user_statistics():
    """
    Get comprehensive user statistics for debugging.

    This endpoint retrieves detailed statistics about the current user's
    data including vocabulary, results, AI data, and topic memory.

    Returns:
        JSON response with user statistics or error details
    """
    try:
        username = require_user()

        logger.info(f"Getting statistics for user {username}")

        stats = get_user_statistics(str(username))
        return jsonify(stats)

    except ValueError as e:
        logger.error(f"Validation error getting user statistics: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        return jsonify({"error": str(e)}), 500


@debug_bp.route("/health", methods=["GET"])
def health_check():
    """
    Basic health check endpoint for debugging.

    This endpoint provides basic system health information including
    database connectivity and Redis status.

    Returns:
        JSON response with health status
    """
    try:
        logger.info("Health check request")

        health_status = {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Test database connection
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"

        # Test Redis connection
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

            redis_client.ping()
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }), 500
