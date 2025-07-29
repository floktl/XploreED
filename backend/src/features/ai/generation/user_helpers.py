"""Helper functions for user-related routes."""

import datetime
from core.database.connection import select_rows, select_one, update_row
from features.ai.memory.spaced_repetition import sm2

VOCAB_COLUMNS = [
    "rowid as id",
    "vocab",
    "translation",
    "word_type",
    "article",
    "details",
    "next_review",
    "last_review",
    "context",
    "exercise",
]

TRAIN_COLUMNS = ["rowid as id", "vocab", "translation", "word_type", "article"]


def fetch_vocab_entries(user: str) -> list:
    """Return all vocabulary entries for the given user."""
    rows = select_rows(
        "vocab_log",
        columns=VOCAB_COLUMNS,
        where="username = ?",
        params=(user,),
        order_by="datetime(next_review) ASC",
    )
    return [dict(row) for row in rows] if rows else []


def select_vocab_word_due_for_review(user: str):
    """Return the next vocab word the user should review."""
    return select_one(
        "vocab_log",
        columns=TRAIN_COLUMNS,
        where="username = ? AND datetime(next_review) <= datetime('now')",
        params=(user,),
        order_by="next_review ASC",
    )


def update_vocab_after_review(rowid: int, user: str, quality: int) -> bool:
    """Update spaced repetition values after a review."""
    row = select_one(
        "vocab_log",
        columns=["ef", "repetitions", "interval_days"],
        where="rowid = ? AND username = ?",
        params=(rowid, user),
    )
    if not row:
        return False

    ef, reps, interval = row.get("ef", 2.5), row.get("repetitions", 0), row.get("interval_days", 1)
    ef, reps, interval = sm2(quality, ef, reps, interval)

    next_review = (
        datetime.datetime.now() + datetime.timedelta(days=interval)
    ).isoformat()

    update_row(
        "vocab_log",
        {
            "ef": ef,
            "repetitions": reps,
            "interval_days": interval,
            "next_review": next_review,
        },
        "rowid = ? AND username = ?",
        (rowid, user),
    )
    return True
