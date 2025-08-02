"""
AI Reading Routes

This module contains API routes for AI-powered reading exercise generation and evaluation.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging
from datetime import datetime

from flask import request, jsonify, current_app # type: ignore
from api.middleware.auth import require_user
from config.blueprint import ai_bp
from external.mistral.client import send_prompt
from features.ai.generation.reading_helpers import (
    ai_reading_exercise
)
from features.ai.generation.feedback_helpers import (
    format_feedback_block
)
from features.ai.evaluation import (
    evaluate_topic_qualities_ai,
    update_topic_memory_reading
)
from shared.text_utils import _strip_final_punct, _normalize_umlauts
from features.ai.prompts import (
    feedback_generation_prompt,
    reading_explanation_prompt,
)
from features.ai.memory.vocabulary_memory import (
    extract_words,
    save_vocab
)


logger = logging.getLogger(__name__)


@ai_bp.route("/reading-exercise", methods=["POST"])
def reading_exercise():
    """
    Generate a reading exercise for the user.

    This endpoint creates AI-powered reading exercises with comprehension
    questions based on the user's skill level and learning progress.

    Request Body:
        - skill_level (str, optional): Target skill level for the exercise
        - topic (str, optional): Specific topic or theme for the reading
        - difficulty (str, optional): Exercise difficulty (easy, medium, hard)
        - length (str, optional): Reading length preference (short, medium, long)

    JSON Response Structure:
        {
            "exercise_id": str,                  # Exercise identifier
            "text": str,                         # Reading text content
            "questions": [                       # Comprehension questions
                {
                    "id": str,                   # Question identifier
                    "question": str,             # Question text
                    "type": str,                 # Question type (multiple_choice, open_ended)
                    "options": [str],            # Answer options (for multiple choice)
                    "correct_answer": str        # Correct answer
                }
            ],
            "metadata": {                        # Exercise metadata
                "skill_level": str,              # Target skill level
                "topic": str,                    # Reading topic
                "difficulty": str,               # Exercise difficulty
                "estimated_time": int,           # Estimated completion time in minutes
                "word_count": int,               # Number of words in text
                "vocabulary_level": str          # Vocabulary complexity level
            },
            "generated_at": str                  # Generation timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid parameters
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.info(f"User {username} requesting reading exercise")

        return ai_reading_exercise()

    except ValueError as e:
        logger.error(f"Validation error generating reading exercise: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error generating reading exercise: {e}")
        return jsonify({"error": "Server error"}), 500


@ai_bp.route("/reading-exercise/submit", methods=["POST"])
def submit_reading_exercise():
    """
    Evaluate reading exercise answers and update memory.

    This endpoint processes user answers to reading comprehension questions,
    provides feedback, and updates the user's learning progress.

    Request Body:
        - exercise_id (str, required): Exercise identifier
        - answers (object, required): User's answers to questions
        - time_spent (int, optional): Time spent on exercise in seconds

    Answer Structure:
        {
            "question_id": str,                  # Question identifier
            "answer": str,                       # User's answer
            "confidence": float                  # User's confidence level (0-1)
        }

    JSON Response Structure:
        {
            "exercise_id": str,                  # Exercise identifier
            "results": [                         # Question results
                {
                    "question_id": str,          # Question identifier
                    "correct": bool,             # Whether answer is correct
                    "user_answer": str,          # User's submitted answer
                    "correct_answer": str,       # Correct answer
                    "feedback": str,             # Detailed feedback
                    "score": float,              # Question score
                    "explanation": str           # Explanation of the answer
                }
            ],
            "summary": {                         # Exercise summary
                "total_questions": int,          # Total number of questions
                "correct_answers": int,          # Number of correct answers
                "accuracy_percentage": float,    # Overall accuracy
                "overall_score": float,          # Overall performance score
                "time_spent": int,               # Time spent in seconds
                "mistakes": [str]                # List of mistakes made
            },
            "vocabulary": {                      # Vocabulary analysis
                "new_words": [str],              # New vocabulary words encountered
                "difficult_words": [str],        # Words that may need review
                "vocabulary_score": float        # Vocabulary comprehension score
            },
            "recommendations": [str],            # Learning recommendations
            "completed_at": str                  # Completion timestamp
        }

    Status Codes:
        - 200: Success
        - 400: Invalid data or exercise not found
        - 401: Unauthorized
        - 500: Internal server error
    """
    try:
        username = require_user()
        logger.info(f"User {username} submitting reading exercise")

        data = request.get_json() or {}
        answers = data.get("answers", {})
        exercise_id = data.get("exercise_id")
        cache = current_app.config.get("READING_EXERCISE_CACHE", {})
        exercise = cache.get(exercise_id)
        if not exercise:
            return jsonify({"error": "Exercise not found or expired"}), 400
        text = exercise.get("text", "")
        questions = exercise.get("questions", [])

        logger.debug(f"Processing {len(questions)} questions for user {username}")

        correct = 0
        results = []
        feedback_blocks = []
        mistakes = []

        for q in questions:
            question_id = q.get("id")
            user_answer = answers.get(question_id, "").strip()
            correct_answer = q.get("correct_answer", "").strip()

            # Simple answer comparison (can be enhanced with AI evaluation)
            is_correct = user_answer.lower() == correct_answer.lower()

            if is_correct:
                correct += 1
            else:
                mistakes.append(f"Question {question_id}: Expected '{correct_answer}', got '{user_answer}'")

            results.append({
                "question_id": question_id,
                "correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "score": 1.0 if is_correct else 0.0
            })

        # Calculate summary
        total_questions = len(questions)
        accuracy_percentage = (correct / total_questions * 100) if total_questions > 0 else 0

        # Extract vocabulary from text
        vocabulary_words = extract_words(text)

        # Save vocabulary to user's learning profile
        def save_vocab_bg():
            try:
                for word_tuple in vocabulary_words:
                    word = word_tuple[0] if isinstance(word_tuple, tuple) else word_tuple
                    save_vocab(username, word)
            except Exception as e:
                logger.error(f"Error saving vocabulary for user {username}: {e}")

        # Run vocabulary saving in background
        from threading import Thread
        Thread(target=save_vocab_bg, daemon=True).start()

        return jsonify({
            "exercise_id": exercise_id,
            "results": results,
            "summary": {
                "total_questions": total_questions,
                "correct_answers": correct,
                "accuracy_percentage": round(accuracy_percentage, 2),
                "overall_score": accuracy_percentage / 100,
                "mistakes": mistakes
            },
            "vocabulary": {
                "new_words": vocabulary_words,
                "vocabulary_score": accuracy_percentage / 100
            },
            "recommendations": [
                "Continue practicing reading comprehension",
                "Review vocabulary words encountered in the text",
                "Focus on understanding context clues"
            ],
            "completed_at": datetime.now().isoformat()
        })

    except ValueError as e:
        logger.error(f"Validation error submitting reading exercise: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting reading exercise: {e}")
        return jsonify({"error": "Server error"}), 500
