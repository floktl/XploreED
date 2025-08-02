"""
XplorED - Shared Exceptions

This module contains all custom exceptions used throughout the backend,
following clean architecture principles as outlined in the documentation.

Exception Hierarchy:
- XplorEDException: Base exception for all application errors
  - ConfigurationError: Configuration and setup failures
  - DatabaseError: Database operation failures
  - ValidationError: Input validation failures
  - AuthenticationError: Authentication and authorization failures
  - AIEvaluationError: AI evaluation and processing failures
  - ExerciseGenerationError: Exercise creation and generation failures
  - TopicMemoryError: Spaced repetition and memory operation failures
  - TimeoutError: Operation timeout failures
  - ProcessingError: General processing failures

For detailed architecture information, see: docs/backend_structure.md
"""

# === Base Exception ===
class XplorEDException(Exception):
    """Base exception for all XplorED application errors."""
    pass


# === Configuration Exceptions ===
class ConfigurationError(XplorEDException):
    """Raised when configuration or setup operations fail."""
    pass


# === Database Exceptions ===
class DatabaseError(XplorEDException):
    """Raised when database operations fail."""
    pass


# === Validation Exceptions ===
class ValidationError(XplorEDException):
    """Raised when input validation fails."""
    pass


# === Authentication Exceptions ===
class AuthenticationError(XplorEDException):
    """Raised when authentication or authorization fails."""
    pass


# === AI Layer Exceptions ===
class AIEvaluationError(XplorEDException):
    """Raised when AI evaluation or processing operations fail."""
    pass


class ExerciseGenerationError(XplorEDException):
    """Raised when exercise generation or creation fails."""
    pass


class TopicMemoryError(XplorEDException):
    """Raised when spaced repetition or memory operations fail."""
    pass


# === Processing Exceptions ===
class ProcessingError(XplorEDException):
    """Raised when general processing operations fail."""
    pass


class TimeoutError(XplorEDException):
    """Raised when operations timeout."""
    pass


# === Export Configuration ===
__all__ = [
    "XplorEDException",
    "ConfigurationError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "AIEvaluationError",
    "ExerciseGenerationError",
    "TopicMemoryError",
    "ProcessingError",
    "TimeoutError",
]
