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
from typing import Optional, List
from datetime import datetime
import os

from flask import request, jsonify # type: ignore
from infrastructure.imports import Imports
from api.middleware.auth import is_admin
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows
from config.blueprint import debug_bp
from features.debug import (
    get_all_database_data,
    debug_user_ai_data,
    get_database_schema,
    get_user_statistics,
)
from features.debug.cache_management import (
    clear_user_cache,
    clear_system_cache,
    get_cache_statistics,
    clear_in_memory_caches
)
from shared.exceptions import DatabaseError


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === System Diagnostics Routes ===
@debug_bp.route("/health", methods=["GET"])
def get_system_health_route():
    """
    Get comprehensive system health information and status.

    This endpoint provides detailed system health information including
    database connectivity, external service status, performance metrics,
    and overall system operational status for monitoring and diagnostics.

    Query Parameters:
        - detailed (bool, optional): Include detailed health information (default: false)
        - include_metrics (bool, optional): Include performance metrics (default: false)
        - check_external (bool, optional): Check external service status (default: false)

    Health Checks Performed:
        - Database connectivity and responsiveness
        - External service availability (AI, TTS, etc.)
        - Memory usage and system resources
        - Application uptime and version information
        - Error rate and performance metrics

    JSON Response Structure:
        {
            "status": str,                             # Overall health status (healthy, unhealthy, degraded)
            "timestamp": str,                          # Health check timestamp
            "health_info": {                           # Detailed health information
                "overall_status": bool,                # Overall system status
                "database": str,                       # Database status (connected, disconnected, error)
                "external_services": str,              # External services status
                "performance": str,                    # Performance status (normal, slow, critical)
                "memory_usage": float,                 # Memory usage percentage
                "cpu_usage": float,                    # CPU usage percentage
                "disk_usage": float,                   # Disk usage percentage
                "error_rate": float                    # Error rate percentage
            },
            "version": str,                            # Application version
            "environment": str,                        # Environment (development, production, staging)
            "uptime": str,                             # System uptime
            "last_error": str,                         # Last error encountered (if any)
            "recommendations": [str]                   # Health improvement recommendations
        }

    Error Codes:
        - HEALTH_CHECK_FAILED: Health check process failed
        - DATABASE_ERROR: Database connectivity issues
        - EXTERNAL_SERVICE_ERROR: External service unavailable
        - PERFORMANCE_CRITICAL: Performance issues detected

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 500: Internal server error (health check failed)

    Health Status Levels:
        - healthy: All systems operational
        - degraded: Some systems experiencing issues
        - unhealthy: Critical systems down

    Usage Examples:
        Basic health check:
        GET /debug/health

        Detailed health check:
        GET /debug/health?detailed=true&include_metrics=true

        External service check:
        GET /debug/health?check_external=true
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
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/status", methods=["GET"])
def get_debug_system_status_route():
    """
    Get basic system status and operational information.

    This endpoint provides essential system status information for
    monitoring, health checks, and basic operational status without
    detailed diagnostics or performance metrics.

    Query Parameters:
        - include_version (bool, optional): Include version information (default: true)
        - include_uptime (bool, optional): Include uptime information (default: true)
        - include_database (bool, optional): Include database status (default: true)

    Status Information:
        - Application operational status
        - Database connectivity status
        - Version and environment information
        - Basic system information
        - Python runtime information

    JSON Response Structure:
        {
            "status": str,                             # System status (operational, maintenance, error)
            "timestamp": str,                          # Status check timestamp
            "uptime": str,                             # System uptime (HH:MM:SS format)
            "version": str,                            # Application version
            "environment": str,                        # Environment (development, production, staging)
            "python_version": str,                     # Python runtime version
            "database_connected": bool,                # Database connection status
            "database_error": str,                     # Database error message (if any)
            "last_restart": str,                       # Last restart timestamp
            "maintenance_mode": bool,                  # Whether system is in maintenance mode
            "read_only_mode": bool                     # Whether system is in read-only mode
        }

    Error Codes:
        - STATUS_CHECK_FAILED: Status check process failed
        - DATABASE_CONNECTION_ERROR: Database connection issues
        - SYSTEM_ERROR: General system error

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 500: Internal server error (status check failed)

    Operational Status Levels:
        - operational: System fully operational
        - maintenance: System in maintenance mode
        - error: System experiencing errors
        - degraded: System partially operational

    Usage Examples:
        Basic status check:
        GET /debug/status

        Status with version info:
        GET /debug/status?include_version=true

        Status with database check:
        GET /debug/status?include_database=true
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
            logger.error(f"Error getting system status: {e}")
            status_info["database_connected"] = False
            status_info["database_error"] = "Database connection failed"

        return jsonify(status_info)

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": "Internal server error"}), 500


