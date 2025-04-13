from utils.imports.imports import *

@lesson_progress_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)

    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_custom("""
        SELECT block_id, completed FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ?
    """, (user_id, lesson_id))

    progress = {row["block_id"]: bool(row["completed"]) for row in rows}
    return jsonify(progress), 200


@lesson_progress_bp.route("/lesson-progress", methods=["POST"])
def update_lesson_progress():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    print(f"📨 lesson-progress payload: {data}", flush=True)

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
    print(f"====================================================@lesson_progress_bp.route(lesson-progress-compl============================================================", flush=True)
    session_id = request.cookies.get("session_id")

    user_id = session_manager.get_user(session_id)

    if not user_id:
        print("❌ Unauthorized: No user found for session", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json()
        print(f"📨 Received JSON payload: {data}", flush=True)

        if not data or "lesson_id" not in data:
            print("⚠️ Missing lesson_id in request", flush=True)
            return jsonify({"error": "Missing lesson_id in request"}), 400

        lesson_id = int(data.get("lesson_id"))
        print(f"📘 Parsed lesson_id = {lesson_id}", flush=True)

        if lesson_id <= 0:
            print("❌ lesson_id must be greater than 0", flush=True)
            return jsonify({"error": "Lesson ID must be > 0"}), 400

    except (TypeError, ValueError) as e:
        print(f"❌ Error parsing lesson_id: {e}", flush=True)
        return jsonify({"error": "Invalid lesson ID"}), 400

    print("🔎 Reading stored num_blocks in lesson_content...", flush=True)
    num_blocks_res = fetch_custom(
        "SELECT num_blocks FROM lesson_content WHERE lesson_id = ?", (lesson_id,)
    )
    total_blocks = num_blocks_res[0]["num_blocks"] if num_blocks_res else 0
    print(f"📦 Total lesson_blocks (from num_blocks) = {total_blocks}", flush=True)

    print("🔎 Checking completed blocks by user...", flush=True)
    completed_blocks_res = fetch_custom("""
        SELECT COUNT(*) as count FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ? AND completed = 1
    """, (user_id, lesson_id))
    completed_blocks = completed_blocks_res[0]["count"] if completed_blocks_res else 0
    print(f"✅ User completed blocks = {completed_blocks}", flush=True)

    print(f"🔍 Completion check — user: {user_id}, lesson: {lesson_id}, completed: {completed_blocks}, total: {total_blocks}", flush=True)

    if completed_blocks < total_blocks and total_blocks > 0:
        print("❌ Lesson not fully completed", flush=True)
        return jsonify({"error": "Lesson not fully completed"}), 400

    print("✅ Lesson confirmed as complete 🎉", flush=True)
        # ✅ Update percentage completion to 100%
    print("💾 Updating all progress blocks for this lesson to completed = 1...", flush=True)
    with get_connection() as conn:
        conn.execute("""
            UPDATE lesson_progress SET completed = 1
            WHERE user_id = ? AND lesson_id = ?
        """, (user_id, lesson_id))
        conn.commit()
    print("🔄 Progress entries updated to 100% complete ✅", flush=True)
    return jsonify({"status": "lesson confirmed mplete"}), 200



@lesson_progress_bp.route("/lesson-completed", methods=["POST"])
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

    total_blocks_res = fetch_custom(
        "SELECT COUNT(*) as count FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,)
    )
    total_blocks = total_blocks_res[0]["count"] if total_blocks_res else 0

    completed_blocks_res = fetch_custom("""
        SELECT COUNT(*) as count FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ? AND completed = 1
    """, (user_id, lesson_id))
    completed_blocks = completed_blocks_res[0]["count"] if completed_blocks_res else 0

    completed = total_blocks > 0 and completed_blocks == total_blocks
    return jsonify({"completed": completed})

@lesson_progress_bp.route("/mark-as-completed", methods=["POST"])
def mark_lesson_as_completed():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    lesson_id = data.get("lesson_id")

    if not lesson_id:
        return jsonify({"error": "Missing lesson_id"}), 400

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        # Get total blocks from lesson_content
        row = conn.execute("SELECT num_blocks FROM lesson_content WHERE lesson_id = ?", (lesson_id,)).fetchone()
        total_blocks = row["num_blocks"] if row else 0

        if total_blocks == 0:
            # No blocks — instantly complete
            conn.execute("INSERT INTO results (username, level, correct) VALUES (?, ?, 1)", (user_id, lesson_id))
            conn.commit()
            return jsonify({"status": "completed (no blocks)"}), 200

        # Check completed blocks
        completed = conn.execute("""
            SELECT COUNT(*) as count FROM lesson_progress
            WHERE lesson_id = ? AND user_id = ? AND completed = 1
        """, (lesson_id, user_id)).fetchone()["count"]

        if completed < total_blocks:
            return jsonify({"error": "Lesson is not fully completed"}), 400

        # All blocks completed
        conn.execute("INSERT INTO results (username, level, correct) VALUES (?, ?, 1)", (user_id, lesson_id))
        conn.commit()
        return jsonify({"status": "completed"}), 200

