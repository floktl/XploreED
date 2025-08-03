"""
XplorED - TTS Client Module

This module provides a centralized TTS client for the XplorED platform,
following clean architecture principles as outlined in the documentation.

TTS Client Components:
- ElevenLabs Integration: Handle text-to-speech conversion using ElevenLabs API
- Voice Management: Manage different voice options and configurations
- Error Handling: Handle TTS service errors and timeouts
- Configuration: Support environment-based API key configuration

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
import os
from typing import Optional, Any
from io import BytesIO
from shared.exceptions import DatabaseError
from shared.types import TTSServiceData

logger = logging.getLogger(__name__)

# Import ElevenLabs client
try:
    from elevenlabs.client import ElevenLabs  # type: ignore
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ElevenLabs = None
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs client not available")


class TTSClient:
    """Centralized TTS client for the XplorED platform."""

    _instance: Optional['TTSClient'] = None
    _client: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the TTS client with environment-based configuration."""
        if not ELEVENLABS_AVAILABLE:
            logger.error("ElevenLabs client not available")
            self._client = None
            return

        try:
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                logger.error("ELEVENLABS_API_KEY not configured")
                self._client = None
                return

            self._client = ElevenLabs(api_key=api_key)
            logger.info("TTS client initialized with ElevenLabs")
        except Exception as e:
            logger.error(f"Error initializing TTS client: {e}")
            raise DatabaseError(f"Error initializing TTS client: {str(e)}")

    @property
    def client(self) -> Optional[Any]:
        """Get the TTS client instance."""
        return self._client

    def is_available(self) -> bool:
        """Check if TTS service is available."""
        return self._client is not None and ELEVENLABS_AVAILABLE

    def convert_text_to_speech(
        self,
        text: str,
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128"
    ) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API.

        Args:
            text: The text to convert to speech
            voice_id: The voice ID to use for synthesis
            model_id: The model ID to use for synthesis
            output_format: The output format for the audio

        Returns:
            Audio data as bytes or None if conversion failed
        """
        if not self.is_available():
            logger.error("TTS service not available")
            return None

        if not text or not text.strip():
            logger.error("Text is required for TTS conversion")
            return None

        try:
            audio = self._client.text_to_speech.convert(
                voice_id=voice_id,
                text=text.strip(),
                model_id=model_id,
                output_format=output_format,
            )
            logger.info(f"Successfully converted text to speech: {len(text)} characters")
            return audio
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            raise DatabaseError(f"Error converting text to speech: {str(e)}")

    def get_available_voices(self) -> Optional[TTSServiceData]:
        """
        Get available voices from ElevenLabs.

        Returns:
            Dictionary containing available voices or None if failed
        """
        if not self.is_available():
            logger.error("TTS service not available")
            return None

        try:
            voices = self._client.voices.get_all()
            logger.info(f"Retrieved {len(voices) if voices else 0} available voices")
            return voices
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return None

    def get_voice_by_id(self, voice_id: str) -> Optional[TTSServiceData]:
        """
        Get voice details by ID.

        Args:
            voice_id: The voice ID to retrieve

        Returns:
            Voice details dictionary or None if not found
        """
        if not self.is_available():
            logger.error("TTS service not available")
            return None

        try:
            voice = self._client.voices.get(voice_id=voice_id)
            logger.info(f"Retrieved voice details for ID: {voice_id}")
            return voice
        except Exception as e:
            logger.error(f"Error getting voice by ID {voice_id}: {e}")
            return None

    def validate_text(self, text: str) -> bool:
        """
        Validate text for TTS conversion.

        Args:
            text: The text to validate

        Returns:
            True if text is valid for TTS, False otherwise
        """
        if not text or not text.strip():
            return False

        # Check for reasonable length (adjust as needed)
        if len(text.strip()) > 5000:  # 5000 character limit
            return False

        return True

    def get_default_voice_id(self) -> str:
        """Get the default voice ID for German language."""
        return "JBFqnCBsd6RMkjVDRZzb"

    def get_default_model_id(self) -> str:
        """Get the default model ID for multilingual support."""
        return "eleven_multilingual_v2"

    def get_default_output_format(self) -> str:
        """Get the default output format for audio."""
        return "mp3_44100_128"

# Global TTS client instance
tts_client = TTSClient()
