"""
XplorED - Redis Module

This module provides Redis functionality for the XplorED platform.
"""

from .client import redis_client, RedisClient

__all__ = ['redis_client', 'RedisClient']
