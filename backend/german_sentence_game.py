# german_sentence_game.py
import random
import requests
from colorama import Fore, Style
import sqlite3
from datetime import datetime
import os
import re

DB_FILE = "game_results.db"

try:
    with open("DEEPL_API_KEY") as f:
        API_KEY = f.read().strip()
except Exception:
    API_KEY = None

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
    "Obwohl es regnet, gehen wir spazieren"
]

class User:
    def __init__(self, name):
        self.name = name
        self.progress = []  # store (level, correct, answer, timestamp)

    def add_result(self, level, correct, answer, timestamp):
        self.progress.append({
            "level": level,
            "correct": correct,
            "answer": answer,
            "timestamp": timestamp
        })

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            level INTEGER,
            correct INTEGER,
            answer TEXT,
            timestamp TEXT
        );''')

        conn.execute('''CREATE TABLE IF NOT EXISTS vocab_log (
            username TEXT,
            vocab TEXT,
            translation TEXT
        );''')

init_db()

def vocab_exists(username, word):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT 1 FROM vocab_log WHERE username = ? AND vocab = ?", (username, word.lower()))
        return cursor.fetchone() is not None

def save_vocab(username, german_word):
    if german_word in ["?", "!", ",", "."] or not API_KEY:
        return

    if vocab_exists(username, german_word):
        return

    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": API_KEY,
        "text": german_word,
        "source_lang": "DE",
        "target_lang": "EN"
    }
    try:
        response = requests.post(url, data=data)
        english_word = response.json()["translations"][0]["text"]
    except Exception:
        english_word = "(error)"

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO vocab_log (username, vocab, translation) VALUES (?, ?, ?)",
            (username, german_word.lower(), english_word)
        )

def split_and_clean(text):
    return re.findall(r"\b\w+\b", text)

def translate_to_german(english_sentence, username=None):
    if not API_KEY:
        return "❌ DeepL key is empty."

    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": API_KEY,
        "text": english_sentence,
        "target_lang": "DE"
    }
    response = requests.post(url, data=data)

    try:
        json_data = response.json()
        german_text = json_data["translations"][0]["text"]

        if username:
            words_to_check = split_and_clean(german_text)
            for word in words_to_check:
                save_vocab(username, word)

        return german_text
    except Exception:
        return "❌ API failure"

def get_scrambled_sentence(sentence):
    words = sentence.split()
    random.shuffle(words)
    return words

def evaluate_order(user_answer, correct_sentence):
    user_words = user_answer.strip().split()
    correct_words = correct_sentence.strip().split()

    if user_words == correct_words:
        return True, "✅ Deine Reihenfolge ist korrekt!"

    feedback = []
    for i, word in enumerate(user_words):
        if i < len(correct_words) and word == correct_words[i]:
            feedback.append(Fore.GREEN + word + Style.RESET_ALL)
        else:
            feedback.append(Fore.RED + word + Style.RESET_ALL)
    return False, "📝 Feedback: " + " ".join(feedback)

def get_feedback(student_version, correct_version):
    student_words = student_version.strip().split()
    correct_words = correct_version.strip().split()

    output = []
    explanation = []

    w_question_words = [
        "wie", "was", "wann", "wo", "warum", "wer", "wieso", "woher", "wohin", "welche", "welcher", "welches"
    ]
    first_word = correct_words[0].lower() if correct_words else ""
    is_question = correct_version.strip().endswith("?")
    is_w_question = is_question and first_word in w_question_words
    is_yesno_question = is_question and not is_w_question and first_word.isalpha()

    if sorted([w.lower() for w in student_words]) == sorted([w.lower() for w in correct_words]) \
            and [w.lower() for w in student_words] != [w.lower() for w in correct_words]:

        for idx, word in enumerate(student_words):
            correct_word = correct_words[idx] if idx < len(correct_words) else ""
            if word.lower() == correct_word.lower():
                output.append(Fore.GREEN + word + Style.RESET_ALL)
            elif word.lower() in [w.lower() for w in correct_words]:
                output.append(Fore.RED + word + Style.RESET_ALL)
            else:
                output.append(Fore.YELLOW + word + Style.RESET_ALL)

        user_version_html = "<p><strong>🧩 Deine Version:</strong><br><span style='font-family: monospace;'>" + " ".join(output) + "</span></p>"

        if is_w_question:
            return False, (
                "⚠️ Deine Wörter sind korrekt, aber die Wortstellung ist falsch für eine W-Frage.<br>"
                "📘 Regel: W-Wort – Verb – Subjekt – ...<br>"
                + user_version_html
            )
        elif is_yesno_question:
            return False, (
                "⚠️ Deine Wörter sind korrekt, aber die Wortstellung ist falsch für eine Ja/Nein-Frage.<br>"
                "📘 Regel: Verb – Subjekt – Objekt – ...<br>"
                + user_version_html
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
        if tag == 'equal':
            for w in correct_words[i1:i2]:
                output.append(Fore.GREEN + w + Style.RESET_ALL)
        elif tag == 'replace':
            for w1, w2 in zip(correct_words[i1:i2], student_words[j1:j2]):
                output.append(Fore.RED + w2 + Style.RESET_ALL)
                explanation.append(f"❌ '{w2}' sollte '{w1}' sein.")
        elif tag == 'delete':
            for w in correct_words[i1:i2]:
                output.append(Fore.RED + "___" + Style.RESET_ALL)
                explanation.append(f"❌ Es fehlt das Wort '{w}'.")
        elif tag == 'insert':
            for w in student_words[j1:j2]:
                output.append(Fore.YELLOW + w + Style.RESET_ALL)
                explanation.append(f"🟡 Zusätzliches Wort: '{w}'")

    if not explanation:
        return True, "✅ Deine Übersetzung ist korrekt!"

    feedback_text = "<p><strong>🧩 Deine Version:</strong><br><span style='font-family: monospace;'>" + " ".join(output) + "</span></p>"
    feedback_text += "<p>📘 Erklärungen:<br>" + "<br>".join(explanation) + "</p>"
    return False, feedback_text

def save_result(username, level, correct, answer):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO results (username, level, correct, answer, timestamp) VALUES (?, ?, ?, ?, ?)",
            (username, level, int(correct), answer, datetime.now().isoformat())
        )

def get_all_results():
    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("SELECT username, level, correct, answer, timestamp FROM results ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return [
            {"username": u, "level": l, "correct": c, "answer": a, "timestamp": t}
            for u, l, c, a, t in rows
        ]

def fetch_lessons_for_user(username):
    print(f"[DEBUG] Fetching lessons for user: {username}", flush=True)
    lessons = []

    with sqlite3.connect("game_results.db") as conn:
        cursor = conn.execute("""
            SELECT DISTINCT level, MAX(timestamp), correct
            FROM results
            WHERE username = ?
            GROUP BY level
            ORDER BY MAX(timestamp) DESC
        """, (username,))
        rows = cursor.fetchall()

        for level, last_attempt, correct in rows:
            lessons.append({
                "id": level,
                "title": f"Lesson {level + 1}",
                "completed": bool(correct),
                "last_attempt": last_attempt
            })

    return lessons
