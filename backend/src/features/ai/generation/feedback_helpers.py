"""
XplorED - Feedback Helpers Module

This module provides feedback generation and processing functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Feedback Helpers Components:
- Feedback Generation: Generate AI-powered feedback for exercises
- Feedback Formatting: Format and structure feedback data
- Feedback Processing: Process feedback results and summaries
- Feedback Utilities: Utility functions for feedback handling

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, List, Optional

from core.database.connection import fetch_topic_memory
from features.ai.prompts import feedback_generation_prompt

logger = logging.getLogger(__name__)


def generate_feedback_prompt(
    summary: dict,
    vocab: list | None = None,
    topic_memory: list | None = None,
) -> str:
    """
    Generate a feedback prompt for AI.

    Args:
        summary: Exercise summary data
        vocab: User vocabulary data
        topic_memory: User topic memory data

    Returns:
        Generated feedback prompt
    """
    try:
        logger.debug(f"Generating feedback prompt with summary: {summary}")

        correct = summary.get("correct", 0)
        total = summary.get("total", 0)
        mistakes = summary.get("mistakes", [])

        if total == 0:
            return "No answers were submitted."

        # Format top mistakes
        top_mistakes = [
            f"Q: {m['question']} | Your: {m['your_answer']} | Correct: {m['correct_answer']}"
            for m in mistakes[:2]
        ]
        mistakes_text = "\n".join(top_mistakes)

        # Format vocabulary examples
        top_vocab = [
            f"{v.get('word')} – {v.get('translation')}" for v in (vocab or [])[:3]
            if v.get("word") and v.get("translation")
        ]
        examples_text = ", ".join(top_vocab)

        # Format topic memory data
        topic_counts: dict[str, int] = {}
        for entry in topic_memory or []:
            for topic in str(entry.get("topic", "")).split(","):
                t = topic.strip()
                if t:
                    topic_counts[t] = topic_counts.get(t, 0) + 1
        repeated_topics = [t for t, c in topic_counts.items() if c > 1][:3]
        repeated_text = ", ".join(repeated_topics)

        # Generate feedback prompt
        user_prompt = feedback_generation_prompt(
            correct,
            total,
            mistakes_text,
            examples_text,
            repeated_text
        )

        logger.debug(f"Generated feedback prompt successfully")
        return user_prompt

    except Exception as e:
        logger.error(f"Error generating feedback prompt: {e}")
        return "Error generating feedback."


def format_feedback_block(user_answer, correct_answer, alternatives=None, explanation=None, diff=None, status=None):
    """
    Format a feedback block for display.

    Args:
        user_answer: User's answer
        correct_answer: Correct answer
        alternatives: Alternative correct answers
        explanation: Explanation for the answer
        diff: Difference highlighting
        status: Answer status

    Returns:
        Formatted feedback block
    """
    try:
        from features.ai.evaluation.translation_evaluation import _normalize_umlauts, _strip_final_punct

        # Normalize answers for comparison
        ua = _strip_final_punct(str(user_answer)).strip().lower()
        ca = _strip_final_punct(str(correct_answer)).strip().lower()
        ua = _normalize_umlauts(ua)
        ca = _normalize_umlauts(ca)

        feedback_block = {
            "status": status or ("correct" if ua == ca else "incorrect"),
            "correct": correct_answer,
            "alternatives": alternatives or [],
            "explanation": explanation or "",
            "userAnswer": user_answer,
            "diff": diff,
        }

        logger.debug(f"Formatted feedback block with status: {feedback_block['status']}")
        return feedback_block

    except Exception as e:
        logger.error(f"Error formatting feedback block: {e}")
        return {
            "status": "error",
            "correct": correct_answer,
            "alternatives": [],
            "explanation": "Error formatting feedback",
            "userAnswer": user_answer,
            "diff": None,
        }


def _adjust_gapfill_results(exercises: list, answers: dict, evaluation: dict | None) -> dict | None:
    """
    Ensure AI evaluation for gap-fill exercises matches provided options.

    Args:
        exercises: List of exercises
        answers: User's answers
        evaluation: AI evaluation results

    Returns:
        Adjusted evaluation results
    """
    try:
        from difflib import SequenceMatcher
        from features.ai.evaluation.translation_evaluation import _normalize_umlauts, _strip_final_punct

        if not evaluation or "results" not in evaluation:
            return evaluation

        id_map = {str(r.get("id")): r.get("correct_answer", "") for r in evaluation.get("results", [])}

        for ex in exercises:
            if ex.get("type") != "gap-fill":
                continue
            cid = str(ex.get("id"))
            correct = id_map.get(cid, "")
            options = ex.get("options") or []
            if correct not in options and options:
                norm_corr = str(correct).strip().lower()
                best = options[0]
                best_score = -1.0
                for opt in options:
                    opt_norm = opt.lower()
                    score = SequenceMatcher(None, norm_corr, opt_norm).ratio()
                    if score > best_score:
                        best = opt
                        best_score = score
                    if opt_norm in norm_corr or norm_corr in opt_norm:
                        best = opt
                        break
                id_map[cid] = best

        evaluation["results"] = [{"id": k, "correct_answer": v} for k, v in id_map.items()]

        # Check if all answers are correct
        pass_val = True
        for ex in exercises:
            cid = str(ex.get("id"))
            ans = str(answers.get(cid, "")).strip().lower()
            corr = str(id_map.get(cid, "")).strip().lower()
            # Ignore final . or ? for all exercise types
            ans = _strip_final_punct(ans)
            corr = _strip_final_punct(corr)
            # Normalize umlauts for both answers
            ans = _normalize_umlauts(ans)
            corr = _normalize_umlauts(corr)
            if ans != corr:
                pass_val = False
        evaluation["pass"] = pass_val

        logger.debug(f"Adjusted gap-fill results: pass={pass_val}")
        return evaluation

    except Exception as e:
        logger.error(f"Error adjusting gap-fill results: {e}")
        return evaluation


def get_recent_exercise_topics(username: str, limit: int = 3) -> list[str]:
    """
    Get recent content topics used in exercise blocks to avoid repetition.

    Args:
        username: The username
        limit: Maximum number of topics to return

    Returns:
        List of recent topics
    """
    try:
        from core.database.connection import select_rows

        # Get recent exercise blocks from ai_user_data
        rows = select_rows(
            "ai_user_data",
            columns="exercises, next_exercises",
            where="username = ?",
            params=(username,),
        )

        recent_topics = []
        for row in rows:
            for field in ["exercises", "next_exercises"]:
                if row.get(field):
                    try:
                        import json
                        exercise_data = json.loads(row[field])
                        if isinstance(exercise_data, dict) and exercise_data.get("topic"):
                            topic = exercise_data["topic"]
                            if topic and topic not in recent_topics:
                                recent_topics.append(topic)
                    except (json.JSONDecodeError, KeyError):
                        continue

        logger.debug(f"Retrieved {len(recent_topics[:limit])} recent topics for user {username}")
        return recent_topics[:limit]

    except Exception as e:
        logger.error(f"Error getting recent exercise topics: {e}")
        return []


def create_feedback_summary(exercises: List[Dict], answers: Dict[str, str], evaluation: Dict) -> Dict[str, Any]:
    """
    Create a comprehensive feedback summary.

    Args:
        exercises: List of exercises
        answers: User's answers
        evaluation: AI evaluation results

    Returns:
        Feedback summary dictionary
    """
    try:
        total_exercises = len(exercises)
        correct_answers = 0
        incorrect_answers = 0
        skipped_answers = 0
        mistakes = []

        for i, exercise in enumerate(exercises):
            exercise_id = str(i + 1)
            user_answer = answers.get(exercise_id, "").strip()
            correct_answer = exercise.get("correctAnswer", "")

            if not user_answer:
                skipped_answers += 1
                continue

            # Check if answer is correct
            is_correct = user_answer.lower() == correct_answer.lower()

            if is_correct:
                correct_answers += 1
            else:
                incorrect_answers += 1
                mistakes.append({
                    "question": exercise.get("question", ""),
                    "your_answer": user_answer,
                    "correct_answer": correct_answer
                })

        accuracy = (correct_answers / total_exercises * 100) if total_exercises > 0 else 0

        summary = {
            "total": total_exercises,
            "correct": correct_answers,
            "incorrect": incorrect_answers,
            "skipped": skipped_answers,
            "accuracy": round(accuracy, 2),
            "mistakes": mistakes[:3],  # Limit to first 3 mistakes
            "overall_feedback": evaluation.get("overall_feedback", "")
        }

        logger.debug(f"Created feedback summary: {accuracy:.2f}% accuracy")
        return summary

    except Exception as e:
        logger.error(f"Error creating feedback summary: {e}")
        return {
            "total": 0,
            "correct": 0,
            "incorrect": 0,
            "skipped": 0,
            "accuracy": 0,
            "mistakes": [],
            "overall_feedback": "Error creating feedback summary"
        }
