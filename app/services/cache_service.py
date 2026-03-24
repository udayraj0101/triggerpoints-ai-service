"""
Redis-backed cache service with fallback to in-memory cache.
Persistent across server restarts.
"""
import json
import redis
from app.config.settings import REDIS_URL, CACHE_TTL, USE_REDIS
from app.utils.logger import get_logger

log = get_logger("cache_service")

# Try to initialize Redis, fall back to in-memory if unavailable
_redis_client = None
_memory_cache = {}
_using_redis = False


def _init_redis():
    """Initialize Redis connection."""
    global _redis_client, _using_redis
    
    if not USE_REDIS:
        log.info("Redis disabled via USE_REDIS=false, using in-memory cache")
        return
    
    try:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=5)
        # Test connection
        _redis_client.ping()
        _using_redis = True
        log.info(f"✓ Redis connected ({REDIS_URL})")
    except Exception as e:
        log.warning(f"Failed to connect to Redis: {e}")
        log.warning("Falling back to in-memory cache (not persistent)")
        _redis_client = None
        _using_redis = False


def get(key: str) -> dict | None:
    """
    Get cached response by key.
    Returns None if key not found.
    """
    try:
        if _using_redis and _redis_client:
            result = _redis_client.get(key)
            if result:
                log.debug(f"Redis cache hit")
                return json.loads(result)
        else:
            if key in _memory_cache:
                log.debug(f"Memory cache hit")
                return _memory_cache[key]
    except Exception as e:
        log.error(f"Cache get error: {e}")
    
    return None


def set(key: str, value: dict, ttl: int = CACHE_TTL) -> None:
    """
    Set cached response with TTL (Time To Live).
    Default TTL: 24 hours (86400 seconds)
    """
    try:
        if _using_redis and _redis_client:
            _redis_client.setex(key, ttl, json.dumps(value))
            log.debug(f"Cached response in Redis (TTL: {ttl}s)")
        else:
            _memory_cache[key] = value
            log.debug(f"Cached response in memory")
    except Exception as e:
        log.error(f"Cache set error: {e}")


def clear() -> None:
    """Clear all cache entries."""
    try:
        if _using_redis and _redis_client:
            _redis_client.flushdb()
            log.info("Redis cache cleared")
        else:
            _memory_cache.clear()
            log.info("Memory cache cleared")
    except Exception as e:
        log.error(f"Cache clear error: {e}")


def get_stats() -> dict:
    """Get cache statistics."""
    try:
        if _using_redis and _redis_client:
            info = _redis_client.info()
            return {
                "backend": "redis",
                "keys": _redis_client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected": True,
            }
        else:
            return {
                "backend": "memory",
                "keys": len(_memory_cache),
                "memory_used": "N/A",
                "connected": True,
            }
    except Exception as e:
        log.error(f"Cache stats error: {e}")
        return {"error": str(e), "connected": False}


# Initialize Redis on import
_init_redis()
