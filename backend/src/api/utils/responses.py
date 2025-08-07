"""
XplorED - API Response Helpers

Provide consistent JSON response envelopes across the API.
"""

from __future__ import annotations

from typing import Any, Optional
from flask import jsonify  # type: ignore


def json_success(data: Any | None = None, message: Optional[str] = None, status_code: int = 200):
    payload: dict[str, Any] = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def json_error(message: str, code: str = "error", status_code: int = 400, details: Optional[dict[str, Any]] = None):
    payload: dict[str, Any] = {
        "success": False,
        "error": code,
        "message": message,
    }
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


__all__ = ["json_success", "json_error"]

