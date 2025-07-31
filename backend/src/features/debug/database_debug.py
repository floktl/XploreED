"""
XplorED - Database Debug Module

This module provides database debugging functions for development and troubleshooting,
following clean architecture principles as outlined in the documentation.

Database Debug Components:
- Database Inspection: Retrieve all data from all tables
- Schema Analysis: Get database schema information and table structures
- Data Validation: Check database integrity and table relationships

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import os
from typing import Dict, Any

from core.database.connection import get_connection

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
