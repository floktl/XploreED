"""
AI Lesson Routes

This module contains API routes for AI-powered lesson generation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: German Class Tool Team
Date: 2025
"""

import logging
import datetime
from typing import Dict, Any

from flask import request, jsonify, Response # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user
from config.blueprint import ai_bp
from core.database.connection import select_one
from external.mistral.client import send_prompt
from features.ai.generation.helpers import (
    store_user_ai_data
)
from features.ai.prompts.exercise_prompts import (
    weakness_lesson_prompt
)
from core.utils.html_helpers import clean_html


logger = logging.getLogger(__name__)


@ai_bp.route("/weakness-lesson", methods=["GET"])
def ai_weakness_lesson():
    """
    Return a short HTML lesson focused on the user's weakest topic.

    This endpoint generates personalized lessons based on the user's
    identified weaknesses in their learning progress.

    Returns:
        HTML response with personalized lesson content or error details
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting weakness lesson")

        row = select_one(
            "topic_memory",
            columns="grammar, skill_type",
            where="username = ?",
            params=(username,),
            order_by="ease_factor ASC, repetitions DESC",
        )

        grammar = row.get("grammar") if row else "Modalverben"
        skill = row.get("skill_type") if row else "grammar"

        user_prompt = weakness_lesson_prompt(str(grammar), str(skill))

        cached = select_one(
            "ai_user_data",
            columns="weakness_lesson, weakness_topic",
            where="username = ?",
            params=(username,),
        )
        if cached and cached.get("weakness_lesson") and cached.get("weakness_topic") == grammar:
            logger.info(f"Returning cached weakness lesson for user {username}")
            return Response(cached["weakness_lesson"], mimetype="text/html")

        try:
            resp = send_prompt(
                "You are a helpful German teacher.",
                {"role": "user", "content": user_prompt},
                temperature=0.7,
            )
            if resp.status_code == 200:
                raw_html = resp.json()["choices"][0]["message"]["content"].strip()
                cleaned_html = clean_html(raw_html)

                store_user_ai_data(
                    str(username),
                    {
                        "weakness_lesson": cleaned_html,
                        "weakness_topic": grammar,
                        "lesson_updated_at": datetime.datetime.now().isoformat(),
                    },
                )
                logger.info(f"Successfully generated weakness lesson for user {username}")
                return Response(cleaned_html, mimetype="text/html")
        except Exception as e:
            logger.error(f"Failed to generate weakness lesson for user {username}: {e}")
            return jsonify({"error": "AI service error"}), 500

    except ValueError as e:
        logger.error(f"Validation error generating weakness lesson: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating weakness lesson: {e}")
        return jsonify({"error": "Server error"}), 500
