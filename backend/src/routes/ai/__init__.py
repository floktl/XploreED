"""AI blueprint and route aggregation."""

from utils.imports.imports import *
from pathlib import Path

from app.blueprint import ai_bp

DEFAULT_TOPICS = [
    "dogs",
    "living",
    "family",
    "work",
    "shopping",
    "travel",
    "sports",
    "food",
    "hobbies",
    "weather",
]

FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "mock_data" / "ai_feedback.json"

EXERCISE_TEMPLATE = {
    "lessonId": "dynamic-ai-lesson",
    "title": "AI Generated Exercises",
    "instructions": "Fill in the blanks or translate the sentences.",
    "level": "A1",
    "exercises": [],
    "feedbackPrompt": "",
    "vocabHelp": [],
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

# Import submodules so routes get registered
from . import helpers, tts, exercise_routes, feedback_routes, training_routes, lesson_routes, misc_routes
from .helpers import generate_training_exercises, evaluate_answers_with_ai, generate_reading_exercise

__all__ = [
    "ai_bp",
    "generate_training_exercises",
    "evaluate_answers_with_ai",
    "generate_reading_exercise",
]

