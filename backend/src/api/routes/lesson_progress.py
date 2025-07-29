"""Track per-block progress for lesson content."""

from core.services.import_service import *

@lesson_progress_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    """Return completion status for each block in the lesson."""
    user_id = require_user()

    rows = select_rows(
        "lesson_progress",
        columns=["block_id", "completed"],
        where="user_id = ? AND lesson_id = ?",
        params=(user_id, lesson_id),
    )

    progress = {row["block_id"]: bool(row["completed"]) for row in rows}
    return jsonify(progress), 200


@lesson_progress_bp.route("/lesson-progress", methods=["POST"])
def update_lesson_progress():
    """Mark a single lesson block as completed or not."""
    user_id = require_user()

    data = request.get_json()

    try:
        lesson_id = int(data.get("lesson_id"))
        block_id = str(data.get("block_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lesson_id or block_id format"}), 400

    if not lesson_id or not block_id:
        return jsonify({"error": "Missing lesson_id or block_id"}), 400

    completed = data.get("completed", False)

    execute_query("""
        INSERT INTO lesson_progress (user_id, lesson_id, block_id, completed, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, lesson_id, block_id)
        DO UPDATE SET completed = excluded.completed, updated_at = excluded.updated_at
    """, (user_id, lesson_id, block_id, int(completed), datetime.datetime.utcnow()))

    return jsonify({"status": "success"}), 200



@lesson_progress_bp.route("/lesson-progress-complete", methods=["POST"])
def mark_lesson_complete():
    """Confirm that a lesson is fully completed."""
    user_id = require_user()

    try:
        data = request.get_json()

        if not data or "lesson_id" not in data:
            return jsonify({"error": "Missing lesson_id in request"}), 400

        lesson_id = int(data.get("lesson_id"))

        if lesson_id <= 0:
            print("❌ lesson_id must be greater than 0", flush=True)
            return jsonify({"error": "Lesson ID must be > 0"}), 400

    except (TypeError, ValueError) as e:
        print(f"❌ Error parsing lesson_id: {e}", flush=True)
        return jsonify({"error": "Invalid lesson ID"}), 400

    num_blocks_row = select_one(
        "lesson_content",
        columns="num_blocks",
        where="lesson_id = ?",
        params=(lesson_id,),
    )
    total_blocks = num_blocks_row.get("num_blocks") if num_blocks_row else 0

    completed_blocks_row = select_one(
        "lesson_progress",
        columns="COUNT(*) as count",
        where="user_id = ? AND lesson_id = ? AND completed = 1",
        params=(user_id, lesson_id),
    )
    completed_blocks = completed_blocks_row.get("count") if completed_blocks_row else 0

    if completed_blocks < total_blocks and total_blocks > 0:
        print("❌ Lesson not fully completed", flush=True)
        return jsonify({"error": "Lesson not fully completed"}), 400

    update_row(
        "lesson_progress",
        {"completed": 1},
        "user_id = ? AND lesson_id = ?",
        (user_id, lesson_id),
    )
    return jsonify({"status": "lesson confirmed mplete"}), 200



@lesson_progress_bp.route("/lesson-completed", methods=["POST"])
def check_lesson_marked_complete():
    """Check if the lesson is marked as completed for the user."""
    user_id = require_user()

    try:
        lesson_id = int(request.get_json().get("lesson_id"))
        if lesson_id <= 0:
            return jsonify({"error": "Lesson ID must be > 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lesson ID"}), 400

    total_blocks_row = select_one(
        "lesson_blocks",
        columns="COUNT(*) as count",
        where="lesson_id = ?",
        params=(lesson_id,),
    )
    total_blocks = total_blocks_row.get("count") if total_blocks_row else 0

    completed_blocks_row = select_one(
        "lesson_progress",
        columns="COUNT(*) as count",
        where="user_id = ? AND lesson_id = ? AND completed = 1",
        params=(user_id, lesson_id),
    )
    completed_blocks = completed_blocks_row.get("count") if completed_blocks_row else 0

    completed = total_blocks > 0 and completed_blocks == total_blocks
    return jsonify({"completed": completed})


@lesson_progress_bp.route("/mark-as-completed", methods=["POST"])
def mark_lesson_as_completed():
    """Mark an entire lesson as completed and record results."""
    user_id = require_user()

    data = request.get_json()
    lesson_id = data.get("lesson_id")

    if not lesson_id:
        return jsonify({"error": "Missing lesson_id"}), 400

    num_blocks_row = select_one(
        "lesson_content",
        columns="num_blocks",
        where="lesson_id = ?",
        params=(lesson_id,),
    )
    total_blocks = num_blocks_row.get("num_blocks") if num_blocks_row else 0

    if total_blocks == 0:
        insert_row("results", {"username": user_id, "level": lesson_id, "correct": 1})
        return jsonify({"status": "completed (no blocks)"}), 200

    completed_row = select_one(
        "lesson_progress",
        columns="COUNT(*) as count",
        where="lesson_id = ? AND user_id = ? AND completed = 1",
        params=(lesson_id, user_id),
    )
    completed = completed_row.get("count") if completed_row else 0

    if completed < total_blocks:
        return jsonify({"error": "Lesson is not fully completed"}), 400

    insert_row("results", {"username": user_id, "level": lesson_id, "correct": 1})
    return jsonify({"status": "completed"}), 200

