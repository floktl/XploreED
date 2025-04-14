# utils/auto_fix_blocks.py
import sqlite3
from bs4 import BeautifulSoup

with get_connection() as conn:
    cursor = conn.cursor()
    lessons = cursor.execute("SELECT lesson_id, content FROM lesson_content").fetchall()

    for lesson_id, html in lessons:
        soup = BeautifulSoup(html, "html.parser")
        changed = False

        blocks = soup.select('.interactive-block')
        for i, div in enumerate(blocks):
            if not div.has_attr("data-block-id"):
                div["data-block-id"] = f"block-{i}"
                changed = True

        if changed:
            cursor.execute("""
                UPDATE lesson_content SET content = ? WHERE lesson_id = ?
            """, (str(soup), lesson_id))

    conn.commit()
