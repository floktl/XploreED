import re

NOM_ARTICLES = {"der", "die", "das", "ein", "eine"}
ACC_ARTICLES = {"den", "die", "das", "einen", "eine"}
DAT_ARTICLES = {"dem", "der", "den", "einem", "einer"}
GEN_ARTICLES = {"des", "der", "den", "eines", "einer"}

ACC_PREPS = {"durch", "für", "gegen", "ohne", "um"}
DAT_PREPS = {"aus", "bei", "mit", "nach", "seit", "von", "zu"}
GEN_PREPS = {"während", "trotz", "wegen", "statt"}


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

PRONOUNS = {
    "ich",
    "du",
    "er",
    "sie",
    "es",
    "wir",
    "ihr",
    "sie",
    "sie"  # formal Sie lowercased
}

SEIN_FORMS = {
    "bin",
    "bist",
    "ist",
    "sind",
    "seid",
    "war",
    "warst",
    "wart",
    "waren",
    "gewesen",
}

MODAL_VERB_FORMS = {
    "dürfen",
    "darf",
    "darfst",
    "dürft",
    "dürfen",
    "können",
    "kann",
    "kannst",
    "könnt",
    "mögen",
    "mag",
    "magst",
    "mögt",
    "müssen",
    "muss",
    "musst",
    "müsst",
    "sollen",
    "soll",
    "sollst",
    "sollt",
    "wollen",
    "will",
    "willst",
    "wollt",
}


def detect_language_topics(text: str) -> list[str]:
    """Return a list of language features found in the text."""
    tokens = re.findall(r"\b\w+\b", text.lower())
    features = set()

    case = detect_grammar_case(text)
    if case != "unknown":
        features.add(f"case:{case}")

    if any(tok in SEIN_FORMS for tok in tokens):
        features.add("sein")

    if any(tok in MODAL_VERB_FORMS for tok in tokens):
        features.add("modal verb")

    if any(tok in PRONOUNS for tok in tokens):
        features.add("pronoun")

    return sorted(features)


__all__ = ["detect_grammar_case", "detect_language_topics"]
