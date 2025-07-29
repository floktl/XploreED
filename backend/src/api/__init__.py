"""
German Class Tool - API Layer Module

This module provides the API layer components for the backend application,
following clean architecture principles as outlined in the documentation.

Components:
- routes: HTTP endpoints organized by feature domain
- middleware: Request/response processing and authentication
- schemas: Data validation and serialization schemas
- templates: HTML templates for error pages

For detailed architecture information, see: docs/backend_structure.md
"""

from . import routes
from . import middleware
from . import schemas
from . import templates

__all__ = [
    "routes",
    "middleware",
    "schemas",
    "templates",
]
