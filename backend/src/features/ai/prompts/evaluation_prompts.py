"""
XplorED - Evaluation Prompts Module

This module provides prompt templates for exercise evaluation and assessment,
following clean architecture principles as outlined in the documentation.

Evaluation Components:
- Answer Evaluation: Assessment of student responses to exercises
- Quality Evaluation: Detailed quality scoring for grammar topics
- Topic Detection: Language topic identification in text
- Alternative Answers: Generation of multiple correct answer variations
- Explanations: Grammar and vocabulary explanations for correct answers

For detailed architecture information, see: docs/backend_structure.md
"""

from __future__ import annotations
import json


def detect_topics_prompt(text: str) -> dict:
    """Return prompt for detecting grammar topics in text."""
    return {
        "role": "user",
        "content": (
            f"Analyze this German text and identify the grammar topics present:\n\n{text}\n\n"
            "Return a JSON array of topic strings (lowercase, no duplicates). "
            "Common topics: present tense, past tense, future tense, modal verbs, "
            "articles, adjectives, prepositions, cases (nominative, accusative, dative, genitive), "
            "pronouns, word order, subordination, coordination, etc."
        ),
    }


def evaluate_translation_prompt(english: str, student: str) -> dict:
    """Return prompt for evaluating a translation."""
    return {
        "role": "user",
        "content": f"""
Evaluate this German translation:

English: "{english}"
Student's German: "{student}"

Return JSON with:
- "correct": true/false
- "reason": brief explanation in English
""",
    }


def quality_evaluation_prompt(
    english: str,
    reference: str,
    student: str,
    topics: list[str],
) -> dict:
    """Return prompt for evaluating quality of grammar topics."""
    topics_str = ", ".join(topics)

    if english:
        # Translation exercise
        context_line = f"English sentence: '{english}'\n"
        exercise_type = "translation"
    else:
        # Gap-fill exercise (no English translation)
        context_line = ""
        exercise_type = "gap-fill"

    return {
        "role": "user",
        "content": (
            f"You are a helpful German teacher grading a student's {exercise_type}.\n\n"
            f"{context_line}"
            f"Reference answer: '{reference}'\n"
            f"Student answer: '{student}'\n\n"
            "IMPORTANT: For gap-fill exercises, if the gap tests related grammar concepts (like personal pronoun + verb conjugation), evaluate them together in the context since they must agree, but still evaluate them individually.\n"
            "For translation exercises, evaluate each grammar topic individually.\n\n"
            "Return a JSON object where each grammar topic is a key (all lowercase, spaces only), "
            "and its value is an integer from 0 to 5 representing the SM2 quality scale:\n\n"
            "EVALUATION RULES:\n"
            "- Use the FULL 0-5 scale for nuanced evaluation:\n"
            "  * 5 = Perfect usage of the grammar element\n"
            "  * 4 = Correct but with slight hesitation or minor error\n"
            "  * 3 = Correct but with difficulty or noticeable error\n"
            "  * 2 = Incorrect but the student seemed to know the concept\n"
            "  * 1 = Incorrect but some knowledge was shown\n"
            "  * 0 = Complete blackout or completely wrong usage\n"
            "- For translation: Evaluate each grammar element independently\n"
            "- Consider the student's apparent understanding level\n\n"
            "For example:\n"
            "{\n"
            "  \"adjective\": 5,\n"
            "  \"nominative case\": 4,\n"
            "  \"modal verb\": 3,\n"
            "  \"verb conjugation\": 2,\n"
            "  \"article\": 1,\n"
            "  \"preposition\": 0\n"
            "}\n\n"
            f"Topics: {topics_str}"
        ),
    }


def answers_evaluation_prompt(instructions: str, formatted: list) -> dict:
    """Return prompt for checking exercise answers."""
    return {
        "role": "user",
        "content": instructions + "\n" + json.dumps(formatted, ensure_ascii=False),
    }


def alternative_answers_prompt(correct_sentence: str) -> dict:
    """Return prompt for generating alternative ways to say the same thing in German."""
    return {
        "role": "user",
        "content": (
            f"Give up to 3 alternative ways to say the following sentence in German, with the same meaning and register. "
            f"Return only a JSON array of strings, no explanations, no extra text, no markdown, no labels.\nSentence: {correct_sentence}"
        ),
    }


def explanation_prompt(question: str, correct_answer: str) -> dict:
    """Return prompt for generating a short grammar/vocabulary explanation for the correct answer."""
    return {
        "role": "user",
        "content": (
            "Given the following exercise and correct answer, give a very short grammar or vocabulary explanation (1-2 sentences) for a German learner. "
            "Do NOT mention the user's answer, do NOT restate the correct answer, and do NOT say if it is correct or incorrect. "
            "Only explain the grammar or vocabulary used in the correct answer, as briefly as possible.\n"
            f"Exercise: {question}\nCorrect answer: {correct_answer}\nReply in English."
        ),
    }
