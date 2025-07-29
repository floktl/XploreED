"""Type definitions for the application."""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Exercise:
    """Exercise data structure."""
    id: str
    type: str
    question: str
    correct_answer: str
    options: Optional[List[str]] = None


@dataclass
class ExerciseBlock:
    """Exercise block data structure."""
    lesson_id: str
    title: str
    level: int
    topic: str
    exercises: List[Exercise]
    feedback_prompt: str


@dataclass
class TopicMemoryEntry:
    """Topic memory entry data structure."""
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
    """Vocabulary entry data structure."""
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


# Type aliases
QualityScore = int  # 0-5
UserLevel = int  # 1-10
CEFRLevel = str  # A1, A2, B1, B2, C1, C2
ExerciseType = str  # "gap-fill", "translation"
SkillType = str  # "gap-fill", "translation", "reading"
TopicName = str  # "family", "weather", etc.

# Dictionary types
TopicQualities = Dict[str, QualityScore]
ExerciseAnswers = Dict[str, str]
UserData = Dict[str, Any]
