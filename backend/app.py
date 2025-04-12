from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import os

# Load environment variables from .env
from dotenv import load_dotenv

# Initialize database tables
from game.german_sentence_game import init_db


# Flask-Limiter instance for rate limiting
from utils.init_app.extensions import limiter

# Centralized list of all Blueprints
from utils.blueprint import registered_blueprints

# === Load environment variables ===
env_path = Path(__file__).resolve().parent / 'secrets' / '.env'
load_dotenv(dotenv_path=env_path)

# === Create and configure Flask app ===
app = Flask(__name__)
app.secret_key = os.getenv("JWT_SECRET_KEY", "super-secret")

# === JWT (JSON Web Token) configuration for secure cookie sessions ===
app.config["JWT_SECRET_KEY"] = app.secret_key
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token_cookie"
app.config["JWT_COOKIE_SECURE"] = False  # Set to True in production (HTTPS)
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # CSRF protection off (for development)

# === Enable CORS (Cross-Origin Resource Sharing) ===
CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": "http://localhost:5173",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

print("🔐 ADMIN_PASSWORD:", os.getenv("ADMIN_PASSWORD"))

# === Initialize rate limiter and database ===
limiter.init_app(app)
init_db()

# === Register all route Blueprints (defined in utils/blueprint.py) ===
for bp in registered_blueprints:
    app.register_blueprint(bp)

# === Run app ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))  # Use .env value or default to 5050
    app.run(host="0.0.0.0", port=port, debug=True)
