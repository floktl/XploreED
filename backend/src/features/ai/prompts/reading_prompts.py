"""
XplorED - Reading Prompts Module

This module provides prompt templates for reading exercises and games,
following clean architecture principles as outlined in the documentation.

Reading Components:
- Reading Exercise Generation: AI-powered reading text creation
- Reading Explanations: Explanations for reading exercise answers
- Game Sentences: Sentence generation for language games
- Interactive Content: Engaging reading materials

For detailed architecture information, see: docs/backend_structure.md
"""

from __future__ import annotations


def reading_exercise_prompt(style: str, cefr_level: str, extra: str) -> dict:
    """Return prompt for generating a reading exercise."""
    return {
        "role": "user",
        "content": (
            "Create a short "
            f"{style} in German for level {cefr_level}. "
            f"{extra}"
            "In the 'text' field, use double newlines (\\n\\n) between paragraphs for clear Absätze (paragraphs). "
            "Return JSON with keys 'text', 'questions' (each with id, question, options, correctAnswer)."
        ),
    }


def reading_explanation_prompt(
    user_answer: str,
    question: str,
    correct_answer: str
) -> dict:
    """Return prompt for generating reading exercise explanations."""
    return {
        "role": "user",
        "content": f"Explain in one short sentence (no more than 12 words) why the answer '{user_answer}' is incorrect for the question: {question} (correct answer: {correct_answer})"
    }


def game_sentence_prompt(vocab_list: list[str], topics: list[str]) -> dict:
    """Return prompt for creating a short game sentence."""
    vocab = ", ".join(vocab_list)
    tpcs = ", ".join(topics)
    return {
        "role": "user",
        "content": (
            "Create one short (max 8 words) German sentence for a beginner."
            f"Use some of these words: {vocab}. "
            f"Topics to consider: {tpcs}. "
            "Only return the sentence."
        ),
    }
