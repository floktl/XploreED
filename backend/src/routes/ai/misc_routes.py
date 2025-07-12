"""Miscellaneous AI endpoints."""

import traceback
import logging
from flask import request, jsonify

from . import ai_bp
from utils.helpers.helper import require_user
from utils.ai.ai_api import send_prompt
from .helpers.misc_helpers import stream_ai_answer
from database import select_rows, insert_row, select_one


MAX_CHAT_HISTORY = 10  # Limit the number of chat history messages sent to the AI
MAX_CHAT_HISTORY_STORAGE = 50  # Limit the number of chat messages stored per user


def format_page_context(page_context):
    if not page_context:
        return None
    if isinstance(page_context, dict) and page_context.get("page") == "ai-feedback":
        feedback = page_context.get("feedback")
        exercises = page_context.get("exercises")
        answers = page_context.get("answers")
        lines = ["---\n**Current AI Feedback Context:**"]
        if feedback:
            lines.append(f"\n**Feedback summary:**\n{feedback}")
        if exercises:
            lines.append("\n**Exercises:**")
            for i, ex in enumerate(exercises, 1):
                q = ex.get("question", "")
                user_ans = answers.get(str(ex.get("id")), "") if answers else ""
                correct = ex.get("correctAnswer", "")
                lines.append(f"{i}. {q}\n   Your answer: {user_ans}\n   Correct answer: {correct}")
        return "\n".join(lines)
    # fallback: just str()
    return str(page_context)


@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():
    """Forward a single question to Mistral and return the answer, with app and user context."""
    username = require_user()

    data = request.get_json() or {}
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question required"}), 400

    page_context = data.get("pageContext")
    formatted_page_context = format_page_context(page_context)

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
        (f"If there is a 'Current AI Feedback Context' below, use it to answer the user's question as specifically as possible.\n\n{formatted_page_context}\n\n" if formatted_page_context else "") +
        f"App info: {app_knowledge}\n"
        f"User info: Skill level: {skill_level}. "
        f"Recent results: {results_summary}. "
        f"Vocab words: {vocab_total}. "
        f"Weakest topics: {weaknesses_summary}. "
        f"Lesson progress: {lesson_progress_summary}. "
        f"User question: {question}"
    )

    print("[ask-ai] Full AI prompt:\n" + context, flush=True)
    try:
        resp = send_prompt(
            "You are an assistant for the XplorED app. Use the app and user info to answer questions about the platform, features, or user progress. Always be helpful and specific.",
            {"role": "user", "content": context},
            temperature=0.3,
        )
        # Detailed debug log of raw Mistral response
        try:
            resp_json = resp.json()
        except Exception as ex:
            print("[ask-ai] ERROR: Could not parse JSON from Mistral response:", ex, flush=True)
            print("[ask-ai] Raw response text:", resp.text, flush=True)
            raise
        print("[ask-ai] Raw Mistral response:", resp_json, flush=True)
        if resp.status_code == 200:
            answer = resp.json()["choices"][0]["message"]["content"].strip()
            # Fix: never save empty/null answer to chat history
            if not answer:
                answer = "[No answer returned by AI]"
            return jsonify({"answer": answer})
    except Exception as e:
        logging.error("=== AI ERROR in /ask-ai ===")
        logging.error("Error type: %s", type(e).__name__)
        logging.error("Error message: %s", str(e))
        logging.error("User: %s", username)
        logging.error("Question: %s", question)
        logging.error("Page context: %s", page_context)
        logging.error("Full stack trace:\n%s", traceback.format_exc())
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

    page_context = data.get("pageContext")
    formatted_page_context = format_page_context(page_context)

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
        (f"If there is a 'Current AI Feedback Context' below, use it to answer the user's question as specifically as possible.\n\n{formatted_page_context}\n\n" if formatted_page_context else "") +
        f"App info: {app_knowledge}\n"
        f"User info: Skill level: {skill_level}. "
        f"Recent results: {results_summary}. "
        f"Vocab words: {vocab_total}. "
        f"Weakest topics: {weaknesses_summary}. "
        f"Lesson progress: {lesson_progress_summary}. "
        + (f"Page context: {formatted_page_context}\n" if formatted_page_context else "")
        + f"User question: {question}"
    )

    print("[ask-ai-stream] Full AI prompt:\n" + context, flush=True)
    return stream_ai_answer(context)


@ai_bp.route("/mistral-chat-history", methods=["GET"])
def get_mistral_chat_history():
    """Get chat history for the current user."""
    username = require_user()

    # If you want to include chat history in the AI prompt, fetch only the most recent MAX_CHAT_HISTORY messages:
    # chat_history = select_rows(
    #     "mistral_chat_history",
    #     columns=["question", "answer", "created_at"],
    #     where="username = ?",
    #     params=(username,),
    #     order_by="created_at DESC",
    #     limit=MAX_CHAT_HISTORY
    # )
    # Then include chat_history in the prompt construction as needed.
    rows = select_rows(
        "mistral_chat_history",
        columns=["id", "question", "answer", "created_at"],
        where="username = ?",
        params=(username,),
        order_by="created_at DESC",
        limit=20
    )

    return jsonify(rows if rows else [])


@ai_bp.route("/mistral-chat-history", methods=["POST"])
def add_mistral_chat_history():
    """Add a new chat entry."""
    username = require_user()
    data = request.get_json()

    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()

    # Fix: always allow saving, even if answer is empty/null, but store a placeholder
    if not question:
        return jsonify({"error": "Missing question"}), 400
    if not answer:
        answer = "[No answer returned by AI]"

    try:
        success = insert_row("mistral_chat_history", {
            "username": username,
            "question": question,
            "answer": answer
        })

        if not success:
            logging.error("=== CHAT HISTORY SAVE ERROR ===")
            logging.error("User: %s", username)
            logging.error("Question: %s", question)
            logging.error("Answer: %s", answer)
            logging.error("Insert operation returned False")
            return jsonify({"error": "Failed to save chat history"}), 500

        # After successful insert, delete older messages if over limit
        # Keep only the most recent MAX_CHAT_HISTORY_STORAGE messages
        rows = select_rows(
            "mistral_chat_history",
            columns=["id"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
        )
        if rows and len(rows) > MAX_CHAT_HISTORY_STORAGE:
            # Get ids to delete (all except the newest MAX_CHAT_HISTORY_STORAGE)
            ids_to_delete = [row["id"] for row in rows[MAX_CHAT_HISTORY_STORAGE:]]
            if ids_to_delete:
                from database import delete_rows
                delete_rows(
                    "mistral_chat_history",
                    where="id IN ({})".format(",".join([str(i) for i in ids_to_delete]))
                )

        return jsonify({"status": "saved"})
    except Exception as e:
        logging.error("=== CHAT HISTORY SAVE EXCEPTION ===")
        logging.error("Error type: %s", type(e).__name__)
        logging.error("Error message: %s", str(e))
        logging.error("User: %s", username)
        logging.error("Question: %s", question)
        logging.error("Answer: %s", answer)
        logging.error("Full stack trace:\n%s", traceback.format_exc())
        return jsonify({"error": "Failed to save chat history"}), 500
