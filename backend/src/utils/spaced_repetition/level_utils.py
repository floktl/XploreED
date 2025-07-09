"""Helpers for level progress tracking and initialization."""

import datetime
from database import select_rows, select_one, insert_row, update_row


# Mapping of numeric skill levels (0-10) to grammar topics that should be
# mastered for that level. These topics are simplified examples.
LEVEL_TOPICS: dict[int, list[str]] = {
    0: ["personal pronouns", "sein", "haben"],
    1: ["nominative case", "present tense", "question words"],
    2: ["accusative case", "modal verbs", "accusative prepositions"],
    3: ["dative case", "separable verbs", "perfekt tense"],
    4: ["subordinating conjunctions", "weil", "dass clauses"],
    5: ["reflexive verbs", "praeteritum", "adjective endings"],
    6: ["passive voice", "relative clauses", "indirect speech"],
    7: ["konjunktiv ii", "noun compounds", "advanced connectors"],
    8: ["participles", "advanced passive", "nominalisierung"],
    9: ["konjunktiv i", "advanced syntax", "complex sentences"],
    10: ["academic writing", "advanced idioms", "subordinate clauses"],
}


def initialize_topic_memory_for_level(username: str, level: int) -> None:
    """Insert placeholder topic memory rows for the given level."""
    topics = LEVEL_TOPICS.get(level, [])
    if not topics:
        return

    now = datetime.datetime.now().isoformat()
    for grammar in topics:
        existing = select_rows(
            "topic_memory",
            columns="id",
            where="username = ? AND grammar = ?",
            params=(username, grammar),
        )
        if existing:
            continue
        insert_row(
            "topic_memory",
            {
                "username": username,
                "grammar": grammar,
                "skill_type": "initial",
                "context": "signup",
                "lesson_content_id": None,
                "ease_factor": 2.5,
                "intervall": 0,
                "next_repeat": now,
                "repetitions": 0,
                "last_review": None,
                "correct": 0,
                "quality": 0,
            },
        )


def calculate_level_progress(username: str, level: int) -> float:
    """Return fraction of level topics answered correctly by the user."""
    topics = LEVEL_TOPICS.get(level, [])
    if not topics:
        return 0.0

    placeholders = ",".join(["?"] * len(topics))
    rows = select_rows(
        "topic_memory",
        columns="DISTINCT grammar",
        where=f"username = ? AND grammar IN ({placeholders}) AND quality >= 4",
        params=tuple([username] + topics),
    )
    count = len(rows) if rows else 0
    return count / len(topics)


def check_auto_level_up(username: str) -> bool:
    """Increase user's level if 90% of targets are correct."""
    row = fetch_one("users", "WHERE username = ?", (username,))
    if not row:
        return False
    level = row.get("skill_level", 0) or 0
    progress = calculate_level_progress(username, level)
    if progress >= 0.9 and level < 10:
        update_row(
            "users",
            {"skill_level": level + 1},
            "username = ?",
            (username,),
        )
        return True
    return False
