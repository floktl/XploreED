from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sqlite3

profile_bp = Blueprint("profile", __name__, url_prefix="/api")

@profile_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    session_id = get_jwt_identity()
    username = session_manager.get_user(session_id)

    if not username:
        return jsonify({"error": "Invalid session"}), 401

    with sqlite3.connect("user_data.db") as conn:
        cursor = conn.execute("""
            SELECT level, answer, correct, timestamp
            FROM results
            WHERE username = ?
            ORDER BY timestamp DESC
        """, (username,))
        rows = cursor.fetchall()

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
