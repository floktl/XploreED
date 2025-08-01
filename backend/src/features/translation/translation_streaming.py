"""
XplorED - Translation Streaming Module

This module provides translation streaming and feedback functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Translation Streaming Components:
- Streaming Feedback: Stream translation feedback in real-time
- Feedback Generation: Generate comprehensive translation feedback
- Memory Integration: Integrate with vocabulary memory system
- Error Handling: Handle streaming errors and timeouts

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import json
import time
import os
import redis
from typing import Dict, Any, Optional, Tuple

from core.services.import_service import *
from features.ai.generation.feedback_helpers import format_feedback_block
from features.ai.memory.vocabulary_memory import translate_to_german
from features.ai.evaluation import evaluate_translation_ai
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


def stream_translation_feedback(english: str, student_input: str, username: str) -> str:
    """
    Stream translation feedback for real-time processing.

    Args:
        english: The English text to translate
        student_input: The student's translation attempt
        username: The username

    Returns:
        JSON string containing streaming feedback data

    Raises:
        ValueError: If required parameters are missing
    """
    try:
        if not english or not student_input or not username:
            raise ValueError("English text, student input, and username are required")

        logger.info(f"Starting translation feedback stream for user {username}")

        # Initialize feedback data
        feedback_data = {
            "english": english,
            "student_input": student_input,
            "username": username,
            "status": "processing",
            "steps": [],
            "result": None,
            "error": None,
            "timestamp": time.time()
        }

        try:
            # Step 1: Get AI translation
            feedback_data["steps"].append({
                "step": "ai_translation",
                "status": "processing",
                "message": "Getting AI translation..."
            })

            ai_translation = translate_to_german(english)
            if not ai_translation:
                feedback_data["steps"][-1]["status"] = "error"
                feedback_data["steps"][-1]["message"] = "Failed to get AI translation"
                feedback_data["status"] = "error"
                feedback_data["error"] = "AI translation failed"
                return json.dumps(feedback_data)

            feedback_data["steps"][-1]["status"] = "completed"
            feedback_data["steps"][-1]["message"] = "AI translation received"
            feedback_data["steps"][-1]["data"] = {"ai_translation": ai_translation}

            # Step 2: Evaluate student translation
            feedback_data["steps"].append({
                "step": "evaluation",
                "status": "processing",
                "message": "Evaluating your translation..."
            })

            evaluation_result = evaluate_translation_ai(english, student_input, ai_translation)
            if not evaluation_result:
                feedback_data["steps"][-1]["status"] = "error"
                feedback_data["steps"][-1]["message"] = "Failed to evaluate translation"
                feedback_data["status"] = "error"
                feedback_data["error"] = "Evaluation failed"
                return json.dumps(feedback_data)

            feedback_data["steps"][-1]["status"] = "completed"
            feedback_data["steps"][-1]["message"] = "Translation evaluated"
            feedback_data["steps"][-1]["data"] = {"evaluation": evaluation_result}

            # Step 3: Update vocabulary memory
            feedback_data["steps"].append({
                "step": "memory_update",
                "status": "processing",
                "message": "Updating vocabulary memory..."
            })

            try:
                update_memory_async(username, english, student_input, evaluation_result)
                feedback_data["steps"][-1]["status"] = "completed"
                feedback_data["steps"][-1]["message"] = "Vocabulary memory updated"
            except Exception as e:
                logger.warning(f"Failed to update vocabulary memory: {e}")
                feedback_data["steps"][-1]["status"] = "warning"
                feedback_data["steps"][-1]["message"] = "Memory update failed (non-critical)"

            # Step 4: Generate final feedback
            feedback_data["steps"].append({
                "step": "feedback_generation",
                "status": "processing",
                "message": "Generating feedback..."
            })

            formatted_feedback = format_feedback_block(evaluation_result)
            feedback_data["steps"][-1]["status"] = "completed"
            feedback_data["steps"][-1]["message"] = "Feedback generated"
            feedback_data["steps"][-1]["data"] = {"feedback": formatted_feedback}

            # Prepare final result
            feedback_data["status"] = "completed"
            feedback_data["result"] = {
                "english": english,
                "student_input": student_input,
                "ai_translation": ai_translation,
                "evaluation": evaluation_result,
                "feedback": formatted_feedback,
                "processed_at": time.time()
            }

            logger.info(f"Completed translation feedback stream for user {username}")
            return json.dumps(feedback_data)

        except Exception as e:
            logger.error(f"Error in translation feedback stream: {e}")
            feedback_data["status"] = "error"
            feedback_data["error"] = str(e)
            feedback_data["steps"].append({
                "step": "error",
                "status": "error",
                "message": f"Processing error: {str(e)}"
            })
            return json.dumps(feedback_data)

    except ValueError as e:
        logger.error(f"Validation error in translation feedback stream: {e}")
        error_data = {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }
        return json.dumps(error_data)
    except Exception as e:
        logger.error(f"Unexpected error in translation feedback stream: {e}")
        error_data = {
            "status": "error",
            "error": "Unexpected error occurred",
            "timestamp": time.time()
        }
        return json.dumps(error_data)
