"""Helper functions used by AI routes."""

import logging
import json
from flask import current_app  # type: ignore

from utils.spaced_repetition.vocab_utils import review_vocab_word, extract_words
from database import *
from utils.grammar.grammar_utils import detect_language_topics
from utils.ai.translation_utils import _update_single_topic
from utils.data.json_utils import extract_json
from utils.ai.prompts import answers_evaluation_prompt
from utils.ai.ai_api import send_prompt

logger = logging.getLogger(__name__)


def evaluate_answers_with_ai(
    exercises: list, answers: dict, mode: str = "strict"
) -> dict | None:
    """Ask Mistral to evaluate student answers and return JSON results."""
    logger.info(f"Starting AI evaluation with mode={mode}, exercises_count={len(exercises)}, answers_count={len(answers)}")

    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]
    logger.info(f"Formatted {len(formatted)} exercises for evaluation")

    instructions = (
        "Evaluate these answers for a German exercise. "
        "Return JSON with 'pass' (true/false) and a 'results' list. "
        "Each result must include 'id' and 'correct_answer'. "
        "Mark pass true only if all answers are fully correct."
    )
    if mode == "argue":
        instructions = (
            "Reevaluate the student's answers carefully. "
            "Consider possible alternative correct solutions. "
            + instructions
        )

    logger.info(f"Generated evaluation instructions for mode={mode}")
    user_prompt = answers_evaluation_prompt(instructions, formatted)

    try:
        logger.info(f"Sending evaluation request to Mistral API")
        resp = send_prompt(
            "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            logger.info(f"Mistral evaluation response successful")
            content = resp.json()["choices"][0]["message"]["content"]
            logger.info(f"Raw evaluation response length: {len(content)} characters")

            parsed = extract_json(content)
            if parsed:
                logger.info(f"Successfully parsed evaluation JSON")
                return parsed
            else:
                logger.error(f"Failed to parse evaluation JSON from response")
        else:
            logger.error(f"Mistral evaluation request failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        current_app.logger.error("AI evaluation failed: %s", e)

    logger.error(f"AI evaluation failed - returning None")
    return None


def generate_alternative_answers(correct_sentence: str) -> list:
    """Use the AI to generate 2-3 alternative ways to say the same thing in German."""
    import re
    prompt = {
        "role": "user",
        "content": (
            f"Give up to 3 alternative ways to say the following sentence in German, with the same meaning and register. "
            f"Return only a JSON array of strings, no explanations, no extra text, no markdown, no labels.\nSentence: {correct_sentence}"
        ),
    }
    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            import json as _json
            content = resp.json()["choices"][0]["message"]["content"]
            # Try to extract a JSON array from the response robustly
            try:
                # Find the first [ ... ] block in the response
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    arr_str = match.group(0)
                    alternatives = _json.loads(arr_str)
                    if isinstance(alternatives, list):
                        return alternatives
                # Fallback: try to parse the whole content
                alternatives = _json.loads(content)
                if isinstance(alternatives, list):
                    return alternatives
            except Exception as e:
                pass
    except Exception as e:
        logger.error(f"generate_alternative_answers failed: {e}")
    return []


def generate_explanation(question: str, user_answer: str, correct_answer: str) -> str:
    """Use the AI to generate a short explanation for why the correct answer is correct or why the user's answer is wrong."""
    prompt = {
        "role": "user",
        "content": (
            f"Given the following exercise, user answer, and correct answer, give a short explanation (1-2 sentences) for a German learner. "
            f"If the user's answer is correct, explain why. If it's wrong, explain the mistake.\n"
            f"Exercise: {question}\nUser answer: {user_answer}\nCorrect answer: {correct_answer}\n"
            f"Reply in English."
        ),
    }
    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return content.strip()
    except Exception as e:
        logger.error(f"generate_explanation failed: {e}")
    return ""


def _strip_final_punct(s):
    s = s.strip()
    if s and s[-1] in ".?":
        return s[:-1].strip()
    return s


def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    logger.info(f"Processing AI answers for user {username}, block {block_id}, answers_count={len(answers)})")

    if not exercise_block:
        logger.error(f"Missing exercise block for processing user {username}")
        return

    all_exercises = exercise_block.get("exercises", [])
    exercise_map = {str(e.get("id")): e for e in all_exercises}
    logger.info(f"Processing {len(all_exercises)} exercises for user {username}")

    results = []
    reviewed: set[str] = set()
    for ex_id, user_ans in answers.items():
        ex = exercise_map.get(str(ex_id))
        if not ex:
            logger.warning(f"Exercise {ex_id} not found in exercise map for user {username}")
            continue

        correct_ans = str(ex.get("correctAnswer", "")).strip().lower()
        user_ans = str(user_ans).strip().lower()
        # Ignore final . or ? for all exercise types
        correct_ans = _strip_final_punct(correct_ans)
        user_ans = _strip_final_punct(user_ans)
        is_correct = int(user_ans == correct_ans)
        quality = 5 if is_correct else 2

        logger.info(f"Exercise {ex_id} for user {username}: correct={is_correct}, quality={quality}")

        features = detect_language_topics(
            f"{ex.get('question', '')} {correct_ans}"
        ) or ["unknown"]
        skill = ex.get("type", "")
        logger.info(f"Detected features for exercise {ex_id}: {features}")

        for feature in features:
            logger.info(f"Updating topic memory for user {username}, feature={feature}, skill={skill}")
            _update_single_topic(
                username,
                feature,
                skill,
                ex.get("question", ""),
                quality,
            )

            results.append(
                {
                    "topic_memory": {
                        "grammar": feature,
                        "skill_type": skill,
                        "quality": quality,
                        "correct": is_correct,
                    }
                }
            )

        words = set(
            [w for w, _ in extract_words(ex.get("question", ""))]
            + [w for w, _ in extract_words(correct_ans)]
        )
        logger.info(f"Extracted {len(words)} words from exercise {ex_id} for user {username}")

        for vocab in words:
            review_vocab_word(username, vocab, quality, seen=reviewed)

    logger.info(f"Completed processing AI answers for user {username}: {len(results)} results")
