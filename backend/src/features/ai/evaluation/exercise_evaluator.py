"""
XplorED - AI Exercise Evaluation Module

This module provides AI-powered exercise evaluation functions for German language learning,
following clean architecture principles as outlined in the documentation.

Evaluation Components:
- Answer Evaluation: AI-powered assessment of student responses
- Alternative Generation: Creation of multiple correct answer variations
- Explanation Generation: Grammar and vocabulary explanations for correct answers
- Answer Processing: Comprehensive processing with topic memory and vocabulary tracking

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
from features.grammar.detector import detect_language_topics
from features.ai.evaluation.translation_evaluator import _update_single_topic, _normalize_umlauts
from core.utils.json_helpers import extract_json
from features.ai.prompts import answers_evaluation_prompt, alternative_answers_prompt, explanation_prompt
from external.mistral.client import send_prompt
from features.ai.memory.logger import topic_memory_logger

logger = logging.getLogger(__name__)


def _normalize_umlauts(text: str) -> str:
    """Normalize German umlauts for comparison."""
    umlaut_map = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        'ß': 'ss'
    }
    for umlaut, replacement in umlaut_map.items():
        text = text.replace(umlaut, replacement)
    return text


def _strip_final_punct(text: str) -> str:
    """Strip final punctuation from text."""
    return text.rstrip(".,!?;:")


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
            "haben": ["habe", "hast", "hat", "haben", "habt"],
            "sein": ["bin", "bist", "ist", "sind", "seid"]
        }

        for verb, forms in verb_patterns.items():
            if verb in question:
                if user_ans in forms and correct_ans in forms:
                    logger.debug(f"Correct verb conjugation for '{verb}'")
                    return True

        # Pattern 3: Articles and gender
        articles = {
            "der": ["der", "den", "dem", "des"],
            "die": ["die", "der", "den"],
            "das": ["das", "dem", "des"]
        }

        for article, forms in articles.items():
            if article in question:
                if user_ans in forms and correct_ans in forms:
                    logger.debug(f"Correct article form for '{article}'")
                    return True

        # Pattern 4: Case endings
        case_endings = {
            "nominative": ["", "e", "er", "es"],
            "accusative": ["en", "e", "es"],
            "dative": ["em", "er", "en"],
            "genitive": ["es", "er", "en"]
        }

        # If no specific patterns match, check for similar forms
        if _normalize_umlauts(user_ans) == _normalize_umlauts(correct_ans):
            logger.debug("Normalized umlaut match found")
            return True

        # Check for common abbreviations
        abbreviations = {
            "ich": "i",
            "du": "d",
            "sie": "s",
            "er": "e",
            "es": "e"
        }

        if user_ans in abbreviations and abbreviations[user_ans] == correct_ans:
            logger.debug(f"Correct abbreviation: {user_ans} -> {correct_ans}")
            return True

        if correct_ans in abbreviations and abbreviations[correct_ans] == user_ans:
            logger.debug(f"Correct abbreviation: {correct_ans} -> {user_ans}")
            return True

        logger.debug("No pattern match found, answer is incorrect")
        return False

    except Exception as e:
        logger.error(f"Error checking gap-fill correctness: {e}")
        return False


def evaluate_answers_with_ai(
    exercises: List[Dict], answers: Dict[str, str], mode: str = "strict"
) -> Optional[Dict]:
    """Evaluate student answers using AI and return JSON results.

    Args:
        exercises: List of exercise dictionaries with id, question, type
        answers: Dictionary mapping exercise IDs to student answers
        mode: Evaluation mode - "strict" or "argue"

    Returns:
        Dictionary with evaluation results or None if evaluation fails
    """
    logger.info(f"Starting AI evaluation with mode={mode}, exercises_count={len(exercises)}, answers_count={len(answers)}")

    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]
    logger.info(f"Formatted {len(formatted)} exercises for evaluation")

    instructions = (
        "Evaluate these answers for a German exercise. "
        "Return JSON with 'pass' (true/false) and a 'results' list. "
        "Each result must include 'id' and 'correct_answer'. "
        "Mark pass true only if all answers are fully correct."
    )
    if mode == "argue":
        instructions = (
            "Reevaluate the student's answers carefully. "
            "Consider possible alternative correct solutions. "
            + instructions
        )

    logger.info(f"Generated evaluation instructions for mode={mode}")
    user_prompt = answers_evaluation_prompt(instructions, formatted)
    logger.info(f"User prompt type: {type(user_prompt)}, content: {user_prompt}")

    try:
        logger.info("Sending evaluation request to Mistral API")
        resp = send_prompt(
            "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        logger.info(f"Mistral response status: {resp.status_code}")

        if resp.status_code == 200:
            logger.info("Mistral evaluation response successful")
            content = resp.json()["choices"][0]["message"]["content"]
            logger.info(f"Raw evaluation response length: {len(content)} characters")

            parsed = extract_json(content)
            if parsed:
                logger.info("Successfully parsed evaluation JSON")
                return parsed
            else:
                logger.error("Failed to parse evaluation JSON from response")
        else:
            logger.error(f"Mistral evaluation request failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        logger.error(f"Exception type: {type(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

    logger.error("AI evaluation failed - returning None")
    return None


def generate_alternative_answers(correct_sentence: str) -> List[str]:
    """Generate alternative ways to say the same thing in German.

    Args:
        correct_sentence: The original German sentence

    Returns:
        List of alternative German sentences with the same meaning
    """
    prompt = alternative_answers_prompt(correct_sentence)
    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            # Try to extract a JSON array from the response robustly
            try:
                # Find the first [ ... ] block in the response
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    arr_str = match.group(0)
                    alternatives = json.loads(arr_str)
                    if isinstance(alternatives, list):
                        return alternatives
                # Fallback: try to parse the whole content
                alternatives = json.loads(content)
                if isinstance(alternatives, list):
                    return alternatives
            except Exception as e:
                logger.error(f"Failed to parse alternatives JSON: {e}")
    except Exception as e:
        logger.error(f"generate_alternative_answers failed: {e}")
    return []


def generate_explanation(question: str, user_answer: str, correct_answer: str) -> str:
    """Generate a short grammar/vocabulary explanation for the correct answer.

    Args:
        question: The exercise question
        user_answer: The student's answer (not used in explanation)
        correct_answer: The correct answer to explain

    Returns:
        Short grammar or vocabulary explanation in English
    """
    prompt = explanation_prompt(question, correct_answer)
    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return content.strip()
    except Exception as e:
        logger.error(f"generate_explanation failed: {e}")
    return ""


def process_ai_answers(
    username: str,
    block_id: str,
    answers: Dict[str, str],
    exercise_block: Optional[Dict] = None
) -> List[Dict]:
    """Process AI answers and update topic memory and vocabulary.

    Args:
        username: The user's username
        block_id: The exercise block identifier
        answers: Dictionary mapping exercise IDs to student answers
        exercise_block: Optional exercise block data

    Returns:
        List of processed results
    """
    logger.info(f"Processing AI answers for user: {username}, block: {block_id}, answers_count: {len(answers)}")

    # Extract block topic for all exercises
    block_topic = exercise_block.get("topic", "general") if exercise_block else "general"
    logger.info(f"Using block topic: '{block_topic}' for all exercises")

    # Create exercise map for easy lookup
    all_exercises = exercise_block.get("exercises", []) if exercise_block else []
    exercise_map = {str(ex.get("id")): ex for ex in all_exercises}
    logger.info(f"Created exercise map with {len(exercise_map)} exercises")

    results: List[Dict] = []
    reviewed: set = set()

    for ex_id, user_answer in answers.items():
        logger.info(f"Processing exercise ID: {ex_id} with answer: '{user_answer}'")
        ex = exercise_map.get(ex_id)
        if not ex:
            logger.warning(f"Exercise {ex_id} not found in exercise map")
            continue

        skill = ex.get("type", "unknown")
        correct_ans = ex.get("correctAnswer", "")
        quality = 2  # Default quality value, will be overridden in specific cases

        # Normalize answers for comparison
        user_ans = _normalize_umlauts(user_answer.strip().lower())
        correct_ans_norm = _normalize_umlauts(correct_ans.strip().lower())

        if user_ans == correct_ans_norm:
            is_correct = True
        else:
            # For gap-fill exercises, check if the answer makes grammatical sense
            exercise_type = ex.get("type", "")
            if exercise_type == "gap-fill":
                is_correct = check_gap_fill_correctness(ex, user_ans, correct_ans_norm)
            else:
                # For other exercise types, use exact match
                is_correct = user_ans == correct_ans_norm

        # Use AI topic evaluation for gap-fill exercises to get nuanced 0-5 scores
        exercise_type = ex.get("type", "")

        # Handle case where user_answer might be the entire question instead of just the gap
        if exercise_type == "gap-fill" and user_answer == ex.get('question', ''):
            logger.warning(f"User answer appears to be the entire question, not just the gap for exercise {ex_id}")

        if exercise_type == "gap-fill":
            # For gap-fill exercises, use AI topic evaluation for nuanced grading
            logger.info("Using AI topic evaluation for gap-fill exercise")

            # Construct the complete sentences for AI evaluation
            question_text = ex.get('question', '')

            # Handle case where user_answer might be the entire question
            actual_user_answer = user_answer
            use_ai_evaluation = True

            if user_answer == question_text:
                logger.warning(f"User answer is the entire question, cannot construct proper sentence for exercise {ex_id}")
                # Fallback: since we can't construct a proper sentence,
                # we'll use the simple binary grading for this exercise
                use_ai_evaluation = False
            else:
                # Normal case: user_answer is just the gap answer
                actual_user_answer = user_answer

            if use_ai_evaluation:
                # Use AI topic evaluation for nuanced grading
                # Construct complete German sentences by replacing ____ with answers
                reference_sentence = question_text.replace('____', correct_ans)
                student_sentence = question_text.replace('____', actual_user_answer)

                from features.ai.evaluation.translation_evaluator import evaluate_topic_qualities_ai
                logger.info(f"Calling evaluate_topic_qualities_ai for gap-fill exercise")
                logger.info(f"Reference sentence: '{reference_sentence}'")
                logger.info(f"Student sentence: '{student_sentence}'")

                topic_qualities = evaluate_topic_qualities_ai(
                    english="",  # No English translation needed for gap-fill
                    reference=reference_sentence,
                    student=student_sentence
                )

                logger.info(f"AI topic qualities: {topic_qualities}")

                # Use the AI topic qualities for individual grammar elements
                features = list(topic_qualities.keys()) if topic_qualities else ["unknown"]

                for feature in features:
                    feature_quality = topic_qualities.get(feature, 2)  # Default to 2 if not found
                    logger.info(f"Updating topic memory for user: {username}, feature: {feature}, skill: {skill}, quality: {feature_quality}")
                    _update_single_topic(
                        username,
                        feature,
                        skill,
                        ex.get("question", ""),
                        feature_quality,
                        block_topic  # Use the block topic for all exercises
                    )
                    logger.info(f"Topic memory updated for feature: {feature} with quality: {feature_quality}")

                # Set quality for vocabulary review (use average of topic qualities or default to 2)
                if topic_qualities:
                    quality = sum(topic_qualities.values()) // len(topic_qualities)
                else:
                    quality = 2
            else:
                # Fallback: use simple binary grading
                if is_correct:
                    quality = 5
                else:
                    quality = 2

                logger.info(f"Using fallback binary grading: {quality}")

                # Use simple topic detection
                features = detect_language_topics(f"{question_text} {correct_ans}") or ["unknown"]
                for feature in features:
                    _update_single_topic(username, feature, skill, question_text, quality, block_topic)
        else:
            # For other exercise types, use simple binary grading
            if is_correct:
                quality = 5
            else:
                quality = 2

            logger.info(f"Exercise {ex_id} - Correct: {is_correct} (Quality: {quality})")

            # Use simple topic detection for non-gap-fill exercises
            logger.info(f"Detecting language topics for exercise: {ex_id}")
            features = detect_language_topics(
                f"{ex.get('question', '')} {correct_ans}"
            ) or ["unknown"]
            logger.info(f"Detected features: {features} for skill: {skill}")

            for feature in features:
                logger.info(f"Updating topic memory for user: {username}, feature: {feature}, skill: {skill}")
                _update_single_topic(
                    username,
                    feature,
                    skill,
                    ex.get("question", ""),
                    quality,
                    block_topic  # Use the block topic for all exercises
                )
                logger.info(f"Topic memory updated for feature: {feature}")

        # Extract and review vocabulary
        logger.info(f"Extracting vocabulary from exercise: {ex_id}")
        question_text_safe = ex.get("question", "") or ""
        correct_ans_safe = correct_ans or ""

        words = (
            [w for w, _ in extract_words(question_text_safe)]
            + [w for w, _ in extract_words(correct_ans_safe)]
        )
        logger.info(f"Extracted {len(words)} words from exercise {ex_id}")

        for vocab in words:
            logger.info(f"Reviewing vocabulary word: '{vocab}'")
            review_vocab_word(username, vocab, quality, seen=reviewed)
            logger.info(f"Vocabulary word '{vocab}' reviewed")

    logger.info(f"Completed processing AI answers for user {username}: {len(results)} results")

    # End session and generate report
    logger.info("About to call topic_memory_logger.end_session")
    report_path = topic_memory_logger.end_session()
    logger.info(f"topic_memory_logger.end_session returned: {report_path}")

    if report_path:
        logger.info(f"Report generated: {report_path}")
    else:
        logger.info("No session to end")

    return results
