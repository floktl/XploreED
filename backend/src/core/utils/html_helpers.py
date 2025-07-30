"""
German Class Tool - HTML Processing Utilities

This module provides HTML processing and manipulation utilities for lesson content,
following clean architecture principles as outlined in the documentation.

HTML Operations:
- Content Cleaning: Remove unwanted HTML elements and styling
- Block Management: Lesson block identification and manipulation
- AI Data Handling: Exercise payload processing and cleanup
- Format Conversion: ANSI to HTML color code conversion

For detailed architecture information, see: docs/backend_structure.md
"""

import re
from bs4 import BeautifulSoup  # type: ignore
import sqlite3
from core.database.connection import get_connection
from typing import Set


# === HTML Content Cleaning ===
def clean_html(raw_html: str) -> str:
    """
    Remove wrappers and style blocks from HTML text.

    This function cleans HTML content by removing:
    - Markdown code block wrappers (```html)
    - Style blocks and CSS
    - HTML document structure elements (html, head, body, meta, title)

    Args:
        raw_html: Raw HTML string to clean

    Returns:
        str: Cleaned HTML content
    """
    if raw_html.startswith("```html"):
        raw_html = raw_html.replace("```html", "").strip()
    if raw_html.endswith("```"):
        raw_html = raw_html[:-3].strip()
    raw_html = re.sub(r"<style[\s\S]*?</style>", "", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"</?(html|head|body|meta|title)[^>]*>", "", raw_html, flags=re.IGNORECASE)
    return raw_html.strip()


# === Lesson Block Management ===
def update_lesson_blocks_from_html(lesson_id: int, html: str) -> None:
    """
    Store all data-block-id values for lesson_id in the database.

    This function parses HTML content to extract block IDs and updates
    the lesson_blocks table to maintain the relationship between
    lessons and their interactive blocks.

    Args:
        lesson_id: ID of the lesson to update blocks for
        html: HTML content containing data-block-id attributes
    """
    soup = BeautifulSoup(html, "html.parser")
    block_ids: Set[str] = set()

    # Extract all data-block-id values
    for block in soup.select('[data-block-id]'):
        block_id = block.get("data-block-id")
        if block_id:
            block_ids.add(str(block_id))

    # Update database with block IDs
    with get_connection() as conn:
        cursor = conn.cursor()

        # Remove existing blocks for this lesson
        cursor.execute("DELETE FROM lesson_blocks WHERE lesson_id = ?", (lesson_id,))

        # Insert new block IDs
        for block_id in block_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO lesson_blocks (lesson_id, block_id) VALUES (?, ?)",
                (lesson_id, block_id)
            )

        conn.commit()


def inject_block_ids(html: str) -> str:
    """
    Insert numeric data-block-id attributes into lesson HTML.

    This function automatically assigns sequential block IDs to
    interactive blocks in lesson content for tracking and management.

    Args:
        html: HTML content containing .interactive-block elements

    Returns:
        str: HTML with injected data-block-id attributes
    """
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select(".interactive-block")

    for i, block in enumerate(blocks):
        block['data-block-id'] = f"block-{i}"

    return str(soup)


# === AI Data Processing ===
def strip_ai_data(html: str) -> str:
    """
    Remove encoded AI exercise payloads before storing.

    This function cleans HTML content by removing AI exercise data
    attributes that contain sensitive or temporary information
    before storing in the database.

    Args:
        html: HTML content containing AI exercise data

    Returns:
        str: HTML with AI data attributes removed
    """
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select('[data-ai-exercise]'):
        if 'data-ai-data' in el.attrs:
            del el['data-ai-data']
    return str(soup)


# === Format Conversion ===
def ansi_to_html(text: str) -> str:
    """
    Convert ANSI color codes to HTML spans.

    This function converts terminal ANSI color codes to HTML
    span elements with appropriate CSS styling for web display.

    Args:
        text: Text containing ANSI color codes

    Returns:
        str: HTML with color spans instead of ANSI codes
    """
    return (
        text.replace("\x1b[31m", '<span style="color:red;">')
        .replace("\x1b[32m", '<span style="color:green;">')
        .replace("\x1b[33m", '<span style="color:orange;">')
        .replace("\x1b[0m", "</span>")
    )


# === Export Configuration ===
__all__ = [
    # HTML content cleaning
    "clean_html",

    # Lesson block management
    "update_lesson_blocks_from_html",
    "inject_block_ids",

    # AI data processing
    "strip_ai_data",

    # Format conversion
    "ansi_to_html",
]
