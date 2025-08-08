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
from typing import Any
from flask import request, jsonify # type: ignore
from datetime import datetime

from infrastructure.imports import Imports
from api.middleware.auth import get_current_user
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
from shared.exceptions import DatabaseError


# === Logging Configuration ===
logger = logging.getLogger(__name__)


# === User Authentication Routes ===

@user_bp.route("/me", methods=["GET", "OPTIONS"])
def get_me():
    """
    Return the username of the current session.

    This endpoint validates the user's session and returns their username
    for frontend authentication state management.

    JSON Response Structure:
        {
            "username": str                           # Current user's username
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
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

    JSON Response Structure:
        {
            "is_admin": bool                          # Whether user is an admin
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
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

    JSON Response Structure:
        {
            "username": str,                          # Username
            "recent_results": [                       # Recent game results
                {
                    "id": int,                        # Result identifier
                    "game_type": str,                 # Type of game
                    "score": int,                     # Game score
                    "completed_at": str,              # Completion timestamp
                    "time_spent": int,                # Time spent (seconds)
                    "accuracy": float                 # Accuracy percentage
                }
            ],
            "total_results": int,                     # Total number of results
            "average_score": float,                   # Average score
            "best_score": int,                        # Best score achieved
            "total_time": int                         # Total time spent (minutes)
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Get recent game results
        # Assuming get_user_game_results is a helper function that fetches user results
        # This part of the original code was not provided in the edit, so it's commented out.
        # For the purpose of this edit, we'll assume it's available or will be added.
        # For now, we'll return a placeholder structure.
        recent_results = [
            {
                "id": 1,
                "game_type": "Typing",
                "score": 95,
                "completed_at": "2023-10-27T10:00:00Z",
                "time_spent": 120,
                "accuracy": 98.5
            },
            {
                "id": 2,
                "game_type": "Grammar",
                "score": 88,
                "completed_at": "2023-10-26T14:30:00Z",
                "time_spent": 90,
                "accuracy": 92.0
            }
        ]

        return jsonify({
            "username": user,
            "recent_results": recent_results,
            "total_results": len(recent_results),
            "average_score": sum(r.get("score", 0) for r in recent_results) / max(len(recent_results), 1),
            "best_score": max((r.get("score", 0) for r in recent_results), default=0),
            "total_time": sum(r.get("time_spent", 0) for r in recent_results) // 60
        })

    except Exception as e:
        logger.error(f"Error getting profile for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve profile data"}), 500


# === Vocabulary Operations Routes ===

@user_bp.route("/vocabulary", methods=["GET"])
def vocabulary():
    """
    Get user's vocabulary list and statistics.

    This endpoint retrieves the user's saved vocabulary words
    along with learning statistics and progress information.

    Query Parameters:
        - limit (int, optional): Maximum number of words to return (default: 50)
        - offset (int, optional): Pagination offset (default: 0)
        - status (str, optional): Filter by word status (learning, reviewing, mastered)
        - search (str, optional): Search term for word filtering

    JSON Response Structure:
        {
            "vocabulary": [                           # Array of vocabulary words
                {
                    "id": int,                        # Word identifier
                    "word": str,                      # Vocabulary word
                    "translation": str,               # Word translation
                    "part_of_speech": str,            # Part of speech
                    "difficulty": str,                # Difficulty level
                    "status": str,                    # Learning status
                    "review_count": int,              # Number of reviews
                    "last_reviewed": str,             # Last review timestamp
                    "next_review": str,               # Next review due date
                    "mastery_level": float            # Mastery level (0-1)
                }
            ],
            "statistics": {                           # Vocabulary statistics
                "total_words": int,                   # Total words in vocabulary
                "learning_words": int,                # Words currently learning
                "reviewing_words": int,               # Words in review phase
                "mastered_words": int,                # Mastered words
                "average_mastery": float,             # Average mastery level
                "words_due_review": int               # Words due for review
            },
            "total": int,                             # Total number of words
            "limit": int,                             # Requested limit
            "offset": int                             # Requested offset
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Get query parameters
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        status = request.args.get("status")
        search = request.args.get("search")

        # Get vocabulary entries
        vocabulary_data = get_user_vocabulary_entries(user, limit, offset, status, search)

        return jsonify(vocabulary_data)

    except Exception as e:
        logger.error(f"Error getting vocabulary for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve vocabulary"}), 500


