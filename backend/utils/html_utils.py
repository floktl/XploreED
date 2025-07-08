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

