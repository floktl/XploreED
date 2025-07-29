"""Endpoints for the sentence ordering game."""

from core.services.import_service import *
from core.utils.html_helpers import ansi_to_html

@game_bp.route("/level", methods=["POST"])
@limiter.limit("10/minute")
def level_game():
    """Return a scrambled sentence for the requested game level."""
    username = require_user()

    data = request.get_json() or {}
    level = data.get("level")
    if level is None:
        row = fetch_one("users", "WHERE username = ?", (username,))
        level = row.get("skill_level", 0) if row else 0
    level = int(level)
    sentence = generate_ai_sentence(username)
    if not sentence:
        sentence = LEVELS[level % len(LEVELS)]
    scrambled = get_scrambled_sentence(sentence)
    return jsonify({"level": level, "sentence": sentence, "scrambled": scrambled})


@game_bp.route("/level/submit", methods=["POST"])
@limiter.limit("20/minute")
def submit_level():
    """Check the player's answer and store the game result."""
    username = require_user()

    data = request.get_json()
    level = int(data.get("level", 0))
    sentence = data.get("sentence") or LEVELS[level % len(LEVELS)]
    user_answer = data.get("answer", "").strip()

    correct, feedback = evaluate_order(user_answer, sentence)
    save_result(username, level, correct, user_answer)

    if correct:
        for word, art in extract_words(sentence):
            save_vocab(
                username,
                word,
                context=sentence,
                exercise=f"game_level_{level}",
                article=art,
            )

    return jsonify(
        {
            "correct": correct,
            "feedback": ansi_to_html(feedback),
            "correct_sentence": (
                sentence if os.getenv("FLASK_ENV") != "production" else None
            ),
        }
    )
