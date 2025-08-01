"""
XplorED - Grammar Package

This package provides grammar detection and analysis functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Grammar Components:
- Language Topic Detection: Detect grammar topics in text using AI
- Grammar Templates: German grammar rules and patterns
- Grammar Analysis: Analyze text for grammatical structures
- Pattern Recognition: Recognize German grammar patterns

For detailed architecture information, see: docs/backend_structure.md
"""

from .detector import (
    detect_language_topics
)

# Re-export all grammar functions for backward compatibility
__all__ = [
    # Grammar Detection
    "detect_language_topics"
]
