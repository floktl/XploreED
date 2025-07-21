"""SQLite helper functions used across the backend."""

import os
import sqlite3
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv(dotenv_path=None, **_):  # type: ignore
        if dotenv_path and os.path.exists(dotenv_path):
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key, value)

# Load env just in case (won't override if already loaded)
env_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)

DB = os.getenv("DB_FILE")
if not DB:
    raise RuntimeError("\u274c DB_FILE is not set in .env or environment variables.")

# Ensure the directory for the database exists. sqlite3 will create the file
# if the directory is present, but attempting to connect when the path does
# not exist raises an OperationalError.
db_path = Path(DB)
db_path.parent.mkdir(parents=True, exist_ok=True)
if not db_path.exists():
    db_path.touch()

def get_connection():
    """Return a connection to the configured SQLite database file."""
    return sqlite3.connect(DB)

def execute_query(query, params=(), fetch=False, many=False):
    """Execute ``query`` with optional parameters and return fetch results."""

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
                    raise

            try:
                conn.commit()
                return True
            except Exception as e:
                raise

    except Exception as e:
        return None



def fetch_all(
    table,
    where_clause: str = "",
    params=(),
    columns="*",
    order_by: str | None = None,
    limit: int | None = None,
    group_by: str | None = None,
):
    """Return multiple rows from ``table`` using basic query building."""

    cols = ", ".join(columns) if isinstance(columns, (list, tuple)) else str(columns)

    query = f"SELECT {cols} FROM {table} {where_clause}"
    if group_by:
        query += f" GROUP BY {group_by}"
    if order_by:
        query += f" ORDER BY {order_by}"
    if limit is not None:
        query += f" LIMIT {limit}"

    # Debug print for SQL and params
    # print(f"[DB DEBUG] Executing SQL: {query}")
    # print(f"[DB DEBUG] With params: {repr(params)}")

    return execute_query(query, params, fetch=True)


def fetch_one(
    table,
    where_clause: str = "",
    params=(),
    columns="*",
    order_by: str | None = None,
):
    """Return a single row from ``table``."""

    rows = fetch_all(
        table,
        where_clause,
        params,
        columns=columns,
        order_by=order_by,
        limit=1,
    )
    return rows[0] if rows else None


def fetch_topic_memory(username: str, include_correct: bool = False) -> list:
    """Retrieve topic memory rows for a user.

    If ``include_correct`` is ``False`` (default), only entries that were
    answered incorrectly are returned.
    """
    where = "username = ?"
    if not include_correct:
        where += " AND (correct IS NULL OR correct = 0)"
    try:
        rows = select_rows(
            "topic_memory",
            columns=[
                "grammar",
                "topic",
                "skill_type",
                "context",
                "lesson_content_id",
                "ease_factor",
                "intervall",
                "next_repeat",
                "repetitions",
                "last_review",
                "correct",
                "quality",
            ],
            where=where,
            params=(username,),
        )
        return rows if rows else []
    except Exception:
        # Table might not exist yet
        return []


def insert_row(table, data):
    """Insert ``data`` as a new row into ``table``."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return execute_query(query, tuple(data.values()))

def update_row(table, updates: dict, where_clause: str, params=()):
    """Update rows in ``table`` matching ``where_clause`` with ``updates``."""
    set_clause = ", ".join([f"{col} = ?" for col in updates])
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause.lstrip('WHERE ')}"
    all_params = tuple(updates.values()) + tuple(params)
    return execute_query(query, all_params)

def delete_rows(table, where_clause="", params=()):
    """Delete rows from ``table`` that satisfy ``where_clause``."""
    query = f"DELETE FROM {table} {where_clause}"
    return execute_query(query, params)

def fetch_custom(query, params=()):
    """Return rows from a custom ``SELECT`` query."""
    return execute_query(query, params, fetch=True)

def fetch_one_custom(query, params=()):
    """Return the first row from a custom query or ``None``."""
    results = fetch_custom(query, params)
    return results[0] if results else None


def select_rows(
    table: str,
    *,
    columns="*",
    where: str | None = None,
    params=(),
    order_by: str | None = None,
    limit: int | None = None,
    group_by: str | None = None,
):
    """Convenience wrapper around SELECT queries."""

    where_clause = f" WHERE {where}" if where else ""
    return fetch_all(
        table,
        where_clause,
        params,
        columns=columns,
        order_by=order_by,
        group_by=group_by,
        limit=limit,
    )


def select_one(
    table: str,
    *,
    columns="*",
    where: str | None = None,
    params=(),
    order_by: str | None = None,
    group_by: str | None = None,
):
    """Return a single row from ``table`` using :func:`select_rows`."""

    rows = select_rows(
        table,
        columns=columns,
        where=where,
        params=params,
        order_by=order_by,
        group_by=group_by,
        limit=1,
    )
    return rows[0] if rows else None

