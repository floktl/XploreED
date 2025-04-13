from bs4 import BeautifulSoup
import sqlite3
from .db_utils import get_connection

def update_lesson_blocks_from_html(lesson_id, html):
    print(f"🧱 [update_lesson_blocks_from_html] for lesson_id={lesson_id}")
    print("📥 HTML length:", len(html))

    soup = BeautifulSoup(html, "html.parser")
    block_ids = set()

    for block in soup.select('[data-block-id]'):
        block_id = block.get("data-block-id")
        if block_id:
            block_ids.add(block_id)
            print(f"📌 Found block_id: {block_id}")

    print(f"🔢 Total unique block_ids extracted: {len(block_ids)}")

    with get_connection() as conn:
        cursor = conn.cursor()

        print("🧹 Deleting old lesson_blocks entries...")
        cursor.execute("DELETE FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,))

        for block_id in block_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id) VALUES (?, ?)",
                (lesson_id, block_id)
            )
            print(f"➕ Inserted block_id={block_id}")

        conn.commit()
        print(f"✅ [update_lesson_blocks_from_html] Synced {len(block_ids)} blocks for lesson {lesson_id}")



def inject_block_ids(html):
    print("🧠 [inject_block_ids] Called")
    print("📥 Raw HTML:", html[:200], "...")  # print first 200 chars

    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select(".interactive-block")
    print(f"🔍 Found {len(blocks)} interactive blocks")

    for i, block in enumerate(blocks):
        block['data-block-id'] = f"block-{i}"
        print(f"🔗 Assigned data-block-id='block-{i}'")

    result = str(soup)
    print("✅ [inject_block_ids] Done, returning HTML length:", len(result))
    return result