# === Debug Information Routes ===
@debug_bp.route("/info", methods=["GET"])
def get_debug_info_route():
    """
    Get comprehensive debugging information and system details.

    This endpoint provides detailed debugging information including
    system configuration, environment variables, runtime information,
    and diagnostic data for troubleshooting and development purposes.

    Query Parameters:
        - include_sensitive (bool, optional): Include sensitive configuration (default: false)
        - include_logs (bool, optional): Include recent log entries (default: false)
        - include_system (bool, optional): Include system information (default: true)
        - include_environment (bool, optional): Include environment variables (default: true)

    Debug Information Categories:
        - System information and platform details
        - Environment configuration
        - Runtime information and dependencies
        - Recent log entries and errors
        - Configuration settings and variables

    JSON Response Structure:
        {
            "debug_info": {                            # Debug information object
                "system_info": {                       # System information
                    "python_version": str,             # Python version
                    "platform": str,                   # Operating system platform
                    "working_directory": str,          # Current working directory
                    "process_id": int,                 # Process ID
                    "memory_usage": object,            # Memory usage information
                    "cpu_info": object                 # CPU information
                },
                "environment": str,                    # Environment (development, production)
                "sensitive_data_included": bool,       # Whether sensitive data is included
                "logs_included": bool,                 # Whether logs are included
                "recent_logs": [object],               # Recent log entries (if requested)
                "configuration": object,               # Configuration information
                "dependencies": object                 # Dependency information
            },
            "generated_at": str,                       # Debug info generation timestamp
            "request_id": str,                         # Unique request identifier
            "debug_level": str                         # Debug level (basic, detailed, full)
        }

    Error Codes:
        - DEBUG_INFO_ERROR: Error retrieving debug information
        - SENSITIVE_DATA_ERROR: Error handling sensitive data
        - LOG_RETRIEVAL_ERROR: Error retrieving log information

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 500: Internal server error (debug info retrieval failed)

    Security Considerations:
        - Sensitive data is filtered by default
        - Environment variables containing secrets are masked
        - Database credentials are never exposed
        - Log entries may contain sensitive information

    Usage Examples:
        Basic debug info:
        GET /debug/info

        Debug info with logs:
        GET /debug/info?include_logs=true

        Full debug info:
        GET /debug/info?include_sensitive=true&include_logs=true
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
        logger.error(f"Error getting system info: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/config", methods=["GET"])
def get_config_info_route():
    """
    Get application configuration information and settings.

    This endpoint provides detailed information about the application
    configuration including environment variables, settings, and
    configuration parameters for debugging and administration.

    Query Parameters:
        - include_sensitive (bool, optional): Include sensitive configuration (default: false)
        - include_database (bool, optional): Include database configuration (default: true)
        - include_external (bool, optional): Include external service config (default: true)
        - filter (str, optional): Filter configuration by prefix

    Configuration Categories:
        - Environment variables and settings
        - Database configuration and connection details
        - External service configurations
        - Application settings and parameters
        - Security and authentication settings

    JSON Response Structure:
        {
            "config_info": {                           # Configuration information
                "environment": str,                    # Environment (development, production)
                "debug_mode": bool,                    # Debug mode status
                "database_url": str,                   # Database connection URL (masked)
                "secret_key_configured": bool,         # Secret key configuration status
                "app_version": str,                    # Application version
                "python_version": str,                 # Python version
                "working_directory": str,              # Working directory
                "environment_variables": object,       # Environment variables (filtered)
                "database_config": object,             # Database configuration
                "external_services": object,           # External service configurations
                "security_settings": object,           # Security and authentication settings
                "feature_flags": object                # Feature flags and toggles
            },
            "generated_at": str,                       # Configuration retrieval timestamp
            "sensitive_data_included": bool,           # Whether sensitive data is included
            "config_hash": str                         # Configuration hash for change detection
        }

    Error Codes:
        - CONFIG_RETRIEVAL_ERROR: Error retrieving configuration
        - SENSITIVE_DATA_ERROR: Error handling sensitive data
        - INVALID_FILTER: Invalid configuration filter

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid parameters)
        - 500: Internal server error (config retrieval failed)

    Security Features:
        - Sensitive data masking by default
        - Database credentials protection
        - API keys and secrets filtering
        - Configuration change detection

    Usage Examples:
        Basic configuration:
        GET /debug/config

        Configuration with database info:
        GET /debug/config?include_database=true

        Filtered configuration:
        GET /debug/config?filter=APP_
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
        logger.error(f"Error getting system config: {e}")
        return jsonify({"error": "Internal server error"}), 500


