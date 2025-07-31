"""
Exercise Evaluator

This module contains exercise evaluation and processing functionality for
assessing user responses and generating feedback.

Author: XplorED Team
Date: 2025
"""

import logging
import re
import os
import redis
import json
import time
from typing import Dict, Any, List, Optional, Tuple

from core.services.import_service import *
from features.ai.evaluation.exercise_evaluator import (
    evaluate_answers_with_ai,
    generate_alternative_answers,
    generate_explanation
)
from features.ai.generation.exercise_generator import evaluate_exercises
from features.ai.generation.helpers import _adjust_gapfill_results
from core.database.connection import select_one, select_rows, insert_row, update_row, delete_rows, fetch_one, fetch_all, fetch_custom, execute_query, get_connection

logger = logging.getLogger(__name__)

# Connect to Redis (host from env, default 'localhost')
redis_url = os.getenv('REDIS_URL')
if redis_url:
    redis_client = redis.from_url(redis_url, decode_responses=True)
else:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


def check_gap_fill_correctness(exercise: dict, user_answer: str, correct_answer: str) -> bool:
    """
    Check if a gap-fill answer is correct based on grammatical context.

    Args:
        exercise: The exercise dictionary containing question and type
        user_answer: The user's submitted answer
        correct_answer: The correct answer for comparison

    Returns:
        True if the answer is correct, False otherwise
    """
    try:
        # Get the question text to understand the context
        question = exercise.get("question", "").lower()
        user_ans = user_answer.lower().strip()
        correct_ans = correct_answer.lower().strip()

        logger.debug(f"Checking gap-fill: question='{question}', user='{user_ans}', correct='{correct_ans}'")

        # First try exact match
        if user_ans == correct_ans:
            logger.debug("Exact match found")
            return True

        # Check for common German grammar patterns
        # Pattern 1: Personal pronouns with verb conjugation
        if "habe" in question or "habe " in question:
            # "____ habe einen Hund" - should be "Ich" (1st person singular)
            if user_ans in ["ich", "i"] and correct_ans in ["ich", "i"]:
                logger.debug("Correct 1st person singular with 'habe'")
                return True
            elif user_ans in ["du", "d"] and correct_ans in ["ich", "i"]:
                logger.debug("Wrong: 'du' with 'habe' should be 'ich'")
                return False

        if "bist" in question or "bist " in question:
            # "____ bist glücklich" - should be "Du" (2nd person singular)
            if user_ans in ["du", "d"] and correct_ans in ["du", "d"]:
                logger.debug("Correct 2nd person singular with 'bist'")
                return True
            elif user_ans in ["ich", "i"] and correct_ans in ["du", "d"]:
                logger.debug("Wrong: 'ich' with 'bist' should be 'du'")
                return False

        if "ist" in question or "ist " in question:
            # "____ ist ein Student" - could be "Er", "Sie", "Es" (3rd person singular)
            if user_ans in ["er", "sie", "es"] and correct_ans in ["er", "sie", "es"]:
                logger.debug("Correct 3rd person singular with 'ist'")
                return True

        if "sind" in question or "sind " in question:
            # "____ sind Studenten" - could be "Sie" (3rd person plural) or "Wir" (1st person plural)
            if user_ans in ["sie", "wir"] and correct_ans in ["sie", "wir"]:
                logger.debug("Correct plural with 'sind'")
                return True

        # Pattern 2: Verb conjugation in translations
        # Check for common verb forms
        verb_patterns = {
            "gehen": ["gehe", "gehst", "geht", "gehen", "geht"],
            "kommen": ["komme", "kommst", "kommt", "kommen", "kommt"],
            "machen": ["mache", "machst", "macht", "machen", "macht"],
            "sehen": ["sehe", "siehst", "sieht", "sehen", "seht"],
            "haben": ["habe", "hast", "hat", "haben", "habt"],
            "sein": ["bin", "bist", "ist", "sind", "seid"]
        }

        for base_verb, forms in verb_patterns.items():
            if base_verb in question.lower():
                if user_ans in forms and correct_ans in forms:
                    logger.debug(f"Correct verb conjugation for '{base_verb}'")
                    return True

        # Pattern 3: Articles and gender
        articles = {
            "der": ["der", "den", "dem", "des"],
            "die": ["die", "der", "den"],
            "das": ["das", "dem", "des"]
        }

        for article, forms in articles.items():
            if article in question.lower():
                if user_ans in forms and correct_ans in forms:
                    logger.debug(f"Correct article form for '{article}'")
                    return True

        # If no patterns match, return False
        logger.debug("No matching patterns found, answer incorrect")
        return False

    except Exception as e:
        logger.error(f"Error checking gap-fill correctness: {e}")
        return False


