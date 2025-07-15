"""Utility helpers for vocabulary management and translation."""

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from utils.ai.prompts import analyze_word_prompt, translate_sentence_prompt
from database import update_row, select_one, fetch_one, insert_row
from .algorithm import sm2
from utils.ai.ai_api import send_prompt


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
    if not word:
        return None

    user_prompt = analyze_word_prompt(word)

    try:
        resp = send_prompt(
            "You are a helpful German linguist.",
            user_prompt,
            temperature=0.3,
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


def _singularize(noun: str) -> str:
    """Improved heuristic to get the singular form of a German noun."""
    lower = noun.lower()
    # Handle common feminine plural endings
    if lower.endswith("innen"):
        return noun[:-5] + "in"  # Freundinnen -> Freundin
    if lower.endswith("nen"):
        return noun[:-3] + "ne"
    # Remove plural 'en' (but not for diminutives)
    if lower.endswith("en") and not lower.endswith(("chen", "lein")):
        return noun[:-2]
    # Remove plural 'e'
    if lower.endswith("e") and len(noun) > 3:
        return noun[:-1]
    # Remove plural 'n'
    if lower.endswith("n") and len(noun) > 3:
        return noun[:-1]
    return noun


def normalize_word(word: str, article: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """Normalize a word for duplicate checks."""
    if not word:
        return word, "other", article

    token = word.strip()

    # Treat capitalized words or words with an article as nouns
    if article or token[:1].isupper():
        normalized = _singularize(token.capitalize())
        return normalized, "noun", article

    normalized = token.lower()
    return normalized, "other", article


def vocab_exists(username: str, german_word: str) -> bool:
    """Check if a vocab entry already exists for a user."""
    row = fetch_one(
        "vocab_log",
        "WHERE username = ? AND vocab = ?",
        (username, german_word),
        columns="1",
    )
    return row is not None


ENGLISH_ARTICLES = {
    "the": "der",
    "a": "ein",
    "an": "ein",
}


def save_vocab(
    username: str,
    german_word: str,
    context: Optional[str] = None,
    exercise: Optional[str] = None,
    article: Optional[str] = None,
) -> Optional[str]:
    """Store a new vocabulary word for spaced repetition.

    Returns the canonical form of the word that was stored or found. Returns
    ``None`` if nothing was saved (e.g. punctuation)."""

    if german_word in ["?", "!", ",", "."]:
        return None

    lower_word = german_word.lower()
    if lower_word in ENGLISH_ARTICLES:
        normalized = ENGLISH_ARTICLES[lower_word]
        word_type = "article"
        english_word = lower_word
        details = None
    else:
        # Early normalization for existence check
        norm_check, *_ = normalize_word(german_word, article)
        if vocab_exists(username, norm_check):
            return norm_check

        # AI analysis only needed if word is new
        analysis = analyze_word_ai(german_word)
        if analysis:
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
            normalized, word_type, _ = normalize_word(german_word, article)
            english_word = ""
            details = None

    # Avoid saving invalid forms like 'Freundi' (unless valid endings)
    valid_i_endings = ("ei", "ie", "ai", "oi", "ui")
    if normalized.endswith("i") and not normalized.endswith(valid_i_endings):
        return None

    # Check again after potential AI normalization
    if vocab_exists(username, normalized):
        return normalized

    now = datetime.now().isoformat()
    insert_row(
        "vocab_log",
        {
            "username": username,
            "vocab": normalized,
            "translation": english_word,
            "word_type": word_type,
            "article": article,
            "details": details,
            "context": context,
            "exercise": exercise,
            "next_review": now,
            "created_at": now,
            "last_review": now,
        },
    )

    return normalized


def translate_to_german(english_sentence: str, username: Optional[str] = None) -> str:
    """Translate an English sentence using Mistral AI and optionally store vocab."""

    user_prompt = translate_sentence_prompt(english_sentence)

    try:
        resp = send_prompt(
            "You are a helpful German translator.",
            user_prompt,
            temperature=0.3,
        )
        if resp.status_code == 200:
            german_text = resp.json()["choices"][0]["message"]["content"].strip()
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
        print("❌ Error calling Mistral:", e)

    return "❌ API failure"


def review_vocab_word(
    username: str,
    word: str,
    quality: int,
    seen: Optional[set[str]] = None,
) -> None:
    """Update spaced repetition data for a vocab word using SM2."""
    if not word or not word.isalpha():
        return

    normalized, *_ = normalize_word(word)
    if seen is not None:
        if normalized in seen:
            return
        seen.add(normalized)

    row = select_one(
        "vocab_log",
        columns=["ef", "repetitions", "interval_days"],
        where="username = ? AND vocab = ?",
        params=(username, normalized),
    )

    if not row:
        saved = save_vocab(username, word, exercise="ai")
        if saved:
            normalized = saved
        row = select_one(
            "vocab_log",
            columns=["ef", "repetitions", "interval_days"],
            where="username = ? AND vocab = ?",
            params=(username, normalized),
        )
        if row:
            ef = row.get("ef", 2.5)
            reps = row.get("repetitions", 0)
            interval = row.get("interval_days", 1)
        else:
            ef = 2.5
            reps = 0
            interval = 1
    else:
        ef = row.get("ef", 2.5)
        reps = row.get("repetitions", 0)
        interval = row.get("interval_days", 1)

    # Apply SM2 algorithm
    ef, reps, interval = sm2(quality, ef, reps, interval)

    # Compute next due date
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
