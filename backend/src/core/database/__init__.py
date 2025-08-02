"""
XplorED - Core Database Module

This module provides database connection and management functionality,
following clean architecture principles as outlined in the documentation.

Database Components:
- connection: Database connection and query management
- db_helpers: Database helper utilities and convenient imports

Note: Database migrations have been moved to scripts/migrations/ for better separation.

For detailed architecture information, see: docs/backend_structure.md
"""

from . import connection
from . import db_helpers

# Re-export commonly used items for convenience
from .connection import (
    get_connection,
    execute_query,
    fetch_all,
    fetch_one,
    insert_row,
    update_row,
    delete_rows,
    select_rows,
    select_one,
)

# Re-export db_helpers functions
from .db_helpers import (
    get_connection as db_get_connection,
    execute_query as db_execute_query,
    fetch_all as db_fetch_all,
    fetch_one as db_fetch_one,
    fetch_topic_memory,
    fetch_custom,
    fetch_one_custom,
    insert_row as db_insert_row,
    update_row as db_update_row,
    delete_rows as db_delete_rows,
    select_rows as db_select_rows,
    select_one as db_select_one,
)


# === Export Configuration ===
__all__ = [
    # Module imports
    "connection",
    "db_helpers",

    # Connection management
    "get_connection",
    "db_get_connection",

    # Query execution
    "execute_query",
    "db_execute_query",

    # Data retrieval
    "fetch_all",
    "fetch_one",
    "db_fetch_all",
    "db_fetch_one",
    "fetch_topic_memory",
    "fetch_custom",
    "fetch_one_custom",

    # Data modification
    "insert_row",
    "update_row",
    "delete_rows",
    "db_insert_row",
    "db_update_row",
    "db_delete_rows",

    # Modern interface
    "select_rows",
    "select_one",
    "db_select_rows",
    "db_select_one",
]
