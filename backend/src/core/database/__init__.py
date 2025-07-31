"""
XplorED - Core Database Module

This module provides database connection and management functionality,
following clean architecture principles as outlined in the documentation.

Database Components:
- connection: Database connection and query management
- migrations: Database schema creation and updates

For detailed architecture information, see: docs/backend_structure.md
"""

from . import connection
from . import migrations

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


# === Export Configuration ===
__all__ = [
    # Module imports
    "connection",
    "migrations",

    # Connection management
    "get_connection",

    # Query execution
    "execute_query",

    # Data retrieval
    "fetch_all",
    "fetch_one",

    # Data modification
    "insert_row",
    "update_row",
    "delete_rows",

    # Modern interface
    "select_rows",
    "select_one",
]
