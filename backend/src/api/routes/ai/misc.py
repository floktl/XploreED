"""
AI Miscellaneous Routes

This module contains API routes for miscellaneous AI operations including
general AI questions, streaming responses, and chat history management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from flask import request, jsonify # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user
from config.blueprint import ai_bp
from core.database.connection import select_one, select_rows, insert_row
from features.ai.generation.misc_helpers import stream_ai_answer
from external.mistral.client import send_prompt


logger = logging.getLogger(__name__)


@ai_bp.route("/ask-ai", methods=["POST"])
def ask_ai():
    """
    Forward a single question to Mistral and return the answer, with app and user context.

    This endpoint provides contextual AI assistance by including user-specific
    information such as skill level, recent results, vocabulary progress, and
    lesson completion status.

    Returns:
        JSON response with AI answer or error details
    """
    try:
        username = require_user()
        logger.info(f"User {username} asking AI question")

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
        user_row = select_one("users", columns="skill_level", where="username = ?", params=(username,))
        skill_level = user_row.get("skill_level", 0) if user_row else 0

        # Recent results
        results = select_rows(
            "results",
            columns="level, correct, answer, timestamp",
            where="username = ?",
            params=(username,),
            order_by="timestamp DESC",
            limit=5,
        )
        results_summary = ", ".join([
            f"Level {r['level']}: {'correct' if r['correct'] else 'incorrect'} ({r['timestamp']})"
            for r in results
        ]) if results and isinstance(results, list) else "No recent results."

        # Vocab stats
        vocab_count = select_rows(
            "vocab_log", columns="COUNT(*) as count", where="username = ?", params=(username,)
        )
        vocab_total = vocab_count[0]["count"] if vocab_count and isinstance(vocab_count, list) else 0

        # Weakest topics
        weaknesses = select_rows(
            "topic_memory",
            columns="grammar, AVG(quality) AS avg_q",
            where="username = ?",
            params=(username,),
            group_by="grammar",
            order_by="avg_q ASC",
            limit=3,
        )
        weaknesses_summary = ", ".join([
            f"{w['grammar']} ({round((1 - (w['avg_q'] or 0) / 5) * 100)}% weak)" for w in weaknesses
        ]) if weaknesses and isinstance(weaknesses, list) else "No weaknesses detected."

        # Lesson progress (percent complete for last 3 lessons)
        lessons = select_rows(
            "lesson_content",
            columns="lesson_id, title, num_blocks",
            where="published = 1",
            order_by="created_at DESC",
            limit=3,
        )
        lesson_progress = []
        for lesson in (lessons if isinstance(lessons, list) else []):
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
        lesson_progress_summary = "; ".join(lesson_progress) if lesson_progress else "No recent lessons."

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
                "You are a helpful German teacher.",
                {"role": "user", "content": context},
                temperature=0.7,
            )
            if resp.status_code == 200:
                answer = resp.json()["choices"][0]["message"]["content"].strip()
                logger.info(f"Successfully generated AI answer for user {username}")
                return jsonify({"answer": answer})
            else:
                logger.error(f"Mistral API error for user {username}: {resp.status_code}")
                return jsonify({"error": "AI service error"}), 500
        except Exception as e:
            logger.error(f"Failed to get AI answer for user {username}: {e}")
            return jsonify({"error": "AI service error"}), 500

    except ValueError as e:
        logger.error(f"Validation error asking AI: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error asking AI: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ask-ai-stream", methods=["POST"])
def ask_ai_stream():
    """
    Stream AI responses for real-time interaction.

    This endpoint provides streaming AI responses for better user experience
    during longer AI interactions.

    Returns:
        Streaming response with AI answer
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting streaming AI response")

        data = request.get_json() or {}
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "Question required"}), 400

        return stream_ai_answer(question)

    except ValueError as e:
        logger.error(f"Validation error asking AI stream: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error asking AI stream: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/mistral-chat-history", methods=["GET"])
def get_mistral_chat_history():
    """
    Get the chat history for the current user.

    This endpoint retrieves stored chat history for the authenticated user.

    Returns:
        JSON response with chat history or error details
    """
    try:
        username = require_user()
        logger.debug(f"Getting chat history for user {username}")

        history = select_rows(
            "mistral_chat_history",
            columns="id, question, answer, created_at",
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=50,
        )

        return jsonify({"history": history})

    except ValueError as e:
        logger.error(f"Validation error getting chat history: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/mistral-chat-history", methods=["POST"])
def add_mistral_chat_history():
    """
    Add a new chat entry to the user's history.

    This endpoint stores a new question-answer pair in the user's chat history
    for future reference.

    Returns:
        JSON response with success status or error details
    """
    try:
        username = require_user()
        logger.info(f"Adding chat history for user {username}")

        data = request.get_json() or {}
        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()

        if not question or not answer:
            return jsonify({"error": "Question and answer required"}), 400

        insert_row(
            "mistral_chat_history",
            {
                "username": username,
                "question": question,
                "answer": answer,
            },
        )

        logger.info(f"Successfully added chat history for user {username}")
        return jsonify({"success": True})

    except ValueError as e:
        logger.error(f"Validation error adding chat history: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding chat history: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/ask-ai-context", methods=["POST"])
def ask_ai_context():
    """
    Ask AI with additional context information.

    This endpoint allows users to ask AI questions with additional context
    that can be used to provide more relevant answers.

    Returns:
        JSON response with AI answer or error details
    """
    try:
        username = require_user()
        logger.info(f"User {username} asking AI question with context")

        data = request.get_json() or {}
        question = data.get("question", "").strip()
        context_raw = data.get("context", "")

        # Handle context - it could be a string or an object
        if isinstance(context_raw, dict):
            # If context is an object, convert it to a string representation
            context = str(context_raw)
        else:
            # If context is already a string, use it as is
            context = str(context_raw).strip()

        if not question:
            return jsonify({"error": "Question required"}), 400

        # Combine question with context
        full_question = f"{context}\n\nQuestion: {question}" if context else question

        try:
            resp = send_prompt(
                "You are a helpful German teacher.",
                {"role": "user", "content": full_question},
                temperature=0.7,
            )
            if resp.status_code == 200:
                answer = resp.json()["choices"][0]["message"]["content"].strip()
                logger.info(f"Successfully generated contextual AI answer for user {username}")
                return jsonify({"answer": answer})
            else:
                logger.error(f"Mistral API error for user {username}: {resp.status_code}")
                return jsonify({"error": "AI service error"}), 500
        except Exception as e:
            logger.error(f"Failed to get contextual AI answer for user {username}: {e}")
            return jsonify({"error": "AI service error"}), 500

    except ValueError as e:
        logger.error(f"Validation error asking AI with context: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error asking AI with context: {e}")
        return jsonify({"error": "Server error"}), 500
