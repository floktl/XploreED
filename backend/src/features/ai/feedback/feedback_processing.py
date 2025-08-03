"""
XplorED - AI Feedback Processing Module

This module provides feedback processing and evaluation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Feedback Processing Components:
- Evaluation Summary Processing: Process evaluation results into summaries
- User Data Fetching: Fetch user vocabulary and topic memory
- Data Processing: Process and format user data for feedback
- Text Processing: Process and clean text data

For detailed architecture information, see: docs/backend_structure.md
"""

import logging

from core.database.connection import select_rows
from shared.exceptions import DatabaseError, AIEvaluationError
from shared.types import ExerciseList, ExerciseAnswers, VocabularyList, TopicMemoryList, AnalyticsData

logger = logging.getLogger(__name__)


def _process_evaluation_summary(exercises: ExerciseList, answers: ExerciseAnswers,
                            evaluation: AnalyticsData) -> AnalyticsData:
    """
    Process evaluation results into a summary.

    Args:
        exercises: List of exercises
        answers: User's answers
        evaluation: AI evaluation results

    Returns:
        Dictionary containing evaluation summary
    """
    try:
        total_exercises = len(exercises)
        correct_answers = 0
        incorrect_answers = 0
        skipped_answers = 0

        exercise_details = []

        for i, exercise in enumerate(exercises):
            exercise_id = str(i + 1)
            user_answer = answers.get(exercise_id, "")
            is_correct = evaluation.get(exercise_id, {}).get("correct", False)

            if user_answer.strip() == "":
                skipped_answers += 1
                status = "skipped"
            elif is_correct:
                correct_answers += 1
                status = "correct"
            else:
                incorrect_answers += 1
                status = "incorrect"

            exercise_details.append({
                "exercise_id": exercise_id,
                "user_answer": user_answer,
                "correct_answer": exercise.get("correct_answer", ""),
                "status": status,
                "feedback": evaluation.get(exercise_id, {}).get("feedback", "")
            })

        accuracy = (correct_answers / total_exercises * 100) if total_exercises > 0 else 0

        summary = {
            "total_exercises": total_exercises,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "skipped_answers": skipped_answers,
            "accuracy_percentage": round(accuracy, 2),
            "exercise_details": exercise_details,
            "overall_feedback": evaluation.get("overall_feedback", "")
        }

        logger.debug(f"Processed evaluation summary: {accuracy:.2f}% accuracy")
        return summary

    except Exception as e:
        logger.error(f"Error processing evaluation summary: {e}")
        raise AIEvaluationError(f"Error processing evaluation summary: {str(e)}")


def _fetch_user_vocabulary(username: str) -> VocabularyList:
    """
    Fetch user vocabulary data.

    Args:
        username: The username

    Returns:
        List of vocabulary items
    """
    try:
        vocabulary = select_rows(
            "vocab_log",
            columns=["vocab", "created_at", "last_reviewed"],
            where="username = ?",
            params=(username,),
            order_by="created_at DESC",
            limit=50
        )

        if vocabulary is None:
            vocabulary = []

        logger.debug(f"Fetched {len(vocabulary)} vocabulary items for user {username}")
        return vocabulary

    except Exception as e:
        logger.error(f"Error fetching user vocabulary: {e}")
        raise DatabaseError(f"Error fetching user vocabulary: {str(e)}")


def _fetch_user_topic_memory(username: str) -> TopicMemoryList:
    """
    Fetch user topic memory data.

    Args:
        username: The username

    Returns:
        List of topic memory items
    """
    try:
        topic_memory = select_rows(
            "topic_memory",
            columns=["topic", "strength", "last_reviewed"],
            where="username = ?",
            params=(username,),
            order_by="last_reviewed DESC",
            limit=20
        )

        if topic_memory is None:
            topic_memory = []

        logger.debug(f"Fetched {len(topic_memory)} topic memory items for user {username}")
        return topic_memory

    except Exception as e:
        logger.error(f"Error fetching user topic memory: {e}")
        raise DatabaseError(f"Error fetching user topic memory: {str(e)}")

