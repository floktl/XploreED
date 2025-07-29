"""Centralised import lists to keep route modules short."""

# ✅ Common imports used in most route files
from flask import Blueprint, request, jsonify, make_response, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.session.session_manager import session_manager
import sqlite3
import datetime
import os
from collections import OrderedDict
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash, check_password_hash

from utils.html.lesson_parser import (
    update_lesson_blocks_from_html,
    inject_block_ids,
    strip_ai_data,
)
from database import (
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
from utils.helpers.helper import (
    is_admin,
    get_current_user,
    user_exists,
    require_user,
)
from app.blueprint import (
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

from game.sentence_order_game import (
    LEVELS,
    get_scrambled_sentence,
    evaluate_order,
    save_result,
    get_feedback,
    generate_ai_sentence,
)

from utils.spaced_repetition.vocab_utils import (
    split_and_clean,
    save_vocab,
    translate_to_german,
    extract_words,
)
from utils.ai.translation_utils import (
    evaluate_translation_ai,
    update_topic_memory_translation,
)
from utils.spaced_repetition.algorithm import sm2
from routes.ai.helpers.ai_evaluation_helpers import (
    evaluate_answers_with_ai,
    process_ai_answers,
)
from routes.ai.helpers.exercise_helpers import (
    fetch_vocab_and_topic_data,
    compile_score_summary,
    save_exercise_submission_async,
    evaluate_exercises,
    parse_submission_data,
    generate_new_exercises,
    generate_training_exercises,
    prefetch_next_exercises,
)
from routes.ai.helpers.helpers import (
    generate_feedback_prompt,
    store_user_ai_data,
    _adjust_gapfill_results,
)
from routes.ai.helpers.lesson_helpers import update_reading_memory_async
from routes.ai.helpers.misc_helpers import stream_ai_answer
from routes.ai.helpers.reading_helpers import (
    generate_reading_exercise,
    ai_reading_exercise,
)
from routes.ai.helpers.translate_helpers import update_memory_async
from routes.ai.helpers.user_helpers import (
    fetch_vocab_entries,
    select_vocab_word_due_for_review,
    update_vocab_after_review,
)

from utils.ai.prompts import (
    exercise_generation_prompt,
    feedback_generation_prompt,
)
from utils.ai.prompt_utils import (
    make_prompt,
)
from utils.ai.ai_api import (
    send_request,
    send_prompt,
)
from utils.data.json_utils import extract_json

# ✅ Route-specific grouped imports
class Imports:
    admin = [
        "admin_bp", "request", "jsonify", "session_manager", "require_user", "BeautifulSoup",
        "fetch_all", "fetch_one", "insert_row", "update_row", "delete_rows",
        "update_lesson_blocks_from_html", "inject_block_ids", "strip_ai_data",
        "is_admin", "OrderedDict"
    ]

    auth = [
        "auth_bp", "request", "jsonify", "make_response", "os", "sqlite3", "session_manager",
        "generate_password_hash", "check_password_hash", "limiter", "user_exists",
        "fetch_one", "insert_row", "execute_query", "fetch_custom"
    ]

    debug = [
        "debug_bp", "jsonify", "current_app", "sqlite3", "os"
    ]

    game = [
        "game_bp", "request", "jsonify",
        "session_manager", "require_user", "os", "LEVELS", "get_scrambled_sentence",
        "evaluate_order", "save_result", "save_vocab", "extract_words",
        "generate_ai_sentence"
    ]

    lesson_progress = [
        "lesson_progress_bp", "request", "jsonify", "datetime",
        "session_manager", "require_user", "fetch_all", "fetch_one", "execute_query", "fetch_custom"
    ]

    lessons = [
        "lessons_bp", "request", "jsonify", "session_manager", "require_user",
        "fetch_all", "fetch_one", "execute_query", "fetch_custom"
    ]

    profile = [
        "profile_bp", "jsonify", "session_manager", "require_user",
        "fetch_all", "fetch_custom", "request"
    ]

    translate = [
        "translate_bp", "request", "jsonify",
        "session_manager", "require_user", "translate_to_german",
        "get_feedback", "evaluate_translation_ai", "evaluate_topic_qualities_ai",
        "update_topic_memory_translation", "compare_topic_qualities"
    ]

    user = [
        "user_bp", "request", "jsonify", "session_manager", "require_user", "fetch_all",
        "get_current_user", "fetch_custom", "fetch_one_custom",
        "insert_row", "delete_rows", "save_vocab", "extract_words",
        "sm2"
    ]

    ai = [
        "ai_bp", "request", "jsonify", "session_manager", "require_user",
        "evaluate_answers_with_ai", "generate_training_exercises", "compile_score_summary",
        "save_exercise_submission_async", "evaluate_exercises", "generate_new_exercises"
    ]

    support = [
        "support_bp", "request", "jsonify", "insert_row", "fetch_custom", "is_admin"
    ]

    settings = [
        "settings_bp", "request", "jsonify", "session_manager", "require_user", "os",
        "generate_password_hash", "check_password_hash", "fetch_one",
        "update_row", "delete_rows"
    ]

    progress_test = [
        "progress_test_bp", "request", "jsonify", "session_manager", "require_user",
        "generate_ai_sentence", "get_scrambled_sentence", "evaluate_order",
        "generate_training_exercises", "evaluate_answers_with_ai",
        "generate_reading_exercise", "translate_to_german",
        "evaluate_translation_ai", "fetch_one", "update_row", "random", "LEVELS"
    ]

# ✅ Export list
__all__ = [
    # Flask & system
    "Blueprint", "request", "jsonify", "make_response", "current_app",
    "Limiter", "get_remote_address", "session_manager",
    "sqlite3", "datetime", "os", "OrderedDict", "BeautifulSoup",
    "generate_password_hash", "check_password_hash",

    # DB
    "fetch_all", "fetch_one", "insert_row", "update_row", "delete_rows",
    "execute_query", "get_connection", "fetch_custom", "fetch_one_custom",
    "select_rows", "select_one",

    # Lesson helpers
    "update_lesson_blocks_from_html", "inject_block_ids", "strip_ai_data",

    # Global utils
    "is_admin", "get_current_user", "user_exists", "require_user",

    # Blueprints
    "admin_bp", "auth_bp", "debug_bp", "game_bp", "lesson_progress_bp",
    "lessons_bp", "profile_bp", "translate_bp", "user_bp",
    "ai_bp", "support_bp", "settings_bp", "progress_test_bp",

    # Game logic
    "LEVELS", "get_scrambled_sentence", "evaluate_order", "save_result",
    "get_feedback", "generate_ai_sentence",

    # Vocab & AI
    "split_and_clean", "save_vocab", "translate_to_german", "extract_words",
    "evaluate_translation_ai", "update_topic_memory_translation",

    # Spaced repetition
    "sm2",

    # AI Evaluation
    "evaluate_answers_with_ai", "evaluate_exercises", "compile_score_summary",
    "generate_new_exercises", "generate_training_exercises", "save_exercise_submission_async",

    # Prompt helpers
    "make_prompt", "extract_json", "send_request", "send_prompt",
    "exercise_generation_prompt", "feedback_generation_prompt",

    # Grouped imports
    "Imports"
]
