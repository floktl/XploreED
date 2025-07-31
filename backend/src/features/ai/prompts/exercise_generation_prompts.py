"""
XplorED - Exercise Generation Prompts Module

This module provides prompt templates for exercise generation and feedback,
following clean architecture principles as outlined in the documentation.

Generation Components:
- Exercise Generation: AI-powered creation of grammar and translation exercises
- Feedback Generation: Comprehensive feedback for exercise results
- Weakness Lessons: Personalized lessons targeting user weaknesses

For detailed architecture information, see: docs/backend_structure.md
"""

from __future__ import annotations
import json


def exercise_generation_prompt(
    level_val: int,
    cefr_level: str,
    example_exercise_block: dict,
    vocabular: list,
    filtered_topic_memory: list,
    recent_questions: str = "",
    recent_topics: list | None = None,
) -> dict:
    """Return the user prompt for generating a new exercise block, including recent questions to avoid repeats."""

    # Create a unique title based on weaknesses/topics
    weakness_topics = []
    if filtered_topic_memory:
        topics = set()
        for entry in filtered_topic_memory:
            if entry.get("grammar"):
                topics.add(entry["grammar"])
            if entry.get("topic"):
                topics.add(entry["topic"])
        weakness_topics = list(topics)[:3]  # Take up to 3 topics

    # Get recently used topics to avoid repetition
    recent_topics_str = ""
    if recent_topics:
        recent_topics_str = f"\n⚠️ **AVOID these recently used content topics:** {', '.join(recent_topics)}"

    available_topics = ["weather", "dogs", "family", "shopping", "travel", "food", "hobbies", "work", "sports", "living"]

    title_suggestion = ""
    if weakness_topics:
        topics_str = ", ".join(weakness_topics)
        title_suggestion = f"Create a unique, engaging title that combines grammar practice with content context. Format: 'Building confidence in [grammar topics] in the context of [content topic]'. For example: 'Building confidence in present tense and accusative case in the context of Work'. Use the specific weaknesses: {topics_str} and choose an appropriate content topic from: {', '.join(available_topics)}. Make the exercises focus on the grammar concepts mentioned in the title.{recent_topics_str}"
    else:
        title_suggestion = f"Create a unique, engaging title that combines grammar practice with content context. Format: 'Building confidence in [grammar topics] in the context of [content topic]'. For example: 'Building confidence in present tense and accusative case in the context of Work'. Choose appropriate grammar topics for the user's level and an appropriate content topic from: {', '.join(available_topics)}.{recent_topics_str}"

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
   - `question`: a string (either a full sentence with a blank depending on the students level, or a translation task with the same conditions, remember to always put a full sentence, be sure that this sentence is grammarly correct and make sense)
   - For "gap-fill":
     - `options`: list of 4 strings, one of them has to be the correct answer, be sure to include the right answer.
     - `correctAnswer`: the correct string
   - For "translation":
     - `correctAnswer`: the correct German translation

 2. The overall JSON must contain:
   - `lessonId`, `title`, `level`
   - `topic`: a string describing the main content topic for the entire exercise block (e.g., "weather", "dogs", "family", "shopping", "travel", "food", "hobbies", "work", "sports", "living")
   - `exercises`: list of 3 total exercises (mix of both types)
   - `feedbackPrompt`

⚠️ Do not change field names or format.
⚠️ Do not include other types like "sentenceCreation", "prompt", or "hint".
⚠️ All keys must match the example exactly.
⚠️ Do not repeat or reuse any example sentences from previous exercises or memory.
⚠️ **NEVER repeat any of these questions the user has seen recently:**\n{recent_questions}\n
⚠️ Always generate new, unique sentences that were not seen in earlier exercises.
⚠️ **IMPORTANT**: For gap-fill exercises, use ONLY the exact sentence with ____ for gaps. Do NOT add any hints, parentheses, or additional guidance text like "(D...)" or "(to...)". Keep questions clean and simple.

{title_suggestion}

Here is an example structure for reference (do not reuse content!):
{json.dumps(example_exercise_block, indent=2)}

Here is the learner's vocabulary list (prioritize vocab with next_repeat due soon, include one or two per sentence, try to teach the learner new words based):
{json.dumps(vocabular, indent=2)}

Here is the topic memory (form the exercises to train the weaknesses seen in the entries:):
{json.dumps(filtered_topic_memory, indent=2)}

**IMPORTANT**: Create exercises that directly target the specific weaknesses and topics mentioned in the title. Each exercise should focus on the grammar concepts or vocabulary areas that the user needs to practice. Make sure the exercise content aligns with the educational focus indicated by the title.

Create a new exercise block using the **same structure** and **same field names**, but adapt the **content** to the learner's weaknesses and level.
""",
    }


def feedback_generation_prompt(
    correct: int,
    total: int,
    mistakes_text: str,
    repeated_text: str,
    examples_text: str,
) -> dict:
    """Return prompt for generating comprehensive feedback."""
    return {
        "role": "user",
        "content": f"""
You are a helpful German teacher providing feedback on an exercise.

Results: {correct}/{total} correct.

Mistakes made:
{mistakes_text}

Repeated mistakes:
{repeated_text}

Examples and explanations:
{examples_text}

Provide encouraging, constructive feedback in 2-3 sentences. Focus on:
1. What they did well
2. Areas for improvement
3. Encouragement to continue learning

Keep it positive and motivating.
""",
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
