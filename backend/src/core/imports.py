"""
XplorED - Core Imports

This module provides centralized imports for the application,
following clean architecture principles as outlined in the documentation.

Import Categories:
- Flask and web framework imports
- Core database and utility imports
- Feature layer imports
- External service imports
- Shared constants and types

For detailed architecture information, see: docs/backend_structure.md
"""

# === Flask and Web Framework Imports ===
from flask import request, jsonify, render_template, make_response, abort # type: ignore
from flask_cors import CORS # type: ignore
from bs4 import BeautifulSoup # type: ignore
import os
import sys # type: ignore
from pathlib import Path

# === Core Layer Imports ===
from core.database.connection import (
    select_rows, insert_row, update_row, delete_rows, fetch_one, select_one
)
from core.authentication import user_exists, get_user_by_username, is_user_admin, validate_user_credentials
from core.processing import strip_ai_data, run_in_background, run_with_timeout, extract_block_ids_from_html
from core.services import UserService, GameService, ExerciseService, VocabularyService

# === Configuration Imports ===
from config.extensions import limiter
from config.blueprint import (
    admin_bp, auth_bp, debug_bp, game_bp, lesson_progress_bp, lessons_bp,
    profile_bp, translate_bp, user_bp, ai_bp, support_bp, settings_bp
)

# === Features Layer Imports ===
# Note: Some functionality has been moved to core.services
# Import specific functions that are still available in features

# Individual feature imports for specific functions
from features.ai.generation.exercise_creation import generate_training_exercises
from features.ai.evaluation import evaluate_answers_with_ai
from features.ai.generation.reading_helpers import generate_reading_exercise
from features.ai.generation.lesson_generator import update_reading_memory_async
from features.ai.generation.misc_helpers import stream_ai_answer
from features.ai.generation.translate_helpers import update_memory_async

# === Vocabulary Feature Imports ===
from features.vocabulary import (
    lookup_vocabulary_word, get_user_vocabulary_entries, delete_user_vocabulary,
    delete_specific_vocabulary, search_vocabulary_with_ai, update_vocabulary_entry,
    get_vocabulary_statistics, get_vocabulary_learning_progress,
    get_vocabulary_difficulty_analysis, get_vocabulary_study_recommendations,
    get_vocabulary_export_data
)

# === Exercise Feature Imports ===
from features.exercise import (
    create_exercise_block,
    get_exercise_block,
    get_user_exercise_blocks,
    submit_exercise_answers,
    get_exercise_results,
    delete_exercise_block,
    update_exercise_block_status,
    get_exercise_statistics,
    check_gap_fill_correctness,
    parse_submission_data,
    evaluate_first_exercise,
    create_immediate_results,
    evaluate_remaining_exercises_async,
    argue_exercise_evaluation,
    get_topic_memory_status,
)


# === Progress Feature Imports ===
# Note: Progress functionality has been moved to ProgressService in core.services
# These imports are kept for backward compatibility but should be replaced with ProgressService calls

# === Lesson Feature Imports ===
# Note: Most lesson functionality has been moved to LessonService in core.services
# These imports are kept for backward compatibility but should be replaced with LessonService calls
from features.lessons import (
    validate_block_completion, update_lesson_content,
    publish_lesson, get_lesson_analytics
)

# === Translation Feature Imports ===
from features.translation import (
    create_translation_job, process_translation_job, get_translation_job_status,
    get_translation_status, stream_translation_feedback, cleanup_expired_jobs
)

# === Profile Feature Imports ===
from features.profile import (
    get_user_game_results, get_user_profile_summary, get_user_achievements,
    get_user_activity_timeline
)

# === Settings Feature Imports ===
from features.settings import (
    update_user_password, deactivate_user_account, debug_delete_user_data,
    get_user_settings, update_user_settings, get_account_statistics,
    export_user_data, import_user_data, validate_import_data
)

# === Support Feature Imports ===
from features.support import (
    submit_feedback, get_feedback_list, get_feedback_by_id, delete_feedback,
    get_feedback_statistics, search_feedback, get_user_feedback, create_support_ticket,
    create_support_request, get_system_status, get_help_content, get_help_topics,
    search_help_content, get_support_request, update_support_request_status,
    get_user_support_requests, get_pending_support_requests
)

# === Admin Feature Imports ===
from features.admin import (
    get_all_game_results,
    get_admin_user_game_results,
    create_lesson_content,
    get_all_lessons,
    get_lesson_by_id,
    update_admin_lesson_content,
    delete_lesson_content,
    get_lesson_progress_summary,
    get_individual_lesson_progress,
    get_all_users,
    update_user_data,
    delete_user_data,
)

# === Debug Feature Imports ===
from features.debug import (
    get_all_database_data,
    debug_user_ai_data,
    get_database_schema,
    get_user_statistics,
)

# === Grammar Feature Imports ===
from features.grammar import (
    detect_language_topics
)

# === Game Feature Imports ===
from features.game import (
    get_user_game_level,
    generate_game_sentence,
    create_game_round,
    evaluate_game_answer,
    get_game_statistics,
    create_game_session,
    update_game_progress,
    calculate_game_score,
)
from features.game.sentence_order import (
    generate_ai_sentence, get_scrambled_sentence, evaluate_order,
    get_feedback, save_result, get_all_results
)

# === User Feature Imports ===
from features.user import (
    create_user_analytics_report, generate_learning_insights, create_comprehensive_user_report
)

# === Auth Feature Imports ===
from features.auth import (
    authenticate_user,
    authenticate_admin,
    create_user_account,
    destroy_user_session,
    get_user_session_info,
    validate_session,
    get_auth_user_statistics,
)

# === External Layer Imports ===
from external.mistral.client import send_prompt, send_request

