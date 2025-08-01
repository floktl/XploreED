"""
XplorED - AI Package

This package provides AI-powered features for the XplorED platform,
following clean architecture principles as outlined in the documentation.

AI Components:
- AI Evaluation: Exercise evaluation and assessment
- AI Generation: Content and exercise generation
- AI Memory: Vocabulary and topic memory management
- AI Prompts: Prompt templates and management
- AI Feedback: Feedback generation and processing

For detailed architecture information, see: docs/backend_structure.md
"""

# AI Templates
EXERCISE_TEMPLATE = {
    "lessonId": "dynamic-ai-lesson",
    "title": "AI Feedback",
    "level": "A1",
    "exercises": [],
}

READING_TEMPLATE = {
    "lessonId": "ai-reading",
    "style": "story",
    "text": "Guten Morgen!",
    "questions": [],
    "feedbackPrompt": "",
    "vocabHelp": [],
}

CEFR_LEVELS = [
    "A1", "A1", "A2", "A2", "B1",
    "B1", "B2", "B2", "C1", "C1", "C2"
]

FEEDBACK_FILE = [
    {
        "id": "fb1",
        "title": "Feedback After Set 1",
        "instructions": "Here are notes on your first round of exercises.",
        "type": "mixed",
        "feedbackPrompt": "You mixed up some plural forms like 'wir sind' and 'sie sind'. Review the pronouns before continuing.",
        "created_at": "2025-06-12T09:00:00Z"
    },
    {
        "id": "fb2",
        "title": "Feedback After Set 2",
        "instructions": "Comments on your second round of practice.",
        "type": "mixed",
        "feedbackPrompt": "Great improvement! Keep an eye on word order in translations and continue practicing.",
        "created_at": "2025-06-12T09:10:00Z"
    }
]

# Import feedback functions from feedback package
from .feedback import (
    create_feedback_session,
    get_feedback_progress,
    update_feedback_progress,
    get_feedback_result,
    generate_feedback_with_progress,
    generate_ai_feedback_simple,
    get_cached_feedback_list,
    get_cached_feedback_item,
)

# Re-export all AI feedback functions for backward compatibility
__all__ = [
    # AI Templates
    "EXERCISE_TEMPLATE",
    "READING_TEMPLATE",
    "CEFR_LEVELS",
    "FEEDBACK_FILE",

    # Feedback Session
    "create_feedback_session",
    "get_feedback_progress",
    "update_feedback_progress",
    "get_feedback_result",

    # Feedback Generation
    "generate_feedback_with_progress",
    "generate_ai_feedback_simple",
    "get_cached_feedback_list",
    "get_cached_feedback_item",
]
