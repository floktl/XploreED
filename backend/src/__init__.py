"""
German Class Tool - Backend Source Module

This module serves as the main entry point for the German Class Tool backend application,
following clean architecture principles as outlined in the documentation.

Application Components:
- main: Application entry point and factory
- app: Backward compatibility module
- api: API layer with routes, middleware, and schemas
- config: Application configuration and settings
- core: Core business logic and infrastructure
- external: External service integrations
- features: Feature-specific business logic
- shared: Shared constants, types, and exceptions

For detailed architecture information, see: docs/backend_structure.md
"""

# === Application Entry Point ===
# The main application entry point is in main.py
# This module provides the overall structure and organization

# === Export Configuration ===
__all__ = [
    # Main application components
    "main",
    "app",

    # Architectural layers
    "api",
    "config",
    "core",
    "external",
    "features",
    "shared",
]
