"""
User Account and Vocabulary Routes

This module contains API routes for user account management, profile data,
and vocabulary operations. All business logic has been moved to appropriate
helper modules to maintain separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
from typing import Dict, Any

from core.services.import_service import *
from features.user.vocabulary_helpers import (
    lookup_vocabulary_word,
    search_vocabulary_with_ai,
    get_user_vocabulary_entries,
    delete_user_vocabulary,
    delete_specific_vocabulary
)
from features.ai.generation.user_helpers import select_vocab_word_due_for_review, update_vocab_after_review


logger = logging.getLogger(__name__)


@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    """
    Return the username of the current session.

    Returns:
        JSON response with username or unauthorized error
    """
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
    """
    Return whether the logged in user is an admin.

    Returns:
        JSON response with admin status or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    return jsonify({"is_admin": user == "admin"})


@user_bp.route("/profile", methods=["GET"])
def profile():
    """
    Return recent game results for the current user.

    Returns:
        JSON response with user's recent results or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        rows = select_rows(
            "results",
            columns="level, correct, answer, timestamp",
            where="username = ?",
            params=(user,),
            order_by="timestamp DESC",
        )

        results = [
            {
                "level": row["level"],
                "correct": bool(row["correct"]),
                "answer": row["answer"],
                "timestamp": row["timestamp"],
            }
            for row in (rows if isinstance(rows, list) else [])
        ]

        return jsonify(results)

    except Exception as e:
        logger.error(f"Error fetching profile for user {user}: {e}")
        return jsonify({"msg": "Failed to fetch profile"}), 500


@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    """
    Return the user's vocabulary list ordered by next review date.

    Returns:
        JSON response with vocabulary entries or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        entries = get_user_vocabulary_entries(user)
        return jsonify(entries)

    except Exception as e:
        logger.error(f"Error fetching vocabulary for user {user}: {e}")
        return jsonify({"msg": "Failed to fetch vocabulary"}), 500


@user_bp.route("/vocabulary", methods=["DELETE"])
def delete_all_vocab():
    """
    Delete all vocabulary entries for the logged in user.

    Returns:
        JSON response confirming deletion or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        success = delete_user_vocabulary(user)
        if success:
            return jsonify({"msg": "All vocabulary entries deleted"})
        else:
            return jsonify({"msg": "Failed to delete vocabulary"}), 500

    except Exception as e:
        logger.error(f"Error deleting vocabulary for user {user}: {e}")
        return jsonify({"msg": "Failed to delete vocabulary"}), 500


@user_bp.route("/vocab-train", methods=["GET", "POST"])
def vocab_train():
    """
    Serve spaced repetition training data and record reviews.

    GET: Returns the next vocabulary word due for review
    POST: Records the review result and updates the spaced repetition algorithm

    Returns:
        JSON response with training data or review confirmation
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        try:
            row = select_vocab_word_due_for_review(user)
            return jsonify(row or {})

        except Exception as e:
            logger.error(f"Error fetching vocab training data for user {user}: {e}")
            return jsonify({"msg": "Failed to fetch training data"}), 500

    elif request.method == "POST":
        try:
            data = request.get_json() or {}
            vocab_id = data.get("vocab_id")
            quality = data.get("quality")

            if not vocab_id or quality is None:
                return jsonify({"msg": "Missing vocab_id or quality"}), 400

            update_vocab_after_review(user, vocab_id, quality)
            return jsonify({"msg": "Review recorded"})

        except Exception as e:
            logger.error(f"Error recording vocab review for user {user}: {e}")
            return jsonify({"msg": "Failed to record review"}), 500


@user_bp.route("/save-vocab", methods=["POST"])
def save_vocab_words():
    """
    Save vocabulary words to the user's vocabulary list.

    Returns:
        JSON response confirming save or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        words = data.get("words", [])
        context = data.get("context", "")
        exercise = data.get("exercise", "")

        if not words:
            return jsonify({"msg": "No words provided"}), 400

        saved_words = []
        for word in words:
            if word.strip():
                saved_word = save_vocab(user, word.strip(), context=context, exercise=exercise)
                if saved_word:
                    saved_words.append(saved_word)

        return jsonify({
            "msg": f"Saved {len(saved_words)} words",
            "saved_words": saved_words
        })

    except Exception as e:
        logger.error(f"Error saving vocabulary for user {user}: {e}")
        return jsonify({"msg": "Failed to save vocabulary"}), 500


@user_bp.route("/vocabulary/<int:vocab_id>", methods=["DELETE"])
def delete_vocab_word(vocab_id: int):
    """
    Delete a specific vocabulary word for the logged in user.

    Args:
        vocab_id: The ID of the vocabulary entry to delete

    Returns:
        JSON response confirming deletion or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        success = delete_specific_vocabulary(user, vocab_id)
        if success:
            return jsonify({"msg": "Vocabulary word deleted"})
        else:
            return jsonify({"msg": "Failed to delete vocabulary word"}), 500

    except Exception as e:
        logger.error(f"Error deleting vocabulary word {vocab_id} for user {user}: {e}")
        return jsonify({"msg": "Failed to delete vocabulary word"}), 500


