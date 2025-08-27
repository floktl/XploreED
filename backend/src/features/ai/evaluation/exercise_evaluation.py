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
from typing import List, Optional
from shared.types import ExerciseList, ExerciseAnswers, AnalyticsData

from flask import current_app  # type: ignore

from features.ai.memory.vocabulary_memory import review_vocab_word, extract_words
from core.database.connection import *
from features.grammar import detect_language_topics
from features.ai.evaluation.gap_fill_check import check_gap_fill_correctness
from shared.text_utils import _extract_json as extract_json
from features.ai.prompts import answers_evaluation_prompt, alternative_answers_prompt, explanation_prompt
from external.mistral.client import send_prompt
from features.ai.memory.logger import topic_memory_logger
from core.services import ExerciseService

logger = logging.getLogger(__name__)


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
        Dictionary containing evaluation results for each exercise
    """
    return ExerciseService.evaluate_answers_with_ai(exercises, answers, mode)


def generate_alternative_answers(correct_sentence: str) -> List[str]:
    """
    Generate alternative correct answers for a given sentence.

    Args:
        correct_sentence: The correct sentence to generate alternatives for

    Returns:
        List of alternative correct answers
    """
    # Use service staticmethod (available in ExerciseService)
    return ExerciseService._generate_alternative_answers(correct_sentence)


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
    # Use service staticmethod (available in ExerciseService)
    return ExerciseService._generate_explanation(question, user_answer, correct_answer)
