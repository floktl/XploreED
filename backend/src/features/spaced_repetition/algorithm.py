"""
Spaced Repetition Algorithms

This module contains spaced repetition algorithms such as SM2 for
optimizing learning intervals and memory retention.

Author: German Class Tool Team
Date: 2025
"""

from __future__ import annotations


def sm2(quality: int, ef: float = 2.5, repetitions: int = 0, interval: int = 1):
    """Apply the SM-2 algorithm to compute new spaced repetition values.

    The SM-2 (SuperMemo 2) algorithm is a spaced repetition algorithm that
    adjusts intervals based on the quality of the user's response.

    Args:
        quality: Answer quality (0-5).
        ef: Existing easiness factor.
        repetitions: Number of successful reviews so far.
        interval: Current review interval in days.

    Returns:
        Tuple of (new_ef, new_repetitions, new_interval).
    """
    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ef)
        repetitions += 1
        ef = max(1.3, ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    return ef, repetitions, interval


__all__ = ["sm2"]
