"""Endpoints serving lessons and lesson metadata."""

from utils.imports.imports import *
from database import select_rows, select_one

@lessons_bp.route("/lessons", methods=["GET"])
def get_lessons():
    """Return summary information for all published lessons for the user."""
    user = require_user()

    lessons = select_rows(
        "lesson_content",
        columns=[
            "lesson_id",
            "title",
            "created_at",
            "target_user",
            "num_blocks",
            "ai_enabled",
        ],
        where="(target_user IS NULL OR target_user = ?) AND published = 1",
        params=(user,),
        order_by="created_at DESC",
    )

    results = []

    for lesson in lessons:
        lid = lesson["lesson_id"]

        total_blocks = lesson.get("num_blocks") or 0

        completed_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="lesson_id = ? AND user_id = ? AND completed = 1",
            params=(lid, user),
        )
        completed_blocks = completed_row.get("count") if completed_row else 0

        completed = bool(
            select_one(
                "results",
                columns="1",
                where="username = ? AND level = ? AND correct = 1",
                params=(user, lid),
            )
        )

        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks else 100
        if completed:
            percent_complete = 100

        latest_row = select_one(
            "results",
            columns="MAX(timestamp) as ts",
            where="username = ? AND level = ?",
            params=(user, lid),
        )
        latest = latest_row.get("ts") if latest_row else None

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
    """Return HTML content and metadata for a single lesson."""
    user = require_user()

    row = select_rows(
        "lesson_content",
        columns=["title", "content", "created_at", "num_blocks", "ai_enabled"],
        where="lesson_id = ? AND (target_user IS NULL OR target_user = ?) AND published = 1",
        params=(lesson_id, user),
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
    """Return completion status of each block in the lesson."""
    user = require_user()

    rows = select_rows(
        "lesson_progress",
        columns=["block_id", "completed"],
        where="user_id = ? AND lesson_id = ?",
        params=(user, lesson_id),
    )

    progress = {row[0]: bool(row[1]) for row in rows}
    return jsonify(progress)
