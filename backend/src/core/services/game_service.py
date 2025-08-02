"""
XplorED - Game Service

This module provides core game business logic services,
following clean architecture principles as outlined in the documentation.

Game Service Components:
- Game level management
- Game round creation
- Answer evaluation
- Score calculation

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import random
from typing import Dict, Any, Optional, List
from core.database.connection import select_one, fetch_one, insert_row
from core.authentication import user_exists
from core.services.user_service import UserService
from shared.exceptions import ValidationError

logger = logging.getLogger(__name__)


class GameService:
    """Core game business logic service."""

    @staticmethod
    def get_user_game_level(username: str, requested_level: Optional[int] = None) -> int:
        """
        Get the appropriate game level for a user.

        Args:
            username: The username
            requested_level: Optional specific level request

        Returns:
            int: The game level to use

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            if requested_level is not None:
                return int(requested_level)

            # Get user's skill level from database
            level = UserService.get_user_level(username)

            logger.info(f"Using game level {level} for user {username}")
            return int(level)

        except ValidationError as e:
            logger.error(f"Validation error getting game level: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting game level for user {username}: {e}")
            return 1

    @staticmethod
    def create_game_round(username: str, level: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new game round for a user.

        Args:
            username: The username
            level: Optional specific level for the round

        Returns:
            Dict[str, Any]: Dictionary containing game round data

        Raises:
            ValueError: If username is invalid
        """
        try:
            if not username:
                raise ValidationError("Username is required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            # Get appropriate level
            game_level = GameService.get_user_game_level(username, level)

            # Generate sentence for the round
            sentence = GameService._generate_game_sentence(username, game_level)

            # Create round data
            round_data = {
                "username": username,
                "level": game_level,
                "sentence": sentence,
                "scrambled_sentence": GameService._scramble_sentence(sentence),
                "timestamp": GameService._get_current_timestamp(),
                "status": "active"
            }

            logger.info(f"Created game round for user {username} at level {game_level}")
            return round_data

        except ValidationError as e:
            logger.error(f"Validation error creating game round: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating game round for user {username}: {e}")
            raise

    @staticmethod
    def evaluate_game_answer(username: str, level: int, sentence: str, user_answer: str) -> Dict[str, Any]:
        """
        Evaluate a user's game answer.

        Args:
            username: The username
            level: The game level
            sentence: The original sentence
            user_answer: The user's answer

        Returns:
            Dict[str, Any]: Evaluation results

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            if not username or not sentence or user_answer is None:
                raise ValidationError("Username, sentence, and user_answer are required")

            if not user_exists(username):
                raise ValidationError(f"User {username} does not exist")

            # Normalize answers for comparison
            normalized_sentence = GameService._normalize_text(sentence)
            normalized_answer = GameService._normalize_text(user_answer)

            # Check if answer is correct
            is_correct = normalized_answer == normalized_sentence

            # Calculate score
            score = 100 if is_correct else 0

            # Generate feedback
            feedback = GameService._generate_feedback(is_correct, sentence, user_answer)

            # Save vocabulary from sentence
            GameService._save_game_vocabulary(username, sentence, level)

            # Create evaluation result
            result = {
                "username": username,
                "level": level,
                "sentence": sentence,
                "user_answer": user_answer,
                "correct": is_correct,
                "score": score,
                "feedback": feedback,
                "timestamp": GameService._get_current_timestamp()
            }

            # Save result to database
            GameService._save_game_result(result)

            logger.info(f"Evaluated game answer for user {username}: correct={is_correct}, score={score}")
            return result

        except ValueError as e:
            logger.error(f"Validation error evaluating game answer: {e}")
            raise
        except Exception as e:
            logger.error(f"Error evaluating game answer for user {username}: {e}")
            raise

    @staticmethod
    def calculate_game_score(answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall game score from multiple answers.

        Args:
            answers: List of answer evaluation results

        Returns:
            Dict[str, Any]: Overall game score and statistics
        """
        try:
            if not answers:
                return {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "score": 0,
                    "percentage": 0.0,
                    "feedback": "No answers provided"
                }

            total_questions = len(answers)
            correct_answers = sum(1 for answer in answers if answer.get("correct", False))
            score = sum(answer.get("score", 0) for answer in answers)
            percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0.0

            # Generate overall feedback
            if percentage >= 90:
                feedback = "Excellent! You're doing great!"
            elif percentage >= 70:
                feedback = "Good job! Keep practicing!"
            elif percentage >= 50:
                feedback = "Not bad! Try to improve your accuracy."
            else:
                feedback = "Keep practicing! You'll get better with time."

            result = {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "score": score,
                "percentage": round(percentage, 2),
                "feedback": feedback,
                "answers": answers
            }

            logger.info(f"Calculated game score: {correct_answers}/{total_questions} ({percentage:.1f}%)")
            return result

        except Exception as e:
            logger.error(f"Error calculating game score: {e}")
            return {
                "total_questions": 0,
                "correct_answers": 0,
                "score": 0,
                "percentage": 0.0,
                "feedback": "Error calculating score",
                "error": str(e)
            }

    @staticmethod
    def _generate_game_sentence(username: str, level: int) -> str:
        """Generate a sentence for the game at the specified level."""
        try:
            # TODO: Integrate with AI sentence generation
            # For now, use predefined sentences based on level
            predefined_sentences = [
                "Ich gehe zur Schule.",
                "Das ist ein schönes Haus.",
                "Wir essen zusammen zu Abend.",
                "Der Hund läuft im Park.",
                "Sie liest ein interessantes Buch.",
                "Die Kinder spielen im Garten.",
                "Er arbeitet im Büro.",
                "Wir fahren mit dem Auto.",
                "Die Katze schläft auf dem Sofa.",
                "Sie kocht das Abendessen."
            ]

            # Select sentence based on level
            sentence_index = (level - 1) % len(predefined_sentences)
            sentence = predefined_sentences[sentence_index]

            logger.debug(f"Generated sentence for level {level}: {sentence}")
            return sentence

        except Exception as e:
            logger.error(f"Error generating game sentence: {e}")
            return "Das ist ein Test."

    @staticmethod
    def _scramble_sentence(sentence: str) -> str:
        """Scramble the words in a sentence."""
        try:
            words = sentence.split()
            if len(words) <= 1:
                return sentence

            # Don't scramble the first and last words (keep sentence structure)
            if len(words) <= 3:
                return sentence

            # Scramble middle words
            middle_words = words[1:-1]
            random.shuffle(middle_words)

            scrambled = [words[0]] + middle_words + [words[-1]]
            return " ".join(scrambled)

        except Exception as e:
            logger.error(f"Error scrambling sentence: {e}")
            return sentence

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for comparison."""
        try:
            return text.lower().strip().replace(".", "").replace(",", "").replace("!", "").replace("?", "")
        except Exception as e:
            logger.error(f"Error normalizing text: {e}")
            return text.lower().strip()

    @staticmethod
    def _generate_feedback(is_correct: bool, sentence: str, user_answer: str) -> str:
        """Generate feedback for the user's answer."""
        try:
            if is_correct:
                return "Correct! Well done!"
            else:
                return f"Not quite right. The correct answer is: {sentence}"
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return "Answer evaluated."

    @staticmethod
    def _save_game_vocabulary(username: str, sentence: str, level: int) -> None:
        """Save vocabulary words from the game sentence."""
        try:
            # TODO: Implement vocabulary extraction and saving
            logger.debug(f"Would save vocabulary from sentence for user {username}")
        except Exception as e:
            logger.error(f"Error saving game vocabulary: {e}")

    @staticmethod
    def _save_game_result(result: Dict[str, Any]) -> None:
        """Save game result to database."""
        try:
            insert_row("results", result)
            logger.debug(f"Saved game result for user {result.get('username')}")
        except Exception as e:
            logger.error(f"Error saving game result: {e}")

    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current timestamp string."""
        try:
            from datetime import datetime
            return datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error getting timestamp: {e}")
            return ""
