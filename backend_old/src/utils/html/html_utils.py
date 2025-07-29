"""HTML cleaning helpers."""

import re


def clean_html(raw_html: str) -> str:
    """Remove wrappers and style blocks from HTML text."""
    if raw_html.startswith("```html"):
        raw_html = raw_html.replace("```html", "").strip()
    if raw_html.endswith("```"):
        raw_html = raw_html[:-3].strip()
    raw_html = re.sub(r"<style[\s\S]*?</style>", "", raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r"</?(html|head|body|meta|title)[^>]*>", "", raw_html, flags=re.IGNORECASE)
    return raw_html.strip()

def ansi_to_html(text: str) -> str:
    """Convert ANSI color codes to HTML spans."""
    return (
        text.replace("\x1b[31m", '<span style="color:red;">')
        .replace("\x1b[32m", '<span style="color:green;">')
        .replace("\x1b[33m", '<span style="color:orange;">')
        .replace("\x1b[0m", "</span>")
    )

