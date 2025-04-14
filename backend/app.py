# === app.py ===

from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import os
import sys

# === Load environment variables EARLY ===
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent / 'secrets' / '.env'
load_dotenv(dotenv_path=env_path)

# === Now import modules that rely on env vars ===
from game.german_sentence_game import init_db
import routes.auth  # noqa: F401
import routes.admin
import routes.debug
import routes.game
import routes.lesson_progress
import routes.lessons
import routes.profile
import routes.translate
import routes.user

from utils.init_app.extensions import limiter
from utils.blueprint import registered_blueprints

# === Create and configure Flask app ===
app = Flask(__name__)
# === JWT config ===
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
app.config["JWT_COOKIE_SECURE"] = True
app.config["JWT_COOKIE_SAMESITE"] = "None"
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Prevent CSRF attacks
app.config["JWT_ACCESS_CSRF_HEADER_NAME"] = "X-CSRF-TOKEN"
app.config["JWT_ACCESS_CSRF_FIELD_NAME"] = "csrf_token"

# === Register Blueprints ===
for bp in registered_blueprints:
    app.register_blueprint(bp)

# === Enable CORS ===
CORS(app, origins=os.getenv("FRONTEND_URL"), supports_credentials=True)


# === Init limiter and database ===
limiter.init_app(app)
init_db()

# === Debug registered routes ===
print("\n\ud83d\udd0d Registered Blueprints:", file=sys.stderr, flush=True)
for name, bp in app.blueprints.items():
    print(f" - {name}", file=sys.stderr, flush=True)

print("\n\ud83d\udd0d Registered Routes:", file=sys.stderr, flush=True)
for rule in app.url_map.iter_rules():
    methods = ",".join(sorted(rule.methods))
    print(f" - {rule.rule} [{methods}] \u2192 {rule.endpoint}", file=sys.stderr, flush=True)

# === Run app ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)