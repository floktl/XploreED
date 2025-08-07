"""
XplorED - Vocabulary Memory Module

This module provides vocabulary memory and spaced repetition functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Vocabulary Memory Components:
- Word Analysis: AI-powered German word analysis and translation
- Vocabulary Management: Save, retrieve, and manage vocabulary entries
- Spaced Repetition: Implement spaced repetition for vocabulary learning
- Word Processing: Normalize and process German words and articles

For detailed architecture information, see: docs/backend_structure.md
"""

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple
from features.ai.prompts import analyze_word_prompt, translate_sentence_prompt, translate_word_prompt
from core.database.connection import update_row, select_one, fetch_one, insert_row, select_rows
from features.spaced_repetition import sm2
from external.mistral.client import send_prompt
from features.ai.memory.logger import topic_memory_logger
from shared.text_utils import _extract_json
from shared.exceptions import DatabaseError, AIEvaluationError


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


def analyze_word_ai(word: str) -> Optional[dict]:
    """Return analysis data for a German word using Mistral."""
    if not word:
        return None

    user_prompt = analyze_word_prompt(word)
    # print(f"\033[92m[MISTRAL CALL] analyze_word_ai\033[0m", flush=True)

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
    except AIEvaluationError:
        raise
    except Exception as e:
        print("Error in analyze_word_ai:", e)
        raise AIEvaluationError(f"Error in analyze_word_ai: {str(e)}")

    # Fallback: try simple translation
    try:
        trans_prompt = translate_word_prompt(word)
        resp = send_prompt(
            "You are a helpful German translator.",
            trans_prompt,
            temperature=0.1,
        )
        if resp.status_code == 200:
            translation = resp.json()["choices"][0]["message"]["content"].strip()
            return {
                "base_form": word,
                "type": "unknown",
                "article": None,
                "translation": translation,
                "info": "Fallback translation",
            }
    except AIEvaluationError:
        raise
    except Exception as e:
        print("Error in fallback translation:", e)
        raise AIEvaluationError(f"Error in fallback translation: {str(e)}")

    return None


def split_and_clean(text: str) -> list[str]:
    """Split a text into lowercase word tokens."""
    return re.findall(r"[A-Za-zÄÖÜäöüß]+", text)


