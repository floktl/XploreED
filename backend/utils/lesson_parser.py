from bs4 import BeautifulSoup
import sqlite3
from .db_utils import get_connection

def update_lesson_blocks_from_html(lesson_id, html):
    soup = BeautifulSoup(html, "html.parser")
    block_ids = set()

    for block in soup.select('[data-block-id]'):
        block_id = block.get("data-block-id")
        if block_id:
            block_ids.add(block_id)

    with get_connection() as conn:
        cursor = conn.cursor()

        # Delete existing entries for this lesson
        cursor.execute("DELETE FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,))

        # Insert fresh block IDs
        for block_id in block_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id) VALUES (?, ?)",
                (lesson_id, block_id)
            )

        conn.commit()

    print(f"✅ Synced {len(block_ids)} blocks for lesson {lesson_id}")


def inject_block_ids(html):
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select('.interactive-block')
    for i, block in enumerate(blocks):
        block['data-block-id'] = f"block-{i}"
    return str(soup)