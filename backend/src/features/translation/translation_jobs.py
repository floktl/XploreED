"""
XplorED - Translation Jobs Module

This module provides translation job management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Translation Jobs Components:
- Job Creation: Create and manage translation jobs
- Job Processing: Process translation jobs in background
- Job Status: Track and retrieve job status
- Job Cleanup: Clean up expired and completed jobs

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
import uuid
import time
import os
from typing import Dict, Any, Optional, Tuple
from threading import Thread

from core.services.import_service import *
from features.ai.generation.feedback_helpers import format_feedback_block
from features.ai.memory.vocabulary_memory import translate_to_german
from features.ai.evaluation import evaluate_translation_ai
from features.ai.generation.translate_helpers import update_memory_async
from external.redis import redis_client

logger = logging.getLogger(__name__)


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

        redis_client.setex_json(
            f"translation_job:{job_id}",
            3600,  # Expire after 1 hour
            initial_status
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

        # Start background processing
        thread = Thread(
            target=_process_job_background,
            args=(job_id, english, student_input, username)
        )
        thread.daemon = True
        thread.start()

    except ValueError as e:
        logger.error(f"Validation error processing translation job: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing translation job {job_id}: {e}")
        _update_job_status(job_id, "error", {"error": str(e)})


def _process_job_background(job_id: str, english: str, student_input: str, username: str) -> None:
    """
    Process translation job in background thread.

    Args:
        job_id: The job ID to process
        english: The English text to translate
        student_input: The student's translation attempt
        username: The username
    """
    try:
        logger.info(f"Starting background processing for job {job_id}")

        # Get AI translation
        ai_translation = translate_to_german(english)
        if not ai_translation:
            _update_job_status(job_id, "error", {"error": "Failed to get AI translation"})
            return

        # Evaluate student translation
        evaluation_result = evaluate_translation_ai(english, student_input, ai_translation)
        if not evaluation_result:
            _update_job_status(job_id, "error", {"error": "Failed to evaluate translation"})
            return

        # Update vocabulary memory asynchronously
        try:
            update_memory_async(username, english, student_input, evaluation_result)
        except Exception as e:
            logger.warning(f"Failed to update vocabulary memory for job {job_id}: {e}")

        # Prepare result
        result = {
            "english": english,
            "student_input": student_input,
            "ai_translation": ai_translation,
            "evaluation": evaluation_result,
            "feedback": format_feedback_block(evaluation_result),
            "processed_at": time.time()
        }

        _update_job_status(job_id, "completed", result)
        logger.info(f"Completed background processing for job {job_id}")

    except Exception as e:
        logger.error(f"Error in background processing for job {job_id}: {e}")
        _update_job_status(job_id, "error", {"error": str(e)})


def _update_job_status(job_id: str, status: str, result: Dict[str, Any]) -> None:
    """
    Update the status of a translation job.

    Args:
        job_id: The job ID to update
        status: The new status
        result: The result data
    """
    try:
        job_data = {
            "status": status,
            "result": result,
            "updated_at": time.time()
        }

        redis_client.setex_json(
            f"translation_job:{job_id}",
            3600,  # Expire after 1 hour
            job_data
        )

        logger.info(f"Updated job {job_id} status to {status}")

    except Exception as e:
        logger.error(f"Error updating job {job_id} status: {e}")


def get_translation_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a translation job.

    Args:
        job_id: The job ID to check

    Returns:
        Job status dictionary or None if not found

    Raises:
        ValueError: If job_id is invalid
    """
    try:
        if not job_id:
            raise ValueError("Job ID is required")

        logger.info(f"Getting status for translation job {job_id}")

        job_data = redis_client.get_json(f"translation_job:{job_id}")
        if not job_data:
            logger.warning(f"Translation job {job_id} not found")
            return None

        try:
            status_data = job_data
            logger.info(f"Retrieved status for job {job_id}: {status_data.get('status')}")
            return status_data
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON data for job {job_id}")
            return None

    except ValueError as e:
        logger.error(f"Validation error getting job status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return None


def get_translation_status(job_id: str) -> Dict[str, Any]:
    """
    Get translation status with error handling.

    Args:
        job_id: The job ID to check

    Returns:
        Status dictionary with error handling
    """
    try:
        status_data = get_translation_job_status(job_id)

        if status_data:
            return {
                "job_id": job_id,
                "status": status_data.get("status", "unknown"),
                "result": status_data.get("result"),
                "created_at": status_data.get("created_at"),
                "updated_at": status_data.get("updated_at"),
            }
        else:
            return {
                "job_id": job_id,
                "status": "not_found",
                "result": None,
                "error": "Job not found or expired"
            }

    except Exception as e:
        logger.error(f"Error getting translation status for {job_id}: {e}")
        return {
            "job_id": job_id,
            "status": "error",
            "result": None,
            "error": str(e)
        }


def cleanup_expired_jobs() -> int:
    """
    Clean up expired translation jobs.

    Returns:
        Number of jobs cleaned up
    """
    try:
        logger.info("Starting cleanup of expired translation jobs")

        # Get all translation job keys
        job_keys = redis_client.keys("translation_job:*")
        cleaned_count = 0

        for key in job_keys:
            try:
                job_data = redis_client.get_json(key)
                if job_data:
                    created_at = job_data.get("created_at", 0)

                    # Check if job is older than 1 hour
                    if time.time() - created_at > 3600:
                        redis_client.delete(key)
                        cleaned_count += 1
                        logger.debug(f"Cleaned up expired job: {key}")

            except Exception as e:
                logger.warning(f"Error processing job key {key}: {e}")
                # Delete malformed keys
                redis_client.delete(key)
                cleaned_count += 1

        logger.info(f"Cleaned up {cleaned_count} expired translation jobs")
        return cleaned_count

    except Exception as e:
        logger.error(f"Error during job cleanup: {e}")
        return 0
