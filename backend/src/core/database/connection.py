"""
XplorED - Database Connection Management

This module provides SQLite database connection and query management utilities,
following clean architecture principles as outlined in the documentation.

Database Operations:
- Connection Management: Database file handling and connection creation
- Query Execution: SQL query execution with parameter binding
- Data Retrieval: Fetch operations for single and multiple rows
- Data Modification: Insert, update, and delete operations
- Query Building: Dynamic SQL query construction utilities

For detailed architecture information, see: docs/backend_structure.md
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from shared.exceptions import ConfigurationError

# === Environment Configuration ===
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv(dotenv_path=None, **_):  # type: ignore
        """Manually load environment variables from dotenv file."""
        if dotenv_path and os.path.exists(dotenv_path):
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key, value)

# Load environment variables early
env_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)

# === Database Configuration ===
DB = os.getenv("DB_FILE")
if not DB:
    raise ConfigurationError("❌ DB_FILE is not set in .env or environment variables.")

# Ensure the directory for the database exists
db_path = Path(DB)
db_path.parent.mkdir(parents=True, exist_ok=True)
if not db_path.exists():
    db_path.touch()


# === Connection Management ===
def get_connection():
    """
    Return a connection to the configured SQLite database file.

    Returns:
        sqlite3.Connection: Database connection object

    Raises:
        RuntimeError: If database file path is not configured
    """
    if not DB:
        raise ConfigurationError("Database file path is not configured")
    return sqlite3.connect(DB)


# === Query Execution ===
def execute_query(query: str, params: Tuple = (), fetch: bool = False, many: bool = False) -> Union[List[Dict], bool, None]:
    """
    Execute SQL query with optional parameters and return fetch results.

    Args:
        query: SQL query string to execute
        params: Parameters for the query (default: empty tuple)
        fetch: Whether to fetch and return results (default: False)
        many: Whether to execute multiple statements (default: False)

    Returns:
        Union[List[Dict], bool, None]: Query results or success status

    Raises:
        Exception: Database execution errors
    """
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            try:
                if many:
                    cursor.executemany(query, params)
                else:
                    cursor.execute(query, params)
            except Exception as e:
                raise

            if fetch:
                try:
                    results = [dict(row) for row in cursor.fetchall()]
                    return results
                except Exception as e:
                    return []

            try:
                conn.commit()
                return True if not fetch else []
            except Exception as e:
                raise

    except Exception as e:
        if fetch:
            return []
        return None


# === Data Retrieval Operations ===
def fetch_all(
    table: str,
    where_clause: str = "",
    params: Tuple = (),
    columns: Union[str, List[str]] = "*",
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    group_by: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Return multiple rows from table using basic query building.

    Args:
        table: Table name to query
        where_clause: WHERE clause string (default: empty)
        params: Query parameters (default: empty tuple)
        columns: Columns to select (default: "*")
        order_by: ORDER BY clause (default: None)
        limit: LIMIT clause (default: None)
        group_by: GROUP BY clause (default: None)

    Returns:
        List[Dict[str, Any]]: List of row dictionaries
    """
    cols = ", ".join(columns) if isinstance(columns, (list, tuple)) else str(columns)

    query = f"SELECT {cols} FROM {table} {where_clause}"
    if group_by:
        query += f" GROUP BY {group_by}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit is not None:
        query += f" LIMIT {limit}"
    if offset is not None:
        query += f" OFFSET {offset}"

    result = execute_query(query, params, fetch=True)
    return result if isinstance(result, list) else []