def parse_submission_data(data: Dict[str, Any]) -> Tuple[List[Dict], Dict[str, str], Optional[str]]:
    """
    Parse exercise submission data from request.

    Args:
        data: Request data containing exercises and answers

    Returns:
        Tuple of (exercises, answers, block_id)
    """
    try:
        exercises = data.get("exercises", [])
        answers = data.get("answers", {})
        block_id = data.get("block_id")

        if not exercises:
            raise ValueError("Exercises list is required")

        if not answers:
            raise ValueError("Answers are required")

        logger.info(f"Parsed submission data: {len(exercises)} exercises, {len(answers)} answers")
        return exercises, answers, block_id

    except Exception as e:
        logger.error(f"Error parsing submission data: {e}")
        raise


def evaluate_first_exercise(exercises: List[Dict], answers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Evaluate the first exercise immediately for quick feedback.

    Args:
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers

    Returns:
        Evaluation result for first exercise or None
    """
    try:
        if not exercises:
            return None

        first_exercise = exercises[0]
        exercise_id = str(first_exercise.get("id", 0))
        user_answer = answers.get(exercise_id, "")

        if not user_answer:
            return None

        # Evaluate based on exercise type
        exercise_type = first_exercise.get("type", "gap_fill")

        if exercise_type == "gap_fill":
            correct_answer = first_exercise.get("correct_answer", "")
            is_correct = check_gap_fill_correctness(first_exercise, user_answer, correct_answer)

            result = {
                "exercise_id": exercise_id,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "score": 1.0 if is_correct else 0.0,
                "feedback": "Correct!" if is_correct else f"Correct answer: {correct_answer}"
            }

            logger.info(f"First exercise evaluation: {result}")
            return result

        return None

    except Exception as e:
        logger.error(f"Error evaluating first exercise: {e}")
        return None


def create_immediate_results(exercises: List[Dict], first_result: Optional[Dict]) -> List[Dict[str, Any]]:
    """
    Create immediate results list with first exercise result.

    Args:
        exercises: List of exercise dictionaries
        first_result: Result of first exercise evaluation

    Returns:
        List of exercise results
    """
    try:
        results = []

        if first_result:
            results.append(first_result)

        # Add placeholder results for remaining exercises
        for i in range(1, len(exercises)):
            exercise = exercises[i]
            exercise_id = str(exercise.get("id", i))

            placeholder = {
                "exercise_id": exercise_id,
                "user_answer": "",
                "correct_answer": "",
                "is_correct": False,
                "score": 0.0,
                "feedback": "Processing...",
                "status": "pending"
            }
            results.append(placeholder)

        logger.info(f"Created immediate results for {len(exercises)} exercises")
        return results

    except Exception as e:
        logger.error(f"Error creating immediate results: {e}")
        return []


def evaluate_remaining_exercises_async(username: str, block_id: str, exercises: List[Dict],
                                     answers: Dict[str, str], first_result: Optional[Dict],
                                     exercise_block: Optional[Dict] = None) -> None:
    """
    Evaluate remaining exercises asynchronously.

    Args:
        username: The username
        block_id: Exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        first_result: Result of first exercise evaluation
        exercise_block: Exercise block data
    """
    try:
        logger.info(f"Starting async evaluation for block {block_id}")

        # Store initial results
        initial_results = create_immediate_results(exercises, first_result)

        # Start background evaluation
        from core.utils.helpers import run_in_background
        run_in_background(
            _evaluate_all_exercises,
            username, block_id, exercises, answers, initial_results, exercise_block
        )

    except Exception as e:
        logger.error(f"Error starting async evaluation: {e}")


def _evaluate_all_exercises(username: str, block_id: str, exercises: List[Dict],
                           answers: Dict[str, str], initial_results: List[Dict],
                           exercise_block: Optional[Dict]) -> None:
    """
    Evaluate all exercises in background.

    Args:
        username: The username
        block_id: Exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        initial_results: Initial results list
        exercise_block: Exercise block data
    """
    try:
        logger.info(f"Evaluating all exercises for block {block_id}")

        # Use AI evaluation for comprehensive assessment
        evaluation = evaluate_answers_with_ai(exercises, answers)

        if evaluation:
            # Process and store results
            _process_evaluation_results(username, block_id, exercises, answers, evaluation, exercise_block)
        else:
            logger.error(f"AI evaluation failed for block {block_id}")

    except Exception as e:
        logger.error(f"Error in background evaluation: {e}")


def _process_evaluation_results(username: str, block_id: str, exercises: List[Dict],
                               answers: Dict[str, str], evaluation: Dict,
                               exercise_block: Optional[Dict]) -> None:
    """
    Process and store evaluation results.

    Args:
        username: The username
        block_id: Exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        evaluation: AI evaluation results
        exercise_block: Exercise block data
    """
    try:
        # Store results in database
        results_data = {
            "username": username,
            "block_id": block_id,
            "results": json.dumps(evaluation),
            "created_at": time.time()
        }

        success = insert_row("exercise_results", results_data)

        if success:
            logger.info(f"Stored evaluation results for block {block_id}")
        else:
            logger.error(f"Failed to store evaluation results for block {block_id}")

    except Exception as e:
        logger.error(f"Error processing evaluation results: {e}")


def get_exercise_results(username: str, block_id: str) -> Dict[str, Any]:
    """
    Get exercise results for a user and block.

    Args:
        username: The username
        block_id: Exercise block ID

    Returns:
        Exercise results dictionary
    """
    try:
        logger.info(f"Getting exercise results for user '{username}', block {block_id}")

        # Get results from database
        results = select_one("exercise_results", where="username = ? AND block_id = ?", params=(username, block_id))

        if results:
            try:
                results_data = json.loads(results.get("results", "{}"))
                return {
                    "block_id": block_id,
                    "username": username,
                    "results": results_data,
                    "status": "completed"
                }
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in results for block {block_id}")
                return {"error": "Invalid results data"}
        else:
            # Check if evaluation is still in progress
            redis_key = f"exercise_evaluation:{block_id}"
            if redis_client.exists(redis_key):
                return {
                    "block_id": block_id,
                    "username": username,
                    "status": "processing",
                    "message": "Evaluation in progress"
                }
            else:
                return {
                    "block_id": block_id,
                    "username": username,
                    "status": "not_found",
                    "message": "No results found"
                }

    except Exception as e:
        logger.error(f"Error getting exercise results: {e}")
        return {"error": str(e)}


def argue_exercise_evaluation(block_id: str, exercises: List[Dict], answers: Dict[str, str],
                            exercise_block: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Allow users to argue against exercise evaluation.

    Args:
        block_id: Exercise block ID
        exercises: List of exercise dictionaries
        answers: Dictionary of user answers
        exercise_block: Exercise block data

    Returns:
        Argument evaluation result
    """
    try:
        logger.info(f"Processing exercise evaluation argument for block {block_id}")

        # Re-evaluate with AI
        evaluation = evaluate_answers_with_ai(exercises, answers, allow_arguments=True)

        if evaluation:
            return {
                "block_id": block_id,
                "re_evaluation": evaluation,
                "status": "re_evaluated"
            }
        else:
            return {
                "block_id": block_id,
                "status": "failed",
                "message": "Re-evaluation failed"
            }

    except Exception as e:
        logger.error(f"Error arguing exercise evaluation: {e}")
        return {"error": str(e)}


def get_topic_memory_status(username: str, block_id: str) -> Dict[str, Any]:
    """
    Get topic memory status for a user and exercise block.

    Args:
        username: The username
        block_id: Exercise block ID

    Returns:
        Topic memory status
    """
    try:
        logger.info(f"Getting topic memory status for user '{username}', block {block_id}")

        # Get exercise block to determine topic
        block = select_one("exercise_blocks", where="block_id = ?", params=(block_id,))

        if not block:
            return {"error": "Exercise block not found"}

        # Extract topic from exercises
        try:
            exercises = json.loads(block.get("exercises", "[]"))
            if exercises:
                topic = exercises[0].get("topic", "general")

                # Get memory status from AI memory system
                from features.ai.memory.logger import get_topic_memory_status as get_ai_memory_status
                memory_status = get_ai_memory_status(username, topic)

                return {
                    "username": username,
                    "block_id": block_id,
                    "topic": topic,
                    "memory_status": memory_status
                }
        except json.JSONDecodeError:
            return {"error": "Invalid exercise data"}

    except Exception as e:
        logger.error(f"Error getting topic memory status: {e}")
        return {"error": str(e)}


def _strip_final_punct(text: str) -> str:
    """Remove final punctuation from text."""
    return text.rstrip('.,!?;:')


def _normalize_umlauts(text: str) -> str:
    """Normalize German umlauts in text."""
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss'
    }
    for umlaut, replacement in umlaut_map.items():
        text = text.replace(umlaut, replacement)
    return text
