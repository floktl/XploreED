"""Lesson and reading exercise routes."""

import datetime
from flask import jsonify, Response, current_app  # type: ignore
from . import ai_bp
from .helpers.helpers import fetch_topic_memory, store_user_ai_data
from database import select_one
from utils.html.html_utils import clean_html
from utils.ai.prompts import weakness_lesson_prompt
from utils.helpers.helper import require_user
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
