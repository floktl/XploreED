"""
Features Package

This package contains all feature modules for the German Class Tool application,
organized by business domain and following clean architecture principles.

Author: German Class Tool Team
Date: 2025
"""

# === AI Features ===
from .ai import *

# === Authentication Features ===
from .auth import *

# === User Management Features ===
from .user import *

# === Lesson Features ===
from .lessons import *

# === Exercise Features ===
from .exercise import *

# === Vocabulary Features ===
from .vocabulary import *

# === Grammar Features ===
from .grammar import *

# === Game Features ===
from .game import *

# === Translation Features ===
from .translation import *

# === Profile Features ===
from .profile import *

# === Settings Features ===
from .settings import *

# === Support Features ===
from .support import *

# === Admin Features ===
from .admin import *

# === Debug Features ===
from .debug import *

# === Progress Features ===
from .progress import *

__all__ = [
    # All feature modules are imported above
    # This allows importing from features directly
    # Example: from features import get_user_profile, translate_text
]
