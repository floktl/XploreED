import os
from contextlib import closing
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB = os.getenv("DB_FILE", "user_data.db")  # fallback just in case


def get_connection():
    return sqlite3.connect(DB)

def execute_query(query, params=(), fetch=False, many=False):
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if many:
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params)
            if fetch:
                return [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return True
    except Exception as e:
        print("❌ DB Error:", str(e), flush=True)
        return None


# 🔹 Fetch rows
def fetch_all(table, where_clause="", params=()):
    query = f"SELECT * FROM {table} {where_clause}"
    return execute_query(query, params, fetch=True)


def fetch_one(table, where_clause="", params=()):
    query = f"SELECT * FROM {table} {where_clause} LIMIT 1"
    results = execute_query(query, params, fetch=True)
    return results[0] if results else None


# 🔹 Insert single row
def insert_row(table, data):
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return execute_query(query, tuple(data.values()))


# 🔹 Update rows
def update_row(table, updates: dict, where_clause: str, params=()):
    set_clause = ", ".join([f"{col} = ?" for col in updates])
    query = f"UPDATE {table} SET {set_clause} {where_clause}"
    all_params = tuple(updates.values()) + tuple(params)
    return execute_query(query, all_params)


# 🔹 Delete rows
def delete_rows(table, where_clause="", params=()):
    query = f"DELETE FROM {table} {where_clause}"
    return execute_query(query, params)
