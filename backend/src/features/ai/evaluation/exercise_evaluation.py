"""
XplorED - Exercise Evaluation Module

This module provides core exercise evaluation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Evaluation Components:
- Answer Evaluation: AI-powered assessment of student responses
- Alternative Generation: Creation of multiple correct answer variations
- Explanation Generation: Grammar and vocabulary explanations for correct answers
- Evaluation Processing: Process and format evaluation results

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
import re
import traceback
from typing import Dict, List, Optional

from flask import current_app  # type: ignore

from features.ai.memory.vocabulary_memory import review_vocab_word, extract_words
from core.database.connection import *
from features.grammar import detect_language_topics
from features.ai.evaluation.exercise_helpers import check_gap_fill_correctness
from core.utils.json_helpers import extract_json
from features.ai.prompts import answers_evaluation_prompt, alternative_answers_prompt, explanation_prompt
from external.mistral.client import send_prompt
from features.ai.memory.logger import topic_memory_logger

logger = logging.getLogger(__name__)


def evaluate_answers_with_ai(
    exercises: List[Dict], answers: Dict[str, str], mode: str = "strict"
) -> Optional[Dict]:
    """
    Evaluate exercise answers using AI and return comprehensive results.

    Args:
        exercises: List of exercise dictionaries
        answers: Dictionary mapping exercise IDs to student answers
        mode: Evaluation mode ("strict" or "lenient")

    Returns:
        Dictionary containing evaluation results for each exercise
    """
    try:
        logger.info(f"Starting AI evaluation of {len(exercises)} exercises in {mode} mode")

        results = {}
        overall_feedback = []

        for i, exercise in enumerate(exercises):
            exercise_id = str(i + 1)
            user_answer = answers.get(exercise_id, "").strip()
            exercise_type = exercise.get("type", "unknown")

            logger.debug(f"Evaluating exercise {exercise_id}: type={exercise_type}, answer='{user_answer}'")

            # Skip empty answers
            if not user_answer:
                results[exercise_id] = {
                    "correct": False,
                    "feedback": "No answer provided",
                    "explanation": "",
                    "alternatives": []
                }
                continue

            # Get correct answer
            correct_answer = exercise.get("correctAnswer", "")
            question = exercise.get("question", "")

            # Determine if answer is correct
            is_correct = False
            if exercise_type == "gap-fill":
                is_correct = check_gap_fill_correctness(exercise, user_answer, correct_answer)
            else:
                # For other exercise types, use exact match
                is_correct = user_answer.lower().strip() == correct_answer.lower().strip()

            # Generate AI feedback
            feedback = ""
            explanation = ""
            alternatives = []

            if not is_correct:
                # Generate detailed feedback for incorrect answers
                feedback_prompt = answers_evaluation_prompt(
                    question=question,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    exercise_type=exercise_type
                )

                try:
                    resp = send_prompt(
                        "You are a helpful German teacher.",
                        feedback_prompt,
                        temperature=0.3,
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                        data = extract_json(content)
                        if isinstance(data, dict):
                            feedback = data.get("feedback", "Incorrect answer")
                            explanation = data.get("explanation", "")
                except Exception as e:
                    logger.error(f"Error generating feedback for exercise {exercise_id}: {e}")
                    feedback = "Incorrect answer"

            # Generate alternative answers
            if exercise_type == "gap-fill":
                try:
                    alt_prompt = alternative_answers_prompt(correct_answer)
                    resp = send_prompt(
                        "You are a helpful German teacher.",
                        alt_prompt,
                        temperature=0.3,
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                        data = extract_json(content)
                        if isinstance(data, dict):
                            alternatives = data.get("alternatives", [])
                except Exception as e:
                    logger.error(f"Error generating alternatives for exercise {exercise_id}: {e}")

            # Store results
            results[exercise_id] = {
                "correct": is_correct,
                "feedback": feedback,
                "explanation": explanation,
                "alternatives": alternatives
            }

            # Add to overall feedback
            if not is_correct:
                overall_feedback.append(f"Exercise {exercise_id}: {feedback}")

        # Generate overall feedback
        if overall_feedback:
            results["overall_feedback"] = " ".join(overall_feedback[:3])  # Limit to first 3
        else:
            results["overall_feedback"] = "Great job! All answers are correct."

        logger.info(f"Completed AI evaluation with {len([r for r in results.values() if isinstance(r, dict) and r.get('correct')])} correct answers")
        return results

    except Exception as e:
        logger.error(f"Error in AI evaluation: {e}")
        logger.error(traceback.format_exc())
        return None


def generate_alternative_answers(correct_sentence: str) -> List[str]:
    """
    Generate alternative correct answers for a given sentence.

    Args:
        correct_sentence: The correct sentence to generate alternatives for

    Returns:
        List of alternative correct answers
    """
    try:
        logger.debug(f"Generating alternative answers for: {correct_sentence}")

        prompt = alternative_answers_prompt(correct_sentence)

        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            data = extract_json(content)
            if isinstance(data, dict):
                alternatives = data.get("alternatives", [])
                logger.debug(f"Generated {len(alternatives)} alternative answers")
                return alternatives

        logger.warning("Failed to generate alternative answers")
        return []

    except Exception as e:
        logger.error(f"Error generating alternative answers: {e}")
        return []


def generate_explanation(question: str, user_answer: str, correct_answer: str) -> str:
    """
    Generate an explanation for why an answer is correct or incorrect.

    Args:
        question: The exercise question
        user_answer: The user's answer
        correct_answer: The correct answer

    Returns:
        Explanation string
    """
    try:
        logger.debug(f"Generating explanation for question: {question}")

        prompt = explanation_prompt(question, user_answer, correct_answer)

        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            logger.debug("Generated explanation successfully")
            return content

        logger.warning("Failed to generate explanation")
        return "Explanation not available"

    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        return "Explanation not available"
