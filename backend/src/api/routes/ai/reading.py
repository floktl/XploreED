"""
AI Reading Routes

This module contains API routes for AI-powered reading exercise generation and evaluation.
All business logic has been moved to appropriate helper modules to maintain
separation of concerns.

Author: XplorED Team
Date: 2025
"""

import logging

from flask import request, jsonify, current_app # type: ignore
from core.services.import_service import *
from core.utils.helpers import require_user, run_in_background
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
from features.ai.evaluation.translation_evaluation import _strip_final_punct, _normalize_umlauts
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

    Returns:
        JSON response with reading exercise or error details
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

    Returns:
        JSON response with evaluation results or error details
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
            qid = str(q.get("id"))
            sol = str(q.get("correctAnswer", "")).strip().lower()
            ans = str(answers.get(qid, "")).strip().lower()
            # Ignore final . or ? for all exercise types
            sol = _strip_final_punct(sol)
            ans = _strip_final_punct(ans)
            # Normalize umlauts for both answers
            sol = _normalize_umlauts(sol)
            ans = _normalize_umlauts(ans)
            status = "correct" if ans == sol else "incorrect"
            explanation = ""
            if status == "incorrect":
                # Generate a very short explanation using AI
                prompt = reading_explanation_prompt(
                    answers.get(qid, ''),
                    q.get('question'),
                    q.get('correctAnswer')
                )
                try:
                    resp = send_prompt(
                        "You are a helpful German teacher.",
                        prompt,
                        temperature=0.3
                    )
                    logger.debug(f"AI explanation response: {resp.status_code}")
                    if resp.status_code == 200:
                        explanation = resp.json()["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    logger.error(f"Failed to generate per-question explanation: {e}")
                    explanation = ""
            block = format_feedback_block(
                user_answer=answers.get(qid, ""),
                correct_answer=q.get("correctAnswer"),
                alternatives=[],
                explanation=explanation,
                diff=None,
                status=status
            )
            feedback_blocks.append(block)
            if ans == sol:
                correct += 1
            else:
                mistakes.append({
                    "question": q.get("question"),
                    "your_answer": answers.get(qid, ""),
                    "correct_answer": q.get("correctAnswer"),
                })
            results.append({"id": qid, "correct_answer": q.get("correctAnswer")})

        summary = {"correct": correct, "total": len(questions), "mistakes": mistakes}

        # Generate feedbackPrompt using Mistral
        feedbackPrompt = None
        try:
            mistakes_text = "\n".join([
                f"Q: {m['question']}\nYour answer: {m['your_answer']}\nCorrect: {m['correct_answer']}" for m in mistakes
            ])
            prompt = feedback_generation_prompt(correct, len(questions), mistakes_text, "", "")
            resp = send_prompt(
                "You are a helpful German teacher.",
                {"role": "user", "content": prompt},
                temperature=0.5,
            )
            if resp.status_code == 200:
                feedbackPrompt = resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Failed to generate feedback prompt: {e}")

        # Save vocabulary words in background
        def save_vocab_bg():
            try:
                # Extract German words from the text
                words = extract_words(text)
                for word in words:
                    save_vocab(str(username), str(word), "reading_exercise")
                logger.info(f"Saved {len(words)} vocabulary words for user {username}")
            except Exception as e:
                logger.error(f"Failed to save vocabulary words: {e}")

        run_in_background(save_vocab_bg)

        logger.info(f"Reading exercise completed for user {username}: {correct}/{len(questions)} correct")
        return jsonify({
            "pass": correct >= len(questions) * 0.7,  # 70% threshold
            "summary": summary,
            "feedback_blocks": feedback_blocks,
            "feedbackPrompt": feedbackPrompt,
            "results": results
        })

    except ValueError as e:
        logger.error(f"Validation error submitting reading exercise: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error submitting reading exercise: {e}")
        return jsonify({"error": "Server error"}), 500
