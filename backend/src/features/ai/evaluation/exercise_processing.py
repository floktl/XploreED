"""
XplorED - Exercise Processing Module

This module provides exercise processing and AI integration functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Exercise Processing Components:
- Answer Processing: Process AI answers and update topic memory
- Vocabulary Integration: Integrate vocabulary learning with exercise results
- Topic Memory Updates: Update topic memory based on exercise performance
- Result Processing: Process and format exercise results

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import datetime
from typing import List, Optional

from features.ai.memory.vocabulary_memory import review_vocab_word, extract_words
from core.database.connection import *
from features.grammar import detect_language_topics
from features.ai.evaluation.topic_memory import _update_single_topic
from features.ai.memory.logger import topic_memory_logger
from shared.exceptions import DatabaseError, AIEvaluationError
from shared.types import ExerciseAnswers, AnalyticsData

logger = logging.getLogger(__name__)


def process_ai_answers(
    username: str,
    block_id: str,
    answers: ExerciseAnswers,
    exercise_block: Optional[AnalyticsData] = None
) -> List[AnalyticsData]:
    """
    Process AI answers and update topic memory and vocabulary.

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

    results: List[AnalyticsData] = []
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
                from features.ai.evaluation.gap_fill_check import check_gap_fill_correctness
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

                from features.ai.evaluation.topic_evaluation import evaluate_topic_qualities_ai
                logger.info(f"Calling evaluate_topic_qualities_ai for gap-fill exercise")
                logger.info(f"Reference sentence: '{reference_sentence}'")
                logger.info(f"Student sentence: '{student_sentence}'")

                topic_qualities = evaluate_topic_qualities_ai(
                    english="",  # No English translation needed for gap-fill
                    reference=reference_sentence,
                    student=student_sentence
                )

                if topic_qualities:
                    # Calculate average quality score
                    quality_scores = list(topic_qualities.values())
                    if quality_scores:
                        quality = sum(quality_scores) / len(quality_scores)
                        logger.info(f"AI topic evaluation quality score: {quality:.2f}")

                    # Update topic memory for each detected topic
                    for topic, topic_quality in topic_qualities.items():
                        if topic != "unknown":
                            _update_single_topic(
                                username=username,
                                grammar=topic,
                                skill=skill,
                                context=f"gap-fill-exercise-{ex_id}",
                                quality=int(topic_quality),
                                topic=block_topic
                            )

        # Update vocabulary memory for words in the exercise
        try:
            # Extract words from the exercise question and correct answer
            question_words = extract_words(ex.get('question', ''))
            answer_words = extract_words(correct_ans)

            # Combine all words and review them
            all_words = question_words + answer_words
            for word_tuple in all_words:
                word = word_tuple[0] if isinstance(word_tuple, tuple) else word_tuple
                if word and word not in reviewed:
                    review_vocab_word(username, word, int(quality))
                    reviewed.add(word)
                    logger.debug(f"Reviewed vocabulary word: {word}")

        except Exception as e:
            logger.error(f"Error updating vocabulary memory for exercise {ex_id}: {e}")
            raise DatabaseError(f"Error updating vocabulary memory for exercise {ex_id}: {str(e)}")

        # Store the result
        result = {
            "exercise_id": ex_id,
            "user_answer": user_answer,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "quality": quality,
            "skill": skill,
            "topic": block_topic
        }
        results.append(result)

        logger.info(f"Processed exercise {ex_id}: correct={is_correct}, quality={quality}")

    # Check for auto level up
    try:
        from features.ai.memory.level_manager import check_auto_level_up
        if check_auto_level_up(username):
            logger.info(f"User {username} auto-leveled up!")
    except Exception as e:
        logger.error(f"Error checking auto level up for user {username}: {e}")
        raise DatabaseError(f"Error checking auto level up for user {username}: {str(e)}")

    logger.info(f"Completed processing {len(results)} exercises for user {username}")
    return results