def extract_words(text: str) -> list[tuple[str, Optional[str]]]:
    """Return a list of (word, article) tuples from a German text."""
    # print("\033[95m📖 [TOPIC MEMORY FLOW] 📖 Starting extract_words for text: '{}'\033[0m".format(text[:50] + "..." if len(text) > 50 else text), flush=True)

    tokens = re.findall(r"[A-Za-zÄÖÜäöüß]+", text)
    # print("\033[94m🔤 [TOPIC MEMORY FLOW] 🔤 Found {} tokens: {}\033[0m".format(len(tokens), tokens), flush=True)

    result: list[tuple[str, Optional[str]]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        lower = tok.lower()
        # print("\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Processing token {}: '{}' (lower: '{}')\033[0m".format(i, tok, lower), flush=True)

        if lower in ARTICLES and i + 1 < len(tokens):
            # Attach the article to the following token regardless of
            # capitalization. This helps when users do not capitalize nouns.
            next_tok = tokens[i + 1]
            # print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Found article '{}' attached to '{}'\033[0m".format(lower, next_tok), flush=True)
            result.append((next_tok, lower))
            i += 2
            continue
        # print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Adding word '{}' without article\033[0m".format(tok), flush=True)
        result.append((tok, None))
        i += 1

    # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Extracted {} word-article pairs: {}\033[0m".format(len(result), result), flush=True)
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
    # print("\033[95m💾 [TOPIC MEMORY FLOW] 💾 Starting save_vocab for user: {} word: '{}' article: '{}'\033[0m".format(username, german_word, article), flush=True)

    if german_word in ["?", "!", ",", "."]:
        # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Skipping punctuation: '{}'\033[0m".format(german_word), flush=True)
        return None

    lower_word = german_word.lower()
    # print("\033[94m📝 [TOPIC MEMORY FLOW] 📝 Lowercase word: '{}'\033[0m".format(lower_word), flush=True)

    if lower_word in ENGLISH_ARTICLES:
        # print("\033[93m📚 [TOPIC MEMORY FLOW] 📚 Processing English article: '{}'\033[0m".format(lower_word), flush=True)
        normalized = ENGLISH_ARTICLES[lower_word]
        word_type = "article"
        english_word = lower_word
        details = None
        # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Normalized English article: '{}' -> '{}'\033[0m".format(lower_word, normalized), flush=True)
    else:
        # print("\033[93m🔍 [TOPIC MEMORY FLOW] 🔍 Processing German word: '{}'\033[0m".format(german_word), flush=True)
        # Early normalization for existence check
        norm_check, *_ = normalize_word(german_word, article)
        # print("\033[94m📝 [TOPIC MEMORY FLOW] 📝 Normalized for existence check: '{}'\033[0m".format(norm_check), flush=True)

        if vocab_exists(username, norm_check):
            # print("\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ Word '{}' already exists for user {}\033[0m".format(norm_check, username), flush=True)
            return norm_check

        # AI analysis only needed if word is new
        # print("\033[96m🤖 [TOPIC MEMORY FLOW] 🤖 Analyzing word with AI: '{}'\033[0m".format(german_word), flush=True)
        analysis = analyze_word_ai(german_word)
        if analysis:
            normalized = analysis.get("base_form", german_word)
            word_type = analysis.get("type", "other")
            article = analysis.get("article") or article
            english_word = analysis.get("translation", "")
            details = analysis.get("info")
            # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ AI analysis successful - Type: {} Translation: '{}'\033[0m".format(word_type, english_word), flush=True)

            if word_type == "noun":
                normalized = _singularize(normalized.capitalize())
                # print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Singularized noun: '{}'\033[0m".format(normalized), flush=True)
            else:
                normalized = normalized.lower()
        else:
            # print("\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ AI analysis failed, using fallback normalization\033[0m", flush=True)
            normalized, word_type, _ = normalize_word(german_word, article)
            english_word = ""
            details = None

    # Avoid saving invalid forms like 'Freundi' (unless valid endings)
    valid_i_endings = ("ei", "ie", "ai", "oi", "ui")
    if normalized.endswith("i") and not normalized.endswith(valid_i_endings):
        # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Skipping invalid form ending in 'i': '{}'\033[0m".format(normalized), flush=True)
        return None

    # Check again after potential AI normalization
    if vocab_exists(username, normalized):
        # print("\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ Normalized word '{}' already exists for user {}\033[0m".format(normalized, username), flush=True)
        return normalized

    now = datetime.now().isoformat()
    # print("\033[96m💾 [TOPIC MEMORY FLOW] 💾 Inserting new vocab entry into database\033[0m", flush=True)
    try:
        insert_row(
            "vocab_log",
            {
                "username": username,
                "vocab": normalized,
                "translation": english_word,
                "word_type": word_type,
                "article": article,
                "details": json.dumps(details) if details else None,
                "context": context,
                "exercise": exercise,
                "next_review": now,
                "created_at": now,
                "last_review": now,
            },
        )
        # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully saved vocab word '{}' to database\033[0m".format(normalized), flush=True)
    except DatabaseError:
        raise
    except Exception as e:
        # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Failed to save vocab word '{}': {}\033[0m".format(normalized, str(e)), flush=True)
        raise DatabaseError(f"Failed to save vocab word '{normalized}': {str(e)}")

    return normalized


def translate_to_german(english_sentence: str, username: Optional[str] = None) -> str:
    """Translate an English sentence using Mistral AI and optionally store vocab."""

    import logging
    logger = logging.getLogger(__name__)

    logger.info(f"🔤 [TRANSLATE] Starting translation for: '{english_sentence}'")

    user_prompt = translate_sentence_prompt(english_sentence)
    logger.info(f"🔤 [TRANSLATE] Created prompt: {user_prompt}")

    try:
        logger.info(f"🔤 [TRANSLATE] About to call send_prompt with Mistral...")
        resp = send_prompt(
            "You are a helpful German translator.",
            user_prompt,
            temperature=0.3,
        )
        logger.info(f"🔤 [TRANSLATE] send_prompt returned with status: {resp.status_code}")

        if resp.status_code == 200:
            logger.info(f"🔤 [TRANSLATE] Parsing response JSON...")
            german_text = resp.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"🔤 [TRANSLATE] Got German translation: '{german_text}'")

            if username:
                # Skip vocabulary saving for very short inputs or explanatory responses
                if len(english_sentence.strip()) <= 2:
                    logger.info(f"🔤 [TRANSLATE] Skipping vocabulary saving for very short input: '{english_sentence}'")
                elif "kann" in german_text.lower() and "übersetzt" in german_text.lower():
                    logger.info(f"🔤 [TRANSLATE] Skipping vocabulary saving for explanatory response")
                else:
                    logger.info(f"🔤 [TRANSLATE] Extracting words for vocabulary...")
                    word_count = 0
                    max_words = 5  # Limit to prevent hanging on long responses
                    
                    for word, art in extract_words(german_text):
                        if word_count >= max_words:
                            logger.info(f"🔤 [TRANSLATE] Reached max word limit ({max_words}), stopping vocabulary extraction")
                            break
                            
                        logger.info(f"🔤 [TRANSLATE] Saving vocab word: '{word}' with article: '{art}'")
                        save_vocab(
                            username,
                            word,
                            context=german_text,
                            exercise="translation",
                            article=art,
                        )
                        word_count += 1
                        
                    logger.info(f"🔤 [TRANSLATE] Finished saving vocabulary words (saved {word_count} words)")

            logger.info(f"🔤 [TRANSLATE] Returning translation: '{german_text}'")
            return german_text
        else:
            logger.error(f"🔤 [TRANSLATE] Mistral API returned non-200 status: {resp.status_code}")
            return "❌ API failure - non-200 status"

    except AIEvaluationError:
        logger.error(f"🔤 [TRANSLATE] AIEvaluationError caught")
        raise
    except Exception as e:
        logger.error(f"🔤 [TRANSLATE] Exception caught: {e}")
        import traceback
        logger.error(f"🔤 [TRANSLATE] Full traceback: {traceback.format_exc()}")
        print("❌ Error calling Mistral:", e)
        raise AIEvaluationError(f"Error calling Mistral: {str(e)}")

    logger.error(f"🔤 [TRANSLATE] Reached end of function, returning API failure")
    return "❌ API failure"


