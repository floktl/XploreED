# german_sentence_game.py
"""Logic for the sentence ordering game and feedback helpers."""

from database import get_connection, fetch_custom
from utils.ai.prompts import game_sentence_prompt
from utils.ai.ai_api import send_prompt
import random
from colorama import Fore, Style
from datetime import datetime


LEVELS = [
    "Ich bin Anna",
    "Wir wohnen in Berlin",
    "Er trinkt jeden Morgen Kaffee",
    "Morgen fahre ich mit dem Bus zur Schule",
    "Am Wochenende spiele ich gern Fußball",
    "Sie möchte ein neues Auto kaufen",
    "Kannst du mir bitte helfen",
    "Ich habe gestern einen interessanten Film gesehen",
    "Wenn ich Zeit habe, besuche ich meine Großeltern",
    "Obwohl es regnet, gehen wir spazieren",
]


class User:
    def __init__(self, name):
        self.name = name
        self.progress = []  # store (level, correct, answer, timestamp)

    def add_result(self, level, correct, answer, timestamp):
        self.progress.append(
            {
                "level": level,
                "correct": correct,
                "answer": answer,
                "timestamp": timestamp,
            }
        )


def init_db():
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            level INTEGER,
            correct INTEGER,
            answer TEXT,
            timestamp TEXT
        );"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS vocab_log (
            username TEXT,
            vocab TEXT,
            translation TEXT,
            repetitions INTEGER DEFAULT 0,
            interval_days INTEGER DEFAULT 1,
            ef REAL DEFAULT 2.5,
            next_review DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            context TEXT,
            exercise TEXT
        );"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS lesson_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            published INTEGER DEFAULT 0
        );"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS lesson_blocks (
            lesson_id INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            PRIMARY KEY (lesson_id, block_id)
        );"""
        )


init_db()


def generate_ai_sentence(username=None):
    """Return a short German sentence created by Mistral."""
    try:
        vocab_rows = (
            fetch_custom(
                "SELECT vocab FROM vocab_log WHERE username = ? ORDER BY RANDOM() LIMIT 5",
                (username,),
            )
            if username
            else []
        )
        vocab_list = [row["vocab"] for row in vocab_rows] if vocab_rows else []

        topic_rows = (
            fetch_custom(
                "SELECT topic FROM topic_memory WHERE username = ? AND topic IS NOT NULL ORDER BY RANDOM() LIMIT 3",
                (username,),
            )
            if username
            else []
        )
        topics = [row["topic"] for row in topic_rows] if topic_rows else []

        user_prompt = game_sentence_prompt(vocab_list, topics)

        resp = send_prompt(
            "You are a helpful German teacher.",
            user_prompt,
            temperature=0.7,
        )
        if resp.status_code == 200:
            sentence = resp.json()["choices"][0]["message"]["content"].strip()
            return sentence.strip('"')
    except Exception as e:
        print("AI sentence generation failed:", e)
    return None




def get_scrambled_sentence(sentence):
    words = sentence.split()
    random.shuffle(words)
    return words

from colorama import Fore, Style

def evaluate_order(user_answer, correct_sentence, vocab=None, topic_memory=None):
    user_words = user_answer.strip().split()
    correct_words = correct_sentence.strip().split()

    if user_words == correct_words:
        return True, "✅ Deine Reihenfolge ist korrekt!"

    # Prepare mistakes data
    mistakes = []
    for i, word in enumerate(user_words):
        correct_word = correct_words[i] if i < len(correct_words) else None
        if word != correct_word:
            mistakes.append({
                "question": f"Wort {i+1}: {correct_word}",
                "your_answer": word,
                "correct_answer": correct_word
            })

    summary = {
        "correct": sum(1 for i, word in enumerate(user_words) if i < len(correct_words) and word == correct_words[i]),
        "total": len(correct_words),
        "mistakes": mistakes
    }

    ai_feedback = generate_feedback_prompt(summary, vocab=vocab, topic_memory=topic_memory)

    # Optional visual feedback
    visual = []
    for i, word in enumerate(user_words):
        if i < len(correct_words) and word == correct_words[i]:
            visual.append(Fore.GREEN + word + Style.RESET_ALL)
        else:
            visual.append(Fore.RED + word + Style.RESET_ALL)

    return False, f"📝 Feedback:\n{ai_feedback}\n\n🔍 Visual: {' '.join(visual)}"



def get_feedback(student_version, correct_version, vocab=None, topic_memory=None):
    """Return visual diff plus short AI comment."""
    student_words = student_version.strip().split()
    correct_words = correct_version.strip().split()

    output = []
    explanation = []

    w_question_words = [
        "wie",
        "was",
        "wann",
        "wo",
        "warum",
        "wer",
        "wieso",
        "woher",
        "wohin",
        "welche",
        "welcher",
        "welches",
    ]
    first_word = correct_words[0].lower() if correct_words else ""
    is_question = correct_version.strip().endswith("?")
    is_w_question = is_question and first_word in w_question_words
    is_yesno_question = is_question and not is_w_question and first_word.isalpha()

    mistakes = []

    if sorted([w.lower() for w in student_words]) == sorted(
        [w.lower() for w in correct_words]
    ) and [w.lower() for w in student_words] != [w.lower() for w in correct_words]:

        for idx, word in enumerate(student_words):
            correct_word = correct_words[idx] if idx < len(correct_words) else ""
            if word.lower() == correct_word.lower():
                output.append(Fore.GREEN + word + Style.RESET_ALL)
            elif word.lower() in [w.lower() for w in correct_words]:
                output.append(Fore.RED + word + Style.RESET_ALL)
                mistakes.append({
                    "question": f"Wort {idx+1}: {correct_word}",
                    "your_answer": word,
                    "correct_answer": correct_word,
                })
            else:
                output.append(Fore.YELLOW + word + Style.RESET_ALL)
                mistakes.append({
                    "question": f"Wort {idx+1}: {correct_word}",
                    "your_answer": word,
                    "correct_answer": correct_word,
                })

        user_version_html = (
            "<p><strong>🧩 Deine Version:</strong><br><span style='font-family: monospace;'>"
            + " ".join(output)
            + "</span></p>"
        )

        if is_w_question:
            return False, (
                "⚠️ Deine Wörter sind korrekt, aber die Wortstellung ist falsch für eine W-Frage.<br>"
                "📘 Regel: W-Wort – Verb – Subjekt – ...<br>" + user_version_html
            )
        elif is_yesno_question:
            return False, (
                "⚠️ Deine Wörter sind korrekt, aber die Wortstellung ist falsch für eine Ja/Nein-Frage.<br>"
                "📘 Regel: Verb – Subjekt – Objekt – ...<br>" + user_version_html
            )
        else:
            return False, (
                "⚠️ Deine Wörter sind korrekt, aber die Wortstellung ist nicht ideal.<br>"
                "📘 Regel: Subjekt – Verb – Zeit – Art – Ort – Objekt – Infinitiv<br>"
                + user_version_html
            )

    from difflib import SequenceMatcher

    sm = SequenceMatcher(None, correct_words, student_words)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for w in correct_words[i1:i2]:
                output.append(Fore.GREEN + w + Style.RESET_ALL)
        elif tag == "replace":
            for w1, w2 in zip(correct_words[i1:i2], student_words[j1:j2]):
                output.append(Fore.RED + w2 + Style.RESET_ALL)
                explanation.append(f"❌ '{w2}' sollte '{w1}' sein.")
                mistakes.append({
                    "question": w1,
                    "your_answer": w2,
                    "correct_answer": w1,
                })
        elif tag == "delete":
            for w in correct_words[i1:i2]:
                output.append(Fore.RED + "___" + Style.RESET_ALL)
                explanation.append(f"❌ Es fehlt das Wort '{w}'.")
                mistakes.append({
                    "question": w,
                    "your_answer": "",
                    "correct_answer": w,
                })
        elif tag == "insert":
            for w in student_words[j1:j2]:
                output.append(Fore.YELLOW + w + Style.RESET_ALL)
                explanation.append(f"🟡 Zusätzliches Wort: '{w}'")
                mistakes.append({
                    "question": "Zusätzliches Wort",
                    "your_answer": w,
                    "correct_answer": "",
                })

    summary = {
        "correct": sum(
            1
            for i, w in enumerate(student_words)
            if i < len(correct_words) and w == correct_words[i]
        ),
        "total": len(correct_words),
        "mistakes": mistakes,
    }

    ai_comment = generate_feedback_prompt(summary, vocab=vocab, topic_memory=topic_memory)

    if not explanation:
        return True, f"✅ Deine Übersetzung ist korrekt!<br>{ai_comment}"

    feedback_text = (
        "<p><strong>🧩 Deine Version:</strong><br><span style='font-family: monospace;'>"
        + " ".join(output)
        + "</span></p>"
    )
    feedback_text += "<p>📘 Erklärungen:<br>" + "<br>".join(explanation) + "</p>"
    feedback_text += f"<p>{ai_comment}</p>"
    return False, feedback_text


def save_result(username, level, correct, answer):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO results (username, level, correct, answer, timestamp) VALUES (?, ?, ?, ?, ?)",
            (username, level, int(correct), answer, datetime.now().isoformat()),
        )


def get_all_results():
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT u.username, r.level, r.correct, r.answer, r.timestamp
            FROM users u
            LEFT JOIN results r ON u.username = r.username
            ORDER BY r.timestamp DESC
        """
        )
        rows = cursor.fetchall()

        return [
            {"username": u, "level": l, "correct": c, "answer": a, "timestamp": t}
            for u, l, c, a, t in rows
        ]
