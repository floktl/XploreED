"""Helper functions for exercise routes."""

import json
from threading import Thread
from flask import current_app
from database import insert_row
from utils.spaced_repetition.level_utils import check_auto_level_up
from .helpers import process_ai_answers, fetch_topic_memory
from database import select_rows


def fetch_vocab_and_topic_data(username: str) -> tuple[list, list]:
    """Return vocab and topic memory data for the given user."""
    vocab_rows = select_rows(
        "vocab_log",
        columns=["vocab", "translation"],
        where="username = ?",
        params=(username,),
    )
    vocab_data = [
        {"word": row["vocab"], "translation": row.get("translation")}
        for row in vocab_rows
    ] if vocab_rows else []

    topic_rows = fetch_topic_memory(username)
    topic_data = [dict(row) for row in topic_rows] if topic_rows else []
    return vocab_data, topic_data


def compile_score_summary(exercises: list, answers: dict, id_map: dict) -> dict:
    """Return score summary for the evaluated answers."""
    mistakes = []
    correct = 0
    for ex in exercises:
        cid = str(ex.get("id"))
        user_ans = answers.get(cid, "")
        correct_ans = id_map.get(cid, "")
        if str(user_ans).strip().lower() == str(correct_ans).strip().lower():
            correct += 1
        else:
            mistakes.append({
                "question": ex.get("question"),
                "your_answer": user_ans,
                "correct_answer": correct_ans,
            })
    return {"correct": correct, "total": len(exercises), "mistakes": mistakes}


def save_exercise_submission_async(
    username: str,
    block_id: str,
    answers: dict,
    exercises: list,
) -> None:
    """Save exercise submission and update spaced repetition in a thread."""
    app = current_app._get_current_object()

    def run():
        with app.app_context():
            try:
                process_ai_answers(
                    username,
                    str(block_id),
                    answers,
                    {"exercises": exercises},
                )
                check_auto_level_up(username)
                insert_row(
                    "exercise_submissions",
                    {
                        "username": username,
                        "block_id": str(block_id),
                        "answers": json.dumps(answers),
                    },
                )
            except Exception as e:
                current_app.logger.error("Failed to save exercise submission: %s", e)

    Thread(target=run).start()


from .helpers import evaluate_answers_with_ai, _adjust_gapfill_results


def evaluate_exercises(exercises: list, answers: dict) -> tuple[dict | None, dict]:
    """Return evaluation result and id map after updating exercises."""
    evaluation = evaluate_answers_with_ai(exercises, answers)
    evaluation = _adjust_gapfill_results(exercises, answers, evaluation)
    if not evaluation:
        return None, {}

    id_map = {str(r.get("id")): r.get("correct_answer") for r in evaluation.get("results", [])}
    for ex in exercises:
        cid = str(ex.get("id"))
        if cid in id_map:
            ex["correctAnswer"] = id_map[cid]
    return evaluation, id_map


def parse_submission_data(data: dict) -> tuple[list, dict, str | None]:
    """Validate and extract exercises and answers from submission."""
    answers = data.get("answers", {})
    block = data.get("exercise_block")
    if not isinstance(block, dict):
        return [], {}, "Invalid or missing exercise block."
    exercises = block.get("exercises")
    if not isinstance(exercises, list) or not exercises:
        return [], {}, "No exercises found to evaluate."
    return exercises, answers, None

