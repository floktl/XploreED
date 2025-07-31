"""
XplorED - Shared Constants

This module contains all application-wide constants used throughout the backend,
following clean architecture principles as outlined in the documentation.

Constants are organized by domain:
- Database: Default topics and data structures
- AI Configuration: External AI service settings
- Spaced Repetition: Memory algorithm parameters
- Quality Scores: Assessment and evaluation metrics
- Exercise Types: Learning activity categories
- Skill Types: Competency areas
- User Levels: Proficiency progression
- CEFR Levels: European language standards

For detailed architecture information, see: docs/backend_structure.md
"""

# === Database Constants ===
DEFAULT_TOPICS = [
    "general", "family", "weather", "food", "travel",
    "work", "hobbies", "shopping", "sports", "living"
]

# === AI Configuration ===
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-large-latest"

# === Spaced Repetition Algorithm ===
SM2_DEFAULT_EF = 2.5  # Easiness Factor
SM2_DEFAULT_REPETITIONS = 0  # Number of successful repetitions
SM2_DEFAULT_INTERVAL = 1  # Days until next review

# === Quality Assessment Scores ===
QUALITY_PERFECT = 5      # Perfect response
QUALITY_GOOD = 4         # Good response with minor errors
QUALITY_ACCEPTABLE = 3   # Acceptable response with some errors
QUALITY_POOR = 2         # Poor response with significant errors
QUALITY_VERY_POOR = 1    # Very poor response
QUALITY_BLACKOUT = 0     # Complete failure/blackout

# === Exercise Types ===
EXERCISE_TYPE_GAP_FILL = "gap-fill"      # Fill in the blanks
EXERCISE_TYPE_TRANSLATION = "translation" # Translation exercises

# === Skill Types ===
SKILL_TYPE_GAP_FILL = "gap-fill"      # Grammar and vocabulary gaps
SKILL_TYPE_TRANSLATION = "translation" # Translation skills
SKILL_TYPE_READING = "reading"         # Reading comprehension

# === User Proficiency Levels ===
MIN_USER_LEVEL = 1   # Beginner level
MAX_USER_LEVEL = 10  # Advanced level

# === CEFR Language Proficiency Levels ===
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

# === Export Configuration ===
__all__ = [
    # Database
    "DEFAULT_TOPICS",

    # AI Configuration
    "MISTRAL_API_URL",
    "MISTRAL_MODEL",

    # Spaced Repetition
    "SM2_DEFAULT_EF",
    "SM2_DEFAULT_REPETITIONS",
    "SM2_DEFAULT_INTERVAL",

    # Quality Scores
    "QUALITY_PERFECT",
    "QUALITY_GOOD",
    "QUALITY_ACCEPTABLE",
    "QUALITY_POOR",
    "QUALITY_VERY_POOR",
    "QUALITY_BLACKOUT",

    # Exercise Types
    "EXERCISE_TYPE_GAP_FILL",
    "EXERCISE_TYPE_TRANSLATION",

    # Skill Types
    "SKILL_TYPE_GAP_FILL",
    "SKILL_TYPE_TRANSLATION",
    "SKILL_TYPE_READING",

    # User Levels
    "MIN_USER_LEVEL",
    "MAX_USER_LEVEL",

    # CEFR Levels
    "CEFR_LEVELS",
]
