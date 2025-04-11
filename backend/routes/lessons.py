# backend/routes/lessons.py
from flask import Blueprint, jsonify, request
from session_manager import session_manager
import sqlite3

lessons_bp = Blueprint("lessons", __name__, url_prefix="/api")

@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    print("🟡 SESSION ID:", session_id, flush=True)
    print("🟢 USER FROM SESSION:", user, flush=True)

    if not user:
        print("🔴 No user found in session", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

    results = []
    with sqlite3.connect("user_data.db") as conn:
        conn.row_factory = sqlite3.Row

        print("📥 Fetching lessons from DB for user:", user, flush=True)
        lessons = conn.execute("""
            SELECT lesson_id, title, created_at, target_user
            FROM lesson_content
            WHERE (target_user IS NULL OR target_user = ?)
                AND published = 1
            ORDER BY created_at DESC
        """, (user,)).fetchall()

        print(f"📘 Found {len(lessons)} lessons for user '{user}'", flush=True)
        for lesson in lessons:
            print("———", flush=True)
            print("📗 Lesson row:", dict(lesson), flush=True)

            lid = lesson["lesson_id"]

            total_blocks = conn.execute(
                "SELECT COUNT(*) FROM lesson_blocks WHERE lesson_id = ?", (lid,)
            ).fetchone()[0] or 0
            print(f"📦 Total blocks for lesson {lid}: {total_blocks}", flush=True)

            completed_blocks = conn.execute("""
                SELECT COUNT(*) FROM lesson_progress
                WHERE lesson_id = ? AND user_id = ? AND completed = 1
            """, (lid, user)).fetchone()[0] or 0
            print(f"✅ Completed blocks: {completed_blocks}", flush=True)

            percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks else 0
            print(f"📊 Percent complete: {percent_complete}%", flush=True)

            latest = conn.execute("""
                SELECT MAX(timestamp) FROM results
                WHERE username = ? AND level = ?
            """, (user, lid)).fetchone()[0]
            print(f"🕓 Last attempt: {latest}", flush=True)

            completed_row = conn.execute("""
                SELECT 1 FROM results
                WHERE username = ? AND level = ? AND correct = 1
                LIMIT 1
            """, (user, lid)).fetchone()
            completed = completed_row is not None
            print(f"🏁 Completed: {completed}", flush=True)

            results.append({
                "id": lid,
                "title": lesson["title"] or f"Lesson {lid + 1}",
                "completed": completed,
                "last_attempt": latest,
                "percent_complete": percent_complete
            })

        print("✅ Final results array:", results, flush=True)
        print("====================================", flush=True)

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
            WHERE lesson_id = ?
              AND (target_user IS NULL OR target_user = ?)
              AND published = 1
        """, (lesson_id, user)).fetchall()

    if not rows:
        return jsonify({"msg": "Lesson not found"}), 404

    return jsonify([{"title": t, "content": c, "created_at": d} for t, c, d in rows])


@lessons_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT block_id, completed FROM lesson_progress
            WHERE user_id = ? AND lesson_id = ?
        """, (user, lesson_id))
        progress = {row[0]: bool(row[1]) for row in cursor.fetchall()}

    return jsonify(progress)
