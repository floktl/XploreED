"""
XplorED - AI Assistance Prompts Module

This module provides prompt templates for AI assistance and streaming responses,
following clean architecture principles as outlined in the documentation.

Assistance Components:
- Context-Aware Questions: AI responses with user context
- Contextual Questions: AI questions with additional context
- Streaming Responses: Real-time AI interaction
- User Support: General AI assistance for platform features

For detailed architecture information, see: docs/backend_structure.md
"""

from __future__ import annotations


def ai_context_prompt(
    weaknesses_summary: str,
    lesson_progress_summary: str,
    question: str
) -> dict:
    """Return prompt for AI context-aware question answering."""
    return {
        "role": "user",
        "content": (
            f"Weakest topics: {weaknesses_summary}. "
            f"Lesson progress: {lesson_progress_summary}. "
            f"User question: {question}"
        ),
    }


def ai_question_prompt(context: str, question: str) -> dict:
    """Return prompt for AI question with context."""
    full_question = f"{context}\n\nQuestion: {question}" if context else question
    return {
        "role": "user",
        "content": full_question,
    }


def streaming_prompt(context: str) -> dict:
    """Return prompt for streaming AI responses."""
    return {
        "role": "user",
        "content": context,
    }
