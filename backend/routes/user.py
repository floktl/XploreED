"""User account and vocabulary related routes."""

from utils.imports.imports import *


@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    if request.method == "OPTIONS":
        response = jsonify({"ok": True})
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

    rows = fetch_custom(
        """
        SELECT level, correct, answer, timestamp
        FROM results
        WHERE username = ?
        ORDER BY timestamp DESC
    """,
        (user,),
    )

    results = (
        [
            {
                "level": row["level"],
                "correct": bool(row["correct"]),
                "answer": row["answer"],
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]
        if rows
        else []
    )

    return jsonify(results)


@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_custom(
        """
        SELECT rowid as id, vocab, translation, word_type, article, next_review, created_at, context, exercise
        FROM vocab_log
        WHERE username = ?
        ORDER BY datetime(next_review) ASC
        """,
        (user,),
    )

    return (
        jsonify(
            [
                {
                    "id": row["id"],
                    "vocab": row["vocab"],
                    "translation": row["translation"],
                    "word_type": row.get("word_type"),
                    "article": row.get("article"),
                    "next_review": row.get("next_review"),
                    "created_at": row.get("created_at"),
                    "context": row.get("context"),
                    "exercise": row.get("exercise"),
                }
                for row in rows
            ]
        )
        if rows
        else []
    )


@user_bp.route("/vocab-train", methods=["GET", "POST"])
def vocab_train():
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        row = fetch_one_custom(
            "SELECT rowid as id, vocab, translation, word_type, article FROM vocab_log "
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

    ef, reps, interval = sm2(quality, ef, reps, interval)

    next_review = (
        datetime.datetime.now() + datetime.timedelta(days=interval)
    ).isoformat()

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


@user_bp.route("/save-vocab", methods=["POST"])
def save_vocab_words():
    """Save a list of German words to the user's vocabulary."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    words = data.get("words", [])
    context = data.get("context")
    exercise = data.get("exercise")

    tokens = []
    if isinstance(words, str):
        tokens = extract_words(words)
    else:
        for w in words:
            tokens.extend(extract_words(str(w)))

    for word, art in tokens:
        save_vocab(user, word, context=context, exercise=exercise, article=art)

    return jsonify({"saved": len(tokens)})


@user_bp.route("/topic-memory", methods=["GET"])
def get_topic_memory():
    """Return all topic memory entries for the logged in user."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_custom(
        """
        SELECT id, grammar, topic, skill_type, context, lesson_content_id, ease_factor,
               intervall, next_repeat, repetitions, last_review, correct,
               quality
        FROM topic_memory
        WHERE username = ?
        ORDER BY datetime(next_repeat) ASC
        """,
        (user,),
    )

    return jsonify(rows if rows else [])


@user_bp.route("/topic-memory", methods=["DELETE"])
def clear_topic_memory_route():
    """Delete all topic memory entries for the logged in user."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    delete_rows("topic_memory", "WHERE username = ?", (user,))
    return jsonify({"msg": "cleared"})


@user_bp.route("/topic-weaknesses", methods=["GET"])
def topic_weaknesses():
    """Return the three weakest grammar topics for the logged in user."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = fetch_custom(
        """
        SELECT grammar, AVG(quality) AS avg_q
        FROM topic_memory
        WHERE username = ?
        GROUP BY grammar
        ORDER BY avg_q ASC
        LIMIT 3
        """,
        (user,),
    )

    weaknesses = [
        {
            "grammar": row.get("grammar") or "unknown",
            "percent": round((1 - (row.get("avg_q") or 0) / 5) * 100),
        }
        for row in rows
    ] if rows else []
    return jsonify(weaknesses)


@user_bp.route("/user-level", methods=["GET", "POST"])
def user_level():
    """Get or update the logged in user's skill level."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        row = fetch_one("users", "WHERE username = ?", (user,))
        level = row.get("skill_level", 0) if row else 0
        return jsonify({"level": level})

    data = request.get_json() or {}
    level = int(data.get("level", 0))
    update_row("users", {"skill_level": level}, "username = ?", (user,))
    return jsonify({"msg": "updated", "level": level})
