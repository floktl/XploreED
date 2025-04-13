from utils.imports.imports import *

@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    if request.method == "OPTIONS":
        response = jsonify({'ok': True})
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response

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

    rows = fetch_custom("""
        SELECT level, correct, answer, timestamp
        FROM results
        WHERE username = ?
        ORDER BY timestamp DESC
    """, (user,))

    results = [
        {
            "level": row["level"],
            "correct": bool(row["correct"]),
            "answer": row["answer"],
            "timestamp": row["timestamp"]
        } for row in rows
    ] if rows else []

    return jsonify(results)


@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_custom("""
        SELECT vocab, translation FROM vocab_log WHERE username = ?
    """, (user,))

    return jsonify([
        {"vocab": row["vocab"], "translation": row["translation"]}
        for row in rows
    ]) if rows else []
