"""
XplorED - TTS Module

This module provides TTS functionality for the XplorED platform.
"""

from .client import tts_client, TTSClient
from .service import (
    convert_text_to_speech_service,
    get_available_voices_service,
    get_voice_details_service,
    get_tts_status_service,
    validate_tts_request_service
)

__all__ = [
    'tts_client',
    'TTSClient',
    'convert_text_to_speech_service',
    'get_available_voices_service',
    'get_voice_details_service',
    'get_tts_status_service',
    'validate_tts_request_service'
]
