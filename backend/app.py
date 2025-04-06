from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_cors import cross_origin
import re
import os
import sqlite3
import sys
sys.stdout.flush()

def require_env(var_name):
    value = os.getenv(var_name)
    if value is None or value == '':
        print(f"[ERROR] Missing required environment variable: {var_name}", file=sys.stderr)
        sys.exit(1)
    return value

DEEPL_API_KEY = require_env("DEEPL_API_KEY")
print(f"[DEBUG] DeepL Key Loaded: {'***' if DEEPL_API_KEY else 'NOT SET'}", flush=True)

ADMIN_PASSWORD = require_env("ADMIN_PASSWORD")
print(f"[DEBUG] Admin password loaded: {'***' if ADMIN_PASSWORD else 'NOT SET'}", flush=True)

from german_sentence_game import (
    translate_to_german, get_feedback, get_scrambled_sentence,
    evaluate_order, LEVELS, save_result, get_all_results,
    init_db, User, fetch_lessons_for_user  # 👈 make sure this is here
)


init_db()

# Configure Flask
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'super-secret-key'
CORS(app)

user_profiles = {}

# Utility: Color-to-HTML feedback converter
def ansi_to_html(text):
    ansi_map = {
        "\x1b[31m": '<span style="color:red;">',
        "\x1b[32m": '<span style="color:green;">',
        "\x1b[33m": '<span style="color:orange;">',
        "\x1b[0m": '</span>',
    }
    pattern = re.compile("|".join(re.escape(code) for code in ansi_map))
    return pattern.sub(lambda m: ansi_map[m.group()], text)



# ✅ API: Translation with feedback
@app.route("/api/level/submit", methods=["POST"])
def level_submit():
    data = request.get_json()
    level = int(data.get("level"))
    user_answer = data.get("answer")
    username = data.get("username", "anonymous")

    print(f"[DEBUG] /api/level/submit - User '{username}' submitted answer: {user_answer} for level {level}", flush=True)

    correct_sentence = LEVELS[level]
    correct, feedback = evaluate_order(user_answer, correct_sentence)

    # ✅ Convert ANSI to HTML here
    feedback_html = ansi_to_html(feedback)

    save_result(username, level, correct, user_answer)

    print(f"[DEBUG] Correct: {correct}, Feedback: {feedback}", flush=True)
    return jsonify({
        "correct": correct,
        "feedback": feedback_html,
        "correct_sentence": "correct_sentence"
    })

# ✅ API: Level game
@app.route("/api/level", methods=["POST"])
def level_game_api():
    data = request.get_json()
    level = int(data.get("level", 0))
    print(f"[DEBUG] /api/level - Level requested: {level}", flush=True)
    sentence = LEVELS[level]
    scrambled = get_scrambled_sentence(sentence)
    print(f"[DEBUG] Level {level} sentence: {sentence}", flush=True)
    print(f"[DEBUG] Scrambled: {scrambled}", flush=True)
    return jsonify({
        "level": level,
        "sentence": sentence,
        "scrambled": scrambled
    })

# ✅ API: User history
@app.route("/api/profile/<username>")
def profile_api(username):
    print(f"[DEBUG] /api/profile - Fetching history for user: {username}", flush=True)
    user = user_profiles.get(username, User(username))
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("SELECT level, correct, answer, timestamp FROM results WHERE username = ? ORDER BY timestamp DESC", (username,))
        history = cursor.fetchall()
        for lvl, cor, ans, ts in history:
            user.add_result(lvl, cor, ans, ts)

    return jsonify(user.progress)

# ✅ API: Vocabulary
@app.route("/api/vocabulary/<username>")
def vocabulary_api(username):
    print(f"[DEBUG] /api/vocabulary - Fetching vocab for user: {username}", flush=True)
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("SELECT DISTINCT vocab, translation FROM vocab_log WHERE username = ?", (username,))
        vocab_list = cursor.fetchall()

    return jsonify([
        {"vocab": vocab, "translation": translation}
        for vocab, translation in vocab_list
    ])

# ✅ Admin dashboard
@app.route("/api/admin/results")
def admin_dashboard_api():
    password = request.args.get("password", "")
    print(f"[DEBUG] /api/admin/results - Admin password attempt: {'***' if password else 'EMPTY'}", flush=True)
    if password != ADMIN_PASSWORD:
        print("[WARN] Unauthorized access attempt!", flush=True)
        return jsonify({"error": "unauthorized"}), 401
    results = get_all_results()
    return jsonify(results)

@app.route("/api/translate", methods=["POST", "OPTIONS"])
@cross_origin()
def translate_api():
    data = request.get_json()
    english = data.get("english", "")
    student_input = data.get("student_input", "")
    username = data.get("username", "anonymous")

    print(f"[DEBUG] /api/translate - English: {english} ({type(english)})", flush=True)
    print(f"[DEBUG] /api/translate - Student Input: {student_input} ({type(student_input)})", flush=True)
    print(f"[DEBUG] /api/translate - User: {username}", flush=True)

    try:
        german = translate_to_german(english, username=username)
        print(f"[DEBUG] Translated: {german} ({type(german)})", flush=True)

        if not isinstance(german, str) or "❌" in german:
            print("[WARN] Translation failed or returned placeholder", flush=True)
            return jsonify({
                "german": german,
                "feedback": "❌ Translation failed — check your DeepL API key or sentence."
            }), 200
        
        correct, feedback = get_feedback(german, student_input)

        if not isinstance(feedback, str):
            print(f"[ERROR] get_feedback returned non-string: {feedback} ({type(feedback)})", flush=True)
            feedback = "Feedback generation failed."

        return jsonify({
            "german": german,
            "feedback": ansi_to_html(feedback)
        })


    except Exception as e:
        print(f"[ERROR] Translation error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/api/lessons", methods=["GET"])
def get_lessons():
    username = request.args.get("username", "anonymous")
    lessons = fetch_lessons_for_user(username)
    return jsonify(lessons)

@app.route("/api/profile-stats/<username>")
def profile_stats(username):
    print(f"[DEBUG] Fetching detailed stats for user: {username}", flush=True)
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("""
            SELECT level, correct, answer, timestamp
            FROM results
            WHERE username = ?
            ORDER BY timestamp DESC
        """, (username,))
        results = cursor.fetchall()

    return jsonify([
        {
            "level": level,
            "correct": bool(correct),
            "answer": answer,
            "timestamp": timestamp
        }
        for level, correct, answer, timestamp in results
    ])

# ✅ Launch Flask server
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"[INIT] Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
