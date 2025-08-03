"""
XplorED - Redis Client Module

This module provides a centralized Redis client for the XplorED platform,
following clean architecture principles as outlined in the documentation.

Redis Client Components:
- Connection Management: Handle Redis connections with environment-based configuration
- Client Singleton: Provide a single Redis client instance
- Error Handling: Handle connection errors and timeouts
- Configuration: Support both REDIS_URL and REDIS_HOST configurations

For detailed architecture information, see: docs/backend_structure.md
"""

import os
import logging
import redis
from typing import Optional, Any, List
import json
from shared.exceptions import DatabaseError
from shared.types import RedisData

logger = logging.getLogger(__name__)

class RedisClient:
    """Centralized Redis client for the XplorED platform."""

    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the Redis client with environment-based configuration."""
        try:
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self._client = redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis client initialized with REDIS_URL")
            else:
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                self._client = redis.Redis(
                    host=redis_host,
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                logger.info(f"Redis client initialized with host: {redis_host}")
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}")
            return None

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get the Redis client instance."""
        return self._client

    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            return False

    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        if not self._client:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Error getting Redis key: {e}")
            return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a value in Redis."""
        if not self._client:
            return False
        try:
            return self._client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Error setting Redis key: {e}")
            return False

    def setex(self, key: str, time: int, value: str) -> bool:
        """Set a value in Redis with expiration."""
        if not self._client:
            return False
        try:
            return self._client.setex(key, time, value)
        except Exception as e:
            logger.error(f"Error setting Redis key with expiry: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self._client:
            return False
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting Redis key: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        if not self._client:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Error checking Redis key existence: {e}")
            return False

    def keys(self, pattern: str) -> List[str]:
        """Get keys matching a pattern."""
        if not self._client:
            return []
        try:
            return self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Error getting Redis keys: {e}")
            return []

    def get_json(self, key: str) -> RedisData:
        """Get a JSON value from Redis."""
        value = self.get(key)
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Redis JSON decode error for key {key}: {e}")
            return None

    def set_json(self, key: str, value: RedisData, ex: Optional[int] = None) -> bool:
        """Set a JSON value in Redis."""
        try:
            json_value = json.dumps(value)
            return self.set(key, json_value, ex=ex)
        except Exception:
            return False

    def setex_json(self, key: str, time: int, value: RedisData) -> bool:
        """Set a JSON value in Redis with expiration."""
        try:
            json_value = json.dumps(value)
            return self.setex(key, time, json_value)
        except Exception:
            return False

# Global Redis client instance
redis_client = RedisClient()
