from utils.imports.imports import *
from utils.db_utils import fetch_custom  # Needed for raw SQL queries
from utils.dust_agent.lesson_agent_client import LessonTaskGeneratorClient


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

    rows = fetch_custom("""
        SELECT block_id, completed FROM lesson_progress
        WHERE user_id = ? AND lesson_id = ?
    """, (user, lesson_id))

    progress = {row[0]: bool(row[1]) for row in rows}
    return jsonify(progress)

# generate lesson by ai agent or the user

# @lessons_bp.route("/generate_lesson", methods=["POST"])
# def generate_lesson():
#     session_id = request.cookies.get("session_id")
#     user = session_manager.get_user(session_id)
#     if not user:
#         return jsonify({"msg": "Unauthorized"}), 401

#     data = request.get_json()
#     topic = data.get("topic")
#     level = data.get("level", "intermediate")
#     use_dust = data.get("use_dust", False)

#     if not topic:
#         return jsonify({"error": "Missing topic"}), 400

#     if use_dust:
#         # 🧠 Generate content using Dust AI
#         api_key = os.getenv('DUST_API_KEY')
#         workspace_id = os.getenv('DUST_WORKSPACE_ID')
#         if not api_key or not workspace_id:
#             return jsonify({"error": "Dust API credentials not set"}), 500

#         client = LessonTaskGeneratorClient(api_key, workspace_id)
#         try:
#             html_lesson = client.generate_lesson(topic, level)
#             ai_enabled = True
#         except Exception as e:
#             return jsonify({"error": str(e)}), 500
#     else:
#         # ✍️ Use manual input from the user (expects 'content' in request)
#         html_lesson = data.get("content")
#         if not html_lesson:
#             return jsonify({"error": "Missing content for manual lesson"}), 400
#         ai_enabled = False

#     # 💾 Save to the database
#     try:
#         db = get_db()
#         cursor = db.cursor()
#         cursor.execute("""
#             INSERT INTO lesson_content (title, content, created_at, target_user, num_blocks, ai_enabled, published)
#             VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, 1)
#         """, (topic, html_lesson, user, 1, int(ai_enabled)))  # num_blocks is set to 1 for now
#         db.commit()
#     except Exception as e:
#         return jsonify({"error": "Database error", "details": str(e)}), 500

#     return jsonify({"msg": "Lesson created successfully"})

@lessons_bp.route("/generate-lesson", methods=["POST"])
def generate_lesson():
    session_id = request.cookies.get("session_id")
    user = session_manager.get_user(session_id)
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.json or {}

    title = data.get("title")
    content = data.get("content")
    ai_enabled = bool(data.get("ai_enabled", False))

    if not title and not ai_enabled:
        return jsonify({"msg": "Missing title or ai_enabled"}), 400

    if ai_enabled:
        # Stubbed AI content generation logic
        title = title or "AI Generated Lesson"
        content = content or "This is a placeholder lesson generated by AI."
        # Here you could call your AI service or agent to generate actual content

    now = datetime.utcnow().isoformat()

    success = insert_row("lesson_content", {
        "title": title,
        "content": content,
        "created_at": now,
        "target_user": user,
        "published": 1,
        "num_blocks": 1,
        "ai_enabled": int(ai_enabled),
    })

    if not success:
        return jsonify({"msg": "Failed to create lesson"}), 500

    return jsonify({"msg": "Lesson created", "ai_enabled": ai_enabled})

