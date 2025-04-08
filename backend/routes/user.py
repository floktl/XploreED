# backend/routes/user.py
from flask import Blueprint, request, jsonify
from session_manager import session_manager
import sqlite3

user_bp = Blueprint("user", __name__, url_prefix="/api")


def get_current_user():
    session_id = request.cookies.get("session_id")
    return session_manager.get_user(session_id)


@user_bp.route("/me", methods=["GET"])
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401
    return jsonify({"username": user})


@user_bp.route("/role", methods=["GET"])
def get_role():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401
    return jsonify({"is_admin": user == "admin"})


@user_bp.route("/profile", methods=["GET"])
def profile():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    results = []
    with sqlite3.connect("user_data.db") as conn:
        for lvl, cor, ans, ts in conn.execute("""
            SELECT level, correct, answer, timestamp
            FROM results
            WHERE username = ?
            ORDER BY timestamp DESC
        """, (user,)):
            results.append({
                "level": lvl,
                "correct": bool(cor),
                "answer": ans,
                "timestamp": ts
            })

    return jsonify(results)


@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    with sqlite3.connect("user_data.db") as conn:
        rows = conn.execute("""
            SELECT vocab, translation FROM vocab_log WHERE username = ?
        """, (user,)).fetchall()

    return jsonify([
        {"vocab": v, "translation": t} for v, t in rows
    ])
