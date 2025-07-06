"""Utility helpers for vocabulary management and translation."""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple

from colorama import Fore, Style

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

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}

ARTICLES = {
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einen",
    "einem",
    "einer",
    "eines",
}

PRONOUNS = {
    "ich",
    "du",
    "er",
    "sie",
    "es",
    "wir",
    "ihr",
    "sie",
    "mir",
    "dir",
    "ihm",
    "ihr",
    "uns",
    "euch",
}

CONJUNCTIONS = {"und", "oder", "aber", "denn", "weil", "dass"}

PREPOSITIONS = {
    "in",
    "im",
    "am",
    "an",
    "auf",
    "bei",
    "mit",
    "nach",
    "seit",
    "von",
    "zu",
}

ADVERBS = {"gern", "nicht", "nie", "immer", "oft"}


def _extract_json(text: str):
    """Return parsed JSON object from Mistral output."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def analyze_word_ai(word: str) -> Optional[dict]:
    """Return analysis data for a German word using Mistral."""
    if not MISTRAL_API_KEY or not word:
        return None

    user_prompt = {
        "role": "user",
        "content": (
            "Give dictionary info for the German word '" + word + "'.\n"
            "Return JSON with keys base_form, type, article, translation, info."
            " Use null for article if not a noun."
        ),
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German linguist."},
            user_prompt,
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(
            MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=10
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            data = _extract_json(content)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print("[analyze_word_ai] Mistral error:", e)
    return None


def split_and_clean(text: str) -> list[str]:
    """Split a text into lowercase word tokens."""
    return re.findall(r"[A-Za-zÄÖÜäöüß]+", text)


def extract_words(text: str) -> list[tuple[str, Optional[str]]]:
    """Return a list of (word, article) tuples from a German text."""
    tokens = re.findall(r"[A-Za-zÄÖÜäöüß]+", text)
    result: list[tuple[str, Optional[str]]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        lower = tok.lower()
        if lower in ARTICLES and i + 1 < len(tokens):
            # Attach the article to the following token regardless of
            # capitalization. This helps when users do not capitalize nouns.
            next_tok = tokens[i + 1]
            result.append((next_tok, lower))
            i += 2
            continue
        result.append((tok, None))
        i += 1
    return result


def _normalize_verb(word: str) -> str:
    """Very small heuristic to convert a verb to its infinitive."""
    if word.endswith("en"):
        return word
    if word.endswith("st"):
        return word[:-2] + "en"
    if word.endswith("t"):
        return word[:-1] + "en"
    if word.endswith("e"):
        return word[:-1] + "en"
    return word


def _normalize_adjective(word: str) -> str:
    """Return the base form of an adjective by stripping common endings."""
    lower = word.lower()
    for suffix in ("eren", "erer", "eres", "erem"):
        if lower.endswith(suffix):
            return word[:-4]
    for suffix in ("en", "em", "er", "es", "e"):
        if lower.endswith(suffix) and len(word) - len(suffix) >= 2:
            return word[: -len(suffix)]
    return word


def _guess_article(word: str) -> str:
    """Guess the article for a noun using simple endings."""
    lower = word.lower()
    if lower.endswith(("ung", "keit", "heit", "schaft", "tät", "tion", "ik")):
        return "die"
    if lower.endswith(("chen", "lein", "ment", "tum", "ma", "um")):
        return "das"
    return "der"


def _singularize(noun: str) -> str:
    """Very small heuristic to get the singular form of a noun."""
    lower = noun.lower()
    if lower.endswith("nen"):
        return noun[:-3] + "ne"
    if lower.endswith("en") and not lower.endswith(("chen", "lein")):
        return noun[:-2]
    if lower.endswith("e") and len(noun) > 3:
        return noun[:-1]
    if lower.endswith("n") and len(noun) > 3:
        return noun[:-1]
    return noun


def normalize_word(word: str, article: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """Return the normalized form, detected type and article."""
    if not word:
        return word, "other", article

    raw = word
    candidate = word.lower()

    if article:
        base = _singularize(raw.capitalize())
        return base, "noun", article

    if candidate in ARTICLES:
        return candidate, "article", candidate
    if candidate in PRONOUNS:
        return candidate, "pronoun", None
    if candidate in CONJUNCTIONS:
        return candidate, "conjunction", None
    if candidate in PREPOSITIONS:
        return candidate, "preposition", None
    if candidate in ADVERBS:
        return candidate, "adverb", None

    if raw[0].isupper():
        article_guess = _guess_article(raw)
        base = _singularize(raw.capitalize())
        return base, "noun", article_guess

    # Detect common noun endings even when the word is not capitalized.
    noun_suffixes = (
        "ung",
        "keit",
        "heit",
        "schaft",
        "tät",
        "tion",
        "ik",
        "chen",
        "lein",
        "ment",
        "tum",
        "ma",
        "um",
    )
    if candidate.endswith(noun_suffixes):
        base = _singularize(raw.capitalize())
        return base, "noun", _guess_article(raw)

    if candidate.endswith(("en", "st", "t")):
        return _normalize_verb(candidate), "verb", None

    if candidate.endswith(("ig", "lich", "isch", "bar")):
        return _normalize_adjective(candidate), "adjective", None

    return candidate, "other", None


def vocab_exists(username: str, german_word: str) -> bool:
    """Check if a vocab entry already exists for a user."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM vocab_log WHERE username = ? AND vocab = ?",
            (username, german_word),
        )
        return cursor.fetchone() is not None


