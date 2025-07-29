"""
German Class Tool - Core Module

This module provides core business logic and infrastructure components,
following clean architecture principles as outlined in the documentation.

Components:
- database: Database connection and management
- services: Core business logic services
- utils: General utilities and helpers
- imports: Centralized import management

For detailed architecture information, see: docs/backend_structure.md
"""

from . import database
from . import services
from . import utils
from . import imports

# Re-export commonly used items for convenience
from .imports import *

__all__ = [
    # Module imports
    "database",
    "services",
    "utils",
    "imports",

    # Import all items from imports module
    # (This will include all the imports defined in core/imports.py)
]
