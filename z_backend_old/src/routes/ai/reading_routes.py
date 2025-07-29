from app.imports.imports import ai_bp
from flask import request, jsonify, current_app  # type: ignore
from utils.spaced_repetition.vocab_utils import extract_words, save_vocab
from utils.helpers.helper import require_user
from routes.ai.helpers.lesson_helpers import update_reading_memory_async
from utils.spaced_repetition.vocab_utils import save_vocab, extract_words
from utils.ai.prompts import (
    feedback_generation_prompt,
)
from utils.ai.translation_utils import _normalize_umlauts, _strip_final_punct
from routes.ai.helpers.helpers import format_feedback_block

@ai_bp.route("/reading-exercise", methods=["POST"])
def reading_exercise():
    """Proxy to the lesson reading exercise generator."""
    from .helpers.reading_helpers import ai_reading_exercise

    return ai_reading_exercise()


@ai_bp.route("/reading-exercise/submit", methods=["POST"])
def submit_reading_exercise():
    """Evaluate reading answers and update memory."""
    username = require_user()

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise_id = data.get("exercise_id")
    cache = current_app.config.get("READING_EXERCISE_CACHE", {})
    exercise = cache.get(exercise_id)
    if not exercise:
        return jsonify({"error": "Exercise not found or expired"}), 400
    text = exercise.get("text", "")
    questions = exercise.get("questions", [])

    # Debug: log questions and their fields
    import logging
    logger = logging.getLogger("reading_debug")
    # for q in questions:
    #     logger.info(f"Q: {q}")
    #     logger.info(f"id: {q.get('id')}, question: {q.get('question')}, correctAnswer: {q.get('correctAnswer')}")

    correct = 0
    results = []
    feedback_blocks = []
    mistakes = []
    from utils.ai.ai_api import send_prompt

    for q in questions:
        qid = str(q.get("id"))
        sol = str(q.get("correctAnswer", "")).strip().lower()
        ans = str(answers.get(qid, "")).strip().lower()
        # Ignore final . or ? for all exercise types
        sol = _strip_final_punct(sol)
        ans = _strip_final_punct(ans)
        # Normalize umlauts for both answers
        sol = _normalize_umlauts(sol)
        ans = _normalize_umlauts(ans)
        status = "correct" if ans == sol else "incorrect"
        explanation = ""
        if status == "incorrect":
            # Generate a very short explanation using AI
            prompt = f"Explain in one short sentence (no more than 12 words) why the answer '{answers.get(qid, '')}' is incorrect for the question: {q.get('question')} (correct answer: {q.get('correctAnswer')})"
            try:
                resp = send_prompt(
                    "You are a helpful German teacher.",
                    {"role": "user", "content": prompt},
                    temperature=0.3
                )
                # current_app.logger.info(f"AI explanation response: {resp.status_code} {resp.text}")
                if resp.status_code == 200:
                    explanation = resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                current_app.logger.error(f"Failed to generate per-question explanation: {e}")
                explanation = ""
        block = format_feedback_block(
            user_answer=answers.get(qid, ""),
            correct_answer=q.get("correctAnswer"),
            alternatives=[],
            explanation=explanation,
            diff=None,
            status=status
        )
        feedback_blocks.append(block)
        if ans == sol:
            correct += 1
        else:
            mistakes.append({
                "question": q.get("question"),
                "your_answer": answers.get(qid, ""),
                "correct_answer": q.get("correctAnswer"),
            })
        results.append({"id": qid, "correct_answer": q.get("correctAnswer")})

    summary = {"correct": correct, "total": len(questions), "mistakes": mistakes}

    # Generate feedbackPrompt using Mistral
    feedbackPrompt = None
    try:
        from utils.ai.ai_api import send_prompt
        mistakes_text = "\n".join([
            f"Q: {m['question']}\nYour answer: {m['your_answer']}\nCorrect: {m['correct_answer']}" for m in mistakes
        ])
        prompt = feedback_generation_prompt(correct, len(questions), mistakes_text, "", "")
        resp = send_prompt(
            "You are a helpful German teacher.",
            prompt,
            temperature=0.5,
        )
        if resp.status_code == 200:
            feedbackPrompt = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        current_app.logger.error("Failed to generate feedbackPrompt: %s", e)
        feedbackPrompt = None

    # Save vocab and update topic memory in background threads
    import threading
    def save_vocab_bg():
        for word, art in extract_words(text):
            save_vocab(username, word, context=text, exercise="reading", article=art)
    threading.Thread(target=save_vocab_bg, daemon=True).start()
    threading.Thread(target=update_reading_memory_async, args=(username, text), daemon=True).start()

    return jsonify({"summary": summary, "results": results, "feedbackPrompt": feedbackPrompt, "feedbackBlocks": feedback_blocks})
