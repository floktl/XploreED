from utils.imports.imports import *

@lesson_progress_bp.route("/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)

    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    with get_session() as db:
        rows = (
            db.query(LessonProgress.block_id, LessonProgress.completed)
            .filter_by(user_id=user_id, lesson_id=lesson_id)
            .all()
        )
        progress = {row.block_id: bool(row.completed) for row in rows}
    return jsonify(progress), 200


@lesson_progress_bp.route("/lesson-progress", methods=["POST"])
def update_lesson_progress():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()

    try:
        lesson_id = int(data.get("lesson_id"))
        block_id = str(data.get("block_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lesson_id or block_id format"}), 400

    if not lesson_id or not block_id:
        return jsonify({"error": "Missing lesson_id or block_id"}), 400

    completed = bool(data.get("completed", False))

    with get_session() as db:
        entry = (
            db.query(LessonProgress)
            .filter_by(user_id=user_id, lesson_id=lesson_id, block_id=block_id)
            .first()
        )
        if entry:
            entry.completed = completed
            entry.updated_at = datetime.datetime.utcnow()
        else:
            entry = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                block_id=block_id,
                completed=completed,
                updated_at=datetime.datetime.utcnow(),
            )
            db.add(entry)
        db.commit()

    return jsonify({"status": "success"}), 200



@lesson_progress_bp.route("/lesson-progress-complete", methods=["POST"])
def mark_lesson_complete():
    session_id = request.cookies.get("session_id")

    user_id = session_manager.get_user(session_id)

    if not user_id:
        print("❌ Unauthorized: No user found for session", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

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

    with get_session() as db:
        total_blocks = db.query(LessonContent.num_blocks).filter_by(lesson_id=lesson_id).first()
        total_blocks = total_blocks[0] if total_blocks else 0

        completed_blocks = (
            db.query(LessonProgress)
            .filter_by(user_id=user_id, lesson_id=lesson_id, completed=True)
            .count()
        )

    if completed_blocks < total_blocks and total_blocks > 0:
        print("❌ Lesson not fully completed", flush=True)
        return jsonify({"error": "Lesson not fully completed"}), 400

    with get_session() as db:
        db.query(LessonProgress).filter_by(
            user_id=user_id, lesson_id=lesson_id
        ).update({"completed": True})
        db.commit()
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

    with get_session() as db:
        total_blocks = db.query(LessonBlock).filter_by(lesson_id=lesson_id).count()
        completed_blocks = (
            db.query(LessonProgress)
            .filter_by(user_id=user_id, lesson_id=lesson_id, completed=True)
            .count()
        )

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

    with get_session() as db:
        total_blocks = db.query(LessonContent.num_blocks).filter_by(lesson_id=lesson_id).first()
        total_blocks = total_blocks[0] if total_blocks else 0

        if total_blocks == 0:
            db.add(Result(username=user_id, level=lesson_id, correct=1))
            db.commit()
            return jsonify({"status": "completed (no blocks)"}), 200

        completed = (
            db.query(LessonProgress)
            .filter_by(lesson_id=lesson_id, user_id=user_id, completed=True)
            .count()
        )

        if completed < total_blocks:
            return jsonify({"error": "Lesson is not fully completed"}), 400

        db.add(Result(username=user_id, level=lesson_id, correct=1))
        db.commit()
        return jsonify({"status": "completed"}), 200