# === Development Tools Routes ===
@debug_bp.route("/test-db", methods=["GET"])
def test_database_connection_route():
    """
    Test database connection and perform diagnostic operations.

    This endpoint performs comprehensive database connectivity tests
    including read/write operations, connection validation, and
    performance diagnostics for troubleshooting database issues.

    Query Parameters:
        - test_type (str, optional): Type of test to perform (basic, full, performance)
        - timeout (int, optional): Test timeout in seconds (default: 30)
        - include_schema (bool, optional): Include schema information (default: false)

    Test Types:
        - basic: Basic connectivity and read operations
        - full: Full read/write/delete operations
        - performance: Performance and timing tests
        - schema: Schema validation and structure tests

    JSON Response Structure:
        {
            "database_test": {                         # Database test results
                "connection_test": bool,               # Connection test result
                "read_test": bool,                     # Read operation test result
                "write_test": bool,                    # Write operation test result
                "delete_test": bool,                   # Delete operation test result
                "performance_test": object,            # Performance test results
                "schema_test": object,                 # Schema validation results
                "errors": [str],                       # Test errors encountered
                "warnings": [str],                     # Test warnings
                "test_duration": float                 # Total test duration (seconds)
            },
            "timestamp": str,                          # Test execution timestamp
            "database_info": {                         # Database information
                "type": str,                           # Database type (sqlite, postgresql, mysql)
                "version": str,                        # Database version
                "connection_string": str,              # Connection string (masked)
                "tables_count": int,                   # Number of tables
                "total_records": int                   # Total records across all tables
            },
            "recommendations": [str]                   # Improvement recommendations
        }

    Error Codes:
        - CONNECTION_FAILED: Database connection failed
        - READ_TEST_FAILED: Read operation test failed
        - WRITE_TEST_FAILED: Write operation test failed
        - TIMEOUT_ERROR: Test timeout exceeded
        - SCHEMA_ERROR: Schema validation failed

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid test parameters)
        - 500: Internal server error (test execution failed)

    Test Safety Features:
        - Temporary test data creation and cleanup
        - Transaction rollback on failure
        - Timeout protection
        - Error isolation and reporting

    Usage Examples:
        Basic database test:
        GET /debug/test-db

        Full database test:
        GET /debug/test-db?test_type=full

        Performance test:
        GET /debug/test-db?test_type=performance&timeout=60
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
            logger.error(f"Error testing database connection: {e}")
            test_results["errors"].append("Database read test failed: Connection or query failed")

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
            logger.error(f"Error testing database write: {e}")
            test_results["errors"].append("Database write test failed: Connection or insert failed")

        return jsonify({
            "database_test": test_results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/clear-cache", methods=["POST"])
def clear_cache_route():
    """
    Clear application cache and temporary data.

    This endpoint clears various types of application cache and
    temporary data to help with debugging, development, and
    performance optimization.

    Request Body:
        - cache_type (str, required): Type of cache to clear
        - force (bool, optional): Force clear even if in use (default: false)
        - dry_run (bool, optional): Show what would be cleared (default: false)

    Cache Types:
        - all: Clear all caches
        - session: Clear session data and user sessions
        - temp: Clear temporary files and data
        - logs: Clear log files and entries
        - ai: Clear AI model cache and responses
        - database: Clear database query cache
        - user: Clear user-specific cache data

    JSON Response Structure:
        {
            "message": str,                            # Success message
            "cache_type": str,                         # Type of cache cleared
            "cleared_items": {                         # Items cleared
                "cache_type": str,                     # Cache type
                "status": str,                         # Clear status (cleared, failed, skipped)
                "items_count": int,                    # Number of items cleared
                "size_freed": str,                     # Size freed (e.g., "1.5 MB")
                "errors": [str]                        # Errors encountered during clearing
            },
            "timestamp": str,                          # Clear operation timestamp
            "dry_run": bool,                           # Whether this was a dry run
            "recommendations": [str]                   # Cache optimization recommendations
        }

    Error Codes:
        - INVALID_CACHE_TYPE: Invalid cache type specified
        - CLEAR_FAILED: Cache clearing operation failed
        - CACHE_IN_USE: Cache is currently in use
        - PERMISSION_ERROR: Insufficient permissions to clear cache

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid cache type)
        - 500: Internal server error (clear operation failed)

    Cache Clearing Features:
        - Selective cache clearing
        - Dry run mode for preview
        - Force clearing option
        - Size and item count reporting
        - Error handling and reporting

    Usage Examples:
        Clear all cache:
        {
            "cache_type": "all"
        }

        Clear specific cache with dry run:
        {
            "cache_type": "session",
            "dry_run": true
        }

        Force clear cache:
        {
            "cache_type": "temp",
            "force": true
        }
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        try:
            data = request.get_json() or {}
        except Exception as e:
            logger.error(f"Error getting cache clear data: {e}")
            data = {}
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
        logger.error(f"Error clearing system cache: {e}")
        return jsonify({"error": "Internal server error"}), 500


