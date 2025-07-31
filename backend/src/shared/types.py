"""
XplorED - Shared Type Definitions

This module contains all type definitions and data structures used throughout the backend,
following clean architecture principles as outlined in the documentation.

Type Categories:
- Data Classes: Structured data containers for business entities
- Type Aliases: Simple type definitions for common patterns
- Dictionary Types: Complex data structure definitions

For detailed architecture information, see: docs/backend_structure.md
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime


# === Data Classes ===
@dataclass
class Exercise:
    """Exercise data structure for learning activities."""
    id: str
    type: str
    question: str
    correct_answer: str
    options: Optional[List[str]] = None


@dataclass
class ExerciseBlock:
    """Exercise block containing multiple related exercises."""
    lesson_id: str
    title: str
    level: int
    topic: str
    exercises: List[Exercise]
    feedback_prompt: str


@dataclass
class TopicMemoryEntry:
    """Spaced repetition memory entry for topic-based learning."""
    username: str
    grammar: str
    topic: str
    skill_type: str
    context: str
    ease_factor: float
    repetitions: int
    interval: int
    next_repeat: datetime
    last_review: datetime
    correct: bool
    quality: int


@dataclass
class VocabularyEntry:
    """Spaced repetition memory entry for vocabulary learning."""
    username: str
    word: str
    article: Optional[str]
    translation: str
    ease_factor: float
    repetitions: int
    interval: int
    next_repeat: datetime
    last_review: datetime
    correct: bool
    quality: int


# === Type Aliases ===
QualityScore = int  # 0-5 quality assessment score
UserLevel = int     # 1-10 user proficiency level
CEFRLevel = str     # A1, A2, B1, B2, C1, C2 European standard
ExerciseType = str  # "gap-fill", "translation" exercise categories
SkillType = str     # "gap-fill", "translation", "reading" skill areas
TopicName = str     # "family", "weather", etc. topic categories

# === Dictionary Types ===
TopicQualities = Dict[str, QualityScore]  # Topic -> quality score mapping
ExerciseAnswers = Dict[str, str]          # Exercise ID -> user answer mapping
UserData = Dict[str, Any]                 # Generic user data container


# === Export Configuration ===
__all__ = [
    # Data Classes
    "Exercise",
    "ExerciseBlock",
    "TopicMemoryEntry",
    "VocabularyEntry",

    # Type Aliases
    "QualityScore",
    "UserLevel",
    "CEFRLevel",
    "ExerciseType",
    "SkillType",
    "TopicName",

    # Dictionary Types
    "TopicQualities",
    "ExerciseAnswers",
    "UserData",
]
