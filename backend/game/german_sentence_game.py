# german_sentence_game.py
from utils.db_utils import get_connection, fetch_custom
import random
import requests
from colorama import Fore, Style
import sqlite3
from datetime import datetime
import os
import re

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
if not DEEPL_API_KEY:
    try:
        with open("DEEPL_API_KEY") as f:
            DEEPL_API_KEY = f.read().strip()
    except Exception:
        DEEPL_API_KEY = None

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    try:
        with open("MISTRAL_API_KEY") as f:
            MISTRAL_API_KEY = f.read().strip()
    except Exception:
        MISTRAL_API_KEY = None

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}

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

        user_prompt = {
            "role": "user",
            "content": (
                "Create one short (max 8 words) German sentence for a beginner. "
                f"Use some of these words: {', '.join(vocab_list)}. "
                f"Topics to consider: {', '.join(topics)}. "
                "Only return the sentence."
            ),
        }

        payload = {
            "model": "mistral-medium",
            "messages": [
                {"role": "system", "content": "You are a helpful German teacher."},
                user_prompt,
            ],
            "temperature": 0.7,
        }

        resp = requests.post(
            MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=10
        )
        if resp.status_code == 200:
            sentence = resp.json()["choices"][0]["message"]["content"].strip()
            return sentence.strip('"')
    except Exception as e:
        print("AI sentence generation failed:", e)
    return None


def split_and_clean(text):
    return re.findall(r"\b\w+\b", text)


def vocab_exists(username, german_word):
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM vocab_log WHERE username = ? AND vocab = ?",
            (username, german_word),
        )
        return cursor.fetchone() is not None


def save_vocab(username, german_word, context=None, exercise=None):
    if german_word in ["?", "!", ",", "."] or not DEEPL_API_KEY:
        return

    if vocab_exists(username, german_word):
        return

    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": german_word,
        "source_lang": "DE",
        "target_lang": "EN",
    }

    try:
        response = requests.post(url, data=data)
        english_word = response.json()["translations"][0]["text"]

        # Smart lowercasing: only lowercase if it's a single word and not all-caps
        if english_word.isalpha() and english_word.istitle():
            english_word = english_word.lower()
    except Exception:
        english_word = "(error)"

    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO vocab_log (username, vocab, translation, context, exercise, next_review, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, german_word, english_word, context, exercise, now, now),)


def translate_to_german(english_sentence, username=None):
    if not DEEPL_API_KEY:
        return "❌ DeepL key is empty."

    url = "https://api-free.deepl.com/v2/translate"
    data = {"auth_key": DEEPL_API_KEY, "text": english_sentence, "target_lang": "DE"}

    try:
        response = requests.post(url, data=data)
        german_text = response.json()["translations"][0]["text"]

        if username:
            german_words = split_and_clean(german_text)
            for de_word in german_words:
                save_vocab(
                    username,
                    de_word,
                    context=german_text,
                    exercise="translation",
                )

        return german_text
    except Exception as e:
        print("❌ Error calling DeepL:", e)
        return "❌ API failure"


def get_scrambled_sentence(sentence):
    words = sentence.split()
    random.shuffle(words)
    return words


from mock_data.script import generate_feedback_prompt
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



def get_feedback(student_version, correct_version):
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

    if sorted([w.lower() for w in student_words]) == sorted(
        [w.lower() for w in correct_words]
    ) and [w.lower() for w in student_words] != [w.lower() for w in correct_words]:

        for idx, word in enumerate(student_words):
            correct_word = correct_words[idx] if idx < len(correct_words) else ""
            if word.lower() == correct_word.lower():
                output.append(Fore.GREEN + word + Style.RESET_ALL)
            elif word.lower() in [w.lower() for w in correct_words]:
                output.append(Fore.RED + word + Style.RESET_ALL)
            else:
                output.append(Fore.YELLOW + word + Style.RESET_ALL)

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
        elif tag == "delete":
            for w in correct_words[i1:i2]:
                output.append(Fore.RED + "___" + Style.RESET_ALL)
                explanation.append(f"❌ Es fehlt das Wort '{w}'.")
        elif tag == "insert":
            for w in student_words[j1:j2]:
                output.append(Fore.YELLOW + w + Style.RESET_ALL)
                explanation.append(f"🟡 Zusätzliches Wort: '{w}'")

    if not explanation:
        return True, "✅ Deine Übersetzung ist korrekt!"

    feedback_text = (
        "<p><strong>🧩 Deine Version:</strong><br><span style='font-family: monospace;'>"
        + " ".join(output)
        + "</span></p>"
    )
    feedback_text += "<p>📘 Erklärungen:<br>" + "<br>".join(explanation) + "</p>"
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