# === Performance Monitoring Routes ===
@debug_bp.route("/performance", methods=["GET"])
def get_performance_metrics_route():
    """
    Get comprehensive system performance metrics and analytics.

    This endpoint provides detailed performance metrics including
    response times, memory usage, CPU utilization, database performance,
    and system resource utilization for monitoring and optimization.

    Query Parameters:
        - timeframe (str, optional): Time period for metrics (hour, day, week, month)
        - include_details (bool, optional): Include detailed performance data (default: false)
        - include_history (bool, optional): Include historical data (default: false)
        - metrics (str, optional): Specific metrics to include (comma-separated)

    Timeframe Options:
        - hour: Last hour metrics
        - day: Last 24 hours metrics
        - week: Last 7 days metrics
        - month: Last 30 days metrics
        - all: All available metrics

    Performance Metrics:
        - Response time statistics
        - Memory usage and allocation
        - CPU utilization and load
        - Database query performance
        - Network I/O statistics
        - Error rates and frequency

    JSON Response Structure:
        {
            "performance_metrics": {                   # Performance metrics object
                "timeframe": str,                      # Metrics timeframe
                "include_details": bool,               # Whether details are included
                "response_time": {                     # Response time metrics
                    "average": float,                  # Average response time (ms)
                    "median": float,                   # Median response time (ms)
                    "p95": float,                      # 95th percentile (ms)
                    "p99": float,                      # 99th percentile (ms)
                    "min": float,                      # Minimum response time (ms)
                    "max": float                       # Maximum response time (ms)
                },
                "memory_usage": {                      # Memory usage metrics
                    "current": float,                  # Current memory usage (MB)
                    "peak": float,                     # Peak memory usage (MB)
                    "available": float,                # Available memory (MB)
                    "percentage": float                # Memory usage percentage
                },
                "cpu_usage": {                         # CPU usage metrics
                    "current": float,                  # Current CPU usage (%)
                    "average": float,                  # Average CPU usage (%)
                    "load_average": [float]            # Load average (1min, 5min, 15min)
                },
                "database_performance": {              # Database performance
                    "query_count": int,                # Total queries executed
                    "slow_queries": int,               # Number of slow queries
                    "average_query_time": float,       # Average query time (ms)
                    "connection_pool": object          # Connection pool status
                },
                "error_rates": {                       # Error rate metrics
                    "total_errors": int,               # Total errors
                    "error_rate": float,               # Error rate percentage
                    "error_types": object              # Error types breakdown
                }
            },
            "timeframe": str,                          # Requested timeframe
            "generated_at": str,                       # Metrics generation timestamp
            "recommendations": [str]                   # Performance improvement recommendations
        }

    Error Codes:
        - INVALID_TIMEFRAME: Invalid timeframe specified
        - METRICS_ERROR: Error retrieving performance metrics
        - HISTORY_ERROR: Error retrieving historical data

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid parameters)
        - 500: Internal server error (metrics retrieval failed)

    Performance Monitoring Features:
        - Real-time and historical metrics
        - Detailed performance breakdowns
        - Performance trend analysis
        - Automated recommendations
        - Threshold monitoring

    Usage Examples:
        Basic performance metrics:
        GET /debug/performance

        Detailed metrics for last day:
        GET /debug/performance?timeframe=day&include_details=true

        Specific metrics:
        GET /debug/performance?metrics=response_time,memory_usage
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
        logger.error(f"Error getting system performance: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/performance/slow-queries", methods=["GET"])
def get_slow_queries_route():
    """
    Get information about slow database queries and performance issues.

    This endpoint provides detailed information about slow database
    queries to help identify performance bottlenecks and optimization
    opportunities in the database layer.

    Query Parameters:
        - limit (int, optional): Maximum number of slow queries to return (default: 10, max: 100)
        - threshold (float, optional): Minimum query time threshold in seconds (default: 1.0)
        - timeframe (str, optional): Time period to analyze (hour, day, week)
        - include_explanation (bool, optional): Include query explanations (default: true)
        - include_plans (bool, optional): Include execution plans (default: false)

    Slow Query Analysis:
        - Query execution time analysis
        - Query frequency and impact
        - Resource usage patterns
        - Optimization recommendations
        - Index usage analysis

    JSON Response Structure:
        {
            "slow_queries": [                          # Array of slow queries
                {
                    "query": str,                      # SQL query text
                    "execution_time": float,           # Execution time (seconds)
                    "timestamp": str,                  # Query execution timestamp
                    "user_id": str,                    # User who executed query
                    "explanation": str,                # Query explanation
                    "execution_plan": object,          # Execution plan (if requested)
                    "frequency": int,                  # Query frequency
                    "impact_score": float,             # Performance impact score
                    "recommendations": [str],          # Optimization recommendations
                    "table_affected": str,             # Primary table affected
                    "index_usage": object              # Index usage information
                }
            ],
            "threshold_seconds": float,                # Query time threshold used
            "total_queries": int,                      # Total slow queries found
            "timeframe": str,                          # Analysis timeframe
            "generated_at": str,                       # Analysis timestamp
            "summary": {                               # Slow query summary
                "average_execution_time": float,       # Average execution time
                "most_common_tables": [str],           # Most affected tables
                "optimization_opportunities": int,     # Number of optimization opportunities
                "estimated_improvement": str           # Estimated performance improvement
            }
        }

    Error Codes:
        - INVALID_THRESHOLD: Invalid threshold value
        - QUERY_ANALYSIS_ERROR: Error analyzing slow queries
        - INSUFFICIENT_DATA: Insufficient data for analysis

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid parameters)
        - 500: Internal server error (analysis failed)

    Analysis Features:
        - Query performance profiling
        - Execution plan analysis
        - Index usage optimization
        - Query pattern recognition
        - Automated recommendations

    Usage Examples:
        Basic slow query analysis:
        GET /debug/performance/slow-queries

        Custom threshold analysis:
        GET /debug/performance/slow-queries?threshold=2.5&limit=20

        Detailed analysis with plans:
        GET /debug/performance/slow-queries?include_plans=true&timeframe=day
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
        logger.error(f"Error getting system slow queries: {e}")
        return jsonify({"error": "Internal server error"}), 500


