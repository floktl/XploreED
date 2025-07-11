"""Helper functions used by AI routes."""

from flask import current_app  # type: ignore

from utils.spaced_repetition.vocab_utils import review_vocab_word, extract_words
from database import *
from utils.grammar.grammar_utils import detect_language_topics
from utils.ai.translation_utils import _update_single_topic
from utils.data.json_utils import extract_json
from utils.ai.prompts import answers_evaluation_prompt
from utils.ai.ai_api import send_prompt


def evaluate_answers_with_ai(
    exercises: list, answers: dict, mode: str = "strict"
) -> dict | None:
    """Ask Mistral to evaluate student answers and return JSON results."""
    formatted = [
        {
            "id": ex.get("id"),
            "question": ex.get("question"),
            "type": ex.get("type"),
            "answer": answers.get(str(ex.get("id"))) or "",
        }
        for ex in exercises
    ]

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

    user_prompt = answers_evaluation_prompt(instructions, formatted)

    try:
        resp = send_prompt(
            "You are a strict German teacher." if mode == "strict" else "You are a thoughtful German teacher.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extract_json(content)
            return parsed
    except Exception as e:
        current_app.logger.error("AI evaluation failed: %s", e)

    return None


def process_ai_answers(username: str, block_id: str, answers: dict, exercise_block: dict | None = None) -> list:
    """Evaluate answers and print spaced repetition info using SM2."""
    if not exercise_block:
        print("❌ Missing exercise block for processing", flush=True)
        return

    all_exercises = exercise_block.get("exercises", [])
    exercise_map = {str(e.get("id")): e for e in all_exercises}

    results = []
    reviewed: set[str] = set()
    for ex_id, user_ans in answers.items():
        ex = exercise_map.get(str(ex_id))
        if not ex:
            continue
        correct_ans = str(ex.get("correctAnswer", "")).strip().lower()
        user_ans = str(user_ans).strip().lower()
        is_correct = int(user_ans == correct_ans)
        quality = 5 if is_correct else 2
        features = detect_language_topics(
            f"{ex.get('question', '')} {correct_ans}"
        ) or ["unknown"]
        skill = ex.get("type", "")

        for feature in features:
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
        for vocab in words:
            review_vocab_word(username, vocab, quality, seen=reviewed)

    # print("AI submission results (HJSON):\n", json.dumps(results, indent=2), flush=True)
