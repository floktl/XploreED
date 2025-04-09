from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import os

from dotenv import load_dotenv
from german_sentence_game import init_db
from extensions import limiter
# Load .env
env_path = Path(__file__).resolve().parent / 'secrets' / '.env'
load_dotenv(dotenv_path=env_path)

# Init app
app = Flask(__name__)
app.secret_key = os.getenv("JWT_SECRET_KEY", "super-secret")

# ✅ JWT config
app.config["JWT_SECRET_KEY"] = app.secret_key
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False


# CORS
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Extensions
limiter.init_app(app)
init_db()

# Register Blueprints
from routes.auth import auth_bp
from routes.user import user_bp
from routes.game import game_bp
from routes.translate import translate_bp
from routes.lessons import lessons_bp
from routes.admin import admin_bp
from routes.profile import profile_bp
from routes.lesson_progress import lesson_progress_bp

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(game_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(lessons_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(lesson_progress_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
