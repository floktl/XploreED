"""User authentication routes."""

from utils.imports.imports import *
from utils.level_utils import initialize_topic_memory_for_level

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@auth_bp.route("/debug-login", methods=["GET"])
def debug_login():
    return jsonify({"msg": "working"})

@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute")
def login():
    if request.method == "OPTIONS":
        return '', 200


    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()


    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        row = fetch_one("users", "WHERE username = ?", (username,))

        if not row or not check_password_hash(row["password"], password):
            print("❌ Invalid login attempt: password check failed", flush=True)
            return jsonify({"error": "Invalid username or password"}), 401

        session_id = session_manager.create_session(username)

        resp = make_response(jsonify({"msg": "Login successful"}))
        resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
        return resp
    except Exception as e:
        print(f"❌ Exception during login: {e}", flush=True)
        return jsonify({"error": "Server error"}), 500



@auth_bp.route("/admin/login", methods=["POST", "OPTIONS"])
def admin_login():
    if request.method == "OPTIONS":
        return '', 200
    data = request.get_json()
    if data.get("password") != ADMIN_PASSWORD:
        return jsonify({"error": "Invalid credentials"}), 401

    session_id = session_manager.create_session("admin")
    resp = make_response(jsonify({"msg": "Login successful"}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session_id = request.cookies.get("session_id")
    session_manager.destroy_session(session_id)
    resp = make_response(jsonify({"msg": "Logout successful"}))
    resp.set_cookie("session_id", "", max_age=0)
    return resp

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        if not execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """):

            return jsonify({"error": f"Database error: {str(e)}"}), 500

        if user_exists(username):
            return jsonify({"error": "Username already exists"}), 400

        success = insert_row("users", {"username": username, "password": hashed_pw})
        if not success:
            return jsonify({"error": "User could not be created"}), 500
        initialize_topic_memory_for_level(username, 0)
    except Exception as e:
        print("❌ DB Exception:", e, flush=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"msg": "User created"}), 201
