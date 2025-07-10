"""Helper functions for lesson routes."""

from utils.grammar.grammar_utils import detect_language_topics
from utils.ai.translation_utils import update_topic_memory_reading
from utils.spaced_repetition.level_utils import check_auto_level_up
from utils.helpers.helper import run_in_background


def update_reading_memory_async(username: str, text: str) -> None:
    """Update reading topic memory in a background thread."""
    def task():
        detect_language_topics(text)  # ensure tokenization before context
        update_topic_memory_reading(username, text)
        check_auto_level_up(username)

    run_in_background(task)

