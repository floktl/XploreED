"""Debug endpoints exposing raw database information."""

from app.imports.imports import *

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
