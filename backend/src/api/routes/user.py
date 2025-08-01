"""
XplorED - User Account and Vocabulary Routes

This module contains API routes for user account management, profile data,
and vocabulary operations, following clean architecture principles as outlined
in the documentation.

Route Categories:
- User Authentication: Session validation and role checking
- Profile Management: User profile data and game results
- Vocabulary Operations: Word lookup, training, and management
- Topic Memory: Spaced repetition and learning progress
- User Analytics: Level tracking and performance metrics

Business Logic:
All business logic has been moved to appropriate helper modules to maintain
separation of concerns and follow clean architecture principles.

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any
from flask import request, jsonify # type: ignore

from core.services.import_service import *
from core.utils.helpers import get_current_user
from core.database.connection import select_rows, insert_row, select_one, update_row, delete_rows, fetch_topic_memory
from config.blueprint import user_bp
from features.vocabulary import (
    lookup_vocabulary_word,
    get_user_vocabulary_entries,
    delete_user_vocabulary,
    delete_specific_vocabulary,
    search_vocabulary_with_ai,
    update_vocabulary_entry,
    get_vocabulary_statistics,
)
from features.vocabulary import select_vocab_word_due_for_review, update_vocab_after_review


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === User Authentication Routes ===
@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    """
    Return the username of the current session.

    This endpoint validates the user's session and returns their username
    for frontend authentication state management.

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

    This endpoint checks the user's role and returns their admin status
    for frontend authorization and UI customization.

    Returns:
        JSON response with admin status or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    return jsonify({"is_admin": user == "admin"})


# === Profile Management Routes ===
@user_bp.route("/profile", methods=["GET"])
def profile():
    """
    Return recent game results for the current user.

    This endpoint fetches the user's recent game results and performance
    data for display in their profile dashboard.

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
        return jsonify({"error": "Failed to fetch profile data"}), 500


# === Vocabulary Management Routes ===
@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    """
    Return all vocabulary entries for the current user.

    This endpoint fetches all vocabulary words saved by the user,
    including their learning progress and review status.

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
        return jsonify({"error": "Failed to fetch vocabulary"}), 500


@user_bp.route("/vocabulary", methods=["DELETE"])
def delete_all_vocab():
    """
    Delete all vocabulary entries for the current user.

    This endpoint removes all vocabulary words saved by the user,
    providing a clean slate for vocabulary learning.

    Returns:
        JSON response with success status or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        delete_user_vocabulary(user)
        return jsonify({"message": "All vocabulary deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting vocabulary for user {user}: {e}")
        return jsonify({"error": "Failed to delete vocabulary"}), 500


@user_bp.route("/vocab-train", methods=["GET", "POST"])
def vocab_train():
    """
    Handle vocabulary training operations.

    GET: Retrieve vocabulary words due for review
    POST: Submit vocabulary review results and update progress

    Returns:
        JSON response with training data or review results
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        try:
            # Get vocabulary word due for review
            vocab_word = select_vocab_word_due_for_review(user)
            if vocab_word:
                return jsonify(vocab_word)
            else:
                return jsonify({"message": "No vocabulary words due for review"})
        except Exception as e:
            logger.error(f"Error fetching vocab training for user {user}: {e}")
            return jsonify({"error": "Failed to fetch training data"}), 500

    elif request.method == "POST":
        try:
            data = request.get_json()
            vocab_id = int(data.get("vocab_id", 0))
            quality = data.get("quality", 0)

            # Update vocabulary progress
            update_vocab_after_review(vocab_id, user, quality)
            return jsonify({"message": "Review submitted successfully"})
        except Exception as e:
            logger.error(f"Error submitting vocab review for user {user}: {e}")
            return jsonify({"error": "Failed to submit review"}), 500


