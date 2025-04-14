from utils.imports.imports import *

@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    if request.method == "OPTIONS":
        response = jsonify({'ok': True})
        response.headers.add("Access-Control-Allow-Credentials", "true")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response

    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401
    return jsonify({"username": user})


@auth_bp.route("/role", methods=["GET"])
def get_role():
    session_id = request.cookies.get("session_id")
    print(f"🔍 [role] session_id from cookie: {session_id}", flush=True)

    username = session_manager.get_user(session_id)
    print(f"🧠 [role] resolved username: {username}", flush=True)

    if username is None:
        return jsonify({"msg": "Unauthorized"}), 401

    return jsonify({"role": "admin" if username == "admin" else "user"})



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
