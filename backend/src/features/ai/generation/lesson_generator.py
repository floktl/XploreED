"""Helper functions for lesson routes."""

from features.grammar.detector import detect_language_topics
from features.ai.evaluation.translation_evaluator import update_topic_memory_reading
from features.ai.memory.level_manager import check_auto_level_up
from core.utils.helpers import run_in_background


def update_reading_memory_async(username: str, text: str) -> None:
    """Update reading topic memory in a background thread."""
    def task():
        detect_language_topics(text)  # ensure tokenization before context
        update_topic_memory_reading(username, text)
        check_auto_level_up(username)

    run_in_background(task)

