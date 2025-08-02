"""
XplorED - API Schemas Module

This module provides data validation and serialization schemas for the API layer,
following clean architecture principles as outlined in the documentation.

Schema Components:
- Data validation schemas for request/response validation
- Serialization schemas for API responses
- Type definitions for API data structures

Implemented Schemas:
- UserRegistrationSchema: User registration data validation
- UserLoginSchema: User login data validation
- ProfileUpdateSchema: Profile update data validation
- SupportRequestSchema: Support request data validation

All schemas use Pydantic for automatic validation, type checking, and error handling.

For detailed architecture information, see: docs/backend_structure.md
"""

# === Schema Components ===
# Authentication and User Management Schemas
# - UserRegistrationSchema: Validates user registration data
# - UserLoginSchema: Validates user login credentials
# - ProfileUpdateSchema: Validates profile update requests
# - SupportRequestSchema: Validates support request creation

# Future schema implementations:
# - ExerciseSchema: Exercise data validation and serialization
# - LessonSchema: Lesson data validation and serialization
# - FeedbackSchema: Feedback submission validation
# - GameSchema: Game-related data validation

# === Export Configuration ===
from .auth import (
    UserRegistrationSchema,
    UserLoginSchema,
    ProfileUpdateSchema,
    SupportRequestSchema
)

__all__: list[str] = [
    "UserRegistrationSchema",
    "UserLoginSchema",
    "ProfileUpdateSchema",
    "SupportRequestSchema"
]
