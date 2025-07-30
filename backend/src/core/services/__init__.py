"""
German Class Tool - Core Services Module

This module provides core business logic services for the backend application,
following clean architecture principles as outlined in the documentation.

Service Components:
- import_service: Centralized import management for route modules

For detailed architecture information, see: docs/backend_structure.md
"""

from . import import_service

# Re-export commonly used items for convenience
from .import_service import Imports


# === Export Configuration ===
__all__ = [
    # Module imports
    "import_service",

    # Service classes
    "Imports",
]
