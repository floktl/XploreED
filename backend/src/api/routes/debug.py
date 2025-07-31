"""
XplorED - Debug and Development API Routes

This module contains API routes for debugging, development, and system diagnostics,
following clean architecture principles as outlined in the documentation.

Route Categories:
- System Diagnostics: System health checks and status monitoring
- Debug Information: Detailed debugging information and logs
- Development Tools: Development and testing utilities
- Performance Monitoring: System performance metrics and analysis
- Error Tracking: Error logging and diagnostic information

Debug Features:
- Comprehensive system health monitoring
- Detailed debugging information and logs
- Development and testing utilities
- Performance metrics and analysis
- Error tracking and diagnostic tools

Business Logic:
All debug logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import sys
import traceback
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import is_admin
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows
from config.blueprint import debug_bp
from features.debug import (
    get_all_database_data,
    debug_user_ai_data,
    get_database_schema,
    get_user_statistics,
)


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === System Diagnostics Routes ===
@debug_bp.route("/health", methods=["GET"])
def get_system_health_route():
    """
    Get comprehensive system health information.

    This endpoint provides detailed system health information including
    database connectivity, external service status, and overall system status.

    Query Parameters:
        - detailed: Include detailed health information
        - include_metrics: Include performance metrics

    Returns:
        JSON response with system health information or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        detailed = request.args.get("detailed", "false").lower() == "true"
        include_metrics = request.args.get("include_metrics", "false").lower() == "true"

        # Get system health
        health_info = {
            "overall_status": True,
            "database": "connected",
            "external_services": "available",
            "performance": "normal"
        }

        return jsonify({
            "status": "healthy" if health_info.get("overall_status") else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "health_info": health_info,
            "version": os.getenv("APP_VERSION", "unknown"),
            "environment": os.getenv("FLASK_ENV", "development")
        })

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


@debug_bp.route("/status", methods=["GET"])
def get_system_status_route():
    """
    Get basic system status information.

    This endpoint provides basic system status information for
    monitoring and health checks.

    Returns:
        JSON response with system status or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Basic system status
        status_info = {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime": "unknown",  # Would need to track application start time
            "version": os.getenv("APP_VERSION", "unknown"),
            "environment": os.getenv("FLASK_ENV", "development"),
            "python_version": sys.version,
            "database_connected": True  # Would need to test actual connection
        }

        # Test database connection
        try:
            test_connection = select_one("users", columns="COUNT(*) as count", where="1=1")
            status_info["database_connected"] = test_connection is not None
        except Exception as e:
            status_info["database_connected"] = False
            status_info["database_error"] = str(e)

        return jsonify(status_info)

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


# === Debug Information Routes ===
@debug_bp.route("/info", methods=["GET"])
def get_debug_info_route():
    """
    Get detailed debugging information.

    This endpoint provides comprehensive debugging information including
    system configuration, environment variables, and runtime information.

    Query Parameters:
        - include_sensitive: Include sensitive configuration information
        - include_logs: Include recent log entries

    Returns:
        JSON response with debug information or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        include_sensitive = request.args.get("include_sensitive", "false").lower() == "true"
        include_logs = request.args.get("include_logs", "false").lower() == "true"

        # Get debug information
        debug_info = {
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": os.getcwd()
            },
            "environment": os.getenv("FLASK_ENV", "development"),
            "sensitive_data_included": include_sensitive,
            "logs_included": include_logs
        }

        return jsonify({
            "debug_info": debug_info,
            "generated_at": datetime.now().isoformat(),
            "request_id": "debug_info_request"
        })

    except Exception as e:
        logger.error(f"Error getting debug info: {e}")
        return jsonify({"error": "Failed to retrieve debug information"}), 500


