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
    print("[_extract_json] Raw input:", text, flush=True)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                print("[_extract_json] Failed to parse matched JSON.", flush=True)
                pass
    print("[_extract_json] Returning None.", flush=True)
    return None

def detect_grammar_case(text: str) -> str:
    print("[detect_grammar_case] Input text:", text, flush=True)
    tokens = re.findall(r"\b\w+\b", text.lower())
    print("[detect_grammar_case] Tokens:", tokens, flush=True)
    for tok in tokens:
        if tok in GEN_PREPS or tok in GEN_ARTICLES:
            print("[detect_grammar_case] Matched genitive:", tok, flush=True)
            return "genitive"
    for tok in tokens:
        if tok in DAT_PREPS or tok in DAT_ARTICLES:
            print("[detect_grammar_case] Matched dative:", tok, flush=True)
            return "dative"
    for tok in tokens:
        if tok in ACC_PREPS or tok in ACC_ARTICLES:
            print("[detect_grammar_case] Matched accusative:", tok, flush=True)
            return "accusative"
    for tok in tokens:
        if tok in NOM_ARTICLES:
            print("[detect_grammar_case] Matched nominative:", tok, flush=True)
            return "nominative"
    print("[detect_grammar_case] Case unknown.", flush=True)
    return "unknown"

def detect_language_topics(text: str) -> list[str]:
    # print("[detect_language_topics] 🔍 Input:", text, flush=True)

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
        # print("[detect_language_topics] ✅ Mistral response received.", flush=True)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            # print("[detect_language_topics] 📦 Raw Mistral output:", content, flush=True)
            topics = _extract_json(content)
            if isinstance(topics, list):
                cleaned = [t.strip().lower() for t in topics if isinstance(t, str)]
                # print("[detect_language_topics] ✅ Parsed grammar topics:", cleaned, flush=True)
                return sorted(set(cleaned))
    except Exception as e:
        print("[detect_language_topics] ⚠️ Mistral topic detection failed:", e, flush=True)

    # print("[detect_language_topics] 🔁 Falling back to rule-based detection...", flush=True)
    return _rule_based_detection(text)

def _rule_based_detection(text: str) -> list[str]:
    print("[_rule_based_detection] Fallback triggered for:", text, flush=True)
    tokens = re.findall(r"\b\w+\b", text.lower())
    print("[_rule_based_detection] Tokens:", tokens, flush=True)
    features = set()

    case = detect_grammar_case(text)
    print("[_rule_based_detection] Detected case:", case, flush=True)
    if case != "unknown":
        features.add(f"case:{case}")

    checks = [
        (SEIN_FORMS, "sein"),
        (HABEN_FORMS, "haben auxiliary"),
        (WERDEN_FORMS, "werden auxiliary"),
        (REFLEXIVE_PRONOUNS, "reflexive pronoun"),
        (POSSESSIVE_PRONOUNS, "possessive pronoun"),
        (DIRECT_OBJ_PRONOUNS, "accusative pronoun"),
        (INDIRECT_OBJ_PRONOUNS, "dative pronoun"),
        (NEGATION_WORDS, "negation"),
        (QUESTION_WORDS, "question word"),
        (INTERJECTIONS, "interjection"),
        (COORD_CONJUNCTIONS, "coordinating conjunction"),
        (TWO_WAY_PREPS, "two-way preposition"),
        (TIME_PREPS, "time preposition"),
        (CONTRACTIONS, "contraction"),
        (PAST_SIMPLE_STRONG, "simple past strong"),
        (SUBJUNCTIVE_FORMS, "subjunctive"),
        (MODAL_VERB_FORMS, "modal verb"),
        (SUB_CONJUNCTIONS, "subordinating conjunction"),
        (PRONOUNS, "pronoun")
    ]

    for wordlist, label in checks:
        if any(tok in wordlist for tok in tokens):
            print(f"[_rule_based_detection] Matched {label}.", flush=True)
            features.add(label)

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
    if any(tok.startswith(prefix) and len(tok) > len(prefix) + 2 for tok in tokens for prefix in SEPARABLE_PREFIXES):
        features.add("separable prefix verb")
    if any(tok.startswith(prefix) and len(tok) > len(prefix) + 2 for tok in tokens for prefix in INSEPARABLE_PREFIXES):
        features.add("inseparable prefix verb")
    for i, tok in enumerate(tokens[:-1]):
        if tok == "zu" and tokens[i + 1].endswith("en"):
            features.add("infinitive clause")
    if any(ORDINAL_RE.match(tok) for tok in tokens):
        features.add("ordinal number")

    print("[_rule_based_detection] Final detected features:", features, flush=True)
    return sorted(features)

__all__ = ["detect_grammar_case", "detect_language_topics"]
