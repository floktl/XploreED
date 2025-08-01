"""
XplorED - Spaced Repetition Package

This package provides spaced repetition algorithms and utilities for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Spaced Repetition Components:
- SM2 Algorithm: SuperMemo 2 spaced repetition algorithm implementation
- Learning Optimization: Optimize learning intervals and memory retention
- Memory Management: Manage spaced repetition data and calculations

For detailed architecture information, see: docs/backend_structure.md
"""

from .algorithm import sm2

# Re-export all spaced repetition functions for backward compatibility
__all__ = [
    "sm2",
]
