"""
XplorED - AI Feedback Generation Module

This module provides AI feedback generation functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Feedback Generation Components:
- AI Feedback Generation: Generate AI-powered feedback for exercises
- Progress-Based Generation: Generate feedback with progress tracking
- Simple Feedback Generation: Generate feedback without progress tracking
- Background Processing: Process feedback generation in background

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import random
from typing import List, Optional

from features.ai.evaluation import (
    evaluate_answers_with_ai,
    process_ai_answers
)
from features.ai.generation.feedback_helpers import (
    _adjust_gapfill_results,
    generate_feedback_prompt
)
from core.database.connection import fetch_topic_memory
from core.processing import run_in_background
from core.database.connection import select_rows
from .feedback_session import (
    create_feedback_session,
    update_feedback_progress,
    _mark_feedback_complete,
    _ensure_feedback_completion
)
from .feedback_processing import (
    _process_evaluation_summary,
    _fetch_user_vocabulary,
    _fetch_user_topic_memory
)
from shared.exceptions import DatabaseError, AIEvaluationError
from shared.types import ExerciseAnswers, FeedbackData, FeedbackList, AnalyticsData

from features.ai.memory.logger import topic_memory_logger


def generate_feedback_with_progress(username: str, answers: ExerciseAnswers,
                                  exercise_block: Optional[AnalyticsData] = None) -> str:
    """
    Generate AI feedback with progress tracking.

    Args:
        username: The username
        answers: User's answers
        exercise_block: Optional exercise block data

    Returns:
        Session ID for tracking progress
    """
    try:
        session_id = create_feedback_session()

        def run_feedback_generation():
            try:
                update_feedback_progress(session_id, 10, "Starting feedback generation...", "init")

                # Step 1: Evaluate answers with AI
                update_feedback_progress(session_id, 20, "Evaluating answers with AI...", "evaluation")
                exercises = exercise_block.get("exercises", []) if exercise_block else []
                evaluation = evaluate_answers_with_ai(exercises, answers, "feedback")

                if not evaluation:
                    _mark_feedback_complete(session_id, {"error": "Failed to evaluate answers"})
                    return

                update_feedback_progress(session_id, 40, "Processing evaluation results...", "processing")

                # Step 2: Process evaluation summary
                exercises = exercise_block.get("exercises", []) if exercise_block else []
                summary = _process_evaluation_summary(exercises, answers, evaluation)

                update_feedback_progress(session_id, 60, "Fetching user data...", "data_fetch")

                # Step 3: Fetch user vocabulary and topic memory
                vocabulary = _fetch_user_vocabulary(username)
                topic_memory = _fetch_user_topic_memory(username)

                update_feedback_progress(session_id, 80, "Generating personalized feedback...", "feedback_gen")

                # Step 4: Generate feedback prompt
                feedback_prompt = generate_feedback_prompt(
                    summary=summary,
                    vocab=vocabulary,
                    topic_memory=topic_memory
                )

                # Step 5: Generate AI feedback
                from external.mistral.client import send_prompt
                system_message = "You are a helpful German language teacher providing personalized feedback to students."
                user_prompt = {"role": "user", "content": feedback_prompt}
                response = send_prompt(system_message, user_prompt)
                ai_feedback = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

                if not ai_feedback:
                    _mark_feedback_complete(session_id, {"error": "Failed to generate AI feedback"})
                    return

                # Step 6: Prepare final result
                result = {
                    "session_id": session_id,
                    "username": username,
                    "summary": summary,
                    "ai_feedback": ai_feedback,
                    "vocabulary_count": len(vocabulary),
                    "topic_memory_count": len(topic_memory),
                    "generated_at": "2025-01-27T12:00:00Z"
                }

                update_feedback_progress(session_id, 100, "Feedback generation complete", "complete")
                _mark_feedback_complete(session_id, result)

                print(f"✅ Successfully generated feedback for user {username}")

            except Exception as e:
                print(f"❌ Error in feedback generation: {e}")
                _mark_feedback_complete(session_id, {"error": str(e)})

        # Run in background
        run_in_background(run_feedback_generation)

        return session_id

    except Exception as e:
        print(f"❌ Error starting feedback generation: {e}")
        raise AIEvaluationError(f"Error starting feedback generation: {str(e)}")


def generate_ai_feedback_simple(username: str, answers: ExerciseAnswers,
                            exercise_block: Optional[AnalyticsData] = None) -> FeedbackData:
    """
    Generate AI feedback without progress tracking.

    Args:
        username: The username
        answers: User's answers
        exercise_block: Optional exercise block data

    Returns:
        Dictionary containing feedback result
    """
    try:
        print(f"🔄 Generating simple AI feedback for user {username}")

        # Step 1: Evaluate answers with AI
        exercises = exercise_block.get("exercises", []) if exercise_block else []
        print(f"📝 Evaluating {len(exercises)} exercises for feedback generation")
        evaluation = evaluate_answers_with_ai(exercises, answers, "feedback")
        print(f"📊 Evaluation result: {evaluation}")

        if not evaluation:
            return {"error": "Failed to evaluate answers"}

        # Step 2: Process evaluation summary
        print("🔄 About to process evaluation summary")
        summary = _process_evaluation_summary(exercises, answers, evaluation)
        print(f"✅ Successfully processed evaluation summary: {summary}")

        # Step 3: Fetch user vocabulary and topic memory
        print("📚 About to fetch vocabulary")
        try:
            vocabulary = _fetch_user_vocabulary(username)
            print(f"✅ Successfully fetched vocabulary: {len(vocabulary)} items")
        except Exception as e:
            print(f"❌ Error fetching vocabulary: {e}")
            vocabulary = []

        print("🧠 About to fetch topic memory")
        try:
            topic_memory = _fetch_user_topic_memory(username)
            print(f"✅ Successfully fetched topic memory: {len(topic_memory)} items")
        except Exception as e:
            print(f"❌ Error fetching topic memory: {e}")
            topic_memory = []

        # Step 4: Generate feedback prompt
        feedback_prompt = generate_feedback_prompt(
            summary=summary,
            vocab=vocabulary,
            topic_memory=topic_memory
        )

        # Step 5: Generate AI feedback
        from external.mistral.client import send_prompt
        system_message = "You are a helpful German language teacher providing personalized feedback to students."
        user_prompt = {"role": "user", "content": feedback_prompt}

        try:
            response = send_prompt(system_message, user_prompt)
            response_json = response.json()
            ai_feedback = response_json.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not ai_feedback:
                print(f"⚠️ Empty AI feedback response: {response_json}")
                return {"error": "Failed to generate AI feedback - empty response"}

        except Exception as e:
            print(f"❌ Error calling Mistral API: {e}")
            return {"error": f"Failed to generate AI feedback: {str(e)}"}

        # Step 6: Prepare result
        result = {
            "username": username,
            "summary": summary,
            "ai_feedback": ai_feedback,
            "vocabulary_count": len(vocabulary),
            "topic_memory_count": len(topic_memory),
            "generated_at": "2025-01-27T12:00:00Z"
        }

        print(f"✅ Successfully generated simple feedback for user {username}")
        return result

    except Exception as e:
        print(f"❌ Error generating simple feedback: {e}")
        return {"error": str(e)}


def get_cached_feedback_list() -> FeedbackList:
    """
    Get cached feedback list.

    Returns:
        List of cached feedback items
    """
    try:
        # Return predefined feedback list
        feedback_list = [
            {
                "id": "fb1",
                "title": "Feedback After Set 1",
                "instructions": "Here are notes on your first round of exercises.",
                "type": "mixed",
                "feedbackPrompt": "You mixed up some plural forms like 'wir sind' and 'sie sind'. Review the pronouns before continuing.",
                "created_at": "2025-06-12T09:00:00Z"
            },
            {
                "id": "fb2",
                "title": "Feedback After Set 2",
                "instructions": "Comments on your second round of practice.",
                "type": "mixed",
                "feedbackPrompt": "Great improvement! Keep an eye on word order in translations and continue practicing.",
                "created_at": "2025-06-12T09:10:00Z"
            }
        ]

        print(f"📋 Retrieved {len(feedback_list)} cached feedback items")
        return feedback_list

    except Exception as e:
        print(f"❌ Error getting cached feedback list: {e}")
        return []


def get_cached_feedback_item(feedback_id: str) -> Optional[FeedbackData]:
    """
    Get a specific cached feedback item.

    Args:
        feedback_id: The feedback ID to retrieve

    Returns:
        Feedback item dictionary or None if not found
    """
    try:
        feedback_list = get_cached_feedback_list()

        for item in feedback_list:
            if item.get("id") == feedback_id:
                print(f"📋 Retrieved cached feedback item: {feedback_id}")
                return item

        print(f"⚠️ Feedback item not found: {feedback_id}")
        return None

    except Exception as e:
        print(f"❌ Error getting cached feedback item: {e}")
        return None
