# backend/routes/admin.py
from flask import Blueprint, request, jsonify
from session_manager import session_manager
import sqlite3
from collections import OrderedDict

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/results", methods=["GET"])
def admin_results():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT 
              u.username,
              r.level,
              r.correct,
              r.answer,
              r.timestamp
            FROM users u
            LEFT JOIN results r ON u.username = r.username
            ORDER BY u.username ASC, r.timestamp DESC
        """)
        rows = cursor.fetchall()

        user_latest = OrderedDict()
        for row in rows:
            username = row["username"]
            timestamp = row["timestamp"]
            if username not in user_latest or (timestamp and user_latest[username]["timestamp"] is None) or \
               (timestamp and user_latest[username]["timestamp"] < timestamp):
                user_latest[username] = {
                    "username": username,
                    "level": row["level"],
                    "correct": bool(row["correct"]) if row["correct"] is not None else None,
                    "answer": row["answer"],
                    "timestamp": timestamp
                }

        return jsonify(list(user_latest.values()))


@admin_bp.route("/lesson-content", methods=["POST"])
def insert_lesson_content():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    lesson_id = data.get("lesson_id")
    title = data.get("title", "")
    content = data.get("content", "")
    target_user = data.get("target_user")

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("""
            INSERT INTO lesson_content (lesson_id, title, content, target_user)
            VALUES (?, ?, ?, ?)
        """, (lesson_id, title, content, target_user))

    return jsonify({"status": "ok"})

@admin_bp.route("/profile-stats", methods=["POST"])
def profile_stats():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    username = data.get("username", "").strip()

    if not username:
        return jsonify({"error": "Missing username"}), 400

    with sqlite3.connect("user_data.db") as conn:
        rows = conn.execute("""
            SELECT level, correct, answer, timestamp
            FROM results
            WHERE username = ?
            ORDER BY timestamp DESC
        """, (username,)).fetchall()

    return jsonify([
        {"level": l, "correct": bool(c), "answer": a, "timestamp": t}
        for l, c, a, t in rows
    ])
