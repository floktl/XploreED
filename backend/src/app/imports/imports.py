"""Centralized imports for routes."""

from flask import request, jsonify, render_template, make_response, abort
from flask_cors import CORS
from bs4 import BeautifulSoup
import os
import sys
from pathlib import Path

# Core imports
from core.database.connection import (
    select_rows, insert_row, update_row, delete_rows, fetch_one, select_one
)
from core.utils.helpers import is_admin, require_user, run_in_background, get_current_user, user_exists
from core.utils.html_helpers import strip_ai_data
from app.extensions.extensions import limiter

# Blueprint imports
from app.blueprint import (
    admin_bp, auth_bp, debug_bp, game_bp, lesson_progress_bp, lessons_bp,
    profile_bp, translate_bp, user_bp, ai_bp, support_bp, settings_bp
)

# Features imports
from features.ai.generation.exercise_generator import generate_training_exercises
from features.ai.evaluation.exercise_evaluator import evaluate_answers_with_ai
from features.ai.generation.reading_helpers import generate_reading_exercise
from features.ai.generation.lesson_generator import update_reading_memory_async
from features.ai.generation.misc_helpers import stream_ai_answer
from features.ai.generation.translate_helpers import update_memory_async

# External imports
from external.mistral.client import send_prompt, send_request

# Constants
from features.ai import (
    EXERCISE_TEMPLATE,
    READING_TEMPLATE,
    CEFR_LEVELS,
    FEEDBACK_FILE
)
