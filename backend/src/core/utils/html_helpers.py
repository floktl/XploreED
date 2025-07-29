"""HTML helpers for parsing lesson content."""

import re
from bs4 import BeautifulSoup #type: ignore
import sqlite3
from core.database.connection import get_connection


def clean_html(raw_html: str) -> str:
    """Remove wrappers and style blocks from HTML text."""
    if raw_html.startswith("```html"):
        raw_html = raw_html.replace("```html", "").strip()
    if raw_html.endswith("```"):
        raw_html = raw_html[:-3].strip()
    raw_html = re.sub(r"<style[\s\S]*?</style>", "", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"</?(html|head|body|meta|title)[^>]*>", "", raw_html, flags=re.IGNORECASE)
    return raw_html.strip()

def update_lesson_blocks_from_html(lesson_id, html):
    """Store all ``data-block-id`` values for ``lesson_id`` in the DB."""
    soup = BeautifulSoup(html, "html.parser")
    block_ids = set()

    for block in soup.select('[data-block-id]'):
        block_id = block.get("data-block-id")
        if block_id:
            block_ids.add(block_id)
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,))

        for block_id in block_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id) VALUES (?, ?)",
                (lesson_id, block_id)
            )

        conn.commit()


def inject_block_ids(html):
    """Insert numeric ``data-block-id`` attributes into lesson HTML."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select(".interactive-block")

    for i, block in enumerate(blocks):
        block['data-block-id'] = f"block-{i}"

    result = str(soup)
    return result


def strip_ai_data(html: str) -> str:
    """Remove encoded AI exercise payloads before storing."""
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select('[data-ai-exercise]'):
        if 'data-ai-data' in el.attrs:
            del el['data-ai-data']
    return str(soup)


def ansi_to_html(text: str) -> str:
    """Convert ANSI color codes to HTML spans."""
    return (
        text.replace("\x1b[31m", '<span style="color:red;">')
        .replace("\x1b[32m", '<span style="color:green;">')
        .replace("\x1b[33m", '<span style="color:orange;">')
        .replace("\x1b[0m", "</span>")
    )
