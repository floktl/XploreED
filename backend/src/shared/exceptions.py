"""Custom exceptions for the application."""


class GermanClassToolException(Exception):
    """Base exception for the application."""
    pass


class AIEvaluationError(GermanClassToolException):
    """Raised when AI evaluation fails."""
    pass


class DatabaseError(GermanClassToolException):
    """Raised when database operations fail."""
    pass


class ValidationError(GermanClassToolException):
    """Raised when input validation fails."""
    pass


class AuthenticationError(GermanClassToolException):
    """Raised when authentication fails."""
    pass


class ExerciseGenerationError(GermanClassToolException):
    """Raised when exercise generation fails."""
    pass


class TopicMemoryError(GermanClassToolException):
    """Raised when topic memory operations fail."""
    pass
