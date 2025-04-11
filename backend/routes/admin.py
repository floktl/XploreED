from flask import Blueprint, request, jsonify
from session_manager import session_manager
import sqlite3
from collections import OrderedDict
from utils.lesson_parser import update_lesson_blocks_from_html, inject_block_ids
from bs4 import BeautifulSoup  # make sure this is at the top

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/results", methods=["GET"])
def admin_results():
    print("📊 [ADMIN] /results (game results only!)", flush=True)

    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🔐 Session:", session_id, "| User:", user, flush=True)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT username, level, correct, answer, timestamp
            FROM results
            ORDER BY username ASC, timestamp DESC
        """)

        # Return raw game result rows (no lesson association)
        results = [dict(row) for row in cursor.fetchall()]
        print(f"✅ Returning {len(results)} raw game results", flush=True)
        return jsonify(results)



@admin_bp.route("/lesson-content", methods=["POST"])
def insert_lesson_content():
    print("📚 [ADMIN] /lesson-content [POST]", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🔐 Session:", session_id, "| User:", user, flush=True)
    if user != "admin":
        print("❌ Unauthorized access", flush=True)
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    print("📥 Received content:", data, flush=True)
    lesson_id = data.get("lesson_id")
    title = data.get("title", "")
    content = data.get("content", "")
    target_user = data.get("target_user")
    published = bool(data.get("published", 0))

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("""
            INSERT INTO lesson_content (lesson_id, title, content, target_user, published)
            VALUES (?, ?, ?, ?, ?)
        """, (lesson_id, title, content, target_user, published))

        soup = BeautifulSoup(content, "html.parser")
        block_ids = {el["data-block-id"] for el in soup.select('[data-block-id]')}
        print(f"📦 Block IDs extracted: {block_ids}", flush=True)

        for block_id in block_ids:
            conn.execute("""
                INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id)
                VALUES (?, ?)
            """, (lesson_id, block_id))

    return jsonify({"status": "ok"})


@admin_bp.route("/profile-stats", methods=["POST"])
def profile_stats():
    print("📊 [ADMIN] /profile-stats", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🔐 Session:", session_id, "| User:", user, flush=True)
    if user != "admin":
        print("❌ Unauthorized", flush=True)
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    username = data.get("username", "").strip()
    print("👤 Target username:", username, flush=True)

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
    print("📖 [ADMIN] /lesson-content [GET]", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🔐 Session:", session_id, "| User:", user, flush=True)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT lesson_id, title, content, target_user, published
            FROM lesson_content
            ORDER BY lesson_id ASC
        """)
        lessons = [dict(row) for row in cursor.fetchall()]
        print(f"📚 Found {len(lessons)} lessons", flush=True)

    return jsonify(lessons)


@admin_bp.route("/debug-lessons", methods=["GET"])
def debug_lessons():
    print("🔍 [ADMIN] /debug-lessons", flush=True)
    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM lesson_content")
        return jsonify([dict(row) for row in cursor.fetchall()])


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    print(f"🗑️ [ADMIN] /lesson-content/{lesson_id} [DELETE]", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🔐 Session:", session_id, "| User:", user, flush=True)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("DELETE FROM lesson_content WHERE lesson_id = ?", (lesson_id,))
        print("✅ Lesson deleted", flush=True)
    return jsonify({"status": "deleted"})


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["GET"])
def get_lesson_by_id(lesson_id):
    print(f"📖 [ADMIN] /lesson-content/{lesson_id} [GET]", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM lesson_content WHERE lesson_id = ?", (lesson_id,))
        row = cursor.fetchone()
        if not row:
            print("❌ Lesson not found", flush=True)
            return jsonify({"error": "not found"}), 404
        print("✅ Lesson fetched", flush=True)
        return jsonify(dict(row))


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["PUT"])
def update_lesson_by_id(lesson_id):
    print(f"✏️ [ADMIN] /lesson-content/{lesson_id} [PUT]", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🔐 Session:", session_id, "| User:", user, flush=True)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    print("📥 Updating data:", data, flush=True)
    title = data.get("title")
    content = data.get("content")
    content = inject_block_ids(content)
    target_user = data.get("target_user")
    published = bool(data.get("published", 0))

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("""
            UPDATE lesson_content
            SET title = ?, content = ?, target_user = ?, published = ?
            WHERE lesson_id = ?
        """, (title, content, target_user, published, lesson_id))

    update_lesson_blocks_from_html(lesson_id, content)
    print("✅ Lesson updated and blocks synced", flush=True)
    return jsonify({"status": "updated"})


@admin_bp.route("/lesson-progress-summary", methods=["GET"])
def lesson_progress_summary():
    print("📊 [ADMIN] /lesson-progress-summary", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        lesson_ids = [row["lesson_id"] for row in conn.execute("SELECT DISTINCT lesson_id FROM lesson_content").fetchall()]
        summary = {}

        for lid in lesson_ids:
            total_blocks_row = conn.execute("SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?", (lid,)).fetchone()
            total_blocks = total_blocks_row["total"] if total_blocks_row else 0

            if total_blocks == 0:
                summary[lid] = 0
                continue

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

    print("✅ Progress summary computed", flush=True)
    return jsonify(summary)


@admin_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_individual_lesson_progress(lesson_id):
    print(f"📊 [ADMIN] /lesson-progress/{lesson_id}", flush=True)
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if user != "admin":
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row
        total_blocks = conn.execute("SELECT COUNT(*) FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,)).fetchone()[0] or 0

        if total_blocks == 0:
            print("⚠️ No blocks in lesson", flush=True)
            return jsonify([])

        cursor = conn.execute("""
            SELECT user_id, COUNT(*) AS completed_blocks
            FROM lesson_progress
            WHERE lesson_id = ? AND completed = 1
            GROUP BY user_id
        """, (lesson_id,))

        result = [{
            "user": row["user_id"],
            "completed": row["completed_blocks"],
            "total": total_blocks,
            "percent": round((row["completed_blocks"] / total_blocks) * 100)
        } for row in cursor.fetchall()]

        print("✅ Per-user lesson progress:", result, flush=True)
        return jsonify(result)