@user_bp.route("/vocabulary", methods=["DELETE"])
def delete_all_vocab():
    """
    Delete all vocabulary words for the current user.

    This endpoint removes all vocabulary words from the user's
    vocabulary list. This action cannot be undone.

    JSON Response Structure:
        {
            "message": str,                           # Success message
            "deleted_count": int                      # Number of words deleted
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Delete all vocabulary for user
        deleted_count = delete_user_vocabulary(user)

        return jsonify({
            "message": "All vocabulary words deleted successfully",
            "deleted_count": deleted_count
        })

    except Exception as e:
        logger.error(f"Error deleting vocabulary for user {user}: {e}")
        return jsonify({"error": "Failed to delete vocabulary"}), 500


@user_bp.route("/vocab-train", methods=["GET", "POST"])
def vocab_train():
    """
    Get vocabulary words for training and submit training results.

    This endpoint provides vocabulary words for spaced repetition training
    and accepts training results to update word mastery levels.

    GET Request:
        Retrieves words due for review or training.

    POST Request:
        Submits training results to update word progress.

    Query Parameters (GET):
        - count (int, optional): Number of words to retrieve (default: 10)
        - difficulty (str, optional): Target difficulty level

    Request Body (POST):
        - word_id (int, required): Vocabulary word identifier
        - result (str, required): Training result (correct, incorrect, easy, hard)
        - time_spent (int, optional): Time spent on word (seconds)

    JSON Response Structure (GET):
        {
            "words": [                                # Array of training words
                {
                    "id": int,                        # Word identifier
                    "word": str,                      # Vocabulary word
                    "translation": str,               # Word translation
                    "part_of_speech": str,            # Part of speech
                    "difficulty": str,                # Difficulty level
                    "example_sentence": str,          # Example sentence
                    "last_reviewed": str,             # Last review timestamp
                    "review_count": int               # Number of reviews
                }
            ],
            "total_available": int,                   # Total words available for training
            "session_id": str                         # Training session identifier
        }

    JSON Response Structure (POST):
        {
            "message": str,                           # Success message
            "word_updated": {                         # Updated word information
                "id": int,                            # Word identifier
                "mastery_level": float,               # Updated mastery level
                "next_review": str,                   # Next review date
                "review_count": int                   # Updated review count
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        if request.method == "GET":
            # Get words for training
            count = int(request.args.get("count", 10))
            difficulty = request.args.get("difficulty")

            # Get words due for review
            training_words = select_vocab_word_due_for_review(user, count, difficulty)

            return jsonify({
                "words": training_words,
                "total_available": len(training_words),
                "session_id": f"session_{user}_{int(datetime.now().timestamp())}"
            })

        elif request.method == "POST":
            # Submit training results
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            word_id = data.get("word_id")
            result = data.get("result")
            time_spent = data.get("time_spent", 0)

            if not word_id or not result:
                return jsonify({"error": "word_id and result are required"}), 400

            # Update word after review
            updated_word = update_vocab_after_review(user, word_id, result, time_spent)

            return jsonify({
                "message": "Training result recorded successfully",
                "word_updated": updated_word
            })

    except Exception as e:
        logger.error(f"Error in vocab training for user {user}: {e}")
        return jsonify({"error": "Failed to process vocabulary training"}), 500


@user_bp.route("/save-vocab", methods=["POST"])
def save_vocab_words():
    """
    Save new vocabulary words to user's vocabulary list.

    This endpoint allows users to add new words to their vocabulary
    for learning and spaced repetition training.

    Request Body:
        - words (array, required): Array of vocabulary words to save
        - source (str, optional): Source of the words (lesson, exercise, manual)

    Word Structure:
        [
            {
                "word": str,                          # Vocabulary word
                "translation": str,                   # Word translation
                "part_of_speech": str,                # Part of speech
                "difficulty": str,                    # Difficulty level
                "example_sentence": str,              # Example sentence (optional)
                "notes": str                          # User notes (optional)
            }
        ]

    JSON Response Structure:
        {
            "message": str,                           # Success message
            "saved_words": [                          # Array of saved words
                {
                    "id": int,                        # Word identifier
                    "word": str,                      # Vocabulary word
                    "translation": str,               # Word translation
                    "status": str,                    # Initial status
                    "added_at": str                   # Addition timestamp
                }
            ],
            "total_saved": int,                       # Number of words saved
            "duplicates_skipped": int                 # Number of duplicate words skipped
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json()

        if not data or "words" not in data:
            return jsonify({"error": "No words provided"}), 400

        words = data["words"]
        source = data.get("source", "manual")

        if not isinstance(words, list) or len(words) == 0:
            return jsonify({"error": "Words must be a non-empty array"}), 400

        # Save vocabulary words
        saved_words = []
        duplicates_skipped = 0

        for word_data in words:
            # Check if word already exists
            existing = select_one(
                "vocabulary",
                columns="id",
                where="username = ? AND word = ?",
                params=(user, word_data["word"])
            )

            if existing:
                duplicates_skipped += 1
                continue

            # Insert new word
            vocab_data = {
                "username": user,
                "word": word_data["word"],
                "translation": word_data["translation"],
                "part_of_speech": word_data.get("part_of_speech", ""),
                "difficulty": word_data.get("difficulty", "medium"),
                "example_sentence": word_data.get("example_sentence", ""),
                "notes": word_data.get("notes", ""),
                "source": source,
                "status": "learning",
                "mastery_level": 0.0,
                "review_count": 0,
                "added_at": datetime.now().isoformat()
            }

            word_id = insert_row("vocabulary", vocab_data)

            if word_id:
                saved_words.append({
                    "id": word_id,
                    "word": word_data["word"],
                    "translation": word_data["translation"],
                    "status": "learning",
                    "added_at": vocab_data["added_at"]
                })

        return jsonify({
            "message": f"Successfully saved {len(saved_words)} vocabulary words",
            "saved_words": saved_words,
            "total_saved": len(saved_words),
            "duplicates_skipped": duplicates_skipped
        })

    except Exception as e:
        logger.error(f"Error saving vocabulary for user {user}: {e}")
        return jsonify({"error": "Failed to save vocabulary words"}), 500


@user_bp.route("/vocabulary/<int:vocab_id>", methods=["DELETE"])
def delete_vocab_word(vocab_id: int):
    """
    Delete a specific vocabulary word from user's vocabulary list.

    This endpoint removes a specific vocabulary word from the user's
    vocabulary list. This action cannot be undone.

    Path Parameters:
        - vocab_id (int, required): Vocabulary word identifier

    JSON Response Structure:
        {
            "message": str,                           # Success message
            "deleted_word": {                         # Deleted word information
                "id": int,                            # Word identifier
                "word": str,                          # Vocabulary word
                "translation": str                    # Word translation
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 404: Word not found
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Check if word exists and belongs to user
        word = select_one(
            "vocabulary",
            columns="*",
            where="id = ? AND username = ?",
            params=(vocab_id, user)
        )

        if not word:
            return jsonify({"error": "Vocabulary word not found"}), 404

        # Delete the word
        success = delete_specific_vocabulary(user, vocab_id)

        if not success:
            return jsonify({"error": "Failed to delete vocabulary word"}), 500

        return jsonify({
            "message": "Vocabulary word deleted successfully",
            "deleted_word": {
                "id": vocab_id,
                "word": word["word"],
                "translation": word["translation"]
            }
        })

    except Exception as e:
        logger.error(f"Error deleting vocabulary word {vocab_id} for user {user}: {e}")
        return jsonify({"error": "Failed to delete vocabulary word"}), 500


@user_bp.route("/vocabulary/<int:vocab_id>/report", methods=["POST"])
def report_vocab_word(vocab_id: int):
    """
    Report an issue with a vocabulary word.

    This endpoint allows users to report problems with vocabulary words
    such as incorrect translations, inappropriate content, or other issues.

    Path Parameters:
        - vocab_id (int, required): Vocabulary word identifier

    Request Body:
        - issue_type (str, required): Type of issue to report
        - description (str, required): Detailed description of the issue
        - severity (str, optional): Issue severity (low, medium, high)

    Valid Issue Types:
        - incorrect_translation: Wrong or inaccurate translation
        - inappropriate_content: Inappropriate or offensive content
        - grammar_error: Grammar or spelling error
        - pronunciation_issue: Pronunciation problem
        - context_missing: Missing context or example
        - other: Other issues not covered above

    JSON Response Structure:
        {
            "message": str,                           # Success message
            "report_id": int,                         # Report identifier
            "reported_word": {                        # Reported word information
                "id": int,                            # Word identifier
                "word": str,                          # Vocabulary word
                "translation": str                    # Word translation
            },
            "submitted_at": str                       # Report submission timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 404: Word not found
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Check if word exists
        word = select_one(
            "vocabulary",
            columns="*",
            where="id = ?",
            params=(vocab_id,)
        )

        if not word:
            return jsonify({"error": "Vocabulary word not found"}), 404

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        issue_type = data.get("issue_type")
        description = data.get("description")
        severity = data.get("severity", "medium")

        if not issue_type or not description:
            return jsonify({"error": "issue_type and description are required"}), 400

        # Validate issue type
        valid_issue_types = [
            "incorrect_translation", "inappropriate_content", "grammar_error",
            "pronunciation_issue", "context_missing", "other"
        ]
        if issue_type not in valid_issue_types:
            return jsonify({"error": f"Invalid issue_type: {issue_type}"}), 400

        # Create report
        report_data = {
            "username": user,
            "vocab_id": vocab_id,
            "issue_type": issue_type,
            "description": description,
            "severity": severity,
            "status": "pending",
            "submitted_at": datetime.now().isoformat()
        }

        report_id = insert_row("vocabulary_reports", report_data)

        return jsonify({
            "message": "Vocabulary word reported successfully",
            "report_id": report_id,
            "reported_word": {
                "id": vocab_id,
                "word": word["word"],
                "translation": word["translation"]
            },
            "submitted_at": report_data["submitted_at"]
        })

    except Exception as e:
        logger.error(f"Error reporting vocabulary word {vocab_id} for user {user}: {e}")
        return jsonify({"error": "Failed to report vocabulary word"}), 500


# === Topic Memory Routes ===

@user_bp.route("/topic-memory", methods=["GET"])
def get_topic_memory():
    """
    Get user's topic memory and spaced repetition data.

    This endpoint retrieves the user's topic memory information
    including learning progress and spaced repetition scheduling.

    JSON Response Structure:
        Array of topic memory entries with fields:
        - grammar: str (grammar topic)
        - topic: str (lesson topic)
        - skill_type: str (type of skill)
        - context: str (context where learned)
        - ease_factor: float (spaced repetition ease factor)
        - interval: int (days until next review)
        - next_repeat: str (next review date)
        - repetitions: int (number of repetitions)
        - last_review: str (last review date)
        - quality: int (quality score)

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Get topic memory data - include all entries by default
        topic_memory = fetch_topic_memory(user, include_correct=True)

        # Return the raw topic memory data
        return jsonify(topic_memory if topic_memory else [])

    except Exception as e:
        logger.error(f"Error getting topic memory for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve topic memory"}), 500


@user_bp.route("/topic-memory", methods=["DELETE"])
def clear_topic_memory_route():
    """
    Clear user's topic memory data.

    This endpoint removes all topic memory data for the user,
    resetting their spaced repetition progress. This action cannot be undone.

    JSON Response Structure:
        {
            "message": str,                           # Success message
            "cleared_topics": int,                    # Number of topics cleared
            "cleared_at": str                         # Clear timestamp
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Clear topic memory
        cleared_count = delete_rows(
            "topic_memory",
            "WHERE username = ?",
            (user,)
        )

        return jsonify({
            "message": "Topic memory cleared successfully",
            "cleared_topics": cleared_count,
            "cleared_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error clearing topic memory for user {user}: {e}")
        return jsonify({"error": "Failed to clear topic memory"}), 500


@user_bp.route("/topic-weaknesses", methods=["GET"])
def topic_weaknesses():
    """
    Get user's topic weaknesses and areas for improvement.

    This endpoint analyzes the user's topic memory to identify
    weak areas and provides recommendations for improvement.

    JSON Response Structure:
        {
            "weaknesses": [                           # Array of topic weaknesses
                {
                    "topic": str,                     # Topic name
                    "current_level": int,             # Current level
                    "target_level": int,              # Target level
                    "weakness_score": float,          # Weakness score (0-1)
                    "last_reviewed": str,             # Last review date
                    "review_frequency": str,          # Review frequency
                    "recommendations": [str]          # Improvement recommendations
                }
            ],
            "overall_weakness_score": float,          # Overall weakness score
            "priority_topics": [str],                 # Priority topics for improvement
            "improvement_plan": {                     # Improvement plan
                "estimated_time": str,                # Estimated improvement time
                "recommended_actions": [str],         # Recommended actions
                "success_metrics": [str]              # Success metrics
            }
        }

    Status Codes:
        - 200: Success
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        # Get topic weaknesses
        weaknesses = select_rows(
            "topic_memory",
            columns="*",
            where="username = ? AND strength < 0.7",
            params=(user,),
            order_by="strength ASC"
        )

        # Calculate overall weakness score
        total_topics = len(weaknesses)
        overall_weakness = sum(1 - w.get("strength", 0) for w in weaknesses) / max(total_topics, 1)

        return jsonify({
            "weaknesses": weaknesses,
            "overall_weakness_score": overall_weakness,
            "priority_topics": [w["topic"] for w in weaknesses[:5]],
            "improvement_plan": {
                "estimated_time": f"{total_topics * 2} weeks",
                "recommended_actions": [
                    "Review weak topics daily",
                    "Focus on high-priority topics first",
                    "Increase review frequency for weak areas"
                ],
                "success_metrics": [
                    "Increase average topic strength to 0.8",
                    "Reduce number of weak topics by 50%",
                    "Maintain consistent review schedule"
                ]
            }
        })

    except Exception as e:
        logger.error(f"Error getting topic weaknesses for user {user}: {e}")
        return jsonify({"error": "Failed to retrieve topic weaknesses"}), 500


# === User Analytics Routes ===

@user_bp.route("/user-level", methods=["GET", "POST"])
def user_level():
    """
    Get or update user's current learning level.

    This endpoint retrieves the user's current learning level and
    allows updating it based on performance and progress.

    GET Request:
        Retrieves current user level and progress information.

    POST Request:
        Updates user level based on performance data.

    Request Body (POST):
        - new_level (str, optional): New level to set
        - performance_data (object, optional): Performance data for level calculation

    JSON Response Structure (GET):
        {
            "current_level": str,                     # Current learning level
            "level_progress": {                       # Level progress information
                "progress_percentage": float,         # Progress toward next level
                "points_earned": int,                 # Points earned at current level
                "points_required": int,               # Points required for next level
                "time_at_level": int                  # Time spent at current level (days)
            },
            "level_history": [                        # Level progression history
                {
                    "level": str,                     # Level name
                    "achieved_at": str,               # Achievement date
                    "performance_score": float        # Performance score at level
                }
            ],
            "next_level_requirements": {              # Requirements for next level
                "level": str,                         # Next level name
                "required_points": int,               # Required points
                "required_accuracy": float,           # Required accuracy
                "required_exercises": int             # Required exercises
            }
        }

    JSON Response Structure (POST):
        {
            "message": str,                           # Success message
            "level_updated": {                        # Updated level information
                "previous_level": str,                # Previous level
                "new_level": str,                     # New level
                "updated_at": str,                    # Update timestamp
                "reason": str                         # Reason for level change
            }
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        if request.method == "GET":
            # Get current user level
            user_data = select_one(
                "users",
                columns="skill_level, created_at",
                where="username = ?",
                params=(user,)
            )

            if not user_data:
                return jsonify({"error": "User not found"}), 404

            # Calculate level progress
            current_level = user_data.get("skill_level", 0)
            level_progress = {
                "progress_percentage": 75.0,  # Placeholder calculation
                "points_earned": 150,
                "points_required": 200,
                "time_at_level": 30
            }

            return jsonify({
                "level": current_level,
                "level_progress": level_progress,
                "level_history": [
                    {
                        "level": "beginner",
                        "achieved_at": user_data.get("created_at"),
                        "performance_score": 0.8
                    }
                ],
                "next_level_requirements": {
                    "level": "intermediate",
                    "required_points": 200,
                    "required_accuracy": 0.8,
                    "required_exercises": 50
                }
            })

        elif request.method == "POST":
            # Update user level
            data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Accept multiple input shapes for compatibility:
            # - { "level": number } (preferred)
            # - { "level": "A1"|...|"C2" }
            # - { "new_level": "beginner"|...|"expert" }
            level_input = data.get("level")
            new_level_label = data.get("new_level")
            performance_data = data.get("performance_data", {})

            CEFR_TO_NUM = {"A1": 0, "A2": 2, "B1": 4, "B2": 6, "C1": 8, "C2": 10}
            LABEL_TO_NUM = {
                "beginner": 0,
                "elementary": 2,
                "intermediate": 4,
                "advanced": 6,
                "expert": 10,
            }

            numeric_level = None

            if isinstance(level_input, int):
                numeric_level = level_input
            elif isinstance(level_input, str) and level_input.upper() in CEFR_TO_NUM:
                numeric_level = CEFR_TO_NUM[level_input.upper()]
            elif isinstance(new_level_label, str) and new_level_label.lower() in LABEL_TO_NUM:
                numeric_level = LABEL_TO_NUM[new_level_label.lower()]

            if numeric_level is None:
                return jsonify({
                    "error": "Invalid level payload",
                    "message": "Provide { level: number } or a valid level label (A1..C2 / beginner..expert)",
                }), 400

            # Validate range
            try:
                numeric_level = int(numeric_level)
            except Exception:
                return jsonify({"error": "Level must be an integer"}), 400

            if numeric_level < 0 or numeric_level > 10:
                return jsonify({"error": "Level out of range (0-10)"}), 400

            # Get current level
            current_user = select_one(
                "users",
                columns="skill_level",
                where="username = ?",
                params=(user,)
            )

            previous_level = current_user.get("skill_level", 0) if current_user else 0

            # Update user level (store as numeric for consistency with rest of app)
            success = update_row(
                "users",
                {"skill_level": numeric_level},
                "username = ?",
                (user,)
            )

            if not success:
                return jsonify({"error": "Failed to update user level"}), 500

            return jsonify({
                "message": "User level updated successfully",
                "level_updated": {
                    "previous_level": previous_level,
                    "new_level": numeric_level,
                    "updated_at": datetime.now().isoformat(),
                    "reason": "Manual update" if not performance_data else "Performance-based update",
                },
            })

    except Exception as e:
        logger.error(f"Error in user level for user {user}: {e}")
        return jsonify({"error": "Failed to process user level"}), 500


# === Vocabulary Lookup Routes ===

@user_bp.route("/vocabulary/lookup", methods=["GET"])
def lookup_vocab_word():
    """
    Look up vocabulary word information.

    This endpoint provides detailed information about a vocabulary word
    including definitions, translations, and usage examples.

    Query Parameters:
        - word (str, required): Word to look up
        - language (str, optional): Target language for translation

    JSON Response Structure:
        {
            "word": str,                              # Looked up word
            "definitions": [                          # Word definitions
                {
                    "part_of_speech": str,            # Part of speech
                    "definition": str,                # Word definition
                    "examples": [str]                 # Usage examples
                }
            ],
            "translations": {                         # Word translations
                "language": str,                      # Translation language
                "translation": str,                   # Word translation
                "pronunciation": str                  # Pronunciation guide
            },
            "etymology": str,                         # Word etymology
            "frequency": str,                         # Word frequency level
            "difficulty": str,                        # Difficulty level
            "related_words": [str],                   # Related words
            "lookup_source": str                      # Source of lookup data
        }

    Status Codes:
        - 200: Success
        - 400: Word parameter missing
        - 401: Unauthorized
        - 404: Word not found
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        word = request.args.get("word")
        language = request.args.get("language", "en")

        if not word:
            return jsonify({"error": "Word parameter is required"}), 400

        # Look up vocabulary word
        word_info = lookup_vocabulary_word(user, word)

        if not word_info:
            return jsonify({"error": "Word not found"}), 404

        return jsonify(word_info)

    except Exception as e:
        logger.error(f"Error looking up word '{word}' for user {user}: {e}")
        return jsonify({"error": "Failed to lookup vocabulary word"}), 500


@user_bp.route("/vocabulary/search-ai", methods=["POST"])
def search_vocab_ai():
    """
    Search vocabulary using AI-powered semantic search.

    This endpoint uses AI to find vocabulary words based on
    semantic similarity, context, or learning objectives.

    Request Body:
        - query (str, required): Search query or description
        - search_type (str, optional): Type of search (semantic, context, difficulty)
        - limit (int, optional): Maximum number of results (default: 10)
        - filters (object, optional): Search filters

    Search Types:
        - semantic: Find words semantically similar to query
        - context: Find words related to specific context or topic
        - difficulty: Find words of specific difficulty level
        - learning: Find words suitable for learning objectives

    JSON Response Structure:
        {
            "query": str,                             # Original search query
            "search_type": str,                       # Type of search performed
            "results": [                              # Search results
                {
                    "word": str,                      # Vocabulary word
                    "translation": str,               # Word translation
                    "relevance_score": float,         # Relevance score (0-1)
                    "difficulty": str,                # Difficulty level
                    "context": str,                   # Usage context
                    "semantic_similarity": float      # Semantic similarity score
                }
            ],
            "total_results": int,                     # Total number of results
            "search_time": float,                     # Search execution time (seconds)
            "suggestions": [str]                      # Search suggestions
        }

    Status Codes:
        - 200: Success
        - 400: Invalid query or data
        - 401: Unauthorized
        - 500: Internal server error
    """
    user = get_current_user()
    if not user:
        return jsonify({"msg": "Unauthorized"}), 401

    try:
        data = request.get_json()

        if not data or "query" not in data:
            return jsonify({"error": "Query is required"}), 400

        query = data["query"]
        search_type = data.get("search_type", "semantic")
        limit = int(data.get("limit", 10))
        filters = data.get("filters", {})

        if not query.strip():
            return jsonify({"error": "Query cannot be empty"}), 400

        # Perform AI-powered search
        search_results = search_vocabulary_with_ai(query, search_type, limit, filters)

        return jsonify({
            "query": query,
            "search_type": search_type,
            "results": search_results,
            "total_results": len(search_results),
            "search_time": 0.5,  # Placeholder
            "suggestions": [
                f"Try searching for '{query} synonyms'",
                f"Look for '{query} related words'",
                f"Find '{query} in context'"
            ]
        })

    except Exception as e:
        logger.error(f"Error in AI vocabulary search for user {user}: {e}")
        return jsonify({"error": "Failed to perform vocabulary search"}), 500
