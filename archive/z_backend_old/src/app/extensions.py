"""Application wide Flask extensions."""

from flask_limiter import Limiter # type: ignore
from flask_limiter.util import get_remote_address # type: ignore

# Reusable limiter instance
limiter = Limiter(
    get_remote_address,
    storage_uri="memory://",
)