def review_vocab_word(
    username: str,
    word: str,
    quality: int,
    seen: Optional[set[str]] = None,
) -> None:
    """Update spaced repetition data for a vocab word using SM2."""
    # print("\033[95m🔤 [TOPIC MEMORY FLOW] 🔤 Starting review_vocab_word for user: {} word: '{}' quality: {}\033[0m".format(username, word, quality), flush=True)

    if not word or not word.isalpha():
        # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Skipping non-alphabetic word: '{}'\033[0m".format(word), flush=True)
        return

    # print("\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Normalizing word: '{}'\033[0m".format(word), flush=True)
    normalized, *_ = normalize_word(word)
    # print("\033[93m📝 [TOPIC MEMORY FLOW] 📝 Normalized word: '{}' -> '{}'\033[0m".format(word, normalized), flush=True)

    if seen is not None:
        if normalized in seen:
            # print("\033[91m⚠️ [TOPIC MEMORY FLOW] ⚠️ Word '{}' already reviewed in this session, skipping\033[0m".format(normalized), flush=True)
            return
        seen.add(normalized)
        # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Added '{}' to reviewed set\033[0m".format(normalized), flush=True)

    # print("\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Checking for existing vocab entry in database\033[0m", flush=True)
    row = select_one(
        "vocab_log",
        columns=["ef", "repetitions", "interval_days"],
        where="username = ? AND vocab = ?",
        params=(username, normalized),
    )

    if not row:
        # print("\033[93m🆕 [TOPIC MEMORY FLOW] 🆕 No existing vocab entry found, creating new entry\033[0m", flush=True)
        saved = save_vocab(username, word, exercise="ai")
        if saved:
            normalized = saved
            # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully saved new vocab word: '{}'\033[0m".format(saved), flush=True)
        else:
            # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Failed to save vocab word: '{}'\033[0m".format(word), flush=True)
            return

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
            # print("\033[94m📊 [TOPIC MEMORY FLOW] 📊 Retrieved new entry values - EF: {} Reps: {} Interval: {}\033[0m".format(ef, reps, interval), flush=True)
        else:
            ef = 2.5
            reps = 0
            interval = 1
            # print("\033[94m📊 [TOPIC MEMORY FLOW] 📊 Using default values - EF: {} Reps: {} Interval: {}\033[0m".format(ef, reps, interval), flush=True)

        # 🔥 ADD THIS: Log the new vocabulary entry
        # print(f"🔧 [LOGGER DEBUG] 🔧 About to call topic_memory_logger.log_vocabulary_update for new entry", flush=True)
        topic_memory_logger.log_vocabulary_update(
            username=username,
            word=word,
            quality=quality,
            is_new=True,
            new_values={
                "ease_factor": ef,
                "repetitions": reps,
                "interval": interval
            }
        )
        # print(f"🔧 [LOGGER DEBUG] 🔧 Called topic_memory_logger.log_vocabulary_update for new entry successfully", flush=True)
    else:
        ef = row.get("ef", 2.5)
        reps = row.get("repetitions", 0)
        interval = row.get("interval_days", 1)
        # print("\033[94m📊 [TOPIC MEMORY FLOW] 📊 Retrieved existing values - EF: {} Reps: {} Interval: {}\033[0m".format(ef, reps, interval), flush=True)

        # Store old values for logging
        old_values = {
            "ease_factor": ef,
            "repetitions": reps,
            "interval": interval
        }

    # print("\033[96m🧮 [TOPIC MEMORY FLOW] 🧮 Applying SM2 algorithm with quality: {}\033[0m".format(quality), flush=True)
    # Apply SM2 algorithm
    ef, reps, interval = sm2(quality, ef, reps, interval)
    # print("\033[92m📈 [TOPIC MEMORY FLOW] 📈 SM2 calculated new values - EF: {} Reps: {} Interval: {}\033[0m".format(ef, reps, interval), flush=True)

    # Compute next due date
    next_review = (datetime.now() + timedelta(days=interval)).isoformat()
    # print("\033[93m📅 [TOPIC MEMORY FLOW] 📅 Next review date: {}\033[0m".format(next_review), flush=True)

    # print("\033[96m💾 [TOPIC MEMORY FLOW] 💾 Updating vocab_log with new spaced repetition data\033[0m", flush=True)
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
    # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully updated vocab word '{}' with new spaced repetition data\033[0m".format(normalized), flush=True)

    # 🔥 ADD THIS: Log the vocabulary update for existing entries
    if 'old_values' in locals():
        # print(f"🔧 [LOGGER DEBUG] 🔧 About to call topic_memory_logger.log_vocabulary_update for existing entry", flush=True)
        topic_memory_logger.log_vocabulary_update(
            username=username,
            word=word,
            quality=quality,
            is_new=False,
            old_values=old_values,
            new_values={
                "ease_factor": ef,
                "repetitions": reps,
                "interval": interval
            }
        )
        # print(f"🔧 [LOGGER DEBUG] 🔧 Called topic_memory_logger.log_vocabulary_update for existing entry successfully", flush=True)


def get_user_vocab_stats(username: str) -> dict:
    """
    Get vocabulary statistics for a user.

    Args:
        username: The username to get stats for

    Returns:
        Dictionary containing vocabulary statistics
    """
    try:
        # Get total vocabulary count
        total_result = select_rows(
            "vocab_log",
            columns=["COUNT(*) as total_count"],
            where="username = ?",
            params=(username,)
        )

        # Get mastered vocabulary count (words with high ease factor and repetitions)
        mastered_result = select_rows(
            "vocab_log",
            columns=["COUNT(*) as mastered_count"],
            where="username = ? AND ef >= 2.5 AND repetitions >= 3",
            params=(username,)
        )

        total_count = total_result[0].get('total_count', 0) if total_result else 0
        mastered_count = mastered_result[0].get('mastered_count', 0) if mastered_result else 0

        return {
            'total_count': total_count,
            'mastered_count': mastered_count,
            'learning_count': total_count - mastered_count
        }

    except DatabaseError:
        raise
    except Exception as e:
        print(f"Error getting vocab stats for user {username}: {e}")
        raise DatabaseError(f"Error getting vocab stats for user {username}: {str(e)}")
