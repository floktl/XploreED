"""Admin endpoints for viewing results and managing the app."""

from utils.imports.imports import *
from app.extensions import limiter

@admin_bp.route("/check-admin", methods=["GET"])
def check_admin():
    return jsonify({"is_admin": is_admin()})


@admin_bp.route("/results", methods=["GET"])
def admin_results():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    results = select_rows(
        "results",
        columns=["username", "level", "correct", "answer", "timestamp"],
        order_by="username ASC, timestamp DESC",
    )
    return jsonify(results)


@admin_bp.route("/lesson-content", methods=["POST"])
def insert_lesson_content():

    if not is_admin():
        print("❌ Unauthorized access attempt", flush=True)
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()

    lesson_id = data.get("lesson_id")
    title = data.get("title", "")
    content = strip_ai_data(data.get("content", ""))
    target_user = data.get("target_user")
    published = bool(data.get("published", 0))
    ai_enabled = bool(data.get("ai_enabled", 0))

    # 🧽 Extract block_ids from HTML
    soup = BeautifulSoup(content, "html.parser")
    block_ids = {el["data-block-id"] for el in soup.select('[data-block-id]') if el.has_attr("data-block-id")}
    num_blocks = len(block_ids)

    # 🧾 Insert lesson row with num_blocks
    insert_success = insert_row("lesson_content", {
        "lesson_id": lesson_id,
        "title": title,
        "content": content,
        "target_user": target_user,
        "published": published,
        "num_blocks": num_blocks,
        "ai_enabled": ai_enabled
    })

    if not insert_success:
        print("❌ Failed to insert lesson_content", flush=True)
        return jsonify({"error": "Failed to insert lesson"}), 500

    # ➕ Insert individual blocks
    for block_id in block_ids:
        block_inserted = insert_row("lesson_blocks", {
            "lesson_id": lesson_id,
            "block_id": block_id
        })

    return jsonify({"status": "ok"})



@admin_bp.route("/profile-stats", methods=["POST"])
def profile_stats():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    username = request.get_json().get("username", "").strip()
    if not username:
        return jsonify({"error": "Missing username"}), 400

    rows = select_rows(
        "results",
        columns=["level", "correct", "answer", "timestamp"],
        where="username = ?",
        params=(username,),
        order_by="timestamp DESC",
    )

    return jsonify([
        {
            "level": l,
            "correct": bool(c),
            "answer": a,
            "timestamp": t
        } for l, c, a, t in [tuple(row.values()) for row in rows]
    ])


@admin_bp.route("/lesson-content", methods=["GET"])
def get_all_lessons():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    lessons = select_rows(
        "lesson_content",
        columns=[
            "lesson_id",
            "title",
            "content",
            "target_user",
            "published",
            "ai_enabled",
            "num_blocks",
        ],
        order_by="lesson_id ASC",
    )
    return jsonify(lessons)


@admin_bp.route("/debug-lessons", methods=["GET"])
def debug_lessons():
    return jsonify(select_rows("lesson_content"))


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    try:
        delete_rows("lesson_progress", "WHERE lesson_id = ?", (lesson_id,))
        delete_rows("lesson_blocks", "WHERE lesson_id = ?", (lesson_id,))
        delete_rows("lesson_content", "WHERE lesson_id = ?", (lesson_id,))
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": "Deletion failed", "details": str(e)}), 500


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["GET"])
def get_lesson_by_id(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    lesson = select_one(
        "lesson_content",
        where="lesson_id = ?",
        params=(lesson_id,),
    )
    if not lesson:
        return jsonify({"error": "not found"}), 404
    return jsonify(lesson)


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["PUT"])
def update_lesson_by_id(lesson_id):

    if not is_admin():
        print("❌ Not authorized")
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()

    # 🧠 Inject or reassign block IDs into the HTML and strip AI data
    content = inject_block_ids(data.get("content"))
    content = strip_ai_data(content)

    # 🧽 Count block_ids
    soup = BeautifulSoup(content, "html.parser")
    block_ids = {el["data-block-id"] for el in soup.select('[data-block-id]') if el.has_attr("data-block-id")}
    num_blocks = len(block_ids)
    # ✏️ Update the lesson row including num_blocks
    update_row(
        "lesson_content",
        {
            "title": data.get("title"),
            "content": content,
            "target_user": data.get("target_user"),
            "published": bool(data.get("published", 0)),
            "num_blocks": num_blocks,
            "ai_enabled": bool(data.get("ai_enabled", 0)),
        },
        "WHERE lesson_id = ?",
        (lesson_id,),
    )

    # 🔁 Sync lesson_blocks table
    update_lesson_blocks_from_html(lesson_id, content)

    return jsonify({"status": "updated"})

