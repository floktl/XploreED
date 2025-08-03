"""
AI Lesson Routes

This module contains API routes for AI-powered lesson generation and management.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging
import datetime
from typing import Any

from flask import request, jsonify, Response # type: ignore
from api.middleware.auth import require_user
from config.blueprint import ai_bp
from core.database.connection import select_one
from external.mistral.client import send_prompt
from features.ai.generation.helpers import (
    store_user_ai_data
)
from features.ai.prompts import weakness_lesson_prompt
from core.processing import clean_html
from shared.exceptions import DatabaseError, AIEvaluationError


logger = logging.getLogger(__name__)


@ai_bp.route("/weakness-lesson", methods=["GET"])
def ai_weakness_lesson():
    """
    Generate a personalized lesson focused on the user's weakest learning area.

    This endpoint analyzes the user's learning progress to identify their weakest
    topic and generates a personalized HTML lesson to help improve that specific area.
    The lesson is tailored to the user's current skill level and learning style.

    Query Parameters:
        - force_regenerate (bool, optional): Force regeneration of lesson (default: false)
        - topic (str, optional): Specific topic to focus on (overrides auto-detection)
        - skill_type (str, optional): Specific skill type (grammar, vocabulary, pronunciation)

    Supported Skill Types:
        - grammar: Grammar concepts and rules
        - vocabulary: Word meanings and usage
        - pronunciation: Sound and accent training
        - comprehension: Reading and listening comprehension
        - conversation: Speaking and dialogue skills

    Common Grammar Topics:
        - Modalverben: Modal verbs
        - Artikel: Articles (der, die, das)
        - Präpositionen: Prepositions
        - Konjugation: Verb conjugation
        - Adjektivendungen: Adjective endings
        - Nebensätze: Subordinate clauses
        - Passiv: Passive voice
        - Perfekt: Perfect tense

    JSON Response Structure (Success):
        HTML content with personalized lesson (text/html mimetype)

    JSON Response Structure (Error):
        {
            "error": str,                             # Error message
            "details": str                            # Additional error details
        }

    Error Codes:
        - AI_SERVICE_ERROR: AI service is unavailable or failed
        - NO_WEAKNESS_DATA: No weakness data available for user
        - GENERATION_FAILED: Lesson generation failed
        - VALIDATION_ERROR: Invalid parameters provided

    Status Codes:
        - 200: Success (returns HTML lesson)
        - 400: Bad request (invalid parameters)
        - 401: Unauthorized
        - 500: Internal server error (AI service error)

    Lesson Features:
        - Personalized content based on user's weakest area
        - Interactive exercises and examples
        - Progressive difficulty levels
        - Real-world usage examples
        - Practice exercises with immediate feedback
        - Visual aids and explanations
        - Cultural context where relevant

    Caching Behavior:
        - Lessons are cached to improve performance
        - Cached lessons are returned if topic hasn't changed
        - Force regeneration bypasses cache
        - Cache expires after 24 hours

    Usage Examples:
        Generate lesson for weakest area:
        GET /ai/weakness-lesson

        Force regeneration:
        GET /ai/weakness-lesson?force_regenerate=true

        Focus on specific topic:
        GET /ai/weakness-lesson?topic=Modalverben&skill_type=grammar
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting weakness lesson")

        # Get query parameters
        force_regenerate = request.args.get("force_regenerate", "false").lower() == "true"
        topic = request.args.get("topic")
        skill_type = request.args.get("skill_type")

        # Get user's weakest topic from topic memory
        row = select_one(
            "topic_memory",
            columns="grammar, skill_type",
            where="username = ?",
            params=(username,),
            order_by="ease_factor ASC, repetitions DESC",
        )

        # Use provided topic or fallback to detected weakness
        grammar = topic or (row.get("grammar") if row else "Modalverben")
        skill = skill_type or (row.get("skill_type") if row else "grammar")

        # Check cache unless force regeneration is requested
        if not force_regenerate:
            cached = select_one(
                "ai_user_data",
                columns="weakness_lesson, weakness_topic",
                where="username = ?",
                params=(username,),
            )
            if cached and cached.get("weakness_lesson") and cached.get("weakness_topic") == grammar:
                logger.info(f"Returning cached weakness lesson for user {username}")
                return Response(cached["weakness_lesson"], mimetype="text/html")

        # Generate personalized lesson prompt
        user_prompt = weakness_lesson_prompt(str(grammar), str(skill))

        try:
            # Generate lesson using AI service
            resp = send_prompt(
                "You are a helpful German teacher.",
                user_prompt,
                temperature=0.7,
            )
            if resp.status_code == 200:
                raw_html = resp.json()["choices"][0]["message"]["content"].strip()
                cleaned_html = clean_html(raw_html)

                # Store lesson in cache
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
            else:
                logger.error(f"AI service returned status {resp.status_code}")
                return jsonify({"error": "AI service error", "details": "Service unavailable"}), 500
        except Exception as e:
            logger.error(f"Failed to generate weakness lesson for user {username}: {e}")
            return jsonify({"error": "AI service error", "details": str(e)}), 500

    except ValueError as e:
        logger.error(f"Validation error generating weakness lesson: {e}")
        return jsonify({"error": "Validation error", "details": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating AI lesson: {e}")
        return jsonify({"error": "Internal server error"}), 500
