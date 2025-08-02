"""
XplorED - Shared Type Definitions

This module contains all type definitions and data structures used throughout the backend,
following clean architecture principles as outlined in the documentation.

Type Categories:
- Data Classes: Structured data containers for business entities
- Type Aliases: Simple type definitions for common patterns
- Dictionary Types: Complex data structure definitions
- Service Classes: Core business logic service classes
- Schema Classes: API validation schemas

For detailed architecture information, see: docs/backend_structure.md
"""

from typing import Dict, List, Optional, Union, Any, Tuple
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


@dataclass
class UserAnalyticsData:
    """Data class for storing user analytics information."""
    user_id: str
    total_exercises_completed: int
    average_score: float
    vocabulary_mastered: int
    learning_streak_days: int
    last_activity_date: datetime
    skill_level: int


@dataclass
class GameSession:
    """Game session data structure."""
    session_id: str
    username: str
    level: int
    score: int
    time_taken: int
    created_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class LessonProgress:
    """Lesson progress tracking data."""
    user_id: str
    lesson_id: int
    block_id: str
    completed: bool
    completion_percentage: float
    updated_at: datetime


@dataclass
class SupportRequest:
    """Support request data structure."""
    request_id: int
    username: str
    subject: str
    description: str
    urgency: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None


@dataclass
class FeedbackEntry:
    """User feedback entry data structure."""
    feedback_id: int
    message: str
    username: Optional[str]
    category: Optional[str]
    priority: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class AIFeedback:
    """AI-generated feedback data structure."""
    feedback_id: str
    exercise_id: str
    user_answer: str
    correct_answer: str
    feedback_message: str
    explanation: Optional[str]
    alternatives: Optional[List[str]]
    quality_score: int
    created_at: datetime


@dataclass
class ExerciseFeedback:
    """Exercise feedback data structure."""
    block_id: str
    exercise_id: str
    feedback_type: str  # "immediate", "detailed", "summary"
    feedback_content: str
    quality_score: Optional[int]
    created_at: datetime


@dataclass
class ExerciseBlockData:
    """Exercise block data structure for database storage."""
    block_id: str
    username: str
    block_type: str  # "ai_generated", "training", "manual"
    exercises: str  # JSON string of exercises
    status: str  # "active", "completed", "archived"
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class AIExerciseBlock:
    """AI-generated exercise block data structure."""
    id: str
    username: str
    title: str
    level: int
    topic: str
    exercises: List[Dict[str, Any]]
    feedback_prompt: str
    status: str  # "current", "next", "completed"
    created_at: datetime
    updated_at: Optional[datetime] = None


@dataclass
class ExerciseSubmission:
    """Exercise submission data structure."""
    submission_id: int
    username: str
    block_id: str
    answers: str  # JSON string of answers
    score: Optional[float]
    completed_at: datetime
    created_at: datetime


# === Type Aliases ===
QualityScore = int  # 0-5 quality assessment score
UserLevel = int     # 1-10 user proficiency level
CEFRLevel = str     # A1, A2, B1, B2, C1, C2 European standard
ExerciseType = str  # "gap-fill", "translation" exercise categories
SkillType = str     # "gap-fill", "translation", "reading" skill areas
TopicName = str     # "family", "weather", etc. topic categories
SessionID = str     # Unique session identifier
BlockID = str       # Unique block identifier
LessonID = int      # Unique lesson identifier
UserID = str        # Unique user identifier
RequestID = int     # Unique request identifier
FeedbackID = int    # Unique feedback identifier
FeedbackType = str  # "immediate", "detailed", "summary" feedback types
FeedbackCategory = str  # "bug", "feature", "general" feedback categories
FeedbackStatus = str    # "pending", "reviewed", "resolved" feedback status
BlockType = str         # "ai_generated", "training", "manual" exercise block types
BlockStatus = str       # "active", "completed", "archived" exercise block status
AIBlockStatus = str     # "current", "next", "completed" AI exercise block status

# === Dictionary Types ===
TopicQualities = Dict[str, QualityScore]  # Topic -> quality score mapping
ExerciseAnswers = Dict[str, str]          # Exercise ID -> user answer mapping
UserData = Dict[str, Any]                 # Generic user data container
GameData = Dict[str, Any]                 # Game-related data container
LessonData = Dict[str, Any]               # Lesson-related data container
VocabularyData = Dict[str, Any]           # Vocabulary-related data container
AnalyticsData = Dict[str, Any]            # Analytics data container
SupportData = Dict[str, Any]              # Support-related data container
AIData = Dict[str, Any]                   # AI-related data container
ProgressData = Dict[str, Any]             # Progress tracking data container
FeedbackData = Dict[str, Any]             # Feedback-related data container