def save_vocab(
    username: str,
    german_word: str,
    context: Optional[str] = None,
    exercise: Optional[str] = None,
    article: Optional[str] = None,
) -> None:
    """Store a new vocabulary word for spaced repetition."""
    print(
        Fore.CYAN
        + f"[save_vocab] User: {username}, Word: {german_word}, Context: {context}, Exercise: {exercise}, Article: {article}"
        + Style.RESET_ALL,
        flush=True,
    )

    if german_word in ["?", "!", ",", "."]:
        print(Fore.YELLOW + "[save_vocab] Skipping punctuation." + Style.RESET_ALL, flush=True)
        return

    analysis = analyze_word_ai(german_word)
    if analysis:
        print(Fore.CYAN + f"[save_vocab] AI analysis: {analysis}" + Style.RESET_ALL, flush=True)
        normalized = analysis.get("base_form", german_word)
        word_type = analysis.get("type", "other")
        article = analysis.get("article") or article
        english_word = analysis.get("translation", "")
        details = analysis.get("info")

        if word_type == "noun":
            normalized = _singularize(normalized.capitalize())
        else:
            normalized = normalized.lower()
    else:
        normalized, word_type, art = normalize_word(german_word, article)
        if word_type == "noun":
            article = article or art
        else:
            article = None
        details = None
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
        except Exception as e:
            print(Fore.RED + f"[save_vocab] DeepL error: {e}" + Style.RESET_ALL, flush=True)
            english_word = "(error)"

    if not analysis and english_word.lower() == german_word.lower():
        # Likely an English word accidentally submitted as German
        print(Fore.YELLOW + "[save_vocab] Detected English word, skipping." + Style.RESET_ALL, flush=True)
        return

    if vocab_exists(username, normalized):
        print(Fore.YELLOW + "[save_vocab] Word already exists, skipping." + Style.RESET_ALL, flush=True)
        return

    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO vocab_log (username, vocab, translation, word_type, article, details, context, exercise, next_review, created_at, last_review) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                username,
                normalized,
                english_word,
                word_type,
                article,
                details,
                context,
                exercise,
                now,
                now,
                now,
            ),
        )
        print(
            Fore.GREEN
            + f"[save_vocab] Saved '{normalized}' -> '{english_word}' for {username}."
            + Style.RESET_ALL,
            flush=True,
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
            for word, art in extract_words(german_text):
                save_vocab(
                    username,
                    word,
                    context=german_text,
                    exercise="translation",
                    article=art,
                )
        return german_text
    except Exception as e:
        print("❌ Error calling DeepL:", e)
        return "❌ API failure"


def review_vocab_word(username: str, word: str, quality: int) -> None:
    """Update spaced repetition data for a vocab word using SM2."""
    if not word or not word.isalpha():
        return

    normalized, *_ = normalize_word(word)

    row = fetch_one_custom(
        "SELECT ef, repetitions, interval_days FROM vocab_log WHERE username = ? AND vocab = ?",
        (username, normalized),
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
            "last_review": datetime.now().isoformat(),
        },
        "username = ? AND vocab = ?",
        (username, normalized),
    )
