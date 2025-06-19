import os
import re
import json
import requests

# existing rules kept for fallback
from utils.grammar_templates import (
    NOM_ARTICLES, ACC_ARTICLES, DAT_ARTICLES, GEN_ARTICLES,
    ACC_PREPS, DAT_PREPS, GEN_PREPS, SEIN_FORMS, HABEN_FORMS, WERDEN_FORMS,
    REFLEXIVE_PRONOUNS, POSSESSIVE_PRONOUNS, DIRECT_OBJ_PRONOUNS, INDIRECT_OBJ_PRONOUNS,
    NEGATION_WORDS, QUESTION_WORDS, INTERJECTIONS, COORD_CONJUNCTIONS, TWO_WAY_PREPS,
    TIME_PREPS, SEPARABLE_PREFIXES, INSEPARABLE_PREFIXES, CONTRACTIONS, PAST_SIMPLE_STRONG,
    SUBJUNCTIVE_FORMS, ORDINAL_RE, COMPARATIVE_TRIGGERS, MODAL_VERB_FORMS, SUB_CONJUNCTIONS,
    PRONOUNS
)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {MISTRAL_API_KEY}",
    "Content-Type": "application/json",
}


def _extract_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def detect_grammar_case(text: str) -> str:
    """Guess the grammar case based on articles and prepositions."""
    tokens = re.findall(r"\b\w+\b", text.lower())
    for tok in tokens:
        if tok in GEN_PREPS or tok in GEN_ARTICLES:
            return "genitive"
    for tok in tokens:
        if tok in DAT_PREPS or tok in DAT_ARTICLES:
            return "dative"
    for tok in tokens:
        if tok in ACC_PREPS or tok in ACC_ARTICLES:
            return "accusative"
    for tok in tokens:
        if tok in NOM_ARTICLES:
            return "nominative"
    return "unknown"


def detect_language_topics(text: str) -> list[str]:
    """Return a list of grammar topics used in the sentence using Mistral AI."""
    print("🔍 detect_language_topics input:", text, flush=True)

    user_prompt = {
        "role": "user",
        "content": f"""
You are a helpful German teacher. Identify grammar topics used in the following sentence:

"{text}"

Return only a JSON list of strings such as:
["modal verb", "pronoun", "subordinating conjunction"]
""",
    }

    payload = {
        "model": "mistral-medium",
        "messages": [
            {"role": "system", "content": "You are a helpful German teacher."},
            user_prompt,
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(MISTRAL_API_URL, headers=HEADERS, json=payload, timeout=10)
        print("✅ Mistral response received for grammar topics.", flush=True)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            print("📦 Raw Mistral output:", content, flush=True)
            topics = _extract_json(content)
            if isinstance(topics, list):
                cleaned = [t.strip().lower() for t in topics if isinstance(t, str)]
                print("✅ Parsed grammar topics:", cleaned, flush=True)
                return sorted(set(cleaned))
    except Exception as e:
        print("⚠️ Mistral topic detection failed:", e, flush=True)

    # fallback if Mistral fails
    print("🔁 Falling back to rule-based detection...", flush=True)
    return _rule_based_detection(text)


def _rule_based_detection(text: str) -> list[str]:
    tokens = re.findall(r"\b\w+\b", text.lower())
    features = set()

    case = detect_grammar_case(text)
    if case != "unknown":
        features.add(f"case:{case}")

    if any(tok in SEIN_FORMS for tok in tokens):
        features.add("sein")
    if any(tok in HABEN_FORMS for tok in tokens):
        features.add("haben auxiliary")
    if any(tok in WERDEN_FORMS for tok in tokens):
        features.add("werden auxiliary")
    if any(tok in REFLEXIVE_PRONOUNS for tok in tokens):
        features.add("reflexive pronoun")
    if any(tok in POSSESSIVE_PRONOUNS for tok in tokens):
        features.add("possessive pronoun")
    if any(tok in DIRECT_OBJ_PRONOUNS for tok in tokens):
        features.add("accusative pronoun")
    if any(tok in INDIRECT_OBJ_PRONOUNS for tok in tokens):
        features.add("dative pronoun")
    if any(tok in NEGATION_WORDS for tok in tokens):
        features.add("negation")
    if any(tok in QUESTION_WORDS for tok in tokens):
        features.add("question word")
    if any(tok in INTERJECTIONS for tok in tokens):
        features.add("interjection")
    if any(tok in COORD_CONJUNCTIONS for tok in tokens):
        features.add("coordinating conjunction")
    if any(tok in TWO_WAY_PREPS for tok in tokens):
        features.add("two-way preposition")
    if any(tok in TIME_PREPS for tok in tokens):
        features.add("time preposition")
    if any(tok in CONTRACTIONS for tok in tokens):
        features.add("contraction")
    if any(tok in PAST_SIMPLE_STRONG for tok in tokens):
        features.add("simple past strong")
    if any(re.match(r".+te$", tok) for tok in tokens):
        features.add("simple past weak")
    if any(tok in SUBJUNCTIVE_FORMS for tok in tokens):
        features.add("subjunctive")
    if any(tok in MODAL_VERB_FORMS for tok in tokens):
        features.add("modal verb")
    if any(tok in SUB_CONJUNCTIONS for tok in tokens):
        features.add("subordinating conjunction")
    if any(tok in PRONOUNS for tok in tokens):
        features.add("pronoun")
    if "!" in text:
        features.add("imperative")
    if "?" in text:
        features.add("question")
    if any(tok.endswith("ste") or tok.endswith("sten") for tok in tokens):
        features.add("superlative")
    if any(tok.endswith("er") and "als" in tokens for tok in tokens):
        features.add("comparative")
    if any(re.match(r"ge\w+(t|en)$", tok) for tok in tokens):
        features.add("past participle")
    if any(
        tok.startswith(prefix) and len(tok) > len(prefix) + 2
        for tok in tokens
        for prefix in SEPARABLE_PREFIXES
    ):
        features.add("separable prefix verb")
    if any(
        tok.startswith(prefix) and len(tok) > len(prefix) + 2
        for tok in tokens
        for prefix in INSEPARABLE_PREFIXES
    ):
        features.add("inseparable prefix verb")
    for i, tok in enumerate(tokens[:-1]):
        if tok == "zu" and tokens[i + 1].endswith("en"):
            features.add("infinitive clause")
    if any(ORDINAL_RE.match(tok) for tok in tokens):
        features.add("ordinal number")

    return sorted(features)


__all__ = ["detect_grammar_case", "detect_language_topics"]
