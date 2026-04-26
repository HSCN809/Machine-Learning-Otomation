"""
Redis cache utilities for backend computations.
Provides helper functions for caching heavy Pandas/ML results.
"""

import hashlib
import json
import os
from typing import Any, Optional

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Lazy singleton Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


def make_cache_key(prefix: str, session_id: str, *extra: Any) -> str:
    """Generate a stable cache key from prefix, session_id and extra args."""
    raw = json.dumps({"s": session_id, "x": extra}, sort_keys=True, default=str)
    hashed = hashlib.md5(raw.encode()).hexdigest()
    return f"be:{prefix}:{session_id}:{hashed}"


def cache_get(key: str) -> Optional[Any]:
    """Read a JSON-serialized value from Redis. Returns None on miss or error."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        data = client.get(key)
        if data is not None:
            return json.loads(data)
    except Exception:
        pass
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """Write a JSON-serializable value to Redis with TTL."""
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        pass


def cache_invalidate_session(session_id: str) -> None:
    """Delete all cache entries for a given session."""
    client = get_redis_client()
    if client is None:
        return
    try:
        pattern = f"be:*:{session_id}:*"
        # scan_iter is safe for production unlike KEYS
        for key in client.scan_iter(match=pattern, count=100):
            client.delete(key)
    except Exception:
        pass
