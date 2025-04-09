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
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT block_id, completed FROM lesson_progress
                WHERE user_id = ? AND lesson_id = ?
            """, (user_id, lesson_id))
            progress = {row[0]: bool(row[1]) for row in cursor.fetchall()}
        return jsonify(progress), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch progress", "details": str(e)}), 500


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
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to update progress", "details": str(e)}), 500

@lesson_progress_bp.route("/api/lesson-progress-complete", methods=["POST"])
def mark_lesson_complete():
    session_id = request.cookies.get("session_id")
    user_id = session_manager.get_user(session_id)
    if not user_id:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json()
    lesson_id = data.get("lesson_id")

    if not lesson_id:
        return jsonify({"error": "Missing lesson_id"}), 400

    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id FROM results
                WHERE username = ? AND level = ?
            """, (user_id, lesson_id))
            row = cursor.fetchone()

            if row:
                cursor.execute("""
                    UPDATE results
                    SET correct = 1, timestamp = ?
                    WHERE id = ?
                """, (datetime.datetime.utcnow(), row[0]))
            else:
                cursor.execute("""
                    INSERT INTO results (username, level, correct, timestamp)
                    VALUES (?, ?, 1, ?)
                """, (user_id, lesson_id, datetime.datetime.utcnow()))

            conn.commit()

        return jsonify({"status": "lesson marked as completed"}), 200

    except Exception as e:
        return jsonify({"error": "Failed to mark lesson complete", "details": str(e)}), 500

