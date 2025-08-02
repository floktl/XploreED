"""
XplorED - Authentication Schemas

This module provides data validation schemas for authentication-related API endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator # type: ignore


class UserRegistrationSchema(BaseModel):
    """Schema for user registration requests."""

    username: str = Field(..., min_length=3, max_length=20, description="Username between 3-20 characters")
    password: str = Field(..., min_length=6, description="Password at least 6 characters")
    email: Optional[str] = Field(None, max_length=100, description="User email address")
    skill_level: int = Field(default=1, ge=1, le=10, description="Skill level between 1-10")

    @validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v.strip() if v else None


class UserLoginSchema(BaseModel):
    """Schema for user login requests."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class ProfileUpdateSchema(BaseModel):
    """Schema for profile update requests."""

    display_name: Optional[str] = Field(None, max_length=50, description="Display name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    location: Optional[str] = Field(None, max_length=100, description="User location")
    interests: Optional[list[str]] = Field(None, max_items=10, description="User interests")
    avatar_url: Optional[str] = Field(None, max_length=200, description="Avatar URL")


class SupportRequestSchema(BaseModel):
    """Schema for support request creation."""

    subject: str = Field(..., min_length=1, max_length=100, description="Support request subject")
    description: str = Field(..., min_length=1, max_length=1000, description="Detailed description")
    urgency: str = Field(default="medium", pattern="^(low|medium|high|urgent)$", description="Urgency level")
    contact_method: str = Field(default="email", pattern="^(email|phone|chat)$", description="Contact method")
    attachments: Optional[list[str]] = Field(default=[], description="File attachments")
