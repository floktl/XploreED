# utils/repair_blocks.py
"""Script fixing broken lesson block references in the database."""

import sqlite3
from bs4 import BeautifulSoup

print("🔧 Repairing lesson_blocks...")

with get_connection() as conn:
    cursor = conn.cursor()
    lessons = cursor.execute("SELECT lesson_id, content FROM lesson_content").fetchall()

    for lesson_id, html in lessons:
        soup = BeautifulSoup(html, "html.parser")
        block_ids = {el["data-block-id"] for el in soup.select('[data-block-id]') if el.has_attr("data-block-id")}

        for block_id in block_ids:
            cursor.execute("""
                INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id)
                VALUES (?, ?)
            """, (lesson_id, block_id))

    conn.commit()
