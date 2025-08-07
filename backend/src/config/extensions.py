"""
XplorED - Flask Extensions Configuration

This module provides centralized Flask extension initialization and configuration,
following clean architecture principles as outlined in the documentation.

Extensions:
- Rate Limiting: Request throttling and abuse prevention
- Future Extensions: Database, caching, and other integrations

For detailed architecture information, see: docs/backend_structure.md
"""

from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
import os

# === Rate Limiting Extension ===
# Configure rate limiting for API abuse prevention and resource protection
storage_uri = os.getenv("LIMITER_STORAGE_URI", "memory://")

# Prefer Redis if configured: e.g. redis://redis:6379/0
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["1000 per day", "200 per hour"],
    strategy="fixed-window",
)


# === Export Configuration ===
__all__ = [
    "limiter",
]
