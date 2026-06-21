import time
from functools import wraps
from typing import Any, Callable


class TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time() + self._ttl)

    def invalidate(self, key: str = ""):
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# Session-level caches (keyed by user_id)
_insight_cache: dict[int, TTLCache] = {}
_model_cache: TTLCache = TTLCache(300)  # 5 min TTL for models


def get_insight_cache(user_id: int, ttl: int = 300) -> TTLCache:
    if user_id not in _insight_cache:
        _insight_cache[user_id] = TTLCache(ttl)
    return _insight_cache[user_id]


def cached(ttl: int = 60):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cache = TTLCache(ttl)
            result = cache.get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator
