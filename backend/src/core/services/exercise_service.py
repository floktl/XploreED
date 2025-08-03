"""
XplorED - Exercise Service

This module provides core exercise evaluation business logic services,
following clean architecture principles as outlined in the documentation.

Exercise Service Components:
- Answer evaluation
- Alternative answer generation
- Explanation generation
- Gap-fill correctness checking

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import re
from typing import List, Optional
from shared.text_utils import _extract_json as extract_json
from shared.types import ExerciseList, ExerciseAnswers, AnalyticsData

logger = logging.getLogger(__name__)


class ExerciseService:
    """Core exercise evaluation business logic service."""

    @staticmethod
    def evaluate_answers_with_ai(
        exercises: ExerciseList, answers: ExerciseAnswers, mode: str = "strict"
    ) -> Optional[AnalyticsData]:
        """
        Evaluate exercise answers using AI and return comprehensive results.

        Args:
            exercises: List of exercise dictionaries
            answers: Dictionary mapping exercise IDs to student answers
            mode: Evaluation mode ("strict" or "lenient")

        Returns:
            Optional[AnalyticsData]: Dictionary containing evaluation results for each exercise
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
                is_correct = ExerciseService._check_answer_correctness(
                    exercise, user_answer, correct_answer, exercise_type
                )

                # Generate feedback and explanation
                feedback = ""
                explanation = ""
                alternatives = []

                if not is_correct:
                    # Generate detailed feedback for incorrect answers
                    feedback = ExerciseService._generate_feedback(
                        question, user_answer, correct_answer, exercise_type
                    )
                    explanation = ExerciseService._generate_explanation(
                        question, user_answer, correct_answer
                    )
                    alternatives = ExerciseService._generate_alternative_answers(correct_answer)

                results[exercise_id] = {
                    "correct": is_correct,
                    "feedback": feedback,
                    "explanation": explanation,
                    "alternatives": alternatives,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer
                }

            logger.info(f"Completed AI evaluation with {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in AI evaluation: {e}")
            return None

    @staticmethod
    def check_gap_fill_correctness(exercise: AnalyticsData, user_answer: str, correct_answer: str) -> bool:
        """
        Check if a gap-fill answer is correct.

        Args:
            exercise: Exercise data containing gap-fill data
            user_answer: User's answer
            correct_answer: Correct answer

        Returns:
            bool: True if answer is correct, False otherwise
        """
        try:
            if not user_answer or not correct_answer:
                return False

            # Normalize answers
            normalized_user = ExerciseService._normalize_answer(user_answer)
            normalized_correct = ExerciseService._normalize_answer(correct_answer)

            # Check exact match first
            if normalized_user == normalized_correct:
                return True

            # Check for alternative answers if available
            alternatives = exercise.get("alternatives", [])
            for alt in alternatives:
                if ExerciseService._normalize_answer(alt) == normalized_user:
                    return True

            # Check for partial matches (for lenient mode)
            if ExerciseService._check_partial_match(normalized_user, normalized_correct):
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking gap-fill correctness: {e}")
            return False

    @staticmethod
    def _generate_alternative_answers(correct_sentence: str) -> List[str]:
        """
        Generate alternative correct answers for a sentence.

        Args:
            correct_sentence: The correct sentence

        Returns:
            List[str]: List of alternative correct answers
        """
        try:
            alternatives = []

            # Basic alternatives
            if correct_sentence:
                # Remove punctuation variations
                no_punct = correct_sentence.replace(".", "").replace(",", "").replace("!", "").replace("?", "")
                if no_punct != correct_sentence:
                    alternatives.append(no_punct)

                # Case variations
                lower_case = correct_sentence.lower()
                if lower_case != correct_sentence:
                    alternatives.append(lower_case)

                # Capitalize first letter
                if correct_sentence and correct_sentence[0].islower():
                    capitalized = correct_sentence[0].upper() + correct_sentence[1:]
                    alternatives.append(capitalized)

            logger.debug(f"Generated {len(alternatives)} alternative answers for: {correct_sentence}")
            return alternatives

        except Exception as e:
            logger.error(f"Error generating alternative answers: {e}")
            return []

    @staticmethod
    def _generate_explanation(question: str, user_answer: str, correct_answer: str) -> str:
        """
        Generate explanation for why an answer is correct or incorrect.

        Args:
            question: The exercise question
            user_answer: User's answer
            correct_answer: Correct answer

        Returns:
            str: Explanation text
        """
        try:
            if not user_answer or not correct_answer:
                return "No answer provided."

            # Basic explanation logic
            if user_answer.lower().strip() == correct_answer.lower().strip():
                return "Your answer is correct! Well done!"
            else:
                return f"The correct answer is '{correct_answer}'. Your answer was '{user_answer}'."

        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return "Explanation could not be generated."

    @staticmethod
    def _check_answer_correctness(
        exercise: AnalyticsData, user_answer: str, correct_answer: str, exercise_type: str
    ) -> bool:
        """Check if an answer is correct based on exercise type."""
        try:
            if exercise_type == "gap-fill":
                return ExerciseService.check_gap_fill_correctness(exercise, user_answer, correct_answer)
            else:
                # For other exercise types, use exact match
                return user_answer.lower().strip() == correct_answer.lower().strip()

        except Exception as e:
            logger.error(f"Error checking answer correctness: {e}")
            return False

    @staticmethod
    def _generate_feedback(question: str, user_answer: str, correct_answer: str, exercise_type: str) -> str:
        """Generate feedback for incorrect answers."""
        try:
            if exercise_type == "gap-fill":
                return f"Try again. The correct answer is '{correct_answer}'."
            else:
                return f"Not quite right. The correct answer is '{correct_answer}'."

        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return "Answer evaluated."

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        """Normalize answer for comparison."""
        try:
            return answer.lower().strip().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
        except Exception as e:
            logger.error(f"Error normalizing answer: {e}")
            return answer.lower().strip() if answer else ""

    @staticmethod
    def _check_partial_match(user_answer: str, correct_answer: str) -> bool:
        """Check for partial matches between answers."""
        try:
            # Simple partial match: check if user answer is contained in correct answer
            # or vice versa (for longer/shorter variations)
            user_words = set(user_answer.split())
            correct_words = set(correct_answer.split())

            # If user answer contains most of the correct words
            if len(user_words) >= 2 and len(correct_words) >= 2:
                common_words = user_words.intersection(correct_words)
                if len(common_words) >= min(len(user_words), len(correct_words)) * 0.8:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking partial match: {e}")
            return False
