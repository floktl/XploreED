from utils.imports.imports import *

@profile_bp.route("/profile", methods=["GET"])
def get_profile():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"error": "Invalid session"}), 401

    rows = fetch_custom("""
        SELECT level, answer, correct, timestamp
        FROM results
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (username,))

    if rows is None:
        return jsonify({"error": "Failed to fetch results"}), 500

    print(f"📄 Fetched {len(rows)} result entries for user: {username}", flush=True)

    results = [
        {
            "level": row["level"],
            "answer": row["answer"],
            "correct": row["correct"],
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]

    return jsonify(results)
