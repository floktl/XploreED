"""Application wide Flask extensions."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Reusable limiter instance
limiter = Limiter(
    get_remote_address,
    storage_uri="memory://",
)
