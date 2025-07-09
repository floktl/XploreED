"""Lesson and reading exercise routes."""

import json
import os
import re
import datetime
from flask import request, jsonify, Response, current_app
from . import ai_bp
from .helpers import fetch_topic_memory, generate_reading_exercise, store_user_ai_data
from database import fetch_one, select_one, select_rows
from utils.html.html_utils import clean_html
from utils.spaced_repetition.level_utils import check_auto_level_up
from utils.spaced_repetition.vocab_utils import extract_words, save_vocab
from utils.ai.prompts import weakness_lesson_prompt
from utils.grammar.grammar_utils import detect_language_topics
from utils.ai.translation_utils import _update_single_topic, update_topic_memory_reading
from utils.helpers.helper import run_in_background, session_manager
from utils.ai.ai_api import send_prompt


def create_ai_lesson():
    """Return a mock HTML lesson based on the user's topic memory."""
    username = require_user()

    topic_rows = fetch_topic_memory(username)
    topics = [row.get("grammar") for row in topic_rows if row.get("grammar")] if topic_rows else []

    if topics:
        items = "".join(f"<li>{t}</li>" for t in topics[:5])
        html = (
            "<h2>AI Review Lesson</h2>"
            "<p>Let's review these topics:</p>"
            f"<ul>{items}</ul>"
        )
    else:
        html = """
    <h2>AI Review Lesson: Modalverben (Modal Verbs)</h2>
    <p>Modalverben sind Hilfsverben, die ein anderes Verb im Infinitiv begleiten. Sie drücken Notwendigkeit, Möglichkeit, Erlaubnis oder Wunsch aus.</p>

    <h3>🧠 Die wichtigsten Modalverben:</h3>
    <ul>
    <li><strong>müssen</strong> – to have to, must</li>
    <li><strong>können</strong> – to be able to, can</li>
    <li><strong>wollen</strong> – to want</li>
    <li><strong>sollen</strong> – should, ought to</li>
    <li><strong>dürfen</strong> – may, to be allowed to</li>
    <li><strong>mögen</strong> – to like</li>
    </ul>

    <h3>🔧 Satzbau (Word Order):</h3>
    <p>Im Präsens steht das Modalverb an zweiter Stelle, das Hauptverb am Ende des Satzes im Infinitiv:</p>
    <ul>
    <li>Ich <strong>muss</strong> heute <strong>lernen</strong>.</li>
    <li>Wir <strong>dürfen</strong> hier nicht <strong>parken</strong>.</li>
    </ul>

    <h3>🗣 Konjugation von <code>müssen</code> im Präsens:</h3>
    <table border="1" cellpadding="5">
    <tr><th>Person</th><th>Form</th></tr>
    <tr><td>ich</td><td>muss</td></tr>
    <tr><td>du</td><td>musst</td></tr>
    <tr><td>er/sie/es</td><td>muss</td></tr>
    <tr><td>wir</td><td>müssen</td></tr>
    <tr><td>ihr</td><td>müsst</td></tr>
    <tr><td>sie/Sie</td><td>müssen</td></tr>
    </table>

    <h3>🎯 Beispiele mit verschiedenen Modalverben:</h3>
    <ul>
    <li>Ich <strong>kann</strong> gut schwimmen. (I can swim well.)</li>
    <li>Du <strong>musst</strong> deine Hausaufgaben machen. (You must do your homework.)</li>
    <li>Er <strong>will</strong> Arzt werden. (He wants to become a doctor.)</li>
    <li>Wir <strong>sollen</strong> pünktlich sein. (We should be on time.)</li>
    <li>Ihr <strong>dürft</strong> nicht laut sprechen. (You are not allowed to speak loudly.)</li>
    </ul>

    <h3>📝 Übung:</h3>
    <p>Setze das passende Modalverb ein:</p>
    <ol>
    <li>Ich _______ ins Kino gehen. (Permission)</li>
    <li>Wir _______ jeden Tag Deutsch lernen. (Obligation)</li>
    <li>Du _______ deine Eltern anrufen. (Advice)</li>
    </ol>

    <h3>📌 Merke:</h3>
    <p>Modalverben helfen dir, deine Meinung, Absichten oder Pflichten auszudrücken. Übe sie regelmäßig in verschiedenen Kontexten!</p>
    """


    return Response(html, mimetype="text/html")