# === Complex Type Aliases ===
ExerciseList = List[Dict[str, Any]]       # List of exercise dictionaries
ExerciseBlockList = List[Dict[str, Any]]  # List of exercise blocks
AIExerciseBlockList = List[Dict[str, Any]]  # List of AI exercise blocks
VocabularyList = List[Dict[str, Any]]     # List of vocabulary entries
LessonList = List[Dict[str, Any]]         # List of lesson data
GameList = List[Dict[str, Any]]           # List of game data
SupportList = List[Dict[str, Any]]        # List of support requests
FeedbackList = List[Dict[str, Any]]       # List of feedback entries
AnalyticsList = List[Dict[str, Any]]      # List of analytics data
TopicMemoryList = List[Dict[str, Any]]    # List of topic memory entries

# === Function Return Types ===
EvaluationResult = Optional[Dict[str, Any]]  # Exercise evaluation result
StatisticsResult = Dict[str, Any]            # Statistics data result
LookupResult = Optional[Dict[str, Any]]      # Lookup operation result
ValidationResult = Tuple[bool, Optional[str]]  # Validation result with error message
ProcessingResult = Tuple[bool, Optional[str], Optional[int]]  # Processing result with ID
FeedbackResult = Optional[Dict[str, Any]]    # Feedback operation result
BlockResult = Optional[Dict[str, Any]]       # Exercise block operation result

# === API Response Types ===
APIResponse = Dict[str, Any]               # Generic API response
ErrorResponse = Dict[str, str]             # Error response structure
SuccessResponse = Dict[str, Any]           # Success response structure
ListResponse = Dict[str, List[Dict[str, Any]]]  # List response structure

# === Database Types ===
DatabaseRow = Dict[str, Any]               # Database row data
DatabaseResult = Optional[DatabaseRow]     # Database query result
DatabaseList = List[DatabaseRow]           # Database query result list

# === External Service Types ===
TTSServiceData = Dict[str, Any]            # TTS service data
RedisData = Optional[Dict[str, Any]]       # Redis stored data
MistralData = Dict[str, Any]               # Mistral AI service data

# === Configuration Types ===
ConfigData = Dict[str, Any]                # Configuration data
EnvironmentData = Dict[str, Any]           # Environment configuration

# === Export Configuration ===
__all__ = [
    # Data Classes
    "Exercise",
    "ExerciseBlock",
    "TopicMemoryEntry",
    "VocabularyEntry",
    "UserAnalyticsData",
    "GameSession",
    "LessonProgress",
    "SupportRequest",
    "FeedbackEntry",
    "AIFeedback",
    "ExerciseFeedback",
    "ExerciseBlockData",
    "AIExerciseBlock",
    "ExerciseSubmission",

    # Type Aliases
    "QualityScore",
    "UserLevel",
    "CEFRLevel",
    "ExerciseType",
    "SkillType",
    "TopicName",
    "SessionID",
    "BlockID",
    "LessonID",
    "UserID",
    "RequestID",
    "FeedbackID",
    "FeedbackType",
    "FeedbackCategory",
    "FeedbackStatus",
    "BlockType",
    "BlockStatus",
    "AIBlockStatus",

    # Dictionary Types
    "TopicQualities",
    "ExerciseAnswers",
    "UserData",
    "GameData",
    "LessonData",
    "VocabularyData",
    "AnalyticsData",
    "SupportData",
    "AIData",
    "ProgressData",
    "FeedbackData",

    # Complex Type Aliases
    "ExerciseList",
    "ExerciseBlockList",
    "AIExerciseBlockList",
    "VocabularyList",
    "LessonList",
    "GameList",
    "SupportList",
    "FeedbackList",
    "AnalyticsList",
    "TopicMemoryList",

    # Function Return Types
    "EvaluationResult",
    "StatisticsResult",
    "LookupResult",
    "ValidationResult",
    "ProcessingResult",
    "FeedbackResult",
    "BlockResult",

    # API Response Types
    "APIResponse",
    "ErrorResponse",
    "SuccessResponse",
    "ListResponse",

    # Database Types
    "DatabaseRow",
    "DatabaseResult",
    "DatabaseList",

    # External Service Types
    "TTSServiceData",
    "RedisData",
    "MistralData",

    # Configuration Types
    "ConfigData",
    "EnvironmentData",
]
