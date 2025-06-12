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

    rows = fetch_custom(
        """
        SELECT vocab, translation FROM vocab_log WHERE username = ?
        """,
        (user,),
    )

    return jsonify([
        {"vocab": row["vocab"], "translation": row["translation"]}
        for row in rows
    ]) if rows else []


@user_bp.route("/vocab-train", methods=["GET", "POST"])
def vocab_train():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        row = fetch_one_custom(
            "SELECT rowid as id, vocab, translation FROM vocab_log "
            "WHERE username = ? AND datetime(next_review) <= datetime('now') "
            "ORDER BY next_review ASC LIMIT 1",
            (user,),
        )
        return jsonify(row or {})

    data = request.get_json() or {}
    rowid = data.get("id")
    quality = int(data.get("quality", 0))
    if rowid is None:
        return jsonify({"msg": "Missing id"}), 400

    row = fetch_one_custom(
        "SELECT ef, repetitions, interval_days FROM vocab_log WHERE rowid = ? AND username = ?",
        (rowid, user),
    )
    if not row:
        return jsonify({"msg": "Not found"}), 404

    ef = row.get("ef", 2.5)
    reps = row.get("repetitions", 0)
    interval = row.get("interval_days", 1)

    if quality < 3:
        reps = 0
        interval = 1
    else:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        reps += 1
        ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    next_review = (datetime.datetime.now() + datetime.timedelta(days=interval)).isoformat()

    update_row(
        "vocab_log",
        {
            "ef": ef,
            "repetitions": reps,
            "interval_days": interval,
            "next_review": next_review,
        },
        "rowid = ? AND username = ?",
        (rowid, user),
    )

    return jsonify({"msg": "updated"})
