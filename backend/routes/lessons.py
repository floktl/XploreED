# backend/routes/lessons.py
from flask import Blueprint, jsonify, request
from session_manager import session_manager
import sqlite3

lessons_bp = Blueprint("lessons", __name__, url_prefix="/api")

@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    results = []
    with sqlite3.connect("user_data.db") as conn:
        r = conn.execute("""
            SELECT DISTINCT level, MAX(timestamp), correct
            FROM results WHERE username = ?
            GROUP BY level ORDER BY MAX(timestamp) DESC
        """, (user,)).fetchall()

        for lvl, ts, correct in r:
            results.append({
                "id": lvl,
                "title": f"Lesson {lvl + 1}",
                "completed": bool(correct),
                "last_attempt": ts
            })

        content = conn.execute("""
            SELECT lesson_id, title, created_at, target_user
            FROM lesson_content
            WHERE target_user IS NULL OR target_user = ?
            ORDER BY created_at DESC
        """, (user,)).fetchall()

        existing_ids = {l["id"] for l in results}
        for lid, title, created, target_user in content:
            if lid not in existing_ids:
                results.append({
                    "id": lid,
                    "title": title or f"Lesson {lid+1}",
                    "completed": False,
                    "last_attempt": None
                })

    return jsonify(results)


@lessons_bp.route("/lesson/<int:lesson_id>", methods=["GET"])
def get_lesson_content(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        rows = conn.execute("""
            SELECT title, content, created_at FROM lesson_content
            WHERE lesson_id = ? AND (target_user IS NULL OR target_user = ?)
        """, (lesson_id, user)).fetchall()
    return jsonify([{"title": t, "content": c, "created_at": d} for t, c, d in rows])
