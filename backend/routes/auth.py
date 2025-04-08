# backend/routes/auth.py

from flask import Blueprint, request, jsonify, make_response
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from session_manager import session_manager
from extensions import limiter

auth_bp = Blueprint("auth", __name__, url_prefix="/api")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# === USER SIGNUP ===
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        with sqlite3.connect("user_data.db") as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            if cur.fetchone():
                return jsonify({"error": "Username already exists"}), 400

            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"msg": "User created"}), 201


# === USER LOGIN ===
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    with sqlite3.connect("user_data.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            );
        """)
        cur = conn.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cur.fetchone()

    if not row or not check_password_hash(row[0], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session_id = session_manager.create_session(username)
    resp = make_response(jsonify({"msg": "Login successful"}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp


# === ADMIN LOGIN ===
@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Invalid credentials"}), 401

    session_id = session_manager.create_session("admin")
    resp = make_response(jsonify({"msg": "Login successful"}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp


# === LOGOUT ===
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session_id = request.cookies.get("session_id")
    session_manager.destroy_session(session_id)
    resp = make_response(jsonify({"msg": "Logout successful"}))
    resp.set_cookie("session_id", "", max_age=0)
    return resp
