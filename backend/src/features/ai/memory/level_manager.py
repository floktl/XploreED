"""
XplorED - Level Manager Module

This module provides level progress tracking and initialization functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Level Manager Components:
- Level Initialization: Initialize topic memory for user skill levels
- Progress Calculation: Calculate user progress through skill levels
- Auto Level Up: Automatically increase user levels based on performance
- Topic Management: Manage grammar topics for each skill level

For detailed architecture information, see: docs/backend_structure.md
"""

import datetime
from core.database.connection import (
    select_rows,
    insert_row,
    update_row,
    fetch_one,
    execute_query,
)


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
    # Defensive: ensure table and required columns exist (prod-safe)
    try:
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS topic_memory (
                username TEXT,
                grammar TEXT,
                topic TEXT,
                skill_type TEXT,
                context TEXT,
                ease_factor REAL,
                interval INTEGER,
                next_repeat DATETIME,
                repetitions INTEGER,
                last_review DATETIME,
                correct INTEGER DEFAULT 0,
                quality INTEGER DEFAULT 0
            );
            """
        )
        # Add critical columns if missing (especially 'interval')
        for col_name, col_def in (
            ("interval", "INTEGER"),
            ("next_repeat", "DATETIME"),
            ("repetitions", "INTEGER"),
            ("last_review", "DATETIME"),
            ("correct", "INTEGER DEFAULT 0"),
            ("quality", "INTEGER DEFAULT 0"),
            ("skill_type", "TEXT"),
            ("context", "TEXT"),
            ("ease_factor", "REAL"),
        ):
            execute_query(f"ALTER TABLE topic_memory ADD COLUMN {col_name} {col_def};")
    except Exception:
        # Ignore if columns already exist; we only need best-effort
        pass
    topics = LEVEL_TOPICS.get(level, [])
    if not topics:
        return

    now = datetime.datetime.now().isoformat()
    for topic in topics:
        # Legacy schema may not have an explicit id column; rely on existence check via COUNT(*)
        existing = select_rows(
            "topic_memory",
            columns="COUNT(*) as count",
            where="username = ? AND grammar = ?",
            params=(username, topic),
        )
        if existing and existing[0].get("count", 0) > 0:
            continue
        insert_row(
            "topic_memory",
            {
                "username": username,
                "grammar": topic,
                "skill_type": "level-up",
                "context": f"auto-level-up-{level}",
                "ease_factor": 2.5,
                "interval": 0,
                "next_repeat": now,
                "repetitions": 0,
                "last_review": now,
                "correct": 0,
                "quality": 3
            }
        )


def calculate_level_progress(username: str, level: int) -> float:
    """Return fraction of level topics answered correctly by the user."""
    # print("\033[95m📊 [TOPIC MEMORY FLOW] 📊 Starting calculate_level_progress for user: {} level: {}\033[0m".format(username, level), flush=True)

    topics = LEVEL_TOPICS.get(level, [])
    if not topics:
        print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ No topics defined for level {}\033[0m".format(level), flush=True)
        return 0.0

    # print("\033[94m📚 [TOPIC MEMORY FLOW] 📚 Level {} topics: {}\033[0m".format(level, topics), flush=True)

    placeholders = ",".join(["?"] * len(topics))
    # print("\033[96m🔍 [TOPIC MEMORY FLOW] 🔍 Querying topic_memory for proficient topics (quality >= 4)\033[0m", flush=True)

    rows = select_rows(
        "topic_memory",
        columns="DISTINCT grammar",
        where=f"username = ? AND grammar IN ({placeholders}) AND quality >= 4",
        params=tuple([username] + topics),
    )
    count = len(rows) if rows else 0
    progress = count / len(topics)

    # print("\033[93m📈 [TOPIC MEMORY FLOW] 📈 Found {} proficient topics out of {} total topics\033[0m".format(count, len(topics)), flush=True)
    # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Level progress: {:.1%}\033[0m".format(progress), flush=True)

    return progress


def check_auto_level_up(username: str) -> bool:
    """Increase user's level if 90% of targets are correct."""
    # print("\033[95m📈 [TOPIC MEMORY FLOW] 📈 Starting check_auto_level_up for user: {}\033[0m".format(username), flush=True)

    row = fetch_one("users", "WHERE username = ?", (username,))
    if not row:
        print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ User '{}' not found in database\033[0m".format(username), flush=True)
        return False

    level = row.get("skill_level", 0) or 0
    # print("\033[94m📊 [TOPIC MEMORY FLOW] 📊 Current user level: {}\033[0m".format(level), flush=True)

    progress = calculate_level_progress(username, level)
    # print("\033[93m📈 [TOPIC MEMORY FLOW] 📈 Level progress: {:.1%} (need 90% for advancement)\033[0m".format(progress), flush=True)

    if progress >= 0.9 and level < 10:
        # print("\033[92m🎉 [TOPIC MEMORY FLOW] 🎉 Level advancement criteria met! Advancing from level {} to {}\033[0m".format(level, level + 1), flush=True)
        update_row(
            "users",
            {"skill_level": level + 1},
            "username = ?",
            (username,),
        )
        # print("\033[92m✅ [TOPIC MEMORY FLOW] ✅ Successfully updated user level in database\033[0m", flush=True)
        return True
    else:
        if progress < 0.9:
            # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ Progress {:.1%} below 90% threshold - no advancement\033[0m".format(progress), flush=True)
            pass
        elif level >= 10:
            # print("\033[91m❌ [TOPIC MEMORY FLOW] ❌ User already at maximum level 10 - no advancement\033[0m", flush=True)
            pass
        return False
