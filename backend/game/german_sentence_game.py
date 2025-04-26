# german_sentence_game.py
from utils.db_utils import get_connection
import random
import requests
from colorama import Fore, Style
import sqlite3
from datetime import datetime
import os
import re
import json
from pathlib import Path

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
    with get_connection() as conn:
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

        conn.execute('''CREATE TABLE IF NOT EXISTS lesson_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            published INTEGER DEFAULT 0
        );''')

        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );''')

        conn.execute('''CREATE TABLE IF NOT EXISTS lesson_blocks (
            lesson_id INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            PRIMARY KEY (lesson_id, block_id)
        );''')

init_db()

def split_and_clean(text):
    return re.findall(r"\b\w+\b", text)

def vocab_exists(username, german_word):
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM vocab_log WHERE username = ? AND vocab = ?",
            (username, german_word)
        )
        return cursor.fetchone() is not None

# Dictionary of common German words and their English translations
# This replaces the paid DeepL API with a free alternative
GERMAN_ENGLISH_DICT = {
    # Common nouns
    "ich": "I",
    "du": "you",
    "er": "he",
    "sie": "she/they",
    "es": "it",
    "wir": "we",
    "ihr": "you (plural)",
    "mann": "man",
    "frau": "woman",
    "kind": "child",
    "haus": "house",
    "auto": "car",
    "schule": "school",
    "buch": "book",
    "freund": "friend",
    "freundin": "friend (female)",
    "tag": "day",
    "woche": "week",
    "monat": "month",
    "jahr": "year",
    "zeit": "time",
    "wasser": "water",
    "essen": "food",
    "kaffee": "coffee",
    "tee": "tea",
    "bier": "beer",
    "wein": "wine",
    "brot": "bread",
    "käse": "cheese",
    "obst": "fruit",
    "gemüse": "vegetables",
    "fleisch": "meat",
    "fisch": "fish",
    "ei": "egg",
    "milch": "milk",
    "zucker": "sugar",
    "salz": "salt",
    "pfeffer": "pepper",
    "öl": "oil",
    "butter": "butter",
    "reis": "rice",
    "nudeln": "pasta",
    "kartoffel": "potato",
    "tomate": "tomato",
    "apfel": "apple",
    "banane": "banana",
    "orange": "orange",
    "erdbeere": "strawberry",
    "kirsche": "cherry",
    "traube": "grape",
    "zitrone": "lemon",
    "birne": "pear",
    "ananas": "pineapple",
    "melone": "melon",
    "kiwi": "kiwi",
    "mango": "mango",
    "pflaume": "plum",
    "pfirsich": "peach",
    "nuss": "nut",
    "schokolade": "chocolate",
    "kuchen": "cake",
    "keks": "cookie",
    "eis": "ice cream",
    "salat": "salad",
    "suppe": "soup",
    "sauce": "sauce",
    "gewürz": "spice",
    "frühstück": "breakfast",
    "mittagessen": "lunch",
    "abendessen": "dinner",
    "morgen": "morning",
    "mittag": "noon",
    "abend": "evening",
    "nacht": "night",
    "heute": "today",
    "gestern": "yesterday",
    "morgen": "tomorrow",
    "woche": "week",
    "wochenende": "weekend",
    "montag": "Monday",
    "dienstag": "Tuesday",
    "mittwoch": "Wednesday",
    "donnerstag": "Thursday",
    "freitag": "Friday",
    "samstag": "Saturday",
    "sonntag": "Sunday",
    "januar": "January",
    "februar": "February",
    "märz": "March",
    "april": "April",
    "mai": "May",
    "juni": "June",
    "juli": "July",
    "august": "August",
    "september": "September",
    "oktober": "October",
    "november": "November",
    "dezember": "December",
    "familie": "family",
    "eltern": "parents",
    "mutter": "mother",
    "vater": "father",
    "schwester": "sister",
    "bruder": "brother",
    "großmutter": "grandmother",
    "großvater": "grandfather",
    "tante": "aunt",
    "onkel": "uncle",
    "cousin": "cousin",
    "nichte": "niece",
    "neffe": "nephew",
    "tochter": "daughter",
    "sohn": "son",
    "baby": "baby",
    "junge": "boy",
    "mädchen": "girl",

    # Common verbs
    "sein": "to be",
    "haben": "to have",
    "werden": "to become",
    "können": "can/to be able to",
    "müssen": "must/to have to",
    "sollen": "should/ought to",
    "wollen": "to want",
    "mögen": "to like",
    "dürfen": "may/to be allowed to",
    "machen": "to make/do",
    "gehen": "to go",
    "kommen": "to come",
    "fahren": "to drive",
    "laufen": "to run/walk",
    "sehen": "to see",
    "hören": "to hear",
    "sprechen": "to speak",
    "sagen": "to say",
    "fragen": "to ask",
    "antworten": "to answer",
    "essen": "to eat",
    "trinken": "to drink",
    "schlafen": "to sleep",
    "wohnen": "to live",
    "arbeiten": "to work",
    "spielen": "to play",
    "lesen": "to read",
    "schreiben": "to write",
    "lernen": "to learn",
    "studieren": "to study",
    "unterrichten": "to teach",
    "helfen": "to help",
    "lieben": "to love",
    "mögen": "to like",
    "hassen": "to hate",
    "brauchen": "to need",
    "wissen": "to know",
    "denken": "to think",
    "glauben": "to believe",
    "verstehen": "to understand",
    "vergessen": "to forget",
    "erinnern": "to remember",
    "kaufen": "to buy",
    "verkaufen": "to sell",
    "bezahlen": "to pay",
    "kosten": "to cost",
    "öffnen": "to open",
    "schließen": "to close",
    "beginnen": "to begin",
    "enden": "to end",
    "starten": "to start",
    "stoppen": "to stop",
    "warten": "to wait",
    "suchen": "to search",
    "finden": "to find",
    "verlieren": "to lose",
    "gewinnen": "to win",
    "lachen": "to laugh",
    "weinen": "to cry",
    "lächeln": "to smile",

    # Common adjectives
    "gut": "good",
    "schlecht": "bad",
    "groß": "big/tall",
    "klein": "small",
    "hoch": "high",
    "niedrig": "low",
    "lang": "long",
    "kurz": "short",
    "alt": "old",
    "jung": "young",
    "neu": "new",
    "schön": "beautiful",
    "hässlich": "ugly",
    "schnell": "fast",
    "langsam": "slow",
    "stark": "strong",
    "schwach": "weak",
    "leicht": "light/easy",
    "schwer": "heavy/difficult",
    "heiß": "hot",
    "kalt": "cold",
    "warm": "warm",
    "kühl": "cool",
    "nass": "wet",
    "trocken": "dry",
    "voll": "full",
    "leer": "empty",
    "reich": "rich",
    "arm": "poor",
    "teuer": "expensive",
    "billig": "cheap",
    "früh": "early",
    "spät": "late",
    "offen": "open",
    "geschlossen": "closed",
    "laut": "loud",
    "leise": "quiet",
    "hell": "bright",
    "dunkel": "dark",
    "süß": "sweet",
    "sauer": "sour",
    "bitter": "bitter",
    "salzig": "salty",
    "scharf": "spicy/sharp",
    "weich": "soft",
    "hart": "hard",
    "rund": "round",
    "eckig": "angular",
    "gerade": "straight",
    "krumm": "crooked",
    "glatt": "smooth",
    "rau": "rough",
    "sauber": "clean",
    "schmutzig": "dirty",
    "gesund": "healthy",
    "krank": "sick",
    "müde": "tired",
    "wach": "awake",
    "hungrig": "hungry",
    "durstig": "thirsty",
    "glücklich": "happy",
    "traurig": "sad",
    "wütend": "angry",
    "ängstlich": "afraid",
    "ruhig": "calm",
    "nervös": "nervous",
    "interessant": "interesting",
    "langweilig": "boring",
    "wichtig": "important",
    "unwichtig": "unimportant",
    "richtig": "correct",
    "falsch": "wrong",
    "wahr": "true",
    "unwahr": "false",
    "möglich": "possible",
    "unmöglich": "impossible",
    "einfach": "simple",
    "kompliziert": "complicated",
    "gleich": "same",
    "anders": "different",
    "ähnlich": "similar",
    "fertig": "ready/finished",
    "voll": "full",
    "leer": "empty",
    "frei": "free",
    "besetzt": "occupied",
    "offen": "open",
    "geschlossen": "closed",

    # Common prepositions and conjunctions
    "in": "in",
    "auf": "on",
    "unter": "under",
    "über": "over",
    "vor": "in front of",
    "hinter": "behind",
    "neben": "next to",
    "zwischen": "between",
    "mit": "with",
    "ohne": "without",
    "für": "for",
    "gegen": "against",
    "von": "from",
    "zu": "to",
    "nach": "after/to",
    "bei": "at",
    "aus": "out of",
    "durch": "through",
    "um": "around",
    "an": "at/on",
    "und": "and",
    "oder": "or",
    "aber": "but",
    "denn": "because",
    "wenn": "if/when",
    "als": "when/as",
    "obwohl": "although",
    "während": "while/during",
    "bis": "until",
    "seit": "since",
    "bevor": "before",
    "nachdem": "after",
    "damit": "so that",
    "weil": "because",
    "dass": "that",
    "ob": "whether",
    "als ob": "as if",
    "sowohl als auch": "both...and",
    "weder noch": "neither...nor",
    "entweder oder": "either...or",
    "je desto": "the...the",

    # Question words
    "wer": "who",
    "was": "what",
    "wo": "where",
    "wohin": "where to",
    "woher": "where from",
    "wann": "when",
    "warum": "why",
    "wie": "how",
    "welche": "which",
    "welcher": "which",
    "welches": "which",
    "wessen": "whose",
    "wem": "to whom",
    "wen": "whom",
    "wieso": "why",
    "weshalb": "why",
    "wie viel": "how much",
    "wie viele": "how many",
    "wie oft": "how often",
    "wie lange": "how long",

    # Numbers
    "null": "zero",
    "eins": "one",
    "zwei": "two",
    "drei": "three",
    "vier": "four",
    "fünf": "five",
    "sechs": "six",
    "sieben": "seven",
    "acht": "eight",
    "neun": "nine",
    "zehn": "ten",
    "elf": "eleven",
    "zwölf": "twelve",
    "dreizehn": "thirteen",
    "vierzehn": "fourteen",
    "fünfzehn": "fifteen",
    "sechzehn": "sixteen",
    "siebzehn": "seventeen",
    "achtzehn": "eighteen",
    "neunzehn": "nineteen",
    "zwanzig": "twenty",
    "dreißig": "thirty",
    "vierzig": "forty",
    "fünfzig": "fifty",
    "sechzig": "sixty",
    "siebzig": "seventy",
    "achtzig": "eighty",
    "neunzig": "ninety",
    "hundert": "hundred",
    "tausend": "thousand",
    "million": "million",
    "milliarde": "billion",

    # Colors
    "rot": "red",
    "blau": "blue",
    "gelb": "yellow",
    "grün": "green",
    "schwarz": "black",
    "weiß": "white",
    "grau": "gray",
    "braun": "brown",
    "orange": "orange",
    "lila": "purple",
    "rosa": "pink",
    "türkis": "turquoise",
    "gold": "gold",
    "silber": "silver",

    # Common phrases
    "bitte": "please",
    "danke": "thank you",
    "gern geschehen": "you're welcome",
    "entschuldigung": "excuse me/sorry",
    "es tut mir leid": "I'm sorry",
    "hallo": "hello",
    "guten morgen": "good morning",
    "guten tag": "good day",
    "guten abend": "good evening",
    "gute nacht": "good night",
    "auf wiedersehen": "goodbye",
    "tschüss": "bye",
    "bis später": "see you later",
    "bis bald": "see you soon",
    "bis morgen": "see you tomorrow",
    "willkommen": "welcome",
    "prost": "cheers",
    "guten appetit": "enjoy your meal",
    "gesundheit": "bless you",
    "alles gute": "all the best",
    "herzlichen glückwunsch": "congratulations",
    "frohe weihnachten": "merry christmas",
    "frohes neues jahr": "happy new year",
    "frohe ostern": "happy easter",
    "schönes wochenende": "have a nice weekend",
    "gute reise": "have a good trip",
    "gute besserung": "get well soon",
    "viel glück": "good luck",
    "viel spaß": "have fun",
    "wie geht es dir": "how are you",
    "mir geht es gut": "I'm fine",
    "ich verstehe nicht": "I don't understand",
    "ich weiß nicht": "I don't know",
    "kein problem": "no problem",
    "einen moment bitte": "one moment please",
    "hilfe": "help",
    "notfall": "emergency",
    "wie spät ist es": "what time is it",
    "wie viel kostet das": "how much does this cost",
    "wo ist die toilette": "where is the bathroom",
    "ich bin verloren": "I am lost",
    "ich brauche einen arzt": "I need a doctor",
    "ich bin allergisch gegen": "I am allergic to",
    "sprechen sie englisch": "do you speak English",
    "ich spreche kein deutsch": "I don't speak German",
    "ich lerne deutsch": "I'm learning German",
    "können sie das wiederholen": "can you repeat that",
    "können sie langsamer sprechen": "can you speak more slowly",
    "können sie mir helfen": "can you help me",
    "ich möchte": "I would like",
    "ich hätte gern": "I would like",
    "die rechnung bitte": "the bill please",
    "eine frage": "a question",
    "ich habe eine frage": "I have a question",
    "das stimmt": "that's right",
    "das stimmt nicht": "that's not right",
    "ich bin einverstanden": "I agree",
    "ich bin nicht einverstanden": "I disagree",
    "das ist richtig": "that is correct",
    "das ist falsch": "that is wrong",
    "das ist gut": "that is good",
    "das ist schlecht": "that is bad",
    "das ist wichtig": "that is important",
    "das ist nicht wichtig": "that is not important",
    "das ist interessant": "that is interesting",
    "das ist langweilig": "that is boring",
    "das ist teuer": "that is expensive",
    "das ist billig": "that is cheap",
    "das ist einfach": "that is easy",
    "das ist schwer": "that is difficult",
    "das ist möglich": "that is possible",
    "das ist unmöglich": "that is impossible",
    "das ist genug": "that is enough",
    "das ist zu viel": "that is too much",
    "das ist zu wenig": "that is too little",
    "das ist zu spät": "that is too late",
    "das ist zu früh": "that is too early",
    "das ist zu groß": "that is too big",
    "das ist zu klein": "that is too small",
    "das ist zu heiß": "that is too hot",
    "das ist zu kalt": "that is too cold",
    "das ist zu laut": "that is too loud",
    "das ist zu leise": "that is too quiet",
    "das ist zu hell": "that is too bright",
    "das ist zu dunkel": "that is too dark",
    "das ist zu süß": "that is too sweet",
    "das ist zu sauer": "that is too sour",
    "das ist zu salzig": "that is too salty",
    "das ist zu bitter": "that is too bitter",
    "das ist zu scharf": "that is too spicy",
}

def save_vocab(username, german_word):
    if german_word in ["?", "!", ",", "."]:
        return

    if vocab_exists(username, german_word):
        return

    # Convert to lowercase for dictionary lookup
    german_word_lower = german_word.lower()

    # Try to find the word in our dictionary
    english_word = GERMAN_ENGLISH_DICT.get(german_word_lower, "(unknown)")

    # Smart capitalization: if the original German word was capitalized, capitalize the English word
    if german_word[0].isupper() and english_word != "(unknown)":
        english_word = english_word.capitalize()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO vocab_log (username, vocab, translation) VALUES (?, ?, ?)",
            (username, german_word, english_word)
        )


# Create a reverse dictionary for English to German translation
ENGLISH_GERMAN_DICT = {}
for german, english in GERMAN_ENGLISH_DICT.items():
    # Handle multi-meaning entries like "to be" -> "sein"
    if "/" in english:
        parts = english.split("/")
        for part in parts:
            ENGLISH_GERMAN_DICT[part.strip()] = german
    else:
        ENGLISH_GERMAN_DICT[english] = german

def translate_to_german(english_sentence, username=None):
    """
    Translate English text to German.
    This function now uses the Gemini AI translator with fallback to dictionary.

    Args:
        english_sentence (str): The English text to translate
        username (str, optional): The username for personalization

    Returns:
        str: The German translation
    """
    try:
        # Try to use the Gemini AI translator
        from utils.gemini_translator import translate_with_gemini
        german_text = translate_with_gemini(english_sentence, username)

        # If translation succeeded, save vocabulary for the user
        if username and german_text:
            german_words = split_and_clean(german_text)
            for de_word in german_words:
                save_vocab(username, de_word)

        return german_text

    except Exception as e:
        print(f"❌ Error using Gemini translator: {e}")
        print("⚠️ Falling back to dictionary translation")

        # Fallback to dictionary-based translation
        words = english_sentence.lower().split()
        translated_words = []

        for word in words:
            # Remove punctuation for lookup
            clean_word = word.strip(".,!?;:()\"'")

            # Try to find the word in our dictionary
            if clean_word in ENGLISH_GERMAN_DICT:
                german_word = ENGLISH_GERMAN_DICT[clean_word]
                # Capitalize if it's the first word in the sentence
                if len(translated_words) == 0:
                    german_word = german_word.capitalize()
                translated_words.append(german_word)
            else:
                # If not found, keep the original word
                translated_words.append(clean_word)

        german_text = " ".join(translated_words)

        # Add basic capitalization for German nouns (simplified rule)
        for word in GERMAN_ENGLISH_DICT.keys():
            if len(word) > 1 and word[0].isupper():
                # Replace all occurrences with capitalized version
                pattern = r'\b' + word[0].lower() + word[1:] + r'\b'
                german_text = re.sub(pattern, word, german_text)

        if username:
            german_words = split_and_clean(german_text)
            for de_word in german_words:
                save_vocab(username, de_word)

        return german_text


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
   with get_connection() as conn:
        conn.execute(
            "INSERT INTO results (username, level, correct, answer, timestamp) VALUES (?, ?, ?, ?, ?)",
            (username, level, int(correct), answer, datetime.now().isoformat())
        )

def get_all_results():
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT u.username, r.level, r.correct, r.answer, r.timestamp
            FROM users u
            LEFT JOIN results r ON u.username = r.username
            ORDER BY r.timestamp DESC
        """)
        rows = cursor.fetchall()

        return [
            {
                "username": u,
                "level": l,
                "correct": c,
                "answer": a,
                "timestamp": t
            }
            for u, l, c, a, t in rows
        ]

