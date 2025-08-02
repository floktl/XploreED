"""
XplorED - Shared Package

This package provides shared functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Shared Modules:
- constants: Application-wide constants and configuration
- exceptions: Custom exception classes
- types: Type definitions and data structures
- text_utils: Shared text processing utilities

For detailed architecture information, see: docs/backend_structure.md
"""

from .constants import CEFR_LEVELS
from .exceptions import (
    AIEvaluationError, DatabaseError, ValidationError, AuthenticationError,
    ExerciseGenerationError, TopicMemoryError, XplorEDException,
    ConfigurationError, ProcessingError, TimeoutError
)
from .types import Exercise, ExerciseBlock, QualityScore, UserLevel
from .text_utils import _extract_json, _normalize_umlauts, _strip_final_punct

__all__ = [
    # Constants
    "CEFR_LEVELS",

    # Exceptions
    "AIEvaluationError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "ExerciseGenerationError",
    "TopicMemoryError",
    "XplorEDException",
    "ConfigurationError",
    "ProcessingError",
    "TimeoutError",

    # Types
    "Exercise",
    "ExerciseBlock",
    "QualityScore",
    "UserLevel",

    # Text utilities
    "_extract_json",
    "_normalize_umlauts",
    "_strip_final_punct",
]
