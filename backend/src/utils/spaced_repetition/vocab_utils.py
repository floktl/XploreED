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
    # print(
    #     Fore.CYAN
    #     + f"[save_vocab] User: {username}, Word: {german_word}, Context: {context}, Exercise: {exercise}, Article: {article}"
    #     + Style.RESET_ALL,
    #     flush=True,
    # )

    if german_word in ["?", "!", ",", "."]:
        # print(Fore.YELLOW + "[save_vocab] Skipping punctuation." + Style.RESET_ALL, flush=True)
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
            # print(Fore.YELLOW + "[save_vocab] Word already exists, skipping." + Style.RESET_ALL, flush=True)
            return norm_check

        # AI analysis only needed if word is new
        analysis = analyze_word_ai(german_word)
        if analysis:
            # print(Fore.CYAN + f"[save_vocab] AI analysis: {analysis}" + Style.RESET_ALL, flush=True)
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

    # Check again after potential AI normalization
    if vocab_exists(username, normalized):
        # print(
        #     Fore.YELLOW
        #     + "[save_vocab] Word exists after normalization, skipping."
        #     + Style.RESET_ALL,
        #     flush=True,
        # )
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
        # print(
        #     Fore.GREEN
        #     + f"[save_vocab] Saved '{normalized}' -> '{english_word}' for {username}."
        #     + Style.RESET_ALL,
        #     flush=True,
        # )

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
        # print(f"⚠️ Skipped invalid word: '{word}'", flush=True)
        return

    normalized, *_ = normalize_word(word)
    if seen is not None:
        if normalized in seen:
            # print(f"🔁 Skipping already reviewed word '{normalized}'", flush=True)
            return
        seen.add(normalized)

    # print(f"\n🔁 Reviewing word '{normalized}' for user '{username}' with quality={quality}", flush=True)

    row = select_one(
        "vocab_log",
        columns=["ef", "repetitions", "interval_days"],
        where="username = ? AND vocab = ?",
        params=(username, normalized),
    )

    if not row:
        # print(f"📘 No prior record found for '{normalized}'. Initializing new entry...", flush=True)
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
        # print(f"📂 Retrieved from DB → EF: {ef}, Repetitions: {reps}, Interval: {interval} day(s)", flush=True)

    # Apply SM2 algorithm
    ef, reps, interval = sm2(quality, ef, reps, interval)
    # print(f"📊 After SM2 → New EF: {ef:.2f}, Repetitions: {reps}, New Interval: {interval} day(s)", flush=True)

    # Compute next due date
    next_review = (datetime.now() + timedelta(days=interval)).isoformat()
    # print(f"📅 Next review due on: {next_review}", flush=True)

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

    # print(f"✅ Vocab log updated for '{normalized}'", flush=True)