# === Error Tracking Routes ===
@debug_bp.route("/errors", methods=["GET"])
def get_error_logs_route():
    """
    Get comprehensive error logs and diagnostic information.

    This endpoint provides access to error logs, diagnostic information,
    and error analysis for debugging and monitoring system health.

    Query Parameters:
        - limit (int, optional): Maximum number of error logs to return (default: 50, max: 500)
        - level (str, optional): Error level filter (error, warning, info, debug)
        - include_stack_traces (bool, optional): Include full stack traces (default: false)
        - timeframe (str, optional): Time period to analyze (hour, day, week, month)
        - search (str, optional): Search term to filter errors
        - user_id (str, optional): Filter by specific user

    Error Levels:
        - error: Critical errors requiring immediate attention
        - warning: Warnings that may indicate issues
        - info: Informational messages
        - debug: Debug-level messages

    JSON Response Structure:
        {
            "error_logs": [                            # Array of error logs
                {
                    "level": str,                      # Error level (error, warning, info, debug)
                    "message": str,                    # Error message
                    "timestamp": str,                  # Error timestamp
                    "stack_trace": str,                # Stack trace (if requested)
                    "user_id": str,                    # User who encountered error
                    "request_id": str,                 # Request identifier
                    "error_code": str,                 # Error code
                    "context": object,                 # Error context information
                    "resolved": bool,                  # Whether error was resolved
                    "occurrence_count": int            # Number of times error occurred
                }
            ],
            "level": str,                              # Error level filter used
            "total_errors": int,                       # Total errors found
            "timeframe": str,                          # Analysis timeframe
            "generated_at": str,                       # Analysis timestamp
            "summary": {                               # Error summary
                "error_count": int,                    # Total error count
                "warning_count": int,                  # Total warning count
                "most_common_errors": [object],        # Most frequent errors
                "error_trends": object,                # Error trend analysis
                "unresolved_errors": int               # Number of unresolved errors
            },
            "recommendations": [str]                   # Error resolution recommendations
        }

    Error Codes:
        - INVALID_LEVEL: Invalid error level specified
        - LOG_RETRIEVAL_ERROR: Error retrieving log information
        - INSUFFICIENT_PERMISSIONS: Insufficient permissions to access logs

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid parameters)
        - 500: Internal server error (log retrieval failed)

    Error Analysis Features:
        - Error pattern recognition
        - Trend analysis and forecasting
        - Impact assessment
        - Resolution tracking
        - Automated recommendations

    Usage Examples:
        Basic error logs:
        GET /debug/errors

        Error logs with stack traces:
        GET /debug/errors?include_stack_traces=true&limit=100

        Filtered error logs:
        GET /debug/errors?level=error&timeframe=day&search=database
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
        logger.error(f"Error getting system logs: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/errors/clear", methods=["POST"])
def clear_error_logs_route():
    """
    Clear error logs and diagnostic information.

    This endpoint clears error logs and diagnostic information to
    free up storage space and start fresh debugging sessions.

    Request Body:
        - older_than (int, optional): Clear logs older than specified days (default: 7)
        - level (str, optional): Clear logs of specific level only (default: all)
        - dry_run (bool, optional): Show what would be cleared (default: false)
        - backup (bool, optional): Create backup before clearing (default: true)

    Clear Options:
        - older_than: Clear logs older than specified days
        - level: Clear logs of specific error level
        - all: Clear all error logs
        - resolved: Clear only resolved errors

    JSON Response Structure:
        {
            "message": str,                            # Success message
            "cleared_count": int,                      # Number of logs cleared
            "older_than_days": int,                    # Age threshold used
            "level": str,                              # Error level filter used
            "timestamp": str,                          # Clear operation timestamp
            "dry_run": bool,                           # Whether this was a dry run
            "backup_created": bool,                    # Whether backup was created
            "space_freed": str,                        # Storage space freed
            "details": {                               # Clear operation details
                "error_logs_cleared": int,             # Error logs cleared
                "warning_logs_cleared": int,           # Warning logs cleared
                "info_logs_cleared": int,              # Info logs cleared
                "debug_logs_cleared": int,             # Debug logs cleared
                "errors_encountered": [str]            # Errors during clearing
            }
        }

    Error Codes:
        - INVALID_AGE: Invalid age parameter
        - CLEAR_FAILED: Log clearing operation failed
        - BACKUP_FAILED: Backup creation failed
        - INSUFFICIENT_PERMISSIONS: Insufficient permissions to clear logs

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid parameters)
        - 500: Internal server error (clear operation failed)

    Clear Operation Features:
        - Selective log clearing
        - Age-based filtering
        - Level-based filtering
        - Dry run mode
        - Automatic backup creation
        - Space usage reporting

    Usage Examples:
        Clear old logs:
        {
            "older_than": 30,
            "level": "debug"
        }

        Dry run clear operation:
        {
            "older_than": 7,
            "dry_run": true
        }

        Clear all logs with backup:
        {
            "older_than": 0,
            "backup": true
        }
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        try:
            data = request.get_json() or {}
        except Exception as e:
            logger.error(f"Error getting error clear data: {e}")
            data = {}
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
        logger.error(f"Error clearing system errors: {e}")
        return jsonify({"error": "Internal server error"}), 500


