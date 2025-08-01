"""
XplorED - Vocabulary Package

This package provides vocabulary management and analytics functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Vocabulary Modules:
- vocabulary_lookup: Vocabulary lookup and creation functions
- vocabulary_crud: CRUD operations for vocabulary management
- vocabulary_analytics: Analytics and learning insights functions

For detailed architecture information, see: docs/backend_structure.md
"""

from .vocabulary_lookup import (
    lookup_vocabulary_word,
    search_vocabulary_with_ai,
    select_vocab_word_due_for_review,
)

from .vocabulary_crud import (
    get_user_vocabulary_entries,
    delete_user_vocabulary,
    delete_specific_vocabulary,
    update_vocabulary_entry,
    get_vocabulary_statistics,
    update_vocab_after_review,
)

from .vocabulary_analytics import (
    get_vocabulary_learning_progress,
    get_vocabulary_difficulty_analysis,
    get_vocabulary_study_recommendations,
    get_vocabulary_export_data,
)

# Re-export all vocabulary functions for backward compatibility
__all__ = [
    # Vocabulary lookup
    "lookup_vocabulary_word",
    "search_vocabulary_with_ai",
    "select_vocab_word_due_for_review",

    # Vocabulary CRUD
    "get_user_vocabulary_entries",
    "delete_user_vocabulary",
    "delete_specific_vocabulary",
    "update_vocabulary_entry",
    "get_vocabulary_statistics",
    "update_vocab_after_review",

    # Vocabulary analytics
    "get_vocabulary_learning_progress",
    "get_vocabulary_difficulty_analysis",
    "get_vocabulary_study_recommendations",
    "get_vocabulary_export_data",
]
