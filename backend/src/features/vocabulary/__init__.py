"""
Vocabulary Feature Module

This module contains vocabulary management and analytics functionality.

Author: XplorED Team
Date: 2025
"""

from .vocabulary_manager import (
    lookup_vocabulary_word,
    get_user_vocabulary_entries,
    delete_user_vocabulary,
    delete_specific_vocabulary,
    search_vocabulary_with_ai,
    update_vocabulary_entry,
    get_vocabulary_statistics
)

from .vocabulary_analytics import (
    get_vocabulary_learning_progress,
    get_vocabulary_difficulty_analysis,
    get_vocabulary_study_recommendations,
    get_vocabulary_export_data
)

__all__ = [
    # Vocabulary Manager
    'lookup_vocabulary_word',
    'get_user_vocabulary_entries',
    'delete_user_vocabulary',
    'delete_specific_vocabulary',
    'search_vocabulary_with_ai',
    'update_vocabulary_entry',
    'get_vocabulary_statistics',

    # Vocabulary Analytics
    'get_vocabulary_learning_progress',
    'get_vocabulary_difficulty_analysis',
    'get_vocabulary_study_recommendations',
    'get_vocabulary_export_data'
]
