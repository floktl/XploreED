"""User account and vocabulary related routes."""

from app.imports.imports import *
from routes.user_helpers import (
    fetch_vocab_entries,
    select_vocab_word_due_for_review,
    update_vocab_after_review,
)


@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    """Return the username of the current session."""
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
    """Return whether the logged in user is an admin."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401
    return jsonify({"is_admin": user == "admin"})


@user_bp.route("/profile", methods=["GET"])
def profile():
    """Return recent game results for the current user."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = select_rows(
        "results",
        columns=["level", "correct", "answer", "timestamp"],
        where="username = ?",
        params=(user,),
        order_by="timestamp DESC",
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
    """Return the user's vocabulary list ordered by next review date."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    entries = fetch_vocab_entries(user)
    return jsonify(entries)


@user_bp.route("/vocab-train", methods=["GET", "POST"])
def vocab_train():
    """Serve spaced repetition training data and record reviews."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        row = select_vocab_word_due_for_review(user)
        return jsonify(row or {})

    data = request.get_json() or {}
    rowid = data.get("id")
    quality = int(data.get("quality", 0))
    if rowid is None:
        return jsonify({"msg": "Missing id"}), 400

    if not update_vocab_after_review(rowid, user, quality):
        return jsonify({"msg": "Not found"}), 404

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

    seen: set[str] = set()
    for word, art in tokens:
        canonical = save_vocab(user, word, context=context, exercise=exercise, article=art)
        if canonical:
            seen.add(canonical)

    return jsonify({"saved": len(seen)})


@user_bp.route("/vocabulary/<int:vocab_id>", methods=["DELETE"])
def delete_vocab_word(vocab_id: int):
    """Delete a single vocabulary entry for the logged in user."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    delete_rows("vocab_log", "WHERE rowid = ? AND username = ?", (vocab_id, user))
    return jsonify({"msg": "deleted"})


@user_bp.route("/vocabulary/<int:vocab_id>/report", methods=["POST"])
def report_vocab_word(vocab_id: int):
    """Send a report message about a vocabulary entry."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    row = select_one(
        "vocab_log",
        columns=["vocab", "translation", "article", "word_type"],
        where="rowid = ? AND username = ?",
        params=(vocab_id, user),
    )
    if not row:
        return jsonify({"msg": "Not found"}), 404

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message required"}), 400

    content = (
        "Vocab Report\n"
        f"ID: {vocab_id}\n"
        f"Word: {row.get('vocab')}\n"
        f"Translation: {row.get('translation')}\n"
        f"Article: {row.get('article') or ''}\n"
        f"Type: {row.get('word_type') or ''}\n"
        f"Message: {message}"
    )

    insert_row("support_feedback", {"message": content})
    return jsonify({"status": "ok"})


@user_bp.route("/topic-memory", methods=["GET"])
def get_topic_memory():
    """Return all topic memory entries for the logged in user."""
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    rows = select_rows(
        "topic_memory",
        columns=[
            "id",
            "grammar",
            "topic",
            "skill_type",
            "context",
            "lesson_content_id",
            "ease_factor",
            "intervall",
            "next_repeat",
            "repetitions",
            "last_review",
            "correct",
            "quality",
        ],
        where="username = ?",
        params=(user,),
        order_by="datetime(next_repeat) ASC",
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

    rows = select_rows(
        "topic_memory",
        columns=["grammar", "AVG(quality) AS avg_q"],
        where="username = ?",
        params=(user,),
        group_by="grammar",
        order_by="avg_q ASC",
        limit=3,
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
