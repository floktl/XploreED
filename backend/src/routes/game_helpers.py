"""Helper functions for game routes."""


def ansi_to_html(text: str) -> str:
    """Convert ANSI color codes to HTML spans."""
    return (
        text.replace("\x1b[31m", '<span style="color:red;">')
        .replace("\x1b[32m", '<span style="color:green;">')
        .replace("\x1b[33m", '<span style="color:orange;">')
        .replace("\x1b[0m", "</span>")
    )

