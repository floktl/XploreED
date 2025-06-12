# === utils/db_utils.py ===

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

def get_connection():
    return sqlite3.connect(DB)

def execute_query(query, params=(), fetch=False, many=False):

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
                print("❌ EXECUTE ERROR:", str(e), flush=True)
                raise

            if fetch:
                try:
                    results = [dict(row) for row in cursor.fetchall()]
                    return results
                except Exception as e:
                    print("❌ FETCH ERROR:", str(e), flush=True)
                    raise

            try:
                conn.commit()
                return True
            except Exception as e:
                print("❌ COMMIT ERROR:", str(e), flush=True)
                raise

    except Exception as e:
        print("❌ DB Error (outer):", str(e), flush=True)
        return None



def fetch_all(table, where_clause="", params=()):
    query = f"SELECT * FROM {table} {where_clause}"
    return execute_query(query, params, fetch=True)

def fetch_one(table, where_clause="", params=()):
    query = f"SELECT * FROM {table} {where_clause} LIMIT 1"
    results = execute_query(query, params, fetch=True)
    return results[0] if results else None

def insert_row(table, data):
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return execute_query(query, tuple(data.values()))

def update_row(table, updates: dict, where_clause: str, params=()):
    set_clause = ", ".join([f"{col} = ?" for col in updates])
    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause.lstrip('WHERE ')}"
    all_params = tuple(updates.values()) + tuple(params)
    return execute_query(query, all_params)

def delete_rows(table, where_clause="", params=()):
    query = f"DELETE FROM {table} {where_clause}"
    return execute_query(query, params)

def fetch_custom(query, params=()):
    return execute_query(query, params, fetch=True)

def fetch_one_custom(query, params=()):
    results = fetch_custom(query, params)
    return results[0] if results else None

