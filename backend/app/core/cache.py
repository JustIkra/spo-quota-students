"""
Async Redis cache layer with decorator and invalidation.
"""
import json
import functools
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def init_cache() -> None:
    """Initialize Redis connection."""
    global _redis
    _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await _redis.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis unavailable, caching disabled: {e}")
        _redis = None


async def close_cache() -> None:
    """Close Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis connection closed")


def get_redis() -> Optional[aioredis.Redis]:
    """Get current Redis client (or None if unavailable)."""
    return _redis


def cached(prefix: str, ttl: int = 300):
    """
    Caching decorator for async endpoint functions.

    Builds cache key from prefix + relevant request params.
    The decorated function must be a FastAPI endpoint (kwargs contain
    query params, path params, current_user, db, etc.).

    Args:
        prefix: Cache key prefix (e.g. "admin:spo", "stats")
        ttl: Time-to-live in seconds (default 5 minutes)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            r = _redis
            if r is None:
                return await func(*args, **kwargs)

            # Build cache key from relevant kwargs
            key_parts = [prefix]

            # Include user-scoped data if present
            current_user = kwargs.get("current_user")
            if current_user and hasattr(current_user, "spo_id") and current_user.spo_id:
                key_parts.append(f"spo:{current_user.spo_id}")
            elif current_user and hasattr(current_user, "role"):
                key_parts.append(f"role:{current_user.role.value}")

            # Include query params (skip db and current_user)
            for k, v in sorted(kwargs.items()):
                if k in ("db", "current_user", "request", "credentials"):
                    continue
                if v is not None:
                    key_parts.append(f"{k}:{v}")

            cache_key = ":".join(str(p) for p in key_parts)

            try:
                cached_data = await r.get(cache_key)
                if cached_data is not None:
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

            result = await func(*args, **kwargs)

            try:
                # Serialize: handle Pydantic models, datetime, etc.
                if isinstance(result, list):
                    serialized = json.dumps(
                        [item.model_dump() if hasattr(item, "model_dump") else item for item in result],
                        default=str
                    )
                elif hasattr(result, "model_dump"):
                    serialized = json.dumps(result.model_dump(), default=str)
                else:
                    serialized = json.dumps(result, default=str)
                await r.set(cache_key, serialized, ex=ttl)
            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result
        return wrapper
    return decorator


async def invalidate(*patterns: str) -> None:
    """
    Invalidate cache keys matching given patterns.
    Each pattern is used as a prefix for SCAN-based deletion.

    Usage: await invalidate("admin:spo", "stats")
    """
    r = _redis
    if r is None:
        return

    for pattern in patterns:
        try:
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor, match=f"{pattern}*", count=100)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Cache invalidation error for '{pattern}': {e}")
