"""Debug endpoints exposing raw database information."""

from core.services.import_service import *
from features.ai.generation.helpers import print_ai_user_data_titles

@debug_bp.route("/all-data", methods=["GET"])
def show_all_data():
    """Dump all database tables and rows for debugging."""
    db_path = os.getenv("DB_FILE", "user_data.db")  # or use a fixed path if needed

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            result = {}

            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]

                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()

                result[table] = {
                    "columns": columns,
                    "rows": rows
                }

            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@debug_bp.route("/ai-user-titles", methods=["POST"])
def debug_ai_user_titles():
    """Trigger backend print of ai_user_data titles for the current user."""
    username = require_user()
    print_ai_user_data_titles(username)
    # Fetch and print evaluation status for current and next block ids
    from core.database.connection import select_one
    row = select_one("ai_user_data", columns="exercises, next_exercises", where="username = ?", params=(username,))
    import json as _json
    block_ids = []
    if row:
        if row.get("exercises"):
            try:
                block = _json.loads(row["exercises"]) if isinstance(row["exercises"], str) else row["exercises"]
                if isinstance(block, dict) and block.get("block_id"):
                    block_ids.append(block["block_id"])
            except Exception:
                pass
        if row.get("next_exercises"):
            try:
                block = _json.loads(row["next_exercises"]) if isinstance(row["next_exercises"], str) else row["next_exercises"]
                if isinstance(block, dict) and block.get("block_id"):
                    block_ids.append(block["block_id"])
            except Exception:
                pass
    for bid in block_ids:
        print(f"\033[93m[DEBUG] Evaluation status for block_id: {bid}\033[0m", flush=True)
        # Directly call the logic from get_ai_exercise_results
        from flask import g
        g._force_username = username  # hack to force user context if needed
        try:
            # Use the same redis logic as in get_ai_exercise_results
            import os
            import redis
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
            result_key = f"exercise_result:{username}:{bid}"
            result_json = redis_client.get(result_key)
            if not result_json:
                print("  [status] No evaluation result found.", flush=True)
            else:
                print("  [status]", result_json, flush=True)
        except Exception as e:
            print(f"  [status] Error fetching evaluation status: {e}", flush=True)
    return jsonify({"status": "ok"})
