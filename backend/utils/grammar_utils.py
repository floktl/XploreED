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

HABEN_FORMS = {
    "habe",
    "hast",
    "hat",
    "haben",
    "habt",
    "hatte",
    "hattest",
    "hatten",
    "hattet",
    "gehabt",
}

WERDEN_FORMS = {
    "werde",
    "wirst",
    "wird",
    "werden",
    "werdet",
    "wurde",
    "wurden",
    "geworden",
}

REFLEXIVE_PRONOUNS = {
    "mich",
    "dich",
    "sich",
    "uns",
    "euch",
    "mir",
    "dir",
    "ihm",
    "ihr",
    "ihnen",
}

POSSESSIVE_PRONOUNS = {
    "mein",
    "dein",
    "sein",
    "ihr",
    "unser",
    "euer",
    "ihre",
    "meine",
    "deine",
    "seine",
    "unsere",
    "eure",
    "ihren",
    "meinen",
    "deinen",
    "seinen",
    "unseren",
    "euren",
}

DIRECT_OBJ_PRONOUNS = {"mich", "dich", "ihn", "sie", "es", "uns", "euch"}

INDIRECT_OBJ_PRONOUNS = {"mir", "dir", "ihm", "ihr", "uns", "euch", "ihnen"}

NEGATION_WORDS = {"nicht", "kein", "keine", "keinen", "keinem", "keiner", "keines"}

QUESTION_WORDS = {
    "wer",
    "was",
    "wo",
    "wann",
    "warum",
    "wie",
    "woher",
    "wohin",
    "wessen",
    "wem",
    "wen",
    "welche",
    "welcher",
    "welches",
    "welchen",
}

COORD_CONJUNCTIONS = {"und", "oder", "aber", "denn", "sondern", "doch"}

TWO_WAY_PREPS = {"an", "auf", "hinter", "in", "neben", "über", "unter", "vor", "zwischen"}

TIME_PREPS = {"seit", "vor", "nach", "bis", "ab"}

SEPARABLE_PREFIXES = {"ab", "an", "auf", "aus", "bei", "ein", "mit", "nach", "vor", "weg", "zu", "zurück", "her"}

INSEPARABLE_PREFIXES = {"be", "emp", "ent", "er", "ge", "miss", "ver", "zer"}

CONTRACTIONS = {"im", "am", "ans", "ins", "aufs", "vom", "zum", "zur", "beim", "vorm", "übers", "unterm", "hinterm"}

PAST_SIMPLE_STRONG = {"ging", "kam", "sah", "gab", "stand", "lag", "blieb", "fuhr", "fand", "war", "hatte", "wurde"}

SUBJUNCTIVE_FORMS = {
    "würde",
    "würdest",
    "würden",
    "würdet",
    "hätte",
    "hättest",
    "hätten",
    "hättet",
    "wäre",
    "wärest",
    "wären",
    "wäret",
    "könnte",
    "sollte",
    "müsste",
    "wollte",
}

INTERJECTIONS = {"ach", "oh", "hallo", "na"}

ORDINAL_RE = re.compile(r"\d+\.")

COMPARATIVE_TRIGGERS = {"mehr", "weniger"}

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

# Common subordinating conjunctions for simple topic detection
SUB_CONJUNCTIONS = {
    "weil",
    "obwohl",
    "dass",
    "wenn",
    "als",
    "bevor",
    "nachdem",
    "während",
    "damit",
    "falls",
    "sobald",
    "solange",
    "bis",
    "ob",
    "da",
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

    if any(tok in CONTRACTIONS for tok in tokens):
        features.add("contraction")

    if any(tok.endswith("chen") or tok.endswith("lein") for tok in tokens):
        features.add("diminutive")

    if any(tok in PAST_SIMPLE_STRONG for tok in tokens):
        features.add("simple past strong")

    if any(re.match(r".+te$", tok) for tok in tokens):
        features.add("simple past weak")

    if any(tok in SUBJUNCTIVE_FORMS for tok in tokens):
        features.add("subjunctive")

    if any(tok in WERDEN_FORMS for tok in tokens) and any(re.match(r"ge\w+(t|en)$", tok) for tok in tokens):
        features.add("passive voice")

    if any(re.match(r"ge\w+(t|en)$", tok) for tok in tokens):
        features.add("past participle")

    for i, tok in enumerate(tokens[:-1]):
        if tok == "zu" and tokens[i + 1].endswith("en"):
            features.add("infinitive clause")
            break

    if any(tok in COMPARATIVE_TRIGGERS for tok in tokens) or "als" in tokens:
        for tok in tokens:
            if tok.endswith("er") and len(tok) > 3:
                features.add("comparative")
                break

    if any(tok.endswith("ste") or tok.endswith("sten") for tok in tokens):
        features.add("superlative")

    if any(ORDINAL_RE.match(tok) for tok in tokens):
        features.add("ordinal number")

    if "!" in text:
        features.add("imperative")

    if "?" in text:
        features.add("question")

    if any(tok in MODAL_VERB_FORMS for tok in tokens):
        features.add("modal verb")

    if any(tok in SUB_CONJUNCTIONS for tok in tokens):
        features.add("subordinating conjunction")

    if any(tok in PRONOUNS for tok in tokens):
        features.add("pronoun")

    return sorted(features)


__all__ = ["detect_grammar_case", "detect_language_topics"]
