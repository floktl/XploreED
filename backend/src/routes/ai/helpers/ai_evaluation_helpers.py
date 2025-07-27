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
    # logger.info(f"Starting AI evaluation with mode={mode}, exercises_count={len(exercises)}, answers_count={len(answers)}")

    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]
    # logger.info(f"Formatted {len(formatted)} exercises for evaluation")

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

    # logger.info(f"Generated evaluation instructions for mode={mode}")
    user_prompt = answers_evaluation_prompt(instructions, formatted)

    try:
        # logger.info(f"Sending evaluation request to Mistral API")
        # print(f"\033[92m[MISTRAL CALL] evaluate_answers_with_ai\033[0m", flush=True)
        resp = send_prompt(
            "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            # logger.info(f"Mistral evaluation response successful")
            content = resp.json()["choices"][0]["message"]["content"]
            # logger.info(f"Raw evaluation response length: {len(content)} characters")

            parsed = extract_json(content)
            if parsed:
                # logger.info(f"Successfully parsed evaluation JSON")
                return parsed
            else:
                logger.error(f"Failed to parse evaluation JSON from response")
        else:
            logger.error(f"Mistral evaluation request failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")
        current_app.logger.error("AI evaluation failed: %s", e)

    # logger.error(f"AI evaluation failed - returning None")
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
        # print(f"\033[92m[MISTRAL CALL] generate_alternative_answers\033[0m", flush=True)
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            import json as _json
            content = resp.json()["choices"][0]["message"]["content"]
            # print("[generate_alternative_answers] Raw AI response:", content, flush=True)
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
    """Use the AI to generate a short grammar/vocab explanation for the correct answer only."""
    prompt = {
        "role": "user",
        "content": (
            "Given the following exercise and correct answer, give a very short grammar or vocabulary explanation (1-2 sentences) for a German learner. "
            "Do NOT mention the user's answer, do NOT restate the correct answer, and do NOT say if it is correct or incorrect. "
            "Only explain the grammar or vocabulary used in the correct answer, as briefly as possible.\n"
            f"Exercise: {question}\nCorrect answer: {correct_answer}\nReply in English."
        ),
    }
    try:
        # print(f"\033[92m[MISTRAL CALL] generate_explanation\033[0m", flush=True)
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


def _normalize_umlauts(s):
    # Accept ae == ä, oe == ö, ue == ü (and vice versa)
    s = s.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    s = s.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    return s


def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    print("\033[95m🧠 [TOPIC MEMORY FLOW] 🧠 Starting process_ai_answers for user: {} block: {}\033[0m".format(username, block_id), flush=True)
    print("\033[94m📊 [TOPIC MEMORY FLOW] Processing {} answers\033[0m".format(len(answers)), flush=True)

    # logger.info(f"Processing AI answers for user {username}, block {block_id}, answers_count={len(answers)})")

    if not exercise_block:
        print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Missing exercise block for processing user {}\033[0m".format(username), flush=True)
        logger.error(f"Missing exercise block for processing user {username}")
        return []

    all_exercises = exercise_block.get("exercises", [])
    exercise_map = {str(e.get("id")): e for e in all_exercises}
    print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Created exercise map with {} exercises\033[0m".format(len(all_exercises)), flush=True)
    # logger.info(f"Processing {len(all_exercises)} exercises for user {username}")

    results = []
    reviewed = set()

    for ex_id, user_answer in answers.items():
        print("\033[96m🎯 [TOPIC MEMORY FLOW] 🎯 Processing exercise ID: {} with answer: '{}'\033[0m".format(ex_id, user_answer), flush=True)

        ex = exercise_map.get(str(ex_id))
        if not ex:
            print("\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ Exercise {} not found in exercise map for user {}\033[0m".format(ex_id, username), flush=True)
            # logger.warning(f"Exercise {ex_id} not found in exercise map for user {username}")
            continue

        correct_ans = ex.get("correctAnswer", "")
        is_correct = user_answer.strip().lower() == correct_ans.strip().lower()
        quality = 5 if is_correct else 2

        print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Exercise {} - Correct: {} (Quality: {})\033[0m".format(ex_id, is_correct, quality), flush=True)

        # logger.info(f"Exercise {ex_id} for user {username}: correct={is_correct}, quality={quality}")

        print("\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Detecting language topics for exercise: {}\033[0m".format(ex_id), flush=True)
        features = detect_language_topics(
            f"{ex.get('question', '')} {correct_ans}"
        ) or ["unknown"]
        skill = ex.get("type", "")
        print("\033[93m📚 [TOPIC MEMORY FLOW] 📚 Detected features: {} for skill: {}\033[0m".format(features, skill), flush=True)
        # logger.info(f"Detected features for exercise {ex_id}: {features}")

        for feature in features:
            print("\033[95m💾 [TOPIC MEMORY FLOW] 💾 Updating topic memory for user: {}, feature: {}, skill: {}\033[0m".format(username, feature, skill), flush=True)
            # logger.info(f"Updating topic memory for user {username}, feature={feature}, skill={skill}")
            _update_single_topic(
                username,
                feature,
                skill,
                ex.get("question", ""),
                quality,
            )
            print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Topic memory updated for feature: {}\033[0m".format(feature), flush=True)

        # Extract and review vocabulary
        print("\033[96m📖 [TOPIC MEMORY FLOW] 📖 Extracting vocabulary from exercise: {}\033[0m".format(ex_id), flush=True)
        words = (
            [w for w, _ in extract_words(ex.get("question", ""))]
            + [w for w, _ in extract_words(correct_ans)]
        )
        print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Extracted {} words from exercise {}\033[0m".format(len(words), ex_id), flush=True)
        # logger.info(f"Extracted {len(words)} words from exercise {ex_id} for user {username}")

        for vocab in words:
            print("\033[96m🔤 [TOPIC MEMORY FLOW] 🔤 Reviewing vocabulary word: '{}'\033[0m".format(vocab), flush=True)
            review_vocab_word(username, vocab, quality, seen=reviewed)
            print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Vocabulary word '{}' reviewed\033[0m".format(vocab), flush=True)

    print("\033[95m🎉 [TOPIC MEMORY FLOW] 🎉 Completed processing AI answers for user {}: {} results\033[0m".format(username, len(results)), flush=True)
    # logger.info(f"Completed processing AI answers for user {username}: {len(results)} results")
    return results
