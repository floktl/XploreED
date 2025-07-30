"""
German Class Tool - Flask Extensions Configuration

This module provides centralized Flask extension initialization and configuration,
following clean architecture principles as outlined in the documentation.

Extensions:
- Rate Limiting: Request throttling and abuse prevention
- Future Extensions: Database, caching, and other integrations

For detailed architecture information, see: docs/backend_structure.md
"""

from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore

# === Rate Limiting Extension ===
# Configure rate limiting for API abuse prevention and resource protection
limiter = Limiter(
    get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"],
    strategy="fixed-window",
)


# === Export Configuration ===
__all__ = [
    "limiter",
]
