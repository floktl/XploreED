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
from features.ai.generation.exercise_generator import generate_training_exercises
from features.ai.evaluation.exercise_evaluator import evaluate_answers_with_ai
from features.ai.generation.reading_helpers import generate_reading_exercise
from features.ai.generation.lesson_generator import update_reading_memory_async
from features.ai.generation.misc_helpers import stream_ai_answer
from features.ai.generation.translate_helpers import update_memory_async

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

    # External imports
    "send_prompt", "send_request",

    # Shared imports
    "CEFR_LEVELS", "AIEvaluationError", "DatabaseError", "ValidationError",
    "Exercise", "ExerciseBlock", "QualityScore", "UserLevel",

    # Constants
    "EXERCISE_TEMPLATE", "READING_TEMPLATE", "FEEDBACK_FILE",
]
