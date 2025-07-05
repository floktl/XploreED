"""Utility helpers for vocabulary management and translation."""

import os
import re
from datetime import datetime, timedelta
from typing import Optional

import requests

from .db_utils import get_connection, update_row, fetch_one_custom
from .algorithm import sm2

# Load DeepL API key from environment or optional file
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
if not DEEPL_API_KEY:
    try:
        with open("DEEPL_API_KEY") as f:
            DEEPL_API_KEY = f.read().strip()
    except Exception:
        DEEPL_API_KEY = None

def split_and_clean(text: str) -> list[str]:
    """Split a text into lowercase word tokens."""
    return re.findall(r"\b\w+\b", text)


def vocab_exists(username: str, german_word: str) -> bool:
    """Check if a vocab entry already exists for a user."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM vocab_log WHERE username = ? AND vocab = ?",
            (username, german_word),
        )
        return cursor.fetchone() is not None


def save_vocab(username: str, german_word: str, context: Optional[str] = None, exercise: Optional[str] = None) -> None:
    """Store a new vocabulary word for spaced repetition."""
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
        if english_word.isalpha() and english_word.istitle():
            english_word = english_word.lower()
    except Exception:
        english_word = "(error)"

    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO vocab_log (username, vocab, translation, context, exercise, next_review, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, german_word, english_word, context, exercise, now, now),
        )


def translate_to_german(english_sentence: str, username: Optional[str] = None) -> str:
    """Translate an English sentence using DeepL and optionally store vocab."""
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
                save_vocab(username, de_word, context=german_text, exercise="translation")
        return german_text
    except Exception as e:
        print("❌ Error calling DeepL:", e)
        return "❌ API failure"


def review_vocab_word(username: str, word: str, quality: int) -> None:
    """Update spaced repetition data for a vocab word using SM2."""
    if not word or not word.isalpha():
        return

    row = fetch_one_custom(
        "SELECT ef, repetitions, interval_days FROM vocab_log WHERE username = ? AND vocab = ?",
        (username, word),
    )

    if not row:
        save_vocab(username, word, exercise="ai")
        ef = 2.5
        reps = 0
        interval = 1
    else:
        ef = row.get("ef", 2.5)
        reps = row.get("repetitions", 0)
        interval = row.get("interval_days", 1)

    ef, reps, interval = sm2(quality, ef, reps, interval)
    next_review = (datetime.now() + timedelta(days=interval)).isoformat()

    update_row(
        "vocab_log",
        {
            "ef": ef,
            "repetitions": reps,
            "interval_days": interval,
            "next_review": next_review,
        },
        "username = ? AND vocab = ?",
        (username, word),
    )
