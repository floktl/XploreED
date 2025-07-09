import re

NOM_ARTICLES = {"der", "die", "das", "ein", "eine"}
ACC_ARTICLES = {"den", "die", "das", "einen", "eine"}
DAT_ARTICLES = {"dem", "der", "den", "einem", "einer"}
GEN_ARTICLES = {"des", "der", "den", "eines", "einer"}

ACC_PREPS = {"durch", "für", "gegen", "ohne", "um"}
DAT_PREPS = {"aus", "bei", "mit", "nach", "seit", "von", "zu"}
GEN_PREPS = {"während", "trotz", "wegen", "statt"}

PRONOUNS = {
    "ich", "du", "er", "sie", "es", "wir", "ihr", "sie", "sie"
}

HABEN_FORMS = {
    "habe", "hast", "hat", "haben", "habt",
    "hatte", "hattest", "hatten", "hattet", "gehabt"
}

WERDEN_FORMS = {
    "werde", "wirst", "wird", "werden", "werdet",
    "wurde", "wurden", "geworden"
}

REFLEXIVE_PRONOUNS = {
    "mich", "dich", "sich", "uns", "euch",
    "mir", "dir", "ihm", "ihr", "ihnen"
}

POSSESSIVE_PRONOUNS = {
    "mein", "dein", "sein", "ihr", "unser", "euer", "ihre",
    "meine", "deine", "seine", "unsere", "eure",
    "ihren", "meinen", "deinen", "seinen", "unseren", "euren"
}

DIRECT_OBJ_PRONOUNS = {"mich", "dich", "ihn", "sie", "es", "uns", "euch"}
INDIRECT_OBJ_PRONOUNS = {"mir", "dir", "ihm", "ihr", "uns", "euch", "ihnen"}

NEGATION_WORDS = {"nicht", "kein", "keine", "keinen", "keinem", "keiner", "keines"}

QUESTION_WORDS = {
    "wer", "was", "wo", "wann", "warum", "wie",
    "woher", "wohin", "wessen", "wem", "wen",
    "welche", "welcher", "welches", "welchen"
}

COORD_CONJUNCTIONS = {"und", "oder", "aber", "denn", "sondern", "doch"}

TWO_WAY_PREPS = {"an", "auf", "hinter", "in", "neben", "über", "unter", "vor", "zwischen"}

TIME_PREPS = {"seit", "vor", "nach", "bis", "ab"}

SEPARABLE_PREFIXES = {
    "ab", "an", "auf", "aus", "bei", "ein", "mit", "nach", "vor", "weg", "zu", "zurück", "her"
}

INSEPARABLE_PREFIXES = {
    "be", "emp", "ent", "er", "ge", "miss", "ver", "zer"
}

CONTRACTIONS = {
    "im", "am", "ans", "ins", "aufs", "vom", "zum", "zur",
    "beim", "vorm", "übers", "unterm", "hinterm"
}

PAST_SIMPLE_STRONG = {
    "ging", "kam", "sah", "gab", "stand", "lag", "blieb",
    "fuhr", "fand", "war", "hatte", "wurde"
}

SUBJUNCTIVE_FORMS = {
    "würde", "würdest", "würden", "würdet",
    "hätte", "hättest", "hätten", "hättet",
    "wäre", "wärest", "wären", "wäret",
    "könnte", "sollte", "müsste", "wollte"
}

INTERJECTIONS = {"ach", "oh", "hallo", "na"}

ORDINAL_RE = re.compile(r"\d+\.")

COMPARATIVE_TRIGGERS = {"mehr", "weniger"}

SEIN_FORMS = {
    "bin", "bist", "ist", "sind", "seid",
    "war", "warst", "wart", "waren", "gewesen"
}

MODAL_VERB_FORMS = {
    "dürfen", "darf", "darfst", "dürft", "dürfen",
    "können", "kann", "kannst", "könnt",
    "mögen", "mag", "magst", "mögt",
    "müssen", "muss", "musst", "müsst",
    "sollen", "soll", "sollst", "sollt",
    "wollen", "will", "willst", "wollt"
}

SUB_CONJUNCTIONS = {
    "weil", "obwohl", "dass", "wenn", "als", "bevor", "nachdem",
    "während", "damit", "falls", "sobald", "solange", "bis", "ob", "da"
}