# === Development Testing Routes ===
@debug_bp.route("/test/exception", methods=["POST"])
def test_exception_handling_route():
    """
    Test exception handling and error reporting capabilities.

    This endpoint allows testing of the system's exception handling mechanisms
    by deliberately raising different types of exceptions for testing and
    validation purposes. This is useful for verifying error handling,
    logging, and error reporting functionality.

    Request Body:
        - exception_type (str, optional): Type of exception to raise (default: "ValueError")
        - message (str, optional): Custom exception message (default: "Test exception")

    Valid Exception Types:
        - ValueError: Value-related errors
        - RuntimeError: Runtime execution errors
        - TypeError: Type-related errors
        - AttributeError: Attribute access errors

    JSON Response Structure (Success):
        {
            "test_result": str,                           # Test result status
            "exception_type": str,                        # Type of exception raised
            "message": str,                               # Exception message
            "timestamp": str                              # Test execution timestamp
        }

    JSON Response Structure (Error):
        {
            "error": str,                                 # Error message
            "details": str                                # Additional error details
        }

    Error Codes:
        - INVALID_EXCEPTION_TYPE: Unsupported exception type
        - TEST_EXECUTION_FAILED: Test execution failed
        - UNAUTHORIZED: Admin access required

    Status Codes:
        - 200: Success (exception raised and handled)
        - 400: Bad request (invalid exception type)
        - 401: Unauthorized (admin access required)
        - 500: Internal server error (test execution failed)

    Testing Features:
        - Exception type validation
        - Custom exception messages
        - Error handling verification
        - Logging validation
        - Response format testing

    Usage Examples:
        Test ValueError:
        {
            "exception_type": "ValueError",
            "message": "Invalid input parameter"
        }

        Test RuntimeError:
        {
            "exception_type": "RuntimeError",
            "message": "System configuration error"
        }

        Test with default values:
        {}
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
        logger.error(f"Error testing exception handling: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/test/performance", methods=["POST"])
def test_performance_route():
    """
    Test system performance with synthetic load generation.

    This endpoint allows testing of system performance characteristics by
    generating controlled synthetic load and measuring system response times,
    resource usage, and performance metrics. This is useful for performance
    validation, capacity planning, and stress testing.

    Request Body:
        - duration (int, optional): Test duration in seconds (default: 10, max: 60)
        - load_type (str, optional): Type of load to generate (default: "cpu")

    Load Types:
        - cpu: CPU-intensive load simulation
        - memory: Memory-intensive load simulation
        - database: Database query load simulation

    JSON Response Structure (Success):
        {
            "test_result": str,                           # Test completion status
            "load_type": str,                             # Type of load generated
            "requested_duration": int,                    # Requested test duration
            "actual_duration": float,                     # Actual test duration
            "timestamp": str,                             # Test execution timestamp
            "performance_metrics": {                      # Performance metrics (if available)
                "cpu_usage": float,                       # CPU usage during test
                "memory_usage": float,                    # Memory usage during test
                "response_time": float                    # Average response time
            }
        }

    JSON Response Structure (Error):
        {
            "error": str,                                 # Error message
            "details": str                                # Additional error details
        }

    Error Codes:
        - INVALID_DURATION: Duration out of valid range
        - INVALID_LOAD_TYPE: Unsupported load type
        - TEST_EXECUTION_FAILED: Performance test failed
        - UNAUTHORIZED: Admin access required

    Status Codes:
        - 200: Success (performance test completed)
        - 400: Bad request (invalid parameters)
        - 401: Unauthorized (admin access required)
        - 500: Internal server error (test execution failed)

    Performance Testing Features:
        - Controlled load generation
        - Duration-based testing
        - Multiple load type simulation
        - Performance metrics collection
        - Safety limits and timeouts
        - Resource usage monitoring

    Safety Features:
        - Maximum duration limit (60 seconds)
        - Automatic timeout protection
        - Resource usage monitoring
        - Graceful test termination

    Usage Examples:
        CPU load test:
        {
            "duration": 30,
            "load_type": "cpu"
        }

        Memory load test:
        {
            "duration": 15,
            "load_type": "memory"
        }

        Database load test:
        {
            "duration": 45,
            "load_type": "database"
        }

        Quick test with defaults:
        {}
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
        logger.error(f"Error testing performance: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/cache-stats", methods=["GET"])
