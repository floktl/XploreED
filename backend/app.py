from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_cors import cross_origin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import os
import sqlite3
from dotenv import load_dotenv
import sys
sys.stdout.flush()

# ✅ Load environment variables
print("[DEBUG] Loading environment variables...")
load_dotenv()

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
print(f"[DEBUG] DeepL Key Loaded: {'***' if DEEPL_API_KEY else 'NOT SET'}", flush=True)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("ADMIN_PASSWORD environment variable not set!")

print(f"[DEBUG] Admin password loaded: {'***' if ADMIN_PASSWORD else 'NOT SET'}", flush=True)

# ✅ Import app logic
from german_sentence_game import (
    translate_to_german, get_feedback, get_scrambled_sentence,
    evaluate_order, LEVELS, save_result, get_all_results,
    init_db, User, fetch_lessons_for_user
)

# ✅ Init DB
init_db()

# ✅ Flask app setup
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'super-secret-key'
CORS(app)

# ✅ Rate limiter setup
limiter = Limiter(get_remote_address, app=app)

user_profiles = {}

# ✅ Color-to-HTML converter
def ansi_to_html(text):
    ansi_map = {
        "\x1b[31m": '<span style="color:red;">',
        "\x1b[32m": '<span style="color:green;">',
        "\x1b[33m": '<span style="color:orange;">',
        "\x1b[0m": '</span>',
    }
    pattern = re.compile("|".join(re.escape(code) for code in ansi_map))
    return pattern.sub(lambda m: ansi_map[m.group()], text)

# ✅ Level submit
@limiter.limit("20/minute")
@app.route("/api/level/submit", methods=["POST"])
def level_submit():
    data = request.get_json()
    try:
        level = int(data.get("level", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid level"}), 400

    user_answer = data.get("answer", "").strip()
    username = data.get("username", "anonymous").strip()

    print(f"[DEBUG] /api/level/submit - {username} submitted: {user_answer} for level {level}", flush=True)

    correct_sentence = LEVELS[level]
    correct, feedback = evaluate_order(user_answer, correct_sentence)
    feedback_html = ansi_to_html(feedback)
    save_result(username, level, correct, user_answer)

    return jsonify({
        "correct": correct,
        "feedback": feedback_html,
        "correct_sentence": correct_sentence if os.environ.get("FLASK_ENV") != "production" else None
    })

# ✅ Get a scrambled sentence
@limiter.limit("10/minute")
@app.route("/api/level", methods=["POST"])
def level_game_api():
    data = request.get_json()
    try:
        level = int(data.get("level", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid level"}), 400

    sentence = LEVELS[level]
    scrambled = get_scrambled_sentence(sentence)
    return jsonify({"level": level, "sentence": sentence, "scrambled": scrambled})

# ✅ Profile history
@app.route("/api/profile/<username>")
def profile_api(username):
    print(f"[DEBUG] /api/profile - Fetching history for {username}", flush=True)
    user = user_profiles.get(username, User(username))
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute(
            "SELECT level, correct, answer, timestamp FROM results WHERE username = ? ORDER BY timestamp DESC",
            (username,))
        for lvl, cor, ans, ts in cursor.fetchall():
            user.add_result(lvl, cor, ans, ts)
    return jsonify(user.progress)

# ✅ Vocabulary
@app.route("/api/vocabulary/<username>")
def vocabulary_api(username):
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute(
            "SELECT DISTINCT vocab, translation FROM vocab_log WHERE username = ?", (username,))
        vocab_list = cursor.fetchall()
    return jsonify([{"vocab": v, "translation": t} for v, t in vocab_list])

# ✅ Admin protected endpoint
@app.route("/api/admin/results", methods=["POST"])
def admin_dashboard_api():
    data = request.get_json()
    password = data.get("password", "")

    if password != ADMIN_PASSWORD:
        print("[WARN] Unauthorized access attempt!", flush=True)
        # Apply limiter only here
        @limiter.limit("5 per minute")
        def reject():
            return jsonify({"error": "unauthorized"}), 401
        return reject()

    results = get_all_results()
    return jsonify(results)



# ✅ Translate with DeepL
@limiter.limit("10/minute")
@app.route("/api/translate", methods=["POST", "OPTIONS"])
@cross_origin()
def translate_api():
    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")
    username = data.get("username", "anonymous")

    try:
        german = translate_to_german(english, username)
        if not isinstance(german, str) or "❌" in german:
            return jsonify({
                "german": german,
                "feedback": "❌ Translation failed — check your DeepL API key or sentence."
            })

        correct, feedback = get_feedback(german, student_input)
        return jsonify({
            "german": german,
            "feedback": ansi_to_html(feedback)
        })

    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
        return jsonify({"error": "Translation failed", "details": str(e)}), 500

# ✅ Lessons
@app.route("/api/lessons")
def get_lessons():
    username = request.args.get("username", "anonymous")
    lessons = fetch_lessons_for_user(username)
    return jsonify(lessons)

# ✅ Profile stats
@app.route("/api/profile-stats/<username>", methods=["POST"])
def profile_stats(username):
    data = request.get_json()
    password = data.get("password", "")

    if password != ADMIN_PASSWORD:
        print("[WARN] Unauthorized profile stats access!", flush=True)
        return jsonify({"error": "unauthorized"}), 401

    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute(
            "SELECT level, correct, answer, timestamp FROM results WHERE username = ? ORDER BY timestamp DESC",
            (username,))
        rows = cursor.fetchall()

    return jsonify([
        {"level": l, "correct": bool(c), "answer": a, "timestamp": t}
        for l, c, a, t in rows
    ])


# ✅ Start server
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"[INIT] Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
