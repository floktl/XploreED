"""
XplorED - Translation Prompts Module

This module provides prompt templates for translation and language analysis,
following clean architecture principles as outlined in the documentation.

Translation Components:
- Sentence Translation: English to German translation
- Word Translation: Individual word translation
- Word Analysis: Detailed analysis of German words
- Language Processing: Text analysis and processing

For detailed architecture information, see: docs/backend_structure.md
"""

from __future__ import annotations


def translate_sentence_prompt(english_sentence: str) -> dict:
    """Return prompt for translating English to German."""
    return {
        "role": "user",
        "content": f"Translate this sentence to German:\n{english_sentence}",
    }


def translate_word_prompt(word: str) -> dict:
    """Return prompt for translating a single German word to English."""
    return {
        "role": "user",
        "content": f"Translate the German word '{word}' to English. Respond ONLY with the translation string.",
    }


def analyze_word_prompt(word: str) -> dict:
    """Return prompt for analyzing a German word."""
    return {
        "role": "user",
        "content": f"""
Analyze this German word: "{word}"

Return JSON with:
- "base_form": the base/infinitive form
- "type": noun, verb, adjective, adverb, etc.
- "article": der/die/das (for nouns)
- "translation": English translation
- "info": additional grammatical info
""",
    }
