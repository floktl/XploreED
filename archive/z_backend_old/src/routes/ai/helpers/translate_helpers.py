"""Helper functions for translate routes."""

from utils.ai.translation_utils import evaluate_topic_qualities_ai, update_topic_memory_translation
from utils.helpers.helper import run_in_background


def update_memory_async(username: str, english: str, german: str, student_input: str) -> None:
    """Evaluate topic qualities and update memory in a background thread."""
    def task():
        qualities = evaluate_topic_qualities_ai(english, german, student_input)
        update_topic_memory_translation(username, german, qualities)

    run_in_background(task)

