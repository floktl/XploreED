"""Common user prompt templates."""

from __future__ import annotations
import json


def exercise_generation_prompt(
    level_val: int,
    cefr_level: str,
    example_exercise_block: dict,
    vocabular: list,
    filtered_topic_memory: list,
    recent_questions: str = "",
) -> dict:
    """Return the user prompt for generating a new exercise block, including recent questions to avoid repeats."""
    return {
        "role": "user",
        "content": f"""
You are generating structured grammar and translation exercises for a German learner.
The student's level is {level_val}/10 (CEFR {cefr_level}).
Adjust sentence complexity and vocabulary accordingly.

Here is the required JSON structure — you must follow it **exactly**:

1. Each exercise must include:
   - `id`: a unique ID like `\"ex1\"`
   - `type`: either `\"gap-fill\"` or `\"translation\"`
   - `question`: a string (either a full sentence with a blank depending on the students level, or a translation task with the same conditions, remember to always put a full sentence)
   - For "gap-fill":
     - `options`: list of 4 strings, one of them has to be the correct answer, be sure to include the right answer.
     - `correctAnswer`: the correct string
   - For "translation":
     - `correctAnswer`: the correct German translation

 2. The overall JSON must contain:
   - `lessonId`, `title`, `instructions`, `level`
   - `exercises`: list of 3 total exercises (mix of both types)
   - `feedbackPrompt`

⚠️ Do not change field names or format.
⚠️ Do not include other types like "sentenceCreation", "prompt", or "hint".
⚠️ All keys must match the example exactly.
⚠️ Do not repeat or reuse any example sentences from previous exercises or memory.
⚠️ **NEVER repeat any of these questions the user has seen recently:**\n{recent_questions}\n
⚠️ Always generate new, unique sentences that were not seen in earlier exercises.

Here is an example structure for reference (do not reuse content!):
{json.dumps(example_exercise_block, indent=2)}

Here is the learner’s vocabulary list (prioritize vocab with next_repeat due soon, include one or two per sentence, try to teach the learner new words based):
{json.dumps(vocabular, indent=2)}

Here is the topic memory (form the exercises to train the weaknesses seen in the entries:):
{json.dumps(filtered_topic_memory, indent=2)}
Create new sentences with new words and topics.
Create a new exercise block using the **same structure** and **same field names**, but adapt the **content** to the learner’s weaknesses and level.
""",
    }


def feedback_generation_prompt(
    correct: int,
    total: int,
    mistakes_text: str,
    repeated_text: str,
    examples_text: str,
) -> dict:
    """Return the user prompt for short feedback generation."""
    return {
        "role": "user",
        "content": (
            "You are a helpful German teacher writing a very short feedback message "
            "based on this student's test result.\n\n"
            f"Correct: {correct} out of {total}\n\n"
            f"Mistakes:\n{mistakes_text or 'None'}\n\n"
            f"Repeated grammar issues: {repeated_text or 'None'}\n\n"
            f"Vocabulary used: {examples_text or 'None'}\n\n"
        ),
    }


def detect_topics_prompt(text: str) -> dict:
    """Return prompt for detecting grammar topics."""
    return {
        "role": "user",
        "content": f"""
You are a helpful German teacher. Identify grammar topics used in the following sentence:

"{text}"

Return only a JSON list of strings such as:
["modal verb", "pronoun", "subordinating conjunction"]
""",
    }


def analyze_word_prompt(word: str) -> dict:
    """Return prompt for analyzing a vocabulary word."""
    return {
        "role": "user",
        "content": (
            "Respond ONLY with a valid JSON object containing the following keys for the German word '" + word + "': "
            "base_form (string), type (string like 'noun', 'verb', etc.), article (string or null), "
            "translation (English translation string), info (short description string). Do not include any other text."
        ),
    }


def translate_sentence_prompt(english_sentence: str) -> dict:
    """Return prompt for translating an English sentence to German."""
    return {
        "role": "user",
        "content": f"Translate this sentence to German:\n{english_sentence}",
    }


def evaluate_translation_prompt(english: str, student: str) -> dict:
    """Return prompt for simple translation evaluation."""
    return {
        "role": "user",
        "content": f"""
You are a helpful German teacher verifying a student's translation.

English sentence: \"{english}\"
Student translation: \"{student}\"

Ignore a missing or extra period (.) or question mark (?) at the end of the student's answer when evaluating correctness.
If the german translation has an 'Umlaut' (ä, ö, ü) and the student types instead of ä ae, ö oe, ü ue, then the student is correct.

Answer in JSON with keys `correct` (true/false) and `reason` in one short English sentence.
""",
    }


def quality_evaluation_prompt(
    english: str,
    reference: str,
    student: str,
    topics: list[str],
) -> dict:
    """Return prompt for detailed topic quality evaluation."""
    topics_str = ", ".join(topics)
    return {
        "role": "user",
        "content": (
            "You are a helpful German teacher grading a student's translation.\n\n"
            f"English sentence: '{english}'\n"
            f"Reference translation: '{reference}'\n"
            f"Student translation: '{student}'\n\n"
            "Return a JSON object where each grammar topic is a key (all lowercase, spaces only), "
            "and its value is an integer from 0 to 5 representing the quality of usage.\n\n"
            "For example:\n"
            "{\n"
            "  \"adjective\": 5,\n"
            "  \"nominative case\": 4,\n"
            "  \"modal verb\": 3\n"
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


def weakness_lesson_prompt(grammar: str, skill: str) -> dict:
    """Return prompt for a short weakness lesson."""
    return {
        "role": "user",
        "content": (
            "Create a short HTML lesson in English for a German learner. "
            f"Explain the topic '{grammar}' ({skill})"
            "Return only valid HTML."
        ),
    }


def translate_word_prompt(word: str) -> dict:
    """Return prompt for translating a single German word to English."""
    return {
        "role": "user",
        "content": f"Translate the German word '{word}' to English. Respond ONLY with the translation string.",
    }
