"""
XplorED - Database Helper Utilities

This module provides convenient database operation imports and utilities,
following clean architecture principles as outlined in the documentation.

Database Operations:
- Connection Management: Database connection utilities
- Query Execution: SQL query execution functions
- Data Retrieval: Fetch operations for data access
- Data Modification: Insert, update, and delete operations

For detailed architecture information, see: docs/backend_structure.md
"""

# === Database Connection Imports ===
from core.database.connection import (
    # Connection management
    get_connection,

    # Query execution
    execute_query,

    # Data retrieval
    fetch_all,
    fetch_one,
    fetch_topic_memory,
    fetch_custom,
    fetch_one_custom,

    # Data modification
    insert_row,
    update_row,
    delete_rows,

    # Modern interface
    select_rows,
    select_one,
)


# === Export Configuration ===
__all__ = [
    # Connection management
    "get_connection",

    # Query execution
    "execute_query",

    # Data retrieval
    "fetch_all",
    "fetch_one",
    "fetch_topic_memory",
    "fetch_custom",
    "fetch_one_custom",

    # Data modification
    "insert_row",
    "update_row",
    "delete_rows",

    # Modern interface
    "select_rows",
    "select_one",
]