def fetch_one(
    table: str,
    where_clause: str = "",
    params: Tuple = (),
    columns: Union[str, List[str]] = "*",
    order_by: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return a single row from table using basic query building.

    Args:
        table: Table name to query
        where_clause: WHERE clause string (default: empty)
        params: Query parameters (default: empty tuple)
        columns: Columns to select (default: "*")
        order_by: ORDER BY clause (default: None)

    Returns:
        Optional[Dict[str, Any]]: Single row dictionary or None
    """
    results = fetch_all(table, where_clause, params, columns, order_by, limit=1)
    return results[0] if results else None


def fetch_topic_memory(username: str, include_correct: bool = False) -> Union[List[Dict[str, Any]], bool]:
    """
    Fetch topic memory entries for a specific user.

    Args:
        username: Username to fetch memory for
        include_correct: Whether to include correct answers (default: False)

    Returns:
        Union[List[Dict[str, Any]], bool]: Memory entries or False on error
    """
    try:
        where_clause = "WHERE username = ?"
        params = (username,)

        if not include_correct:
            where_clause += " AND correct = 0"

        return fetch_all("topic_memory", where_clause, params)
    except Exception:
        return False


# === Data Modification Operations ===
def insert_row(table: str, data: Dict[str, Any]) -> bool:
    """
    Insert a single row into the specified table.

    Args:
        table: Table name to insert into
        data: Dictionary of column names and values

    Returns:
        bool: Success status
    """
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

    return execute_query(query, tuple(data.values())) is True


def update_row(table: str, updates: Dict[str, Any], where_clause: str, params: Tuple = ()) -> bool:
    """
    Update rows in the specified table.

    Args:
        table: Table name to update
        updates: Dictionary of column names and new values
        where_clause: WHERE clause string
        params: Query parameters (default: empty tuple)

    Returns:
        bool: Success status
    """
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    query = f"UPDATE {table} SET {set_clause} {where_clause}"

    return execute_query(query, tuple(updates.values()) + params) is True


def delete_rows(table: str, where_clause: str = "", params: Tuple = ()) -> bool:
    """
    Delete rows from the specified table.

    Args:
        table: Table name to delete from
        where_clause: WHERE clause string (default: empty)
        params: Query parameters (default: empty tuple)

    Returns:
        bool: Success status
    """
    query = f"DELETE FROM {table} {where_clause}"
    return execute_query(query, params) is True


# === Custom Query Operations ===
def fetch_custom(query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a custom query and return all results.

    Args:
        query: Custom SQL query string
        params: Query parameters (default: empty tuple)

    Returns:
        List[Dict[str, Any]]: Query results
    """
    result = execute_query(query, params, fetch=True)
    return result if isinstance(result, list) else []


def fetch_one_custom(query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
    """
    Execute a custom query and return a single result.

    Args:
        query: Custom SQL query string
        params: Query parameters (default: empty tuple)

    Returns:
        Optional[Dict[str, Any]]: Single result or None
    """
    results = fetch_custom(query, params)
    return results[0] if results else None


# === Modern Query Interface ===
def select_rows(
    table: str,
    *,
    columns: Union[str, List[str]] = "*",
    where: Optional[str] = None,
    params: Tuple = (),
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    group_by: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Modern interface for selecting multiple rows with keyword arguments.

    Args:
        table: Table name to query
        columns: Columns to select (default: "*")
        where: WHERE clause (default: None)
        params: Query parameters (default: empty tuple)
        order_by: ORDER BY clause (default: None)
        limit: LIMIT clause (default: None)
        group_by: GROUP BY clause (default: None)

    Returns:
        List[Dict[str, Any]]: List of row dictionaries
    """
    where_clause = f"WHERE {where}" if where else ""
    return fetch_all(table, where_clause, params, columns, order_by, limit, offset, group_by)


def select_one(
    table: str,
    *,
    columns: Union[str, List[str]] = "*",
    where: Optional[str] = None,
    params: Tuple = (),
    order_by: Optional[str] = None,
    group_by: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Modern interface for selecting a single row with keyword arguments.

    Args:
        table: Table name to query
        columns: Columns to select (default: "*")
        where: WHERE clause (default: None)
        params: Query parameters (default: empty tuple)
        order_by: ORDER BY clause (default: None)
        group_by: GROUP BY clause (default: None)

    Returns:
        Optional[Dict[str, Any]]: Single row dictionary or None
    """
    where_clause = f"WHERE {where}" if where else ""
    return fetch_one(table, where_clause, params, columns, order_by)


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

