from utils.imports.imports import *

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

    rows = fetch_all("""
        SELECT level, correct, answer, timestamp
        FROM results
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (user,))

    results = [
        {
            "level": lvl,
            "correct": bool(cor),
            "answer": ans,
            "timestamp": ts
        } for lvl, cor, ans, ts in rows
    ]

    return jsonify(results)

@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_all("""
        SELECT vocab, translation FROM vocab_log WHERE username = ?
    """, (user,))

    return jsonify([
        {"vocab": v, "translation": t} for v, t in rows
    ])