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

__all__ = ["detect_grammar_case"]
