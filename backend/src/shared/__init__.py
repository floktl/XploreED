"""
German Class Tool - Shared Module

This module provides shared components used throughout the backend application,
following clean architecture principles as outlined in the documentation.

Components:
- constants: Application-wide constants and configuration values
- exceptions: Custom exception classes for error handling
- types: Type definitions and data structures

For detailed architecture information, see: docs/backend_structure.md
"""

from . import constants
from . import exceptions
from . import types

# Re-export commonly used items for convenience
from .constants import *
from .exceptions import *
from .types import *

__all__ = [
    # Module imports
    "constants",
    "exceptions",
    "types",

    # Constants
    "DEFAULT_TOPICS",
    "MISTRAL_API_URL",
    "MISTRAL_MODEL",
    "SM2_DEFAULT_EF",
    "SM2_DEFAULT_REPETITIONS",
    "SM2_DEFAULT_INTERVAL",
    "QUALITY_PERFECT",
    "QUALITY_GOOD",
    "QUALITY_ACCEPTABLE",
    "QUALITY_POOR",
    "QUALITY_VERY_POOR",
    "QUALITY_BLACKOUT",
    "EXERCISE_TYPE_GAP_FILL",
    "EXERCISE_TYPE_TRANSLATION",
    "SKILL_TYPE_GAP_FILL",
    "SKILL_TYPE_TRANSLATION",
    "SKILL_TYPE_READING",
    "MIN_USER_LEVEL",
    "MAX_USER_LEVEL",
    "CEFR_LEVELS",

    # Exceptions
    "GermanClassToolException",
    "AIEvaluationError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "ExerciseGenerationError",
    "TopicMemoryError",

    # Types
    "Exercise",
    "ExerciseBlock",
    "TopicMemoryEntry",
    "VocabularyEntry",
    "QualityScore",
    "UserLevel",
    "CEFRLevel",
    "ExerciseType",
    "SkillType",
    "TopicName",
    "TopicQualities",
    "ExerciseAnswers",
    "UserData",
]
