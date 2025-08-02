"""
XplorED - Topic Evaluation Module

This module provides topic quality evaluation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Topic Evaluation Components:
- Topic Quality Assessment: Evaluate grammar topic quality using AI
- Topic Detection: Detect grammar topics in text
- Quality Scoring: Score topic quality on a 0-5 scale
- Topic Analysis: Analyze topic performance and patterns

For detailed architecture information, see: docs/backend_structure.md
"""

import json
import re
from typing import Dict, List

from features.grammar import detect_language_topics
from shared.text_utils import _extract_json
from features.ai.prompts import quality_evaluation_prompt
from external.mistral.client import send_prompt

import logging
logger = logging.getLogger(__name__)


def evaluate_topic_qualities_ai(english: str, reference: str, student: str) -> Dict[str, int]:
    """
    Evaluate grammar topic quality using AI.

    Args:
        english: The original English text
        reference: The reference German translation
        student: The student's German translation

    Returns:
        Dictionary mapping grammar topics to quality scores (0-5)
    """
    topics = sorted(
        set(detect_language_topics(reference) or ["unknown"]) |
        set(detect_language_topics(student) or ["unknown"])
    )

    if not topics:
        return {}

    logger.debug(f"Evaluating topics: {topics}")
    logger.debug(f"English: '{english}'")
    logger.debug(f"Reference: '{reference}'")
    logger.debug(f"Student: '{student}'")

    user_prompt = quality_evaluation_prompt(english, reference, student, topics)
    logger.debug("Sending prompt to AI for topic evaluation")

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        logger.debug(f"API call completed, status code: {resp.status_code}")

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            logger.debug(f"AI Response: '{content}'")

            data = _extract_json(content)
            if isinstance(data, dict):
                # Extract quality scores for each topic
                qualities = {}
                for topic in topics:
                    if topic in data:
                        quality = data[topic]
                        if isinstance(quality, (int, float)) and 0 <= quality <= 5:
                            qualities[topic] = int(quality)
                        else:
                            qualities[topic] = 2  # Default score
                    else:
                        qualities[topic] = 2  # Default score

                logger.debug(f"Topic qualities: {qualities}")
                return qualities
            else:
                logger.warning("AI response is not a valid JSON object")
                return {}
        else:
            logger.error(f"API call failed with status code: {resp.status_code}")
            return {}

    except Exception as e:
        logger.error(f"Error in topic quality evaluation: {e}")
        return {}


def compare_topic_qualities(reference: str, student: str) -> Dict[str, int]:
    """
    Compare topic qualities between reference and student text.

    Args:
        reference: The reference text
        student: The student's text

    Returns:
        Dictionary mapping topics to quality scores
    """
    try:
        # Detect topics in both texts
        ref_topics = detect_language_topics(reference) or []
        stu_topics = detect_language_topics(student) or []

        # Combine all topics
        all_topics = sorted(set(ref_topics + stu_topics))

        if not all_topics:
            return {}

        # For each topic, compare usage between reference and student
        qualities = {}
        for topic in all_topics:
            # Simple heuristic: if topic appears in both, give higher score
            ref_has_topic = topic in ref_topics
            stu_has_topic = topic in stu_topics

            if ref_has_topic and stu_has_topic:
                qualities[topic] = 4  # Good usage
            elif stu_has_topic:
                qualities[topic] = 3  # Used but not in reference
            elif ref_has_topic:
                qualities[topic] = 1  # Missing from student
            else:
                qualities[topic] = 2  # Neutral

        return qualities

    except Exception as e:
        logger.error(f"Error comparing topic qualities: {e}")
        return {}


def analyze_topic_performance(topics: List[str], qualities: Dict[str, int]) -> Dict:
    """
    Analyze topic performance based on quality scores.

    Args:
        topics: List of grammar topics
        qualities: Dictionary of topic quality scores

    Returns:
        Dictionary containing performance analysis
    """
    try:
        if not topics or not qualities:
            return {
                "average_score": 0,
                "strong_topics": [],
                "weak_topics": [],
                "missing_topics": []
            }

        # Calculate average score
        scores = [qualities.get(topic, 0) for topic in topics]
        average_score = sum(scores) / len(scores) if scores else 0

        # Categorize topics
        strong_topics = [topic for topic in topics if qualities.get(topic, 0) >= 4]
        weak_topics = [topic for topic in topics if qualities.get(topic, 0) <= 2]
        missing_topics = [topic for topic in topics if topic not in qualities]

        return {
            "average_score": round(average_score, 2),
            "strong_topics": strong_topics,
            "weak_topics": weak_topics,
            "missing_topics": missing_topics,
            "total_topics": len(topics),
            "evaluated_topics": len(qualities)
        }

    except Exception as e:
        logger.error(f"Error analyzing topic performance: {e}")
        return {
            "average_score": 0,
            "strong_topics": [],
            "weak_topics": [],
            "missing_topics": []
        }
