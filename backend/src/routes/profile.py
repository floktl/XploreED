"""Basic profile information for the logged in user."""

from utils.imports.imports import *

@profile_bp.route("/profile", methods=["GET"])
def get_profile():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"error": "Invalid session"}), 401

    rows = select_rows(
        "results",
        columns=["level", "answer", "correct", "timestamp"],
        where="username = ?",
        params=(username,),
        order_by="timestamp DESC",
    )

    if rows is None:
        return jsonify({"error": "Failed to fetch results"}), 500

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
