from utils.imports.imports import *

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_pw = generate_password_hash(password)

    try:
        execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        if user_exists(username):
            return jsonify({"error": "Username already exists"}), 400

        insert_row("users", {"username": username, "password": hashed_pw})
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({"msg": "User created"}), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
    """)

    row = fetch_one("SELECT password FROM users WHERE username = ?", (username,))
    if not row or not check_password_hash(row["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session_id = session_manager.create_session(username)
    resp = make_response(jsonify({"msg": "Login successful"}))
    resp.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return resp


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    print("hello", flush=True)
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
