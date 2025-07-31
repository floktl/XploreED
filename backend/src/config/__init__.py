"""
XplorED - Configuration Module

This module provides centralized configuration management for the backend application,
following clean architecture principles as outlined in the documentation.

Configuration Components:
- app: Flask application configuration and settings
- blueprint: Blueprint registration and management
- extensions: Flask extensions initialization and configuration

For detailed architecture information, see: docs/backend_structure.md
"""

# === Import Configuration Components ===
from .app import create_app_config

# === Export Configuration ===
__all__ = [
    "create_app_config",
]