@admin_bp.route("/lesson-progress-summary", methods=["GET"])
def lesson_progress_summary():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    lesson_ids = [row["lesson_id"] for row in select_rows(
        "lesson_content",
        columns="DISTINCT lesson_id",
    )]

    summary = {}
    for lid in lesson_ids:
        row = select_one(
            "lesson_content",
            columns="num_blocks",
            where="lesson_id = ?",
            params=(lid,),
        )
        total_blocks = row.get("num_blocks") if row else 0

        if total_blocks == 0:
            summary[lid] = {"percent": 0, "num_blocks": 0}
            continue

        user_rows = select_rows(
            "lesson_progress",
            columns="DISTINCT user_id",
            where="lesson_id = ?",
            params=(lid,),
        )
        users = [row["user_id"] for row in user_rows]
        if not users:
            summary[lid] = {"percent": 0, "num_blocks": total_blocks}
            continue

        total_percent = 0
        for uid in users:
            completed_row = select_one(
                "lesson_progress",
                columns="COUNT(*) as count",
                where="lesson_id = ? AND user_id = ? AND completed = 1",
                params=(lid, uid),
            )
            completed = completed_row.get("count") if completed_row else 0
            total_percent += (completed / total_blocks) * 100

        summary[lid] = {
            "percent": round(total_percent / len(users)),
            "num_blocks": total_blocks,
        }

    return jsonify(summary)




@admin_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_individual_lesson_progress(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    num_blocks_row = select_one(
        "lesson_content",
        columns="num_blocks",
        where="lesson_id = ?",
        params=(lesson_id,),
    )
    total_blocks = num_blocks_row.get("num_blocks") if num_blocks_row else 0

    if total_blocks == 0:
        return jsonify([])

    rows = select_rows(
        "lesson_progress",
        columns=["user_id", "COUNT(*) AS completed_blocks"],
        where="lesson_id = ? AND completed = 1",
        params=(lesson_id,),
        group_by="user_id",
    )

    result = [
        {
            "user": row["user_id"],
            "completed": row["completed_blocks"],
            "total": total_blocks,
            "percent": round((row["completed_blocks"] / total_blocks) * 100),
        }
        for row in rows
    ]

    return jsonify(result)


@admin_bp.route("/users", methods=["GET"])
def list_users():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401
    rows = select_rows(
        "users",
        columns=["username", "created_at", "skill_level"],
        order_by="username",
    )
    return jsonify(rows)


@admin_bp.route("/users/<string:username>", methods=["PUT"])
def update_user(username):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}
    new_username = data.get("username", username).strip()
    new_password = data.get("password")
    skill = data.get("skill_level")

    if new_username != username and user_exists(new_username):
        return jsonify({"error": "username taken"}), 400

    if new_username != username:
        update_row("users", {"username": new_username}, "username = ?", (username,))
        update_row("results", {"username": new_username}, "username = ?", (username,))
        update_row("vocab_log", {"username": new_username}, "username = ?", (username,))
        update_row("lesson_progress", {"user_id": new_username}, "user_id = ?", (username,))
        update_row("topic_memory", {"username": new_username}, "username = ?", (username,))
        update_row("ai_user_data", {"username": new_username}, "username = ?", (username,))
        update_row("exercise_submissions", {"username": new_username}, "username = ?", (username,))
        session_manager.destroy_user_sessions(username)
        username = new_username

    if new_password:
        hashed = generate_password_hash(new_password)
        update_row("users", {"password": hashed}, "username = ?", (username,))

    if skill is not None:
        update_row("users", {"skill_level": int(skill)}, "username = ?", (username,))

    return jsonify({"status": "updated"})


@admin_bp.route("/users/<string:username>", methods=["DELETE"])
def delete_user(username):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    delete_rows("results", "WHERE username = ?", (username,))
    delete_rows("vocab_log", "WHERE username = ?", (username,))
    delete_rows("topic_memory", "WHERE username = ?", (username,))
    delete_rows("ai_user_data", "WHERE username = ?", (username,))
    delete_rows("exercise_submissions", "WHERE username = ?", (username,))
    delete_rows("lesson_progress", "WHERE user_id = ?", (username,))
    delete_rows("users", "WHERE username = ?", (username,))
    session_manager.destroy_user_sessions(username)
    return jsonify({"status": "deleted"})
