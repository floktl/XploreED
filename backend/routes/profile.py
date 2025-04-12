from utils.imports.imports import *

@profile_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    session_id = get_jwt_identity()
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"error": "Invalid session"}), 401

    rows = fetch_all("""
        SELECT level, answer, correct, timestamp
        FROM results
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (username,))

    results = [
        {
            "level": row[0],
            "answer": row[1],
            "correct": row[2],
            "timestamp": row[3],
        }
        for row in rows
    ]

    return jsonify(results)