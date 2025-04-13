# utils/imports/imports.py

# ✅ Common imports used in most route files
from flask import Blueprint, request, jsonify, make_response, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.session.session_manager import session_manager
import sqlite3
import datetime
import os
from collections import OrderedDict
from bs4 import BeautifulSoup
from werkzeug.security import generate_password_hash, check_password_hash
from utils.init_app.extensions import limiter

from utils.lesson_parser import update_lesson_blocks_from_html, inject_block_ids
from utils.db_utils import fetch_all, fetch_one, insert_row, update_row, delete_rows, execute_query, get_connection, fetch_custom, fetch_one_custom
from utils.helper import is_admin, get_current_user, user_exists
from utils.blueprint import (
    admin_bp,
    auth_bp,
    debug_bp,
    game_bp,
    lesson_progress_bp,
    lessons_bp,
    profile_bp,
    translate_bp,
    user_bp,
)
from game.german_sentence_game import (
    LEVELS,
    get_scrambled_sentence,
    evaluate_order,
    save_result,
    translate_to_german,
    get_feedback,
)

# ✅ Route-specific grouped imports
class Imports:
    admin = [
        "admin_bp", "request", "jsonify", "session_manager", "BeautifulSoup",
        "fetch_all", "fetch_one", "insert_row", "update_row", "delete_rows",
        "update_lesson_blocks_from_html", "inject_block_ids", "is_admin",
        "OrderedDict"
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
        "game_bp", "request", "jsonify", "Limiter", "get_remote_address",
        "session_manager", "os", "LEVELS", "get_scrambled_sentence",
        "evaluate_order", "save_result"
    ]

    lesson_progress = [
        "lesson_progress_bp", "request", "jsonify", "datetime",
        "session_manager", "fetch_all", "fetch_one", "execute_query", "fetch_custom"
    ]

    lessons = [
        "lessons_bp", "request", "jsonify", "session_manager",
        "fetch_all", "fetch_one", "execute_query", "fetch_custom"
    ]

    profile = [
        "profile_bp", "jsonify", "jwt_required", "get_jwt_identity", "session_manager",
        "fetch_all", "fetch_custom"
    ]

    translate = [
        "translate_bp", "request", "jsonify",
        "session_manager", "translate_to_german", "get_feedback"
    ]

    user = [
        "user_bp", "request", "jsonify", "session_manager", "fetch_all", "get_current_user", "fetch_custom"
    ]
