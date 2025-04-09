# backend/routes/admin.py
from flask import Blueprint, request, jsonify
from session_manager import session_manager
import sqlite3
from collections import OrderedDict
from utils.lesson_parser import update_lesson_blocks_from_html, inject_block_ids


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


from bs4 import BeautifulSoup  # make sure this is at the top

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
    content = inject_block_ids(content)

    with sqlite3.connect("user_data.db") as conn:
        # Save lesson content
        conn.execute("""
            INSERT INTO lesson_content (lesson_id, title, content, target_user)
            VALUES (?, ?, ?, ?)
        """, (lesson_id, title, content, target_user))

        # 🧠 Extract block IDs from content using BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        block_ids = {el["data-block-id"] for el in soup.select('[data-block-id]')}

        # ✅ Save block IDs to lesson_blocks table
        for block_id in block_ids:
            conn.execute("""
                INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id)
                VALUES (?, ?)
            """, (lesson_id, block_id))

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

@admin_bp.route("/lesson-content", methods=["GET"])
def get_all_lessons():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT lesson_id, title, content, target_user
            FROM lesson_content
            ORDER BY lesson_id ASC
        """)
        lessons = [dict(row) for row in cursor.fetchall()]

    return jsonify(lessons)


@admin_bp.route("/debug-lessons", methods=["GET"])
def debug_lessons():
    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM lesson_content")
        return jsonify([dict(row) for row in cursor.fetchall()])

@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("DELETE FROM lesson_content WHERE lesson_id = ?", (lesson_id,))
    return jsonify({"status": "deleted"})

@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["GET"])
def get_lesson_by_id(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM lesson_content WHERE lesson_id = ?", (lesson_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        return jsonify(dict(row))


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["PUT"])
def update_lesson_by_id(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    title = data.get("title")
    content = data.get("content")
    content = inject_block_ids(content)
    target_user = data.get("target_user")

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("""
            UPDATE lesson_content
            SET title = ?, content = ?, target_user = ?
            WHERE lesson_id = ?
        """, (title, content, target_user, lesson_id))

    # ✅ Sync blocks with lesson_blocks table
    update_lesson_blocks_from_html(lesson_id, content)

    return jsonify({"status": "updated"})

@admin_bp.route("/lesson-progress-summary", methods=["GET"])
def lesson_progress_summary():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row

        # Get all lessons
        lesson_ids = [row["lesson_id"] for row in conn.execute("SELECT DISTINCT lesson_id FROM lesson_content").fetchall()]
        summary = {}

        for lid in lesson_ids:
            # Count total blocks
            total_blocks_row = conn.execute("SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?", (lid,)).fetchone()
            total_blocks = total_blocks_row["total"] if total_blocks_row else 0

            if total_blocks == 0:
                summary[lid] = 0
                continue

            # Count users with progress
            user_ids = [row["user_id"] for row in conn.execute("""
                SELECT DISTINCT user_id FROM lesson_progress WHERE lesson_id = ?
            """, (lid,)).fetchall()]

            if not user_ids:
                summary[lid] = 0
                continue

            total_percent = 0
            for uid in user_ids:
                completed = conn.execute("""
                    SELECT COUNT(*) FROM lesson_progress
                    WHERE lesson_id = ? AND user_id = ? AND completed = 1
                """, (lid, uid)).fetchone()[0]

                percent = (completed / total_blocks) * 100
                total_percent += percent

            avg_percent = total_percent / len(user_ids)
            summary[lid] = round(avg_percent)

    return jsonify(summary)

@admin_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_individual_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row

        # Get total blocks
        total_blocks = conn.execute("SELECT COUNT(*) FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,)).fetchone()[0] or 0

        if total_blocks == 0:
            return jsonify([])

        # Per-user completed blocks
        cursor = conn.execute("""
            SELECT user_id, COUNT(*) AS completed_blocks
            FROM lesson_progress
            WHERE lesson_id = ? AND completed = 1
            GROUP BY user_id
        """, (lesson_id,))

        return jsonify([
            {
                "user": row["user_id"],
                "completed": row["completed_blocks"],
                "total": total_blocks,
                "percent": round((row["completed_blocks"] / total_blocks) * 100)
            } for row in cursor.fetchall()
        ])
