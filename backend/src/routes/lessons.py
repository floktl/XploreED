"""Endpoints serving lessons and lesson metadata."""

from utils.imports.imports import *
from database import fetch_custom  # Needed for raw SQL queries

@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if not user:
        print("❌ Unauthorized: No user found for session", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

    lessons = fetch_custom(
        """
        SELECT lesson_id, title, created_at, target_user, num_blocks, ai_enabled
        FROM lesson_content
        WHERE (target_user IS NULL OR target_user = ?)
            AND published = 1
        ORDER BY created_at DESC
    """,
        (user,),
    )

    results = []

    for lesson in lessons:
        lid = lesson["lesson_id"]

        total_blocks = lesson.get("num_blocks") or 0

        completed_blocks_res = fetch_custom("""
            SELECT COUNT(*) as count FROM lesson_progress
            WHERE lesson_id = ? AND user_id = ? AND completed = 1
        """, (lid, user))
        completed_blocks = completed_blocks_res[0]["count"] if completed_blocks_res else 0

        completed_res = fetch_custom("""
            SELECT 1 FROM results
            WHERE username = ? AND level = ? AND correct = 1
            LIMIT 1
        """, (user, lid))
        completed = bool(completed_res)

        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks else 100
        if completed:
            percent_complete = 100

        latest_res = fetch_custom("""
            SELECT MAX(timestamp) as ts FROM results
            WHERE username = ? AND level = ?
        """, (user, lid))
        latest = latest_res[0]["ts"] if latest_res else None

        results.append(
            {
                "id": lid,
                "title": lesson["title"] or f"Lesson {lid + 1}",
                "completed": completed,
                "last_attempt": latest,
                "percent_complete": percent_complete,
                "ai_enabled": bool(lesson.get("ai_enabled", 0)),
            }
        )

    return jsonify(results)


@lessons_bp.route("/lesson/<int:lesson_id>", methods=["GET"])
def get_lesson_content(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)

    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    row = fetch_custom(
        """
        SELECT title, content, created_at, num_blocks, ai_enabled FROM lesson_content
        WHERE lesson_id = ?
          AND (target_user IS NULL OR target_user = ?)
          AND published = 1
    """,
        (lesson_id, user),
    )

    if not row:
        return jsonify({"msg": "Lesson not found"}), 404

    data = {
        "title": row[0]["title"],
        "content": row[0]["content"],
        "created_at": row[0]["created_at"],
        "num_blocks": row[0]["num_blocks"],
        "ai_enabled": bool(row[0].get("ai_enabled", 0)),
    }

    return jsonify(data)






@lessons_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = select_rows(
        "lesson_progress",
        columns=["block_id", "completed"],
        where="user_id = ? AND lesson_id = ?",
        params=(user, lesson_id),
    )

    progress = {row[0]: bool(row[1]) for row in rows}    return jsonify(progress)