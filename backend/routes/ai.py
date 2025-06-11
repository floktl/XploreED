from utils.imports.imports import *
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "mock_data" / "ai_exercises.json"

@ai_bp.route("/ai-exercises", methods=["POST"])
def get_ai_exercises():
    session_id = request.cookies.get("session_id")
    username = session_manager.get_user(session_id)
    if not username:
        return jsonify({"msg": "Unauthorized"}), 401

    with open(DATA_FILE, "r") as f:
        mock_data = json.load(f)

    return jsonify(mock_data)