@user_bp.route("/vocabulary/<int:vocab_id>/report", methods=["POST"])
def report_vocab_word(vocab_id: int):
    """
    Report a vocabulary word as incorrect or problematic.

    Args:
        vocab_id: The ID of the vocabulary entry to report

    Returns:
        JSON response confirming report or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        reason = data.get("reason", "general")

        # Insert report into database
        insert_row(
            "vocab_reports",
            {
                "username": user,
                "vocab_id": vocab_id,
                "reason": reason,
                "reported_at": datetime.datetime.now().isoformat()
            }
        )

        return jsonify({"msg": "Vocabulary word reported"})

    except Exception as e:
        logger.error(f"Error reporting vocabulary word {vocab_id} for user {user}: {e}")
        return jsonify({"msg": "Failed to report vocabulary word"}), 500


@user_bp.route("/topic-memory", methods=["GET"])
def get_topic_memory():
    """
    Get the user's topic memory data.

    Returns:
        JSON response with topic memory data or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        rows = select_rows(
            "topic_memory",
            columns="grammar, topic, skill_type, quality, repetitions, ease_factor, intervall, next_repeat",
            where="username = ?",
            params=(user,),
            order_by="next_repeat ASC"
        )

        return jsonify(rows or [])

    except Exception as e:
        logger.error(f"Error fetching topic memory for user {user}: {e}")
        return jsonify({"msg": "Failed to fetch topic memory"}), 500


@user_bp.route("/topic-memory", methods=["DELETE"])
def clear_topic_memory_route():
    """
    Clear all topic memory data for the logged in user.

    Returns:
        JSON response confirming deletion or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        delete_rows("topic_memory", "WHERE username = ?", (user,))
        return jsonify({"msg": "Topic memory cleared"})

    except Exception as e:
        logger.error(f"Error clearing topic memory for user {user}: {e}")
        return jsonify({"msg": "Failed to clear topic memory"}), 500


@user_bp.route("/topic-weaknesses", methods=["GET"])
def topic_weaknesses():
    """
    Get the user's weakest topics for focused learning.

    Returns:
        JSON response with weakest topics or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        rows = select_rows(
            "topic_memory",
            columns="grammar, skill_type, AVG(quality) as avg_quality, COUNT(*) as practice_count",
            where="username = ?",
            params=(user,),
            group_by="grammar, skill_type",
            order_by="avg_quality ASC",
            limit=5
        )

        weaknesses = [
            {
                "grammar": row["grammar"],
                "skill_type": row["skill_type"],
                "average_quality": float(row["avg_quality"] or 0),
                "practice_count": row["practice_count"]
            }
            for row in (rows if isinstance(rows, list) else [])
        ]

        return jsonify(weaknesses)

    except Exception as e:
        logger.error(f"Error fetching topic weaknesses for user {user}: {e}")
        return jsonify({"msg": "Failed to fetch topic weaknesses"}), 500


@user_bp.route("/user-level", methods=["GET", "POST"])
def user_level():
    """
    Get or update the user's skill level.

    GET: Returns the current skill level
    POST: Updates the skill level based on provided data

    Returns:
        JSON response with skill level or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        try:
            row = select_one(
                "users",
                columns="skill_level",
                where="username = ?",
                params=(user,)
            )

            skill_level = row.get("skill_level", 0) if row else 0
            return jsonify({"skill_level": skill_level})

        except Exception as e:
            logger.error(f"Error fetching skill level for user {user}: {e}")
            return jsonify({"msg": "Failed to fetch skill level"}), 500

    elif request.method == "POST":
        try:
            data = request.get_json() or {}
            new_level = data.get("skill_level")

            if new_level is None:
                return jsonify({"msg": "Missing skill_level"}), 400

            update_row(
                "users",
                {"skill_level": new_level},
                "username = ?",
                (user,)
            )

            return jsonify({"msg": "Skill level updated", "skill_level": new_level})

        except Exception as e:
            logger.error(f"Error updating skill level for user {user}: {e}")
            return jsonify({"msg": "Failed to update skill level"}), 500


@user_bp.route("/vocabulary/lookup", methods=["GET"])
def lookup_vocab_word():
    """
    Lookup a vocabulary word for the current user.

    Returns:
        JSON response with vocabulary details or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    word = request.args.get("word", "").strip()
    if not word:
        return jsonify({"msg": "Missing word parameter"}), 400

    try:
        result = lookup_vocabulary_word(user, word)
        if result:
            return jsonify(result)
        else:
            return jsonify({"msg": "Word not found and could not be created"}), 404

    except Exception as e:
        logger.error(f"Error looking up vocabulary word '{word}' for user {user}: {e}")
        return jsonify({"msg": "Failed to lookup vocabulary word"}), 500


@user_bp.route("/vocabulary/search-ai", methods=["POST"])
def search_vocab_ai():
    """
    Search for a vocabulary word using AI and save it to the user's vocabulary.

    Returns:
        JSON response with vocabulary details or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    data = request.get_json() or {}
    word = data.get("word", "").strip()
    if not word:
        return jsonify({"msg": "Missing word parameter"}), 400

    try:
        result = search_vocabulary_with_ai(user, word)
        if result:
            return jsonify(result)
        else:
            return jsonify({"msg": "Failed to search and save vocabulary word"}), 500

    except Exception as e:
        logger.error(f"Error searching vocabulary with AI for word '{word}' and user {user}: {e}")
        return jsonify({"msg": "Failed to search vocabulary with AI"}), 500