@user_bp.route("/save-vocab", methods=["POST"])
def save_vocab_words():
    """
    Save new vocabulary words for the current user.

    This endpoint processes vocabulary words from lessons or user input
    and saves them to the user's vocabulary list for future review.

    Returns:
        JSON response with success status or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json()
        words = data.get("words", [])

        if not words:
            return jsonify({"error": "No words provided"}), 400

        # Process and save vocabulary words
        saved_words = []
        for word_data in words:
            word = word_data.get("word", "").strip()
            if word:
                # Save vocabulary using helper function
                vocab_id = insert_row("vocab_log", {
                    "username": user,
                    "vocab": word,
                    "created_at": "CURRENT_TIMESTAMP"
                })
                if vocab_id:
                    saved_words.append({"word": word, "id": vocab_id})

        return jsonify({
            "message": f"Saved {len(saved_words)} vocabulary words",
            "saved_words": saved_words
        })

    except Exception as e:
        logger.error(f"Error saving vocabulary for user {user}: {e}")
        return jsonify({"error": "Failed to save vocabulary"}), 500


@user_bp.route("/vocabulary/<int:vocab_id>", methods=["DELETE"])
def delete_vocab_word(vocab_id: int):
    """
    Delete a specific vocabulary word for the current user.

    This endpoint removes a single vocabulary word from the user's
    vocabulary list by its unique identifier.

    Args:
        vocab_id: Unique identifier of the vocabulary word to delete

    Returns:
        JSON response with success status or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Verify the vocabulary word belongs to the user
        vocab = select_one(
            "vocab_log",
            columns="id",
            where="id = ? AND username = ?",
            params=(vocab_id, user)
        )

        if not vocab:
            return jsonify({"error": "Vocabulary word not found"}), 404

        # Delete the vocabulary word
        delete_specific_vocabulary(user, vocab_id)
        return jsonify({"message": "Vocabulary word deleted successfully"})

    except Exception as e:
        logger.error(f"Error deleting vocabulary {vocab_id} for user {user}: {e}")
        return jsonify({"error": "Failed to delete vocabulary word"}), 500


@user_bp.route("/vocabulary/<int:vocab_id>/report", methods=["POST"])
def report_vocab_word(vocab_id: int):
    """
    Report a vocabulary word for review or correction.

    This endpoint allows users to report vocabulary words that may be
    incorrect, inappropriate, or need improvement.

    Args:
        vocab_id: Unique identifier of the vocabulary word to report

    Returns:
        JSON response with success status or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json()
        reason = data.get("reason", "No reason provided")

        # Verify the vocabulary word exists
        vocab = select_one(
            "vocab_log",
            columns="vocab",
            where="id = ?",
            params=(vocab_id,)
        )

        if not vocab:
            return jsonify({"error": "Vocabulary word not found"}), 404

        # Save the report
        insert_row("vocab_reports", {
            "vocab_id": vocab_id,
            "reported_by": user,
            "reason": reason,
            "created_at": "CURRENT_TIMESTAMP"
        })

        return jsonify({"message": "Vocabulary word reported successfully"})

    except Exception as e:
        logger.error(f"Error reporting vocabulary {vocab_id} by user {user}: {e}")
        return jsonify({"error": "Failed to report vocabulary word"}), 500


# === Topic Memory Routes ===
@user_bp.route("/topic-memory", methods=["GET"])
def get_topic_memory():
    """
    Return topic memory entries for the current user.

    This endpoint fetches spaced repetition data for grammar topics
    and learning concepts that the user is studying.

    Returns:
        JSON response with topic memory entries or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Get topic memory entries for the user
        memory_entries = fetch_topic_memory(user, include_correct=False)

        if memory_entries is False:
            return jsonify({"error": "Failed to fetch topic memory"}), 500

        return jsonify(memory_entries)

    except Exception as e:
        logger.error(f"Error fetching topic memory for user {user}: {e}")
        return jsonify({"error": "Failed to fetch topic memory"}), 500


