"""
XplorED - Core Module

This module provides core business logic and infrastructure components,
following clean architecture principles as outlined in the documentation.

Components:
- database: Database connection and management
- services: Core business logic services
- authentication: Authentication and session management utilities
- processing: Content processing and manipulation utilities
- validation: Data validation and parsing utilities
- imports: Centralized import management

Note: Database migrations are now in scripts/migrations/ for better separation.
Import management has been moved to infrastructure/imports/ for better separation.

For detailed architecture information, see: docs/backend_structure.md
"""

from . import database
from . import services
from . import authentication
from . import processing
# Removed validation import - validation folder was removed
from . import imports

# Note: Some functionality has been moved to core.services
# Import specific items that are still available in core.imports

__all__ = [
    # Module imports
    "database",
    "services",
    "authentication",
    "processing",
    # "validation",  # Removed - validation folder was removed
    "imports",
]
