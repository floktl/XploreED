from utils.imports.imports import *

@lesson_progress_bp.route("/api/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_all("""
        SELECT block_id, completed FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ?
    """, (user_id, lesson_id))

    progress = {row[0]: bool(row[1]) for row in rows}
    return jsonify(progress), 200


@lesson_progress_bp.route("/api/lesson-progress", methods=["POST"])
def update_lesson_progress():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    lesson_id = data.get("lesson_id")
    block_id = data.get("block_id")
    completed = data.get("completed", False)

    if not lesson_id or not block_id:
        return jsonify({"error": "Missing lesson_id or block_id"}), 400

    execute_query("""
        INSERT INTO lesson_progress (user_id, lesson_id, block_id, completed, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, lesson_id, block_id)
        DO UPDATE SET completed = excluded.completed, updated_at = excluded.updated_at
    """, (user_id, lesson_id, block_id, int(completed), datetime.datetime.utcnow()))

    return jsonify({"status": "success"}), 200


@lesson_progress_bp.route("/api/lesson-progress-complete", methods=["POST"])
def mark_lesson_complete():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        lesson_id = int(request.get_json().get("lesson_id"))
        if lesson_id <= 0:
            return jsonify({"error": "Lesson ID must be > 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lesson ID"}), 400

    total_blocks = fetch_one("""
        SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?
    """, (lesson_id,))["total"]

    completed_blocks = fetch_one("""
        SELECT COUNT(*) FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ? AND completed = 1
    """, (user_id, lesson_id))[0]

    if total_blocks > 0 and completed_blocks < total_blocks:
        return jsonify({"error": "Lesson not fully completed"}), 400

    return jsonify({"status": "lesson confirmed as complete"}), 200


@lesson_progress_bp.route("/api/lesson-completed", methods=["POST"])
def check_lesson_marked_complete():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        lesson_id = int(request.get_json().get("lesson_id"))
        if lesson_id <= 0:
            return jsonify({"error": "Lesson ID must be > 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lesson ID"}), 400

    total_blocks = fetch_one("""
        SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?
    """, (lesson_id,))["total"]

    completed_blocks = fetch_one("""
        SELECT COUNT(*) FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ? AND completed = 1
    """, (user_id, lesson_id))[0]

    completed = total_blocks > 0 and completed_blocks == total_blocks
    return jsonify({"completed": completed})