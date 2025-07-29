"""Application constants."""

# Database
DEFAULT_TOPICS = ["general", "family", "weather", "food", "travel", "work", "hobbies", "shopping", "sports", "living"]

# AI Configuration
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-large-latest"

# Spaced Repetition
SM2_DEFAULT_EF = 2.5
SM2_DEFAULT_REPETITIONS = 0
SM2_DEFAULT_INTERVAL = 1

# Quality Scores
QUALITY_PERFECT = 5
QUALITY_GOOD = 4
QUALITY_ACCEPTABLE = 3
QUALITY_POOR = 2
QUALITY_VERY_POOR = 1
QUALITY_BLACKOUT = 0

# Exercise Types
EXERCISE_TYPE_GAP_FILL = "gap-fill"
EXERCISE_TYPE_TRANSLATION = "translation"

# Skill Types
SKILL_TYPE_GAP_FILL = "gap-fill"
SKILL_TYPE_TRANSLATION = "translation"
SKILL_TYPE_READING = "reading"

# User Levels
MIN_USER_LEVEL = 1
MAX_USER_LEVEL = 10

# CEFR Levels
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
