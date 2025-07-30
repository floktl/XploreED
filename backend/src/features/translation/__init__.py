"""
Translation Feature Module

This module contains translation services and language tools functionality.

Author: German Class Tool Team
Date: 2025
"""

from .translation_helpers import (
    translate_text,
    translate_with_context,
    get_translation_history,
    save_translation,
    get_user_translations,
    delete_translation,
    get_translation_statistics
)

__all__ = [
    # Translation Helpers
    'translate_text',
    'translate_with_context',
    'get_translation_history',
    'save_translation',
    'get_user_translations',
    'delete_translation',
    'get_translation_statistics'
]
