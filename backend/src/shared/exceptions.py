"""
German Class Tool - Shared Exceptions

This module contains all custom exceptions used throughout the backend,
following clean architecture principles as outlined in the documentation.

Exception Hierarchy:
- GermanClassToolException: Base exception for all application errors
  - AIEvaluationError: AI evaluation and processing failures
  - DatabaseError: Database operation failures
  - ValidationError: Input validation failures
  - AuthenticationError: Authentication and authorization failures
  - ExerciseGenerationError: Exercise creation and generation failures
  - TopicMemoryError: Spaced repetition and memory operation failures

For detailed architecture information, see: docs/backend_structure.md
"""

# === Base Exception ===
class GermanClassToolException(Exception):
    """Base exception for all German Class Tool application errors."""
    pass


# === AI Layer Exceptions ===
class AIEvaluationError(GermanClassToolException):
    """Raised when AI evaluation or processing operations fail."""
    pass


# === Core Layer Exceptions ===
class DatabaseError(GermanClassToolException):
    """Raised when database operations fail."""
    pass


class ValidationError(GermanClassToolException):
    """Raised when input validation fails."""
    pass


# === Authentication Exceptions ===
class AuthenticationError(GermanClassToolException):
    """Raised when authentication or authorization fails."""
    pass


# === Features Layer Exceptions ===
class ExerciseGenerationError(GermanClassToolException):
    """Raised when exercise generation or creation fails."""
    pass


class TopicMemoryError(GermanClassToolException):
    """Raised when spaced repetition or memory operations fail."""
    pass


# === Export Configuration ===
__all__ = [
    "GermanClassToolException",
    "AIEvaluationError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "ExerciseGenerationError",
    "TopicMemoryError",
]
