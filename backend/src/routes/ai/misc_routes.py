"""Miscellaneous AI endpoints."""

from flask import request, jsonify

from . import ai_bp
from utils.helpers.helper import require_user
from utils.ai.ai_api import send_prompt
from .helpers.misc_helpers import stream_ai_answer
from database import select_rows, insert_row, select_one


@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():
    """Forward a single question to Mistral and return the answer, with app and user context."""
    username = require_user()

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    # --- Static app knowledge ---
    app_knowledge = (
        "XplorED is a German learning platform. Features include: "
        "user management, AI-powered exercises (gap-fills, translations, sentence ordering), "
        "vocab trainer with spaced repetition, lesson progress tracking, skill levels, feedback, and admin tools. "
        "You can ask about your progress, how to use features, or for feedback on your learning."
    )

    # --- Dynamic user data ---
    # Skill level
    user_row = select_one("users", columns=["skill_level"], where="username = ?", params=(username,))
    skill_level = user_row.get("skill_level", 0) if user_row else 0

    # Recent results
    results = select_rows(
        "results",
        columns=["level", "correct", "answer", "timestamp"],
        where="username = ?",
        params=(username,),
        order_by="timestamp DESC",
        limit=5,
    )
    results_summary = ", ".join([
        f"Level {r['level']}: {'correct' if r['correct'] else 'incorrect'} ({r['timestamp']})"
        for r in results
    ]) or "No recent results."

    # Vocab stats
    vocab_count = select_rows(
        "vocab_log", columns=["COUNT(*) as count"], where="username = ?", params=(username,)
    )
    vocab_total = vocab_count[0]["count"] if vocab_count else 0

    # Weakest topics
    weaknesses = select_rows(
        "topic_memory",
        columns=["grammar", "AVG(quality) AS avg_q"],
        where="username = ?",
        params=(username,),
        group_by="grammar",
        order_by="avg_q ASC",
        limit=3,
    )
    weaknesses_summary = ", ".join([
        f"{w['grammar']} ({round((1 - (w['avg_q'] or 0) / 5) * 100)}% weak)" for w in weaknesses
    ]) or "No weaknesses detected."

    # Lesson progress (percent complete for last 3 lessons)
    lessons = select_rows(
        "lesson_content",
        columns=["lesson_id", "title", "num_blocks"],
        where="published = 1",
        order_by="created_at DESC",
        limit=3,
    )
    lesson_progress = []
    for lesson in lessons:
        lid = lesson["lesson_id"]
        total_blocks = lesson.get("num_blocks") or 0
        completed_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="lesson_id = ? AND user_id = ? AND completed = 1",
            params=(lid, username),
        )
        completed_blocks = completed_row.get("count") if completed_row else 0
        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks else 100
        lesson_progress.append(f"{lesson['title']}: {percent_complete}% complete")
    lesson_progress_summary = "; ".join(lesson_progress) or "No recent lessons."

    # --- Build context-aware prompt ---
    context = (
        f"App info: {app_knowledge}\n"
        f"User info: Skill level: {skill_level}. "
        f"Recent results: {results_summary}. "
        f"Vocab words: {vocab_total}. "
        f"Weakest topics: {weaknesses_summary}. "
        f"Lesson progress: {lesson_progress_summary}. "
        f"User question: {question}"
    )

    try:
        resp = send_prompt(
            "You are an assistant for the XplorED app. Use the app and user info to answer questions about the platform, features, or user progress. Always be helpful and specific.",
            {"role": "user", "content": context},
            temperature=0.3,
        )
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"].strip()
            return jsonify({"answer": answer})
    except Exception as e:
        print("[ask_ai] Error:", e, flush=True)

    return jsonify({"error": "AI error"}), 500


@ai_bp.route("/ask-ai-stream", methods=["POST"])
def ask_ai_stream():
    """Stream a long AI answer back to the client, with app and user context."""
    username = require_user()

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    # --- Static app knowledge ---
    app_knowledge = (
        "XplorED is a German learning platform. Features include: "
        "user management, AI-powered exercises (gap-fills, translations, sentence ordering), "
        "vocab trainer with spaced repetition, lesson progress tracking, skill levels, feedback, and admin tools. "
        "You can ask about your progress, how to use features, or for feedback on your learning."
    )

    # --- Dynamic user data ---
    user_row = select_one("users", columns=["skill_level"], where="username = ?", params=(username,))
    skill_level = user_row.get("skill_level", 0) if user_row else 0

    results = select_rows(
        "results",
        columns=["level", "correct", "answer", "timestamp"],
        where="username = ?",
        params=(username,),
        order_by="timestamp DESC",
        limit=5,
    )
    results_summary = ", ".join([
        f"Level {r['level']}: {'correct' if r['correct'] else 'incorrect'} ({r['timestamp']})"
        for r in results
    ]) or "No recent results."

    vocab_count = select_rows(
        "vocab_log", columns=["COUNT(*) as count"], where="username = ?", params=(username,)
    )
    vocab_total = vocab_count[0]["count"] if vocab_count else 0

    weaknesses = select_rows(
        "topic_memory",
        columns=["grammar", "AVG(quality) AS avg_q"],
        where="username = ?",
        params=(username,),
        group_by="grammar",
        order_by="avg_q ASC",
        limit=3,
    )
    weaknesses_summary = ", ".join([
        f"{w['grammar']} ({round((1 - (w['avg_q'] or 0) / 5) * 100)}% weak)" for w in weaknesses
    ]) or "No weaknesses detected."

    lessons = select_rows(
        "lesson_content",
        columns=["lesson_id", "title", "num_blocks"],
        where="published = 1",
        order_by="created_at DESC",
        limit=3,
    )
    lesson_progress = []
    for lesson in lessons:
        lid = lesson["lesson_id"]
        total_blocks = lesson.get("num_blocks") or 0
        completed_row = select_one(
            "lesson_progress",
            columns="COUNT(*) as count",
            where="lesson_id = ? AND user_id = ? AND completed = 1",
            params=(lid, username),
        )
        completed_blocks = completed_row.get("count") if completed_row else 0
        percent_complete = int((completed_blocks / total_blocks) * 100) if total_blocks else 100
        lesson_progress.append(f"{lesson['title']}: {percent_complete}% complete")
    lesson_progress_summary = "; ".join(lesson_progress) or "No recent lessons."

    context = (
        f"App info: {app_knowledge}\n"
        f"User info: Skill level: {skill_level}. "
        f"Recent results: {results_summary}. "
        f"Vocab words: {vocab_total}. "
        f"Weakest topics: {weaknesses_summary}. "
        f"Lesson progress: {lesson_progress_summary}. "
        f"User question: {question}"
    )

    return stream_ai_answer(context)


@ai_bp.route("/mistral-chat-history", methods=["GET"])
def get_mistral_chat_history():
    """Get chat history for the current user."""
    username = require_user()

    rows = select_rows(
        "mistral_chat_history",
        columns=["id", "question", "answer", "created_at"],
        where="username = ?",
        params=(username,),
        order_by="created_at DESC",
        limit=50
    )

    return jsonify(rows if rows else [])


@ai_bp.route("/mistral-chat-history", methods=["POST"])
def add_mistral_chat_history():
    """Add a new chat entry."""
    username = require_user()
    data = request.get_json()

    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()

    if not question or not answer:
        return jsonify({"error": "Missing question or answer"}), 400

    success = insert_row("mistral_chat_history", {
        "username": username,
        "question": question,
        "answer": answer
    })

    if not success:
        return jsonify({"error": "Failed to save chat history"}), 500

    return jsonify({"status": "saved"})