@user_bp.route("/topic-memory", methods=["DELETE"])
def clear_topic_memory_route():
    """
    Clear all topic memory entries for the current user.

    This endpoint resets the user's spaced repetition progress,
    allowing them to start fresh with topic learning.

    Returns:
        JSON response with success status or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Delete all topic memory entries for the user
        delete_rows("topic_memory", "WHERE username = ?", (user,))
        return jsonify({"message": "Topic memory cleared successfully"})

    except Exception as e:
        logger.error(f"Error clearing topic memory for user {user}: {e}")
        return jsonify({"error": "Failed to clear topic memory"}), 500


@user_bp.route("/topic-weaknesses", methods=["GET"])
def topic_weaknesses():
    """
    Return user's learning weaknesses and areas for improvement.

    This endpoint analyzes the user's performance data to identify
    topics and concepts that need more attention and practice.

    Returns:
        JSON response with weakness analysis or unauthorized error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Get topic memory entries with low performance
        weak_topics = fetch_topic_memory(user, include_correct=True)

        if weak_topics is False:
            return jsonify({"error": "Failed to fetch topic weaknesses"}), 500

        # Ensure weak_topics is a list before filtering
        if not isinstance(weak_topics, list):
            weak_topics = []

        # Filter for topics with low performance
        weaknesses = [
            topic for topic in weak_topics
            if topic.get("quality", 0) < 3 or topic.get("correct", 0) == 0
        ]

        return jsonify({
            "weaknesses": weaknesses,
            "total_weak_topics": len(weaknesses)
        })

    except Exception as e:
        logger.error(f"Error fetching topic weaknesses for user {user}: {e}")
        return jsonify({"error": "Failed to fetch topic weaknesses"}), 500


# === User Analytics Routes ===
@user_bp.route("/user-level", methods=["GET", "POST"])
def user_level():
    """
    Handle user level and progress tracking.

    GET: Retrieve current user level and progress statistics
    POST: Update user level based on performance

    Returns:
        JSON response with level data or update status
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    if request.method == "GET":
        try:
            # Get user progress data
            progress = select_one(
                "user_progress",
                columns="level, total_exercises, correct_exercises, last_activity",
                where="username = ?",
                params=(user,)
            )

            if progress:
                return jsonify({
                    "level": progress["level"],
                    "total_exercises": progress["total_exercises"],
                    "correct_exercises": progress["correct_exercises"],
                    "accuracy": (progress["correct_exercises"] / max(progress["total_exercises"], 1)) * 100,
                    "last_activity": progress["last_activity"]
                })
            else:
                # Create default progress entry
                insert_row("user_progress", {
                    "username": user,
                    "level": 1,
                    "total_exercises": 0,
                    "correct_exercises": 0
                })
                return jsonify({
                    "level": 1,
                    "total_exercises": 0,
                    "correct_exercises": 0,
                    "accuracy": 0,
                    "last_activity": None
                })

        except Exception as e:
            logger.error(f"Error fetching user level for {user}: {e}")
            return jsonify({"error": "Failed to fetch user level"}), 500

    elif request.method == "POST":
        try:
            data = request.get_json()
            new_level = data.get("level", 1)

            # Update user level
            update_row(
                "user_progress",
                {"level": new_level, "last_activity": "CURRENT_TIMESTAMP"},
                "WHERE username = ?",
                (user,)
            )

            return jsonify({"message": "User level updated successfully"})

        except Exception as e:
            logger.error(f"Error updating user level for {user}: {e}")
            return jsonify({"error": "Failed to update user level"}), 500


# === Vocabulary Lookup Routes ===
@user_bp.route("/vocabulary/lookup", methods=["GET"])
def lookup_vocab_word():
    """
    Look up vocabulary word definitions and translations.

    This endpoint provides detailed information about vocabulary words,
    including definitions, translations, and usage examples.

    Returns:
        JSON response with vocabulary information or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        word = request.args.get("word", "").strip()
        if not word:
            return jsonify({"error": "No word provided"}), 400

        # Look up vocabulary word
        result = lookup_vocabulary_word(user, word)

        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "Word not found"}), 404

    except Exception as e:
        logger.error(f"Error looking up vocabulary for user {user}: {e}")
        return jsonify({"error": "Failed to lookup vocabulary"}), 500


@user_bp.route("/vocabulary/search-ai", methods=["POST"])
def search_vocab_ai():
    """
    Search for vocabulary words using AI-powered assistance.

    This endpoint uses AI to help users find vocabulary words based on
    context, descriptions, or partial information.

    Returns:
        JSON response with AI search results or error details
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json()
        query = data.get("query", "").strip()

        if not query:
            return jsonify({"error": "No search query provided"}), 400

        # Search vocabulary using AI
        results = search_vocabulary_with_ai(user, query)

        return jsonify({
            "query": query,
            "results": results
        })

    except Exception as e:
        logger.error(f"Error searching vocabulary with AI for user {user}: {e}")
        return jsonify({"error": "Failed to search vocabulary"}), 500