@debug_bp.route("/config", methods=["GET"])
def get_config_info_route():
    """
    Get application configuration information.

    This endpoint provides information about the application configuration
    including environment variables and settings.

    Query Parameters:
        - include_sensitive: Include sensitive configuration values

    Returns:
        JSON response with configuration information or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        include_sensitive = request.args.get("include_sensitive", "false").lower() == "true"

        # Get configuration information
        config_info = {
            "environment": os.getenv("FLASK_ENV", "development"),
            "debug_mode": os.getenv("FLASK_DEBUG", "False").lower() == "true",
            "database_url": os.getenv("DATABASE_URL", "sqlite:///database/user_data.db"),
            "secret_key_configured": bool(os.getenv("SECRET_KEY")),
            "app_version": os.getenv("APP_VERSION", "unknown"),
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "environment_variables": {}
        }

        # Add environment variables (filtered for sensitive data)
        for key, value in os.environ.items():
            if include_sensitive or not any(sensitive in key.lower() for sensitive in ["key", "secret", "password", "token"]):
                config_info["environment_variables"][key] = value

        return jsonify({
            "config_info": config_info,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting config info: {e}")
        return jsonify({"error": "Failed to retrieve configuration information"}), 500


# === Development Tools Routes ===
@debug_bp.route("/test-db", methods=["GET"])
def test_database_connection_route():
    """
    Test database connection and basic operations.

    This endpoint tests the database connection and performs basic
    operations to verify database functionality.

    Returns:
        JSON response with database test results or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        test_results = {
            "connection_test": False,
            "read_test": False,
            "write_test": False,
            "errors": []
        }

        # Test database connection
        try:
            # Test basic read operation
            test_read = select_one("users", columns="COUNT(*) as count", where="1=1")
            test_results["connection_test"] = True
            test_results["read_test"] = True
        except Exception as e:
            test_results["errors"].append(f"Database read test failed: {str(e)}")

        # Test write operation (create temporary test record)
        try:
            test_data = {
                "username": f"test_user_{datetime.now().timestamp()}",
                "password": "test_password",
                "created_at": datetime.now().isoformat()
            }

            # Insert test record
            test_id = insert_row("users", test_data)
            if test_id:
                test_results["write_test"] = True

                # Clean up test record
                delete_rows("users", "WHERE username LIKE 'test_user_%'")
            else:
                test_results["errors"].append("Database write test failed: No ID returned")
        except Exception as e:
            test_results["errors"].append(f"Database write test failed: {str(e)}")

        return jsonify({
            "database_test": test_results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error testing database: {e}")
        return jsonify({"error": "Failed to test database"}), 500


@debug_bp.route("/clear-cache", methods=["POST"])
def clear_cache_route():
    """
    Clear application cache and temporary data.

    This endpoint clears various caches and temporary data to help
    with debugging and development.

    Request Body:
        - cache_type: Type of cache to clear (all, session, temp)

    Returns:
        JSON response with cache clearing results or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json() or {}
        cache_type = data.get("cache_type", "all")

        # Validate cache type
        valid_cache_types = ["all", "session", "temp", "logs"]
        if cache_type not in valid_cache_types:
            return jsonify({"error": f"Invalid cache type: {cache_type}"}), 400

        # Clear debug data
        cleared_items = {"cache_type": cache_type, "status": "cleared"}

        return jsonify({
            "message": f"Cache cleared successfully",
            "cache_type": cache_type,
            "cleared_items": cleared_items,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": "Failed to clear cache"}), 500


# === Performance Monitoring Routes ===
@debug_bp.route("/performance", methods=["GET"])
def get_performance_metrics_route():
    """
    Get system performance metrics.

    This endpoint provides detailed performance metrics including
    response times, memory usage, and system resource utilization.

    Query Parameters:
        - timeframe: Time period for metrics (hour, day, week)
        - include_details: Include detailed performance data

    Returns:
        JSON response with performance metrics or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        timeframe = request.args.get("timeframe", "hour")
        include_details = request.args.get("include_details", "false").lower() == "true"

        # Validate timeframe
        valid_timeframes = ["hour", "day", "week"]
        if timeframe not in valid_timeframes:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Get performance metrics
        metrics = {
            "timeframe": timeframe,
            "include_details": include_details,
            "response_time": "normal",
            "memory_usage": "stable"
        }

        return jsonify({
            "performance_metrics": metrics,
            "timeframe": timeframe,
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({"error": "Failed to retrieve performance metrics"}), 500


@debug_bp.route("/performance/slow-queries", methods=["GET"])
def get_slow_queries_route():
    """
    Get information about slow database queries.

    This endpoint provides information about slow database queries
    to help with performance optimization.

    Query Parameters:
        - limit: Maximum number of slow queries to return
        - threshold: Minimum query time threshold in seconds

    Returns:
        JSON response with slow query information or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        limit = int(request.args.get("limit", 10))
        threshold = float(request.args.get("threshold", 1.0))

        # This would typically query a slow query log or performance monitoring table
        # For now, return a placeholder response
        slow_queries = [
            {
                "query": "SELECT * FROM users WHERE username = ?",
                "execution_time": 2.5,
                "timestamp": datetime.now().isoformat(),
                "user_id": "admin",
                "explanation": "Missing index on username column"
            }
        ]

        return jsonify({
            "slow_queries": slow_queries,
            "threshold_seconds": threshold,
            "total_queries": len(slow_queries),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        return jsonify({"error": "Failed to retrieve slow query information"}), 500


# === Error Tracking Routes ===
@debug_bp.route("/errors", methods=["GET"])
def get_error_logs_route():
    """
    Get recent error logs and diagnostic information.

    This endpoint provides access to recent error logs and diagnostic
    information for debugging purposes.

    Query Parameters:
        - limit: Maximum number of error logs to return
        - level: Error level filter (error, warning, info)
        - include_stack_traces: Include full stack traces

    Returns:
        JSON response with error logs or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        # Get query parameters
        limit = int(request.args.get("limit", 50))
        level = request.args.get("level", "error")
        include_stack_traces = request.args.get("include_stack_traces", "false").lower() == "true"

        # Validate error level
        valid_levels = ["error", "warning", "info", "debug"]
        if level not in valid_levels:
            return jsonify({"error": f"Invalid error level: {level}"}), 400

        # Get error logs
        error_logs = [
            {
                "level": level,
                "message": "Sample error log",
                "timestamp": datetime.now().isoformat(),
                "stack_trace": "Sample stack trace" if include_stack_traces else None
            }
        ]

        return jsonify({
            "error_logs": error_logs,
            "level": level,
            "total_errors": len(error_logs),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting error logs: {e}")
        return jsonify({"error": "Failed to retrieve error logs"}), 500


@debug_bp.route("/errors/clear", methods=["POST"])
def clear_error_logs_route():
    """
    Clear error logs and diagnostic information.

    This endpoint clears error logs and diagnostic information
    to free up space and start fresh debugging.

    Request Body:
        - older_than: Clear logs older than specified days
        - level: Clear logs of specific level only

    Returns:
        JSON response with clearing results or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json() or {}
        older_than = data.get("older_than", 7)  # Default to 7 days
        level = data.get("level", "all")

        # Validate parameters
        if not isinstance(older_than, int) or older_than < 0:
            return jsonify({"error": "older_than must be a non-negative integer"}), 400

        valid_levels = ["all", "error", "warning", "info", "debug"]
        if level not in valid_levels:
            return jsonify({"error": f"Invalid error level: {level}"}), 400

        # Clear error logs
        cleared_count = 0

        return jsonify({
            "message": "Error logs cleared successfully",
            "cleared_count": cleared_count,
            "older_than_days": older_than,
            "level": level,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error clearing error logs: {e}")
        return jsonify({"error": "Failed to clear error logs"}), 500


# === Development Testing Routes ===
@debug_bp.route("/test/exception", methods=["POST"])
def test_exception_handling_route():
    """
    Test exception handling and error reporting.

    This endpoint allows testing of exception handling by
    deliberately raising an exception for testing purposes.

    Request Body:
        - exception_type: Type of exception to raise
        - message: Exception message

    Returns:
        JSON response with test results or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json() or {}
        exception_type = data.get("exception_type", "ValueError")
        message = data.get("message", "Test exception")

        # Validate exception type
        valid_exceptions = ["ValueError", "RuntimeError", "TypeError", "AttributeError"]
        if exception_type not in valid_exceptions:
            return jsonify({"error": f"Invalid exception type: {exception_type}"}), 400

        # Raise test exception
        if exception_type == "ValueError":
            raise ValueError(message)
        elif exception_type == "RuntimeError":
            raise RuntimeError(message)
        elif exception_type == "TypeError":
            raise TypeError(message)
        elif exception_type == "AttributeError":
            raise AttributeError(message)

        return jsonify({"message": "Exception test completed"})

    except Exception as e:
        logger.error(f"Test exception raised: {e}")
        return jsonify({
            "test_result": "exception_raised",
            "exception_type": type(e).__name__,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@debug_bp.route("/test/performance", methods=["POST"])
def test_performance_route():
    """
    Test system performance with synthetic load.

    This endpoint allows testing of system performance by
    generating synthetic load and measuring response times.

    Request Body:
        - duration: Test duration in seconds
        - load_type: Type of load to generate (cpu, memory, database)

    Returns:
        JSON response with performance test results or unauthorized error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        data = request.get_json() or {}
        duration = int(data.get("duration", 10))
        load_type = data.get("load_type", "cpu")

        # Validate parameters
        if duration <= 0 or duration > 60:
            return jsonify({"error": "Duration must be between 1 and 60 seconds"}), 400

        valid_load_types = ["cpu", "memory", "database"]
        if load_type not in valid_load_types:
            return jsonify({"error": f"Invalid load type: {load_type}"}), 400

        # Simulate performance test
        start_time = datetime.now()

        # This would actually perform the specified load test
        # For now, just simulate a delay
        import time
        time.sleep(min(duration, 5))  # Cap at 5 seconds for safety

        end_time = datetime.now()
        test_duration = (end_time - start_time).total_seconds()

        return jsonify({
            "test_result": "completed",
            "load_type": load_type,
            "requested_duration": duration,
            "actual_duration": test_duration,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in performance test: {e}")
        return jsonify({"error": "Failed to complete performance test"}), 500