@ai_bp.route("/weakness-lesson", methods=["GET"])
def ai_weakness_lesson():
    """Return a short HTML lesson focused on the user's weakest topic."""
    username = require_user()

    row = select_one(
        "topic_memory",
        columns=["grammar", "skill_type"],
        where="username = ?",
        params=(username,),
        order_by="ease_factor ASC, repetitions DESC",
    )

    grammar = row.get("grammar") if row else "Modalverben"
    skill = row.get("skill_type") if row else "grammar"

    user_prompt = weakness_lesson_prompt(grammar, skill)

    cached = select_one(
        "ai_user_data",
        columns=["weakness_lesson", "weakness_topic"],
        where="username = ?",
        params=(username,),
    )
    if cached and cached.get("weakness_lesson") and cached.get("weakness_topic") == grammar:
        return Response(cached["weakness_lesson"], mimetype="text/html")

    try:
        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.7,
        )
        if resp.status_code == 200:
            raw_html = resp.json()["choices"][0]["message"]["content"].strip()
            cleaned_html = clean_html(raw_html)

            store_user_ai_data(
                username,
                {
                    "weakness_lesson": cleaned_html,
                    "weakness_topic": grammar,
                    "lesson_updated_at": datetime.datetime.now().isoformat(),
                },
            )
            return Response(cleaned_html, mimetype="text/html")
    except Exception as e:
        current_app.logger.error("Failed to generate weakness lesson: %s", e)
    return jsonify({"error": "Mistral API error"}), 500

def ai_reading_exercise():
    """Return a short reading exercise based on the user's level."""
    username = require_user()

    data = request.get_json() or {}
    style = data.get("style", "story")

    row = fetch_one("users", "WHERE username = ?", (username,))
    level = row.get("skill_level", 0) if row else 0

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
    topic_memory = [dict(row) for row in topic_rows] if topic_rows else []

    block = generate_reading_exercise(style, level, vocab_data, topic_memory)
    if not block or not block.get("text") or not block.get("questions"):
        return jsonify({"error": "Mistral error"}), 500
    for q in block.get("questions", []):
        q.pop("correctAnswer", None)
    return jsonify(block)


@ai_bp.route("/reading-exercise/submit", methods=["POST"])
def submit_reading_exercise():
    """Evaluate reading answers and update memory."""
    username = require_user()

    data = request.get_json() or {}
    answers = data.get("answers", {})
    exercise = data.get("exercise") or {}
    text = exercise.get("text", "")
    questions = exercise.get("questions", [])

    correct = 0
    results = []
    for q in questions:
        qid = str(q.get("id"))
        sol = str(q.get("correctAnswer", "")).strip().lower()
        ans = str(answers.get(qid, "")).strip().lower()
        if ans == sol:
            correct += 1
        results.append({"id": qid, "correct_answer": q.get("correctAnswer")})

    summary = {"correct": correct, "total": len(questions), "mistakes": []}
    for q in questions:
        qid = str(q.get("id"))
        if str(answers.get(qid, "")).strip().lower() != str(q.get("correctAnswer", "")).strip().lower():
            summary["mistakes"].append(
                {
                    "question": q.get("question"),
                    "your_answer": answers.get(qid, ""),
                    "correct_answer": q.get("correctAnswer"),
                }
            )

    for word, art in extract_words(text):
        save_vocab(username, word, context=text, exercise="reading", article=art)

    def _background_save():
        features = detect_language_topics(text) or ["unknown"]
        update_topic_memory_reading(username, text)
        check_auto_level_up(username)

    run_in_background(_background_save)

    return jsonify({"summary": summary, "results": results})
