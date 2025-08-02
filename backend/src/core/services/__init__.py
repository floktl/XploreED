"""
XplorED - Core Services Module

This module provides core business logic services for the backend application,
following clean architecture principles as outlined in the documentation.

Service Components:
- user_service: Core user business logic and statistics
- game_service: Core game business logic and evaluation
- exercise_service: Core exercise evaluation business logic
- vocabulary_service: Core vocabulary business logic and analytics
- lesson_service: Core lesson business logic and progress tracking
- progress_service: Core progress business logic and analytics

Note: Import management has been moved to infrastructure/imports/ for better separation.

For detailed architecture information, see: docs/backend_structure.md
"""

from .user_service import UserService
from .game_service import GameService
from .exercise_service import ExerciseService
from .vocabulary_service import VocabularyService
from .lesson_service import LessonService
from .progress_service import ProgressService

# === Export Configuration ===
__all__ = [
    # Core business logic services
    "UserService",
    "GameService",
    "ExerciseService",
    "VocabularyService",
    "LessonService",
    "ProgressService",
]