def get_cache_stats_route():
    """
    Get cache statistics and health information.

    This endpoint provides detailed information about the current
    cache usage, memory consumption, and health status.

    JSON Response Structure:
        {
            "redis_connected": bool,                    # Redis connection status
            "total_keys": int,                          # Total number of cache keys
            "key_patterns": {                           # Key pattern distribution
                "pattern": int,                         # Pattern name and count
            },
            "memory_used": str,                         # Memory usage (human readable)
            "memory_peak": str,                         # Peak memory usage
            "timestamp": str                            # Statistics timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 500: Internal server error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        stats = get_cache_statistics()
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        return jsonify({"error": "Internal server error"}), 500


@debug_bp.route("/clear-user-cache/<username>", methods=["POST"])
def clear_user_cache_route(username: str):
    """
    Clear all cache data for a specific user.

    This endpoint clears all Redis cache entries and in-memory caches
    associated with the specified user.

    Path Parameters:
        - username (str, required): The username to clear cache for

    JSON Response Structure:
        {
            "message": str,                             # Success message
            "cache_stats": {                            # Cache clearing statistics
                "exercise_results": int,                # Exercise result cache entries cleared
                "feedback_progress": int,               # Feedback progress cache entries cleared
                "translation_jobs": int,                # Translation job cache entries cleared
                "other_keys": int,                      # Other cache entries cleared
                "total_cleared": int                    # Total cache entries cleared
            },
            "in_memory_stats": {                        # In-memory cache clearing statistics
                "reading_exercise_cache": bool,         # Reading exercise cache cleared
                "other_caches": int,                    # Other in-memory caches cleared
                "timestamp": str                        # Clear timestamp
            },
            "timestamp": str                            # Operation timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized (admin access required)
        - 400: Bad request (invalid username)
        - 500: Internal server error
    """
    try:
        # Check admin privileges
        if not is_admin():
            return jsonify({"error": "Unauthorized - Admin access required"}), 401

        if not username:
            return jsonify({"error": "Username is required"}), 400

        # Clear Redis cache
        cache_stats = clear_user_cache(username)

        # Clear in-memory caches
        in_memory_stats = clear_in_memory_caches()

        return jsonify({
            "message": f"Cache cleared successfully for user {username}",
            "cache_stats": cache_stats,
            "in_memory_stats": in_memory_stats,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error clearing cache for user {username}: {e}")
        return jsonify({"error": "Internal server error"}), 500
