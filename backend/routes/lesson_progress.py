from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from session_manager import session_manager
import sqlite3
import datetime

lesson_progress_bp = Blueprint("lesson_progress", __name__)

DB = "user_data.db"

@lesson_progress_bp.route("/api/lesson-progress/<int:lesson_id>", methods=["GET"])
def get_lesson_progress(lesson_id):
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    print("🔍 GET lesson progress — session:", session_id, flush=True)
    print("👤 user_id:", user_id, flush=True)
    print("📘 lesson_id:", lesson_id, flush=True)

    if not user_id:
        print("❌ Unauthorized access (no user_id)", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT block_id, completed FROM lesson_progress
                WHERE user_id = ? AND lesson_id = ?
            """, (user_id, lesson_id))
            progress = {row[0]: bool(row[1]) for row in cursor.fetchall()}
        print("✅ Progress fetched:", progress, flush=True)
        return jsonify(progress), 200
    except Exception as e:
        print("❌ DB Error while fetching progress:", str(e), flush=True)
        return jsonify({"error": "Failed to fetch progress", "details": str(e)}), 500


@lesson_progress_bp.route("/api/lesson-progress", methods=["POST"])
def update_lesson_progress():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    print("🔧 UPDATE lesson progress — session:", session_id, flush=True)
    print("👤 user_id:", user_id, flush=True)

    if not user_id:
        print("❌ Unauthorized access (no user_id)", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    print("📥 Received data:", data, flush=True)

    lesson_id = data.get("lesson_id")
    block_id = data.get("block_id")
    completed = data.get("completed", False)

    if not lesson_id or not block_id:
        print("❌ Missing lesson_id or block_id", flush=True)
        return jsonify({"error": "Missing lesson_id or block_id"}), 400

    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lesson_progress (user_id, lesson_id, block_id, completed, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, lesson_id, block_id)
                DO UPDATE SET completed = excluded.completed, updated_at = excluded.updated_at
            """, (user_id, lesson_id, block_id, int(completed), datetime.datetime.utcnow()))
            conn.commit()
        print("✅ Progress updated successfully", flush=True)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("❌ DB Error while updating progress:", str(e), flush=True)
        return jsonify({"error": "Failed to update progress", "details": str(e)}), 500


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

    try:
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row

            # Count total blocks in lesson
            total_blocks = conn.execute("""
                SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?
            """, (lesson_id,)).fetchone()["total"]

            # Count completed blocks by this user
            completed_blocks = conn.execute("""
                SELECT COUNT(*) FROM lesson_progress
                WHERE user_id = ? AND lesson_id = ? AND completed = 1
            """, (user_id, lesson_id)).fetchone()[0]

            if total_blocks > 0 and completed_blocks < total_blocks:
                return jsonify({"error": "Lesson not fully completed"}), 400

            # Optional: Write to a `lesson_completed` table instead (future-proof)
            # Or just let frontend track completed if 100%

            print(f"✅ Lesson {lesson_id} marked complete for user {user_id}", flush=True)
            return jsonify({"status": "lesson confirmed as complete"}), 200

    except Exception as e:
        return jsonify({"error": "Failed to verify completion", "details": str(e)}), 500



@lesson_progress_bp.route("/api/lesson-completed", methods=["POST"])
def check_lesson_marked_complete():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    print("🔎 Check if lesson is completed — session:", session_id, flush=True)
    print("👤 user_id:", user_id, flush=True)

    if not user_id:
        print("❌ Unauthorized", flush=True)
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        lesson_id = int(request.get_json().get("lesson_id"))
        print("📘 lesson_id to check:", lesson_id, flush=True)
        if lesson_id <= 0:
            print("❌ Invalid lesson ID", flush=True)
            return jsonify({"error": "Lesson ID must be > 0"}), 400
    except (TypeError, ValueError) as e:
        print("❌ Error parsing lesson ID:", str(e), flush=True)
        return jsonify({"error": "Invalid lesson ID"}), 400

    try:
        with sqlite3.connect("user_data.db") as conn:
            conn.row_factory = sqlite3.Row

            # Count total blocks in lesson
            total_blocks = conn.execute("""
                SELECT COUNT(*) as total FROM lesson_blocks WHERE lesson_id = ?
            """, (lesson_id,)).fetchone()["total"]

            # Count completed blocks by this user
            completed_blocks = conn.execute("""
                SELECT COUNT(*) FROM lesson_progress
                WHERE user_id = ? AND lesson_id = ? AND completed = 1
            """, (user_id, lesson_id)).fetchone()[0]

            print("📦 total_blocks:", total_blocks, "| ✅ completed_blocks:", completed_blocks, flush=True)

            completed = total_blocks > 0 and completed_blocks == total_blocks
            print("✅ Completion status:", completed, flush=True)

            return jsonify({"completed": completed})

    except Exception as e:
        print("❌ DB error while checking completion:", str(e), flush=True)
        return jsonify({"error": "Database error", "details": str(e)}), 500
