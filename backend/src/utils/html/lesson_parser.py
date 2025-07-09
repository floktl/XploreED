"""HTML helpers for parsing lesson content."""

from bs4 import BeautifulSoup
import sqlite3
from ..data.db_utils import get_connection

def update_lesson_blocks_from_html(lesson_id, html):

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
