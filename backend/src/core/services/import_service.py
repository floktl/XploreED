"""
XplorED - Import Service Management

This module provides centralized import management for route modules,
following clean architecture principles as outlined in the documentation.

Import Categories:
- Flask Framework: Web framework imports and utilities
- Database Operations: Database connection and query functions
- Authentication: Session management and user authentication
- AI Features: AI-powered functionality and evaluation
- Game Features: Interactive learning games and activities
- Utility Functions: Helper functions and utilities

For detailed architecture information, see: docs/backend_structure.md
"""

# === Flask Framework Imports ===
from flask import Blueprint, request, jsonify, make_response, current_app, Response  # type: ignore
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore

# === Standard Library Imports ===
import sqlite3
import datetime
import os
from collections import OrderedDict

# === Third-Party Imports ===
from bs4 import BeautifulSoup  # type: ignore

# === Core Layer Imports ===
# Note: session_manager is imported in route files to avoid circular imports
from core.utils.html_helpers import (
    update_lesson_blocks_from_html,
    inject_block_ids,
    strip_ai_data,
)
from core.database.connection import (
    fetch_all,
    fetch_one,
    insert_row,
    update_row,
    delete_rows,
    execute_query,
    get_connection,
    fetch_custom,
    fetch_one_custom,
    select_rows,
    select_one,
)
from core.utils.helpers import (
    is_admin,
    get_current_user,
    user_exists,
    require_user,
    run_in_background,
)

# === Configuration Imports ===
from config.blueprint import (
    admin_bp,
    auth_bp,
    debug_bp,
    game_bp,
    lesson_progress_bp,
    lessons_bp,
    profile_bp,
    translate_bp,
    user_bp,
    ai_bp,
    support_bp,
    settings_bp,
    progress_test_bp,
)
from config.extensions import limiter

# === Game Features Imports ===
from features.game.sentence_order import (
    LEVELS,
    get_scrambled_sentence,
    evaluate_order,
    save_result,
    get_feedback,
    generate_ai_sentence,
)

# === AI Features Imports ===
from features.ai.memory.vocabulary_memory import (
    split_and_clean,
    save_vocab,
    translate_to_german,
    extract_words,
)
from features.ai.evaluation import (
    evaluate_answers_with_ai,
    process_ai_answers,
    evaluate_translation_ai,
    evaluate_topic_qualities_ai,
    update_topic_memory_translation,
    update_topic_memory_reading,
    compare_topic_qualities
)
from features.spaced_repetition import sm2
from features.ai.generation.exercise_processing import (
    fetch_vocab_and_topic_data,
    compile_score_summary,
    save_exercise_submission_async,
    evaluate_exercises,
    parse_submission_data,
)
from features.ai.generation.exercise_creation import (
    generate_new_exercises,
    generate_training_exercises,
    prefetch_next_exercises,
)
from api.routes.ai.exercise import get_ai_exercise_results
from features.ai.generation.helpers import (
    store_user_ai_data,
)
from features.ai.generation.feedback_helpers import (
    generate_feedback_prompt,
    _adjust_gapfill_results,
)
from features.ai.generation.lesson_generator import update_reading_memory_async
from features.ai.generation.misc_helpers import stream_ai_answer
from features.ai.generation.reading_helpers import (
    generate_reading_exercise,
)
from features.ai.generation.translate_helpers import (
    update_memory_async,
    evaluate_topic_qualities_ai,
)


# === Import Service Class ===
class Imports:
    """
    Centralized import management for route modules.

    This class provides organized import lists for different route modules,
    ensuring consistent imports across the application and reducing code duplication.
    """

    # === Administrative Routes ===
    admin = [
        "admin_bp", "request", "jsonify", "require_user", "BeautifulSoup",
        "fetch_all", "fetch_one", "insert_row", "update_row", "delete_rows",
        "update_lesson_blocks_from_html", "inject_block_ids", "strip_ai_data",
        "is_admin", "OrderedDict"
    ]

    # === Authentication Routes ===
    auth = [
        "auth_bp", "request", "jsonify", "make_response", "os", "sqlite3",
        "generate_password_hash", "check_password_hash", "limiter", "user_exists",
        "fetch_one", "insert_row", "execute_query", "fetch_custom"
    ]

    # === Debug Routes ===
    debug = [
        "debug_bp", "jsonify", "current_app", "sqlite3", "os", "get_ai_exercise_results"
    ]

    # === Game Routes ===
    game = [
        "game_bp", "request", "jsonify",
        "require_user", "os", "LEVELS", "get_scrambled_sentence",
        "evaluate_order", "save_result", "save_vocab", "extract_words",
        "generate_ai_sentence"
    ]

    # === Lesson Progress Routes ===
    lesson_progress = [
        "lesson_progress_bp", "request", "jsonify", "datetime",
        "require_user", "fetch_all", "fetch_one", "execute_query", "fetch_custom"
    ]

    # === Lessons Routes ===
    lessons = [
        "lessons_bp", "request", "jsonify", "require_user",
        "fetch_all", "fetch_one", "execute_query", "fetch_custom"
    ]

    # === Profile Routes ===
    profile = [
        "profile_bp", "jsonify", "require_user",
        "fetch_all", "fetch_custom", "request"
    ]

    # === Translation Routes ===
    translate = [
        "translate_bp", "request", "jsonify",
        "require_user", "translate_to_german",
        "get_feedback", "evaluate_translation_ai", "evaluate_topic_qualities_ai",
        "update_topic_memory_translation", "compare_topic_qualities"
    ]

    # === User Management Routes ===
    user = [
        "user_bp", "request", "jsonify", "require_user", "fetch_all",
        "get_current_user", "fetch_custom", "fetch_one_custom",
        "insert_row", "delete_rows", "save_vocab", "extract_words",
        "sm2"
    ]

    # === AI Features Routes ===
    ai = [
        "ai_bp", "request", "jsonify", "require_user",
        "evaluate_answers_with_ai", "generate_training_exercises", "compile_score_summary",
        "save_exercise_submission_async", "evaluate_exercises", "generate_new_exercises"
    ]

    # === Support Routes ===
    support = [
        "support_bp", "request", "jsonify", "insert_row", "fetch_custom", "is_admin"
    ]

    # === Settings Routes ===
    settings = [
        "settings_bp", "request", "jsonify", "require_user", "os",
        "generate_password_hash", "check_password_hash", "fetch_one",
        "update_row", "delete_rows"
    ]

    # === Progress Test Routes ===
    progress_test = [
        "progress_test_bp", "request", "jsonify", "session_manager", "require_user",
        "fetch_all", "fetch_one", "insert_row", "update_row", "delete_rows",
        "execute_query", "fetch_custom", "fetch_one_custom"
    ]


# === Export Configuration ===
__all__ = [
    "Imports",
]
