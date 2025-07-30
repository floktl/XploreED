"""
German Class Tool - Core Imports

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
from flask import request, jsonify, render_template, make_response, abort
from flask_cors import CORS
from bs4 import BeautifulSoup
import os
import sys
from pathlib import Path

# === Core Layer Imports ===
from core.database.connection import (
    select_rows, insert_row, update_row, delete_rows, fetch_one, select_one
)
from core.utils.helpers import is_admin, require_user, run_in_background, get_current_user, user_exists
from core.utils.html_helpers import strip_ai_data

# === Configuration Imports ===
from config.extensions import limiter
from config.blueprint import (
    admin_bp, auth_bp, debug_bp, game_bp, lesson_progress_bp, lessons_bp,
    profile_bp, translate_bp, user_bp, ai_bp, support_bp, settings_bp
)

# === Features Layer Imports ===
# Import all features for easy access
from features import *

# Individual feature imports for specific functions
from features.ai.generation.exercise_generator import generate_training_exercises
from features.ai.evaluation.exercise_evaluator import evaluate_answers_with_ai
from features.ai.generation.reading_helpers import generate_reading_exercise
from features.ai.generation.lesson_generator import update_reading_memory_async
from features.ai.generation.misc_helpers import stream_ai_answer
from features.ai.generation.translate_helpers import update_memory_async

# === Vocabulary Feature Imports ===
from features.vocabulary.vocabulary_manager import (
    lookup_vocabulary_word, get_user_vocabulary_entries, delete_user_vocabulary,
    delete_specific_vocabulary, search_vocabulary_with_ai, update_vocabulary_entry,
    get_vocabulary_statistics
)
from features.vocabulary.vocabulary_analytics import (
    get_vocabulary_learning_progress, get_vocabulary_difficulty_analysis,
    get_vocabulary_study_recommendations, get_vocabulary_export_data
)

# === Exercise Feature Imports ===
from features.exercise.exercise_manager import (
    create_exercise_block, get_exercise_block, get_user_exercise_blocks,
    submit_exercise_answers, get_exercise_results, delete_exercise_block,
    update_exercise_block_status, get_exercise_statistics
)

# === Progress Feature Imports ===
from features.progress.progress_tracker import (
    track_lesson_progress, get_lesson_progress, track_exercise_progress,
    track_vocabulary_progress, track_game_progress, get_user_progress_summary,
    reset_user_progress, get_progress_trends
)

# === Lesson Feature Imports ===
from features.lessons.lesson_helpers import (
    get_lesson_content, get_user_lessons, create_lesson, update_lesson,
    delete_lesson, get_lesson_statistics
)

# === Translation Feature Imports ===
from features.translation.translation_helpers import (
    translate_text, translate_with_context, get_translation_history,
    save_translation, get_user_translations, delete_translation,
    get_translation_statistics
)

# === Profile Feature Imports ===
from features.profile.profile_helpers import (
    get_user_profile, update_user_profile, get_profile_statistics,
    get_learning_achievements, get_user_preferences, update_user_preferences,
    get_profile_analytics
)

# === Settings Feature Imports ===
from features.settings.settings_helpers import (
    get_user_settings, update_user_settings, get_application_settings,
    update_application_settings, get_notification_settings,
    update_notification_settings, get_privacy_settings, update_privacy_settings
)

# === Support Feature Imports ===
from features.support.support_helpers import (
    get_help_topics, search_help_content, submit_support_ticket,
    get_support_tickets, update_support_ticket, get_faq_content,
    get_tutorial_content, get_contact_information
)

# === Admin Feature Imports ===
from features.admin.admin_helpers import (
    get_all_users, get_user_details, update_user_role, delete_user,
    get_system_statistics, get_lesson_progress_summary,
    get_individual_lesson_progress, get_admin_dashboard_data,
    manage_system_settings
)

# === Debug Feature Imports ===
from features.debug.debug_helpers import (
    get_all_database_data, debug_user_ai_data, get_database_schema,
    get_user_statistics, get_system_health, get_performance_metrics,
    get_error_logs, clear_error_logs
)

# === External Layer Imports ===
from external.mistral.client import send_prompt, send_request

# === Shared Layer Imports ===
from shared.constants import CEFR_LEVELS
from shared.exceptions import AIEvaluationError, DatabaseError, ValidationError
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
    "is_admin", "require_user", "run_in_background", "get_current_user", "user_exists",
    "strip_ai_data", "limiter",

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
    "update_exercise_block_status", "get_exercise_statistics",

    # Progress feature imports
    "track_lesson_progress", "get_lesson_progress", "track_exercise_progress",
    "track_vocabulary_progress", "track_game_progress", "get_user_progress_summary",
    "reset_user_progress", "get_progress_trends",

    # Lesson feature imports
    "get_lesson_content", "get_user_lessons", "create_lesson", "update_lesson",
    "delete_lesson", "get_lesson_statistics",

    # Translation feature imports
    "translate_text", "translate_with_context", "get_translation_history",
    "save_translation", "get_user_translations", "delete_translation",
    "get_translation_statistics",

    # Profile feature imports
    "get_user_profile", "update_user_profile", "get_profile_statistics",
    "get_learning_achievements", "get_user_preferences", "update_user_preferences",
    "get_profile_analytics",

    # Settings feature imports
    "get_user_settings", "update_user_settings", "get_application_settings",
    "update_application_settings", "get_notification_settings",
    "update_notification_settings", "get_privacy_settings", "update_privacy_settings",

    # Support feature imports
    "get_help_topics", "search_help_content", "submit_support_ticket",
    "get_support_tickets", "update_support_ticket", "get_faq_content",
    "get_tutorial_content", "get_contact_information",

    # Admin feature imports
    "get_all_users", "get_user_details", "update_user_role", "delete_user",
    "get_system_statistics", "get_lesson_progress_summary",
    "get_individual_lesson_progress", "get_admin_dashboard_data",
    "manage_system_settings",

    # Debug feature imports
    "get_all_database_data", "debug_user_ai_data", "get_database_schema",
    "get_user_statistics", "get_system_health", "get_performance_metrics",
    "get_error_logs", "clear_error_logs",

    # External imports
    "send_prompt", "send_request",

    # Shared imports
    "CEFR_LEVELS", "AIEvaluationError", "DatabaseError", "ValidationError",
    "Exercise", "ExerciseBlock", "QualityScore", "UserLevel",

    # Constants
    "EXERCISE_TEMPLATE", "READING_TEMPLATE", "FEEDBACK_FILE",
]
