"""Lesson and reading exercise routes."""

import datetime
from flask import jsonify, Response, current_app  # type: ignore
from . import ai_bp
from .helpers.helpers import store_user_ai_data
from database import select_one
from utils.html.html_utils import clean_html
from utils.ai.prompts import weakness_lesson_prompt
from utils.helpers.helper import require_user
from utils.ai.ai_api import send_prompt


@ai_bp.route("/weakness-lesson", methods=["GET"])
def ai_weakness_lesson():
    """Return a short HTML lesson focused on the user's weakest topic."""
    username = require_user()

    row = select_one(
        "topic_memory",
        columns=["grammar", "skill_type"],
        where="username = ?",
        params=(username,),
        order_by="ease_factor ASC, repetitions DESC",
    )

    grammar = row.get("grammar") if row else "Modalverben"
    skill = row.get("skill_type") if row else "grammar"

    user_prompt = weakness_lesson_prompt(grammar, skill)

    cached = select_one(
        "ai_user_data",
        columns=["weakness_lesson", "weakness_topic"],
        where="username = ?",
        params=(username,),
    )
    if cached and cached.get("weakness_lesson") and cached.get("weakness_topic") == grammar:
        return Response(cached["weakness_lesson"], mimetype="text/html")

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.7,
        )
        if resp.status_code == 200:
            raw_html = resp.json()["choices"][0]["message"]["content"].strip()
            cleaned_html = clean_html(raw_html)

            store_user_ai_data(
                username,
                {
                    "weakness_lesson": cleaned_html,
                    "weakness_topic": grammar,
                    "lesson_updated_at": datetime.datetime.now().isoformat(),
                },
            )
            return Response(cleaned_html, mimetype="text/html")
    except Exception as e:
        current_app.logger.error("Failed to generate weakness lesson: %s", e)
    return jsonify({"error": "Mistral API error"}), 500