# === Shared Layer Imports ===
from shared.constants import CEFR_LEVELS
from shared.exceptions import (
    AIEvaluationError, DatabaseError, ValidationError, AuthenticationError,
    ExerciseGenerationError, TopicMemoryError, XplorEDException,
    ConfigurationError, ProcessingError, TimeoutError
)
from shared.types import Exercise, ExerciseBlock, QualityScore, UserLevel

# === AI Feature Constants ===
# Note: These should be moved to shared/constants.py if they're used across modules
EXERCISE_TEMPLATE = "exercise_template"
READING_TEMPLATE = "reading_template"
FEEDBACK_FILE = "feedback_template"


# === Export Configuration ===
__all__ = [
    # Flask imports
    "request", "jsonify", "render_template", "make_response", "abort",
    "CORS", "BeautifulSoup",

    # Core imports
    "select_rows", "insert_row", "update_row", "delete_rows", "fetch_one", "select_one",
    "user_exists", "get_user_by_username", "is_user_admin", "validate_user_credentials",
    "strip_ai_data", "run_in_background", "run_with_timeout", "extract_block_ids_from_html", "limiter",
    "UserService", "GameService", "ExerciseService", "VocabularyService",

    # Blueprint imports
    "admin_bp", "auth_bp", "debug_bp", "game_bp", "lesson_progress_bp", "lessons_bp",
    "profile_bp", "translate_bp", "user_bp", "ai_bp", "support_bp", "settings_bp",

    # Feature imports
    "generate_training_exercises", "evaluate_answers_with_ai", "generate_reading_exercise",
    "update_reading_memory_async", "stream_ai_answer", "update_memory_async",

    # Vocabulary feature imports
    "lookup_vocabulary_word", "get_user_vocabulary_entries", "delete_user_vocabulary",
    "delete_specific_vocabulary", "search_vocabulary_with_ai", "update_vocabulary_entry",
    "get_vocabulary_statistics", "get_vocabulary_learning_progress", "get_vocabulary_difficulty_analysis",
    "get_vocabulary_study_recommendations", "get_vocabulary_export_data",

    # Exercise feature imports
    "create_exercise_block", "get_exercise_block", "get_user_exercise_blocks",
    "submit_exercise_answers", "get_exercise_results", "delete_exercise_block",
    "update_exercise_block_status", "get_exercise_statistics", "check_gap_fill_correctness",
    "parse_submission_data", "evaluate_first_exercise", "create_immediate_results",
    "evaluate_remaining_exercises_async", "argue_exercise_evaluation", "get_topic_memory_status",

    # Progress feature imports
    "track_lesson_progress", "get_lesson_progress", "track_exercise_progress",
    "track_vocabulary_progress", "track_game_progress", "get_user_progress_summary",
    "reset_user_progress", "get_progress_trends", "get_user_lesson_progress",
    "update_block_progress", "mark_lesson_complete", "check_lesson_completion_status",
    "mark_lesson_as_completed", "get_lesson_progress_summary", "reset_lesson_progress",

    # Lesson feature imports
    "get_lesson_content", "get_user_lessons_summary", "get_lesson_progress",
    "update_lesson_progress", "get_lesson_statistics",

    # Translation feature imports
    "create_translation_job", "process_translation_job", "get_translation_job_status",
    "get_translation_status", "stream_translation_feedback", "cleanup_expired_jobs",

    # Profile feature imports
    "get_user_game_results", "get_user_profile_summary", "get_user_achievements",
    "get_user_activity_timeline", "get_user_game_results", "get_user_profile_summary",
    "get_user_achievements",

    # Settings feature imports
    "get_user_settings", "update_user_settings", "update_user_password",
    "deactivate_user_account", "debug_delete_user_data",
    "get_user_settings", "update_user_settings", "get_account_statistics",
    "export_user_data", "import_user_data", "validate_import_data",

    # Support feature imports
    "submit_feedback", "get_feedback_list", "get_feedback_by_id",
    "delete_feedback", "get_feedback_statistics", "search_feedback",
    "get_user_feedback", "create_support_ticket",

    # Admin feature imports
    "get_all_users", "get_all_game_results", "get_admin_user_game_results", "create_lesson_content",
    "get_all_lessons", "get_lesson_progress_summary",
    "get_individual_lesson_progress", "get_lesson_by_id",
    "update_lesson_content",

    # Debug feature imports
    "get_all_database_data", "debug_user_ai_data", "get_database_schema",
    "get_user_statistics", "get_all_database_data", "debug_user_ai_data",
    "get_database_schema", "get_user_statistics",

    # Grammar feature imports
    "detect_language_topics",

    # Game feature imports
    "get_user_game_level", "generate_game_sentence", "create_game_round",
    "evaluate_game_answer", "get_game_statistics", "create_game_session",
    "update_game_progress", "calculate_game_score", "generate_ai_sentence",
    "get_scrambled_sentence", "evaluate_order", "get_feedback", "save_result",
    "get_all_results",

    # User feature imports
    "create_user_analytics_report",

    # Auth feature imports
    "authenticate_user", "authenticate_admin", "create_user_account",
    "destroy_user_session", "get_user_session_info", "validate_session",
    "get_auth_user_statistics",

    # External imports
    "send_prompt", "send_request",

    # Shared imports
    "CEFR_LEVELS", "AIEvaluationError", "DatabaseError", "ValidationError",
    "AuthenticationError", "ExerciseGenerationError", "TopicMemoryError",
    "XplorEDException", "ConfigurationError", "ProcessingError", "TimeoutError",
    "Exercise", "ExerciseBlock", "QualityScore", "UserLevel",

    # Constants
    "EXERCISE_TEMPLATE", "READING_TEMPLATE", "FEEDBACK_FILE",
]
