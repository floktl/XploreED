"""Flask application setup and route registration."""

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from pathlib import Path
import os
import sys

# === Load environment variables EARLY ===
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv(dotenv_path=None, **_):  # type: ignore
        if dotenv_path and os.path.exists(dotenv_path):
            with open(dotenv_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key, value)

env_path = Path(__file__).resolve().parent / 'secrets' / '.env'
load_dotenv(dotenv_path=env_path)

# === Now import modules that rely on env vars ===
import routes.auth  # noqa: F401
import routes.admin
import routes.debug
import routes.game
import routes.lesson_progress
import routes.lessons
import routes.profile
import routes.translate
import routes.user
import routes.ai
import routes.support
import routes.settings
import routes.progress_test

from utils.init_app.extensions import limiter
from utils.blueprint import registered_blueprints

# from routes.ai import ai_bp
# app.register_blueprint(ai_bp, url_prefix="/api")

# === Create and configure Flask app ===
app = Flask(__name__)
# === JWT config ===
debug_mode = os.getenv("FLASK_ENV", "development") == "development"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
app.config["JWT_COOKIE_SECURE"] = os.getenv("JWT_COOKIE_SECURE", "false").lower() == "true"
app.config["JWT_COOKIE_CSRF_PROTECT"] = os.getenv("JWT_COOKIE_CSRF_PROTECT", "false").lower() == "true"
app.config["JWT_ACCESS_CSRF_HEADER_NAME"] = "X-CSRF-TOKEN"
app.config["JWT_ACCESS_CSRF_FIELD_NAME"] = "csrf_token"
if debug_mode:
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
else:
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True

# === Register Blueprints ===
for bp in registered_blueprints:
    app.register_blueprint(bp)

# === Enable CORS ===
allowed_origin = os.getenv("FRONTEND_URL", "").split(",")
CORS(app, origins=allowed_origin, supports_credentials=True)


# === Init limiter and database ===
limiter.init_app(app)


@app.errorhandler(500)
def server_error(_):
    """Return custom 500 error page."""
    return render_template("500.html"), 500

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
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
