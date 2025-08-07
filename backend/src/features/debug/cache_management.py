"""
XplorED - Cache Management Module

This module provides cache management functions for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Cache Management Components:
- User Cache Clearing: Clear all cache data for a specific user
- System Cache Clearing: Clear system-wide cache data
- Cache Statistics: Get cache usage statistics
- Cache Health: Monitor cache health and performance

For detailed architecture information, see: docs/backend_structure.md
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from external.redis import redis_client
from shared.exceptions import DatabaseError

logger = logging.getLogger(__name__)


def clear_user_cache(username: str) -> Dict[str, int]:
    """
    Clear all cache data for a specific user.

    Args:
        username: The username to clear cache for

    Returns:
        Dictionary with cache clearing statistics
    """
    cache_stats = {
        "exercise_results": 0,
        "feedback_progress": 0,
        "translation_jobs": 0,
        "other_keys": 0,
        "total_cleared": 0
    }

    try:
        if not redis_client.is_connected():
            logger.warning("Redis not connected, skipping cache clearing")
            return cache_stats

        # Clear exercise results cache
        exercise_keys = redis_client.keys(f"exercise_result:{username}:*")
        for key in exercise_keys:
            if redis_client.delete(key):
                cache_stats["exercise_results"] += 1

        # Clear feedback progress cache (need to check all feedback sessions)
        feedback_keys = redis_client.keys("feedback_progress:*")
        for key in feedback_keys:
            # Check if this feedback session belongs to the user
            feedback_data = redis_client.get_json(key)
            if feedback_data and feedback_data.get("username") == username:
                if redis_client.delete(key):
                    cache_stats["feedback_progress"] += 1

        # Clear translation jobs for the user
        translation_keys = redis_client.keys("translation_job:*")
        for key in translation_keys:
            job_data = redis_client.get_json(key)
            if job_data and job_data.get("username") == username:
                if redis_client.delete(key):
                    cache_stats["translation_jobs"] += 1

        # Clear any other user-specific keys
        other_keys = redis_client.keys(f"{username}_*")
        for key in other_keys:
            if redis_client.delete(key):
                cache_stats["other_keys"] += 1

        # Clear test keys that might have been created during debugging
        test_keys = redis_client.keys(f"{username}_*_test")
        for key in test_keys:
            if redis_client.delete(key):
                cache_stats["other_keys"] += 1

        cache_stats["total_cleared"] = sum([
            cache_stats["exercise_results"],
            cache_stats["feedback_progress"],
            cache_stats["translation_jobs"],
            cache_stats["other_keys"]
        ])

        logger.info(f"Cleared {cache_stats['total_cleared']} cache entries for user {username}")
        return cache_stats

    except Exception as e:
        logger.error(f"Error clearing cache for user {username}: {e}")
        return cache_stats


def clear_system_cache(cache_type: str = "all") -> Dict[str, any]:
    """
    Clear system-wide cache data.

    Args:
        cache_type: Type of cache to clear ("all", "expired", "temp", "logs")

    Returns:
        Dictionary with cache clearing statistics
    """
    cache_stats = {
        "cache_type": cache_type,
        "cleared_keys": 0,
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }

    try:
        if not redis_client.is_connected():
            logger.warning("Redis not connected, skipping system cache clearing")
            cache_stats["errors"].append("Redis not connected")
            return cache_stats

        if cache_type == "all":
            # Clear all cache keys
            all_keys = redis_client.keys("*")
            for key in all_keys:
                if redis_client.delete(key):
                    cache_stats["cleared_keys"] += 1

        elif cache_type == "expired":
            # Clear expired translation jobs
            translation_keys = redis_client.keys("translation_job:*")
            for key in translation_keys:
                job_data = redis_client.get_json(key)
                if job_data:
                    created_at = job_data.get("created_at", 0)
                    # Check if job is older than 1 hour
                    if datetime.now().timestamp() - created_at > 3600:
                        if redis_client.delete(key):
                            cache_stats["cleared_keys"] += 1

        elif cache_type == "temp":
            # Clear temporary test keys
            temp_keys = redis_client.keys("*_test")
            for key in temp_keys:
                if redis_client.delete(key):
                    cache_stats["cleared_keys"] += 1

        elif cache_type == "logs":
            # Clear log-related cache (if any)
            log_keys = redis_client.keys("*log*")
            for key in log_keys:
                if redis_client.delete(key):
                    cache_stats["cleared_keys"] += 1

        logger.info(f"Cleared {cache_stats['cleared_keys']} system cache entries (type: {cache_type})")
        return cache_stats

    except Exception as e:
        logger.error(f"Error clearing system cache: {e}")
        cache_stats["errors"].append(str(e))
        return cache_stats


def get_cache_statistics() -> Dict[str, any]:
    """
    Get cache usage statistics.

    Returns:
        Dictionary with cache statistics
    """
    stats = {
        "redis_connected": False,
        "total_keys": 0,
        "key_patterns": {},
        "memory_usage": "unknown",
        "timestamp": datetime.now().isoformat()
    }

    try:
        if not redis_client.is_connected():
            return stats

        stats["redis_connected"] = True

        # Get all keys
        all_keys = redis_client.keys("*")
        stats["total_keys"] = len(all_keys)

        # Analyze key patterns
        patterns = {}
        for key in all_keys:
            if ":" in key:
                pattern = key.split(":")[0]
                patterns[pattern] = patterns.get(pattern, 0) + 1
            else:
                patterns["other"] = patterns.get("other", 0) + 1

        stats["key_patterns"] = patterns

        # Try to get memory usage info
        try:
            info = redis_client.client.info("memory")
            stats["memory_used"] = info.get("used_memory_human", "unknown")
            stats["memory_peak"] = info.get("used_memory_peak_human", "unknown")
        except Exception as e:
            logger.debug(f"Could not get Redis memory info: {e}")

        return stats

    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        stats["errors"] = [str(e)]
        return stats


def clear_in_memory_caches() -> Dict[str, any]:
    """
    Clear in-memory caches (Flask app config caches).

    Returns:
        Dictionary with cache clearing results
    """
    cache_stats = {
        "reading_exercise_cache": False,
        "other_caches": 0,
        "timestamp": datetime.now().isoformat()
    }

    try:
        from flask import current_app

        # Clear reading exercise cache
        reading_cache = current_app.config.get("READING_EXERCISE_CACHE", {})
        if reading_cache:
            current_app.config["READING_EXERCISE_CACHE"] = {}
            cache_stats["reading_exercise_cache"] = True
            logger.info("Cleared reading exercise cache")

        # Clear any other in-memory caches
        cache_keys = [key for key in current_app.config.keys() if "cache" in key.lower()]
        for key in cache_keys:
            if key != "READING_EXERCISE_CACHE":
                current_app.config[key] = {}
                cache_stats["other_caches"] += 1

        return cache_stats

    except Exception as e:
        logger.error(f"Error clearing in-memory caches: {e}")
        cache_stats["errors"] = [str(e)]
        return cache_stats
