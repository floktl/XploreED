"""
XplorED - Translation Package

This package provides translation services and language tools functionality for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Translation Modules:
- translation_jobs: Translation job management functions
- translation_streaming: Translation streaming and feedback functions

For detailed architecture information, see: docs/backend_structure.md
"""

from .translation_jobs import (
    create_translation_job,
    process_translation_job,
    get_translation_job_status,
    get_translation_status,
    cleanup_expired_jobs,
)

from .translation_streaming import (
    stream_translation_feedback,
)

# Re-export all translation functions for backward compatibility
__all__ = [
    # Translation jobs
    "create_translation_job",
    "process_translation_job",
    "get_translation_job_status",
    "get_translation_status",
    "cleanup_expired_jobs",

    # Translation streaming
    "stream_translation_feedback",
]
