"""
XplorED - Infrastructure Imports

This module provides infrastructure utilities for import management,
following clean architecture principles as outlined in the documentation.

Infrastructure Components:
- route_imports: Centralized import management for route modules

Note: Consider refactoring to use direct imports in each module for better maintainability.

For detailed architecture information, see: docs/backend_structure.md
"""

from .route_imports import Imports

__all__ = [
    "Imports",
]
