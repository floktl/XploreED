"""
XplorED - TTS Service Module

This module provides TTS service functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

TTS Service Components:
- Text Processing: Process and validate text for TTS conversion
- Voice Selection: Handle voice selection and management
- Audio Formatting: Handle audio format and quality settings
- Error Handling: Provide comprehensive error handling for TTS operations

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, Any, Optional, List
from .client import tts_client

logger = logging.getLogger(__name__)


def convert_text_to_speech_service(
    text: str,
    username: str,
    voice_id: Optional[str] = None,
    model_id: Optional[str] = None,
    output_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert text to speech with comprehensive error handling and logging.

    Args:
        text: The text to convert to speech
        username: The username requesting the conversion
        voice_id: Optional voice ID (uses default if not provided)
        model_id: Optional model ID (uses default if not provided)
        output_format: Optional output format (uses default if not provided)

    Returns:
        Dictionary containing result status and audio data or error information
    """
    try:
        logger.info(f"TTS service request from user {username}: {len(text)} characters")

        # Validate input
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Text is required for TTS conversion",
                "error_code": "MISSING_TEXT"
            }

        if not tts_client.is_available():
            return {
                "success": False,
                "error": "TTS service not available",
                "error_code": "SERVICE_UNAVAILABLE"
            }

        if not tts_client.validate_text(text):
            return {
                "success": False,
                "error": "Text is too long or invalid for TTS conversion",
                "error_code": "INVALID_TEXT"
            }

        # Use defaults if not provided
        voice_id = voice_id or tts_client.get_default_voice_id()
        model_id = model_id or tts_client.get_default_model_id()
        output_format = output_format or tts_client.get_default_output_format()

        # Convert text to speech
        audio = tts_client.convert_text_to_speech(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format
        )

        if audio:
            logger.info(f"TTS conversion successful for user {username}")
            return {
                "success": True,
                "audio": audio,
                "text_length": len(text),
                "voice_id": voice_id,
                "model_id": model_id,
                "output_format": output_format
            }
        else:
            logger.error(f"TTS conversion failed for user {username}")
            return {
                "success": False,
                "error": "TTS conversion failed",
                "error_code": "CONVERSION_FAILED"
            }

    except Exception as e:
        logger.error(f"TTS service error for user {username}: {e}")
        return {
            "success": False,
            "error": "TTS service error",
            "error_code": "SERVICE_ERROR",
            "details": str(e)
        }


def get_available_voices_service() -> Dict[str, Any]:
    """
    Get available voices with error handling.

    Returns:
        Dictionary containing available voices or error information
    """
    try:
        voices = tts_client.get_available_voices()

        if voices:
            return {
                "success": True,
                "voices": voices,
                "count": len(voices) if isinstance(voices, list) else 0
            }
        else:
            return {
                "success": False,
                "error": "Failed to retrieve available voices",
                "error_code": "VOICES_UNAVAILABLE"
            }

    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        return {
            "success": False,
            "error": "Error retrieving voices",
            "error_code": "SERVICE_ERROR",
            "details": str(e)
        }


def get_voice_details_service(voice_id: str) -> Dict[str, Any]:
    """
    Get voice details by ID with error handling.

    Args:
        voice_id: The voice ID to retrieve details for

    Returns:
        Dictionary containing voice details or error information
    """
    try:
        voice = tts_client.get_voice_by_id(voice_id)

        if voice:
            return {
                "success": True,
                "voice": voice,
                "voice_id": voice_id
            }
        else:
            return {
                "success": False,
                "error": f"Voice with ID {voice_id} not found",
                "error_code": "VOICE_NOT_FOUND"
            }

    except Exception as e:
        logger.error(f"Error getting voice details for {voice_id}: {e}")
        return {
            "success": False,
            "error": "Error retrieving voice details",
            "error_code": "SERVICE_ERROR",
            "details": str(e)
        }


def get_tts_status_service() -> Dict[str, Any]:
    """
    Get TTS service status and configuration.

    Returns:
        Dictionary containing TTS service status and configuration
    """
    try:
        status = {
            "available": tts_client.is_available(),
            "default_voice_id": tts_client.get_default_voice_id(),
            "default_model_id": tts_client.get_default_model_id(),
            "default_output_format": tts_client.get_default_output_format(),
            "max_text_length": 5000  # From client validation
        }

        return {
            "success": True,
            "status": status
        }

    except Exception as e:
        logger.error(f"Error getting TTS status: {e}")
        return {
            "success": False,
            "error": "Error retrieving TTS status",
            "error_code": "SERVICE_ERROR",
            "details": str(e)
        }


def validate_tts_request_service(text: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate TTS request parameters.

    Args:
        text: The text to validate
        voice_id: Optional voice ID to validate

    Returns:
        Dictionary containing validation results
    """
    try:
        validation_results = {
            "text_valid": tts_client.validate_text(text),
            "service_available": tts_client.is_available(),
            "text_length": len(text) if text else 0,
            "max_length": 5000
        }

        # Validate voice ID if provided
        if voice_id:
            voice_details = tts_client.get_voice_by_id(voice_id)
            validation_results["voice_valid"] = voice_details is not None
            validation_results["voice_id"] = voice_id
        else:
            validation_results["voice_valid"] = True
            validation_results["voice_id"] = tts_client.get_default_voice_id()

        # Overall validation
        validation_results["request_valid"] = (
            validation_results["text_valid"] and
            validation_results["service_available"] and
            validation_results["voice_valid"]
        )

        return {
            "success": True,
            "validation": validation_results
        }

    except Exception as e:
        logger.error(f"Error validating TTS request: {e}")
        return {
            "success": False,
            "error": "Error validating TTS request",
            "error_code": "VALIDATION_ERROR",
            "details": str(e)
        }
