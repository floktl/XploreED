# ✅ Common imports used in most route files
from flask import Blueprint, request, jsonify
from backend.utils.session.session_manager import session_manager
import sqlite3
import datetime
from collections import OrderedDict
from bs4 import BeautifulSoup

from utils.lesson_parser import update_lesson_blocks_from_html, inject_block_ids
from utils.db_utils import fetch_all, fetch_one, insert_row, update_row, delete_rows, execute_query, get_connection
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

# ✅ Route-specific grouped imports
class Imports:
    admin = [
        "admin_bp", "request", "jsonify", "session_manager", "BeautifulSoup",
        "fetch_all", "fetch_one", "insert_row", "update_row", "delete_rows",
        "update_lesson_blocks_from_html", "inject_block_ids", "is_admin",
        "get_connection"
    ]

    auth = [
        "auth_bp", "request", "jsonify", "os", "sqlite3", "session_manager",
        "generate_password_hash", "check_password_hash"
    ]

    lesson_progress = [
        "lesson_progress_bp", "request", "jsonify", "datetime",
        "session_manager", "fetch_all", "fetch_one", "execute_query",
        "get_connection"
    ]

    lessons = [
        "lessons_bp", "request", "jsonify", "session_manager", "sqlite3",
        "get_connection"
    ]

    profile = [
        "profile_bp", "jsonify", "get_jwt_identity", "session_manager", "sqlite3"
    ]

    translate = [
        "translate_bp", "request", "jsonify"
    ]

    user = [
        "user_bp", "request", "jsonify", "get_current_user", "fetch_all"
    ]
