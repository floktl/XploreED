"""
Translation Helper Functions

This module contains helper functions for translation operations that are used
by the translation routes but should not be in the route files themselves.

Author: German Class Tool Team
Date: 2025
"""

import logging
import json
import uuid
import time
import os
import redis
from typing import Dict, Any, Optional, Tuple
from threading import Thread

from core.services.import_service import *
from features.ai.generation.helpers import format_feedback_block
from features.ai.memory.vocabulary_memory import translate_to_german
from features.ai.evaluation.translation_evaluator import evaluate_translation_ai
from features.ai.generation.translate_helpers import update_memory_async


logger = logging.getLogger(__name__)


# Redis connection setup
redis_url = os.getenv('REDIS_URL')
if redis_url:
    redis_client = redis.from_url(redis_url, decode_responses=True)
else:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    logger.info(f"Connecting to Redis at: {redis_host}")
    redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)


def create_translation_job(english: str, student_input: str, username: str) -> str:
    """
    Create a new translation job and return the job ID.

    Args:
        english: The English text to translate
        student_input: The student's translation attempt
        username: The username

    Returns:
        The job ID for tracking the translation process

    Raises:
        ValueError: If required parameters are missing
    """
    try:
        if not english or not username:
            raise ValueError("English text and username are required")

        job_id = str(uuid.uuid4())
        initial_status = {
            "status": "processing",
            "result": None,
            "created_at": time.time()
        }

        redis_client.set(
            f"translation_job:{job_id}",
            json.dumps(initial_status),
            ex=3600  # Expire after 1 hour
        )

        logger.info(f"Created translation job {job_id} for user {username}")
        return job_id

    except ValueError as e:
        logger.error(f"Validation error creating translation job: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating translation job: {e}")
        raise


def process_translation_job(job_id: str, english: str, student_input: str, username: str) -> None:
    """
    Process a translation job in the background.

    Args:
        job_id: The job ID to process
        english: The English text to translate
        student_input: The student's translation attempt
        username: The username

    Raises:
        ValueError: If required parameters are missing
    """
    try:
        if not job_id or not english or not username:
            raise ValueError("Job ID, English text, and username are required")

        logger.info(f"Processing translation job {job_id} for user {username}")

        # Get German translation
        german = translate_to_german(english, username)

        if not isinstance(german, str) or "❌" in german:
            result = {
                "german": german,
                "feedback": "❌ Translation failed."
            }
            _update_job_status(job_id, "done", result)
            return

        # Evaluate the student's translation
        correct, reason = evaluate_translation_ai(english, german, student_input)

        # Update memory asynchronously
        update_memory_async(username, english, german, student_input)

        # Build feedback block
        feedback_block = format_feedback_block(
            user_answer=student_input,
            correct_answer=german,
            alternatives=[],
            explanation=reason,
            diff=None,
            status="correct" if correct else "incorrect"
        )

        result = {
            "german": german,
            "feedbackBlock": feedback_block
        }

        _update_job_status(job_id, "done", result)
        logger.info(f"Completed translation job {job_id}")

    except ValueError as e:
        logger.error(f"Validation error processing translation job {job_id}: {e}")
        _update_job_status(job_id, "error", {"error": str(e)})
    except Exception as e:
        logger.error(f"Error processing translation job {job_id}: {e}")
        _update_job_status(job_id, "error", {"error": f"Internal error: {e}"})


def _update_job_status(job_id: str, status: str, result: Dict[str, Any]) -> None:
    """
    Update the status of a translation job in Redis.

    Args:
        job_id: The job ID
        status: The new status
        result: The result data
    """
    try:
        job_data = {
            "status": status,
            "result": result,
            "updated_at": time.time()
        }

        redis_client.set(
            f"translation_job:{job_id}",
            json.dumps(job_data),
            ex=3600  # Expire after 1 hour
        )

        logger.debug(f"Updated job {job_id} status to {status}")

    except Exception as e:
        logger.error(f"Error updating job {job_id} status: {e}")


def get_translation_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a translation job from Redis.

    Args:
        job_id: The job ID to check

    Returns:
        Job status data or None if not found

    Raises:
        ValueError: If job_id is invalid
    """
    try:
        if not job_id:
            raise ValueError("Job ID is required")

        job_json = redis_client.get(f"translation_job:{job_id}")

        if not job_json:
            logger.warning(f"Translation job {job_id} not found")
            return None

        job_data = json.loads(job_json)
        logger.debug(f"Retrieved job {job_id} status: {job_data.get('status')}")
        return job_data

    except ValueError as e:
        logger.error(f"Validation error getting job status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id} status: {e}")
        return None


def get_translation_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a translation job.

    Args:
        job_id: The translation job ID

    Returns:
        Dictionary containing job status and results
    """
    # TODO: Implement actual translation status logic
    logger.info(f"Getting translation status for job {job_id}")

    # Placeholder implementation
    return {
        "job_id": job_id,
        "status": "completed",
        "progress": 100,
        "result": {
            "translated_text": "Placeholder translation",
            "confidence": 0.95,
            "processing_time": 1.5
        }
    }


def stream_translation_feedback(english: str, student_input: str, username: str) -> str:
    """
    Generate streaming translation feedback.

    Args:
        english: The English text to translate
        student_input: The student's translation attempt
        username: The username

    Returns:
        JSON string containing the feedback block

    Raises:
        ValueError: If required parameters are missing
    """
    try:
        if not english or not username:
            raise ValueError("English text and username are required")

        logger.info(f"Generating streaming feedback for user {username}")

        # Get German translation
        german = translate_to_german(english, username)

        if not isinstance(german, str) or "❌" in german:
            error_feedback = format_feedback_block(
                user_answer=student_input,
                correct_answer="",
                alternatives=[],
                explanation="Translation failed",
                diff=None,
                status="error"
            )
            return json.dumps({'feedbackBlock': error_feedback})

        # Evaluate the student's translation
        correct, reason = evaluate_translation_ai(english, german, student_input)

        # Build feedback block
        feedback_block = format_feedback_block(
            user_answer=student_input,
            correct_answer=german,
            alternatives=[],
            explanation=reason,
            diff=None,
            status="correct" if correct else "incorrect"
        )

        # Update memory asynchronously
        Thread(
            target=update_memory_async,
            args=(username, english, german, student_input),
            daemon=True
        ).start()

        logger.info(f"Generated feedback for user {username}")
        return json.dumps({'feedbackBlock': feedback_block})

    except ValueError as e:
        logger.error(f"Validation error generating streaming feedback: {e}")
        error_feedback = format_feedback_block(
            user_answer=student_input,
            correct_answer="",
            alternatives=[],
            explanation=f"Error: {str(e)}",
            diff=None,
            status="error"
        )
        return json.dumps({'feedbackBlock': error_feedback})
    except Exception as e:
        logger.error(f"Error generating streaming feedback: {e}")
        error_feedback = format_feedback_block(
            user_answer=student_input,
            correct_answer="",
            alternatives=[],
            explanation=f"Error: {str(e)}",
            diff=None,
            status="error"
        )
        return json.dumps({'feedbackBlock': error_feedback})


def cleanup_expired_jobs() -> int:
    """
    Clean up expired translation jobs from Redis.

    Returns:
        Number of jobs cleaned up
    """
    try:
        # Redis automatically expires keys, but we can also clean up manually
        # This is a placeholder for manual cleanup if needed
        logger.info("Translation job cleanup completed")
        return 0

    except Exception as e:
        logger.error(f"Error cleaning up translation jobs: {e}")
        return 0
