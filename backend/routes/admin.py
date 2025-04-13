from utils.imports.imports import *

@admin_bp.route("/results", methods=["GET"])
def admin_results():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    results = fetch_custom("""
        SELECT username, level, correct, answer, timestamp
        FROM results
        ORDER BY username ASC, timestamp DESC
    """)
    return jsonify(results)


@admin_bp.route("/lesson-content", methods=["POST"])
def insert_lesson_content():
    print("📥 POST /lesson-content hit", flush=True)

    if not is_admin():
        print("❌ Unauthorized access attempt", flush=True)
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    print("🧾 Received data:", data, flush=True)

    lesson_id = data.get("lesson_id")
    title = data.get("title", "")
    content = data.get("content", "")
    target_user = data.get("target_user")
    published = bool(data.get("published", 0))

    print(f"📝 Inserting lesson_id={lesson_id}, title='{title}', published={published}", flush=True)

    insert_success = insert_row("lesson_content", {
        "lesson_id": lesson_id,
        "title": title,
        "content": content,
        "target_user": target_user,
        "published": published
    })

    if not insert_success:
        print("❌ Failed to insert lesson_content", flush=True)
        return jsonify({"error": "Failed to insert lesson"}), 500

    soup = BeautifulSoup(content, "html.parser")
    block_ids = {el["data-block-id"] for el in soup.select('[data-block-id]') if el.has_attr("data-block-id")}
    print(f"🔍 Extracted block_ids: {block_ids}", flush=True)

    for block_id in block_ids:
        block_inserted = insert_row("lesson_blocks", {
            "lesson_id": lesson_id,
            "block_id": block_id
        })
        print(f"📦 Insert block_id={block_id}: {'✅' if block_inserted else '❌'}", flush=True)

    print("✅ Lesson insertion complete", flush=True)
    return jsonify({"status": "ok"})


@admin_bp.route("/profile-stats", methods=["POST"])
def profile_stats():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    username = request.get_json().get("username", "").strip()
    if not username:
        return jsonify({"error": "Missing username"}), 400

    rows = fetch_custom("""
        SELECT level, correct, answer, timestamp
        FROM results
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (username,))

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

    lessons = fetch_custom("""
        SELECT lesson_id, title, content, target_user, published
        FROM lesson_content
        ORDER BY lesson_id ASC
    """)
    return jsonify(lessons)


@admin_bp.route("/debug-lessons", methods=["GET"])
def debug_lessons():
    return jsonify(fetch_custom("SELECT * FROM lesson_content"))


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["DELETE"])
def delete_lesson(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    try:
        delete_rows("lesson_progress", "lesson_id = ?", (lesson_id,))
        delete_rows("lesson_blocks", "lesson_id = ?", (lesson_id,))
        delete_rows("lesson_content", "lesson_id = ?", (lesson_id,))
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": "Deletion failed", "details": str(e)}), 500


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["GET"])
def get_lesson_by_id(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    lesson = fetch_one_custom("SELECT * FROM lesson_content WHERE lesson_id = ?", (lesson_id,))
    if not lesson:
        return jsonify({"error": "not found"}), 404
    return jsonify(lesson)


@admin_bp.route("/lesson-content/<int:lesson_id>", methods=["PUT"])
def update_lesson_by_id(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json()
    content = inject_block_ids(data.get("content"))

    update_row("lesson_content", {
        "title": data.get("title"),
        "content": content,
        "target_user": data.get("target_user"),
        "published": bool(data.get("published", 0))
    }, "lesson_id = ?", (lesson_id,))

    update_lesson_blocks_from_html(lesson_id, content)
    return jsonify({"status": "updated"})


@admin_bp.route("/lesson-progress-summary", methods=["GET"])
def lesson_progress_summary():
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        lesson_ids = [row["lesson_id"] for row in conn.execute("SELECT DISTINCT lesson_id FROM lesson_content").fetchall()]
        summary = {}

        for lid in lesson_ids:
            total_blocks = conn.execute("SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?", (lid,)).fetchone()["total"]
            if total_blocks == 0:
                summary[lid] = 0
                continue

            users = [row["user_id"] for row in conn.execute("SELECT DISTINCT user_id FROM lesson_progress WHERE lesson_id = ?", (lid,)).fetchall()]
            if not users:
                summary[lid] = 0
                continue

            total_percent = 0
            for uid in users:
                completed = conn.execute("SELECT COUNT(*) FROM lesson_progress WHERE lesson_id = ? AND user_id = ? AND completed = 1", (lid, uid)).fetchone()[0]
                total_percent += (completed / total_blocks) * 100

            summary[lid] = round(total_percent / len(users))

    return jsonify(summary)


@admin_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_individual_lesson_progress(lesson_id):
    if not is_admin():
        return jsonify({"error": "unauthorized"}), 401

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        total_blocks = conn.execute("SELECT COUNT(*) FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,)).fetchone()[0]

        if total_blocks == 0:
            return jsonify([])

        cursor = conn.execute("""
            SELECT user_id, COUNT(*) AS completed_blocks
            FROM lesson_progress
            WHERE lesson_id = ? AND completed = 1
            GROUP BY user_id
        """, (lesson_id,))

        result = [
            {
                "user": row["user_id"],
                "completed": row["completed_blocks"],
                "total": total_blocks,
                "percent": round((row["completed_blocks"] / total_blocks) * 100)
            } for row in cursor.fetchall()
        ]

    return jsonify(result)
