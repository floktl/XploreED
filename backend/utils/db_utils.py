# === utils/db_utils.py ===

import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path

# Load env just in case (won't override if already loaded)
env_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"
load_dotenv(dotenv_path=env_path)

DB = os.getenv("DB_FILE")
if not DB:
    raise RuntimeError("\u274c DB_FILE is not set in .env or environment variables.")

def get_connection():
    return sqlite3.connect(DB)

def execute_query(query, params=(), fetch=False, many=False):
    # print("📦 PARAMS:", params, flush=True)
    # print("🔠 PARAM TYPES:", [type(p) for p in params], flush=True)
    # print(f"🔧 fetch={fetch}, many={many}", flush=True)

    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            try:
                if many:
                    # print("📚 Running executemany...", flush=True)
                    cursor.executemany(query, params)
                else:
                    # print("🎯 Running execute...", flush=True)
                    cursor.execute(query, params)
                # print("✅ Query executed", flush=True)
            except Exception as e:
                print("❌ EXECUTE ERROR:", str(e), flush=True)
                print("⚠️ Failed during cursor.execute", flush=True)
                raise

            if fetch:
                try:
                    results = [dict(row) for row in cursor.fetchall()]
                    # print("📤 RESULT:", results, flush=True)
                    return results
                except Exception as e:
                    print("❌ FETCH ERROR:", str(e), flush=True)
                    print("⚠️ Failed during fetchall", flush=True)
                    raise

            try:
                conn.commit()
                # print("💾 Commit successful", flush=True)
                return True
            except Exception as e:
                print("❌ COMMIT ERROR:", str(e), flush=True)
                raise

    except Exception as e:
        print("❌ DB Error (outer):", str(e), flush=True)
        print("⚠️ Failed SQL input →", query, flush=True)
        print("⚠️ Failed SQL params →", params, flush=True)
        return None



def fetch_all(table, where_clause="", params=()):
    query = f"SELECT * FROM {table} {where_clause}"
    return execute_query(query, params, fetch=True)

def fetch_one(table, where_clause="", params=()):
    query = f"SELECT * FROM {table} {where_clause} LIMIT 1"
    results = execute_query(query, params, fetch=True)
    return results[0] if results else None

def insert_row(table, data):
    # print("🔍 Writing to DB path:", os.getenv("DB_FILE"), flush=True)
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
    # print("📥 fetch_custom query:", query, flush=True)
    # print("📦 fetch_custom params:", params, flush=True)
    return execute_query(query, params, fetch=True)

def fetch_one_custom(query, params=()):
    results = fetch_custom(query, params)
    return results[0] if results else None

