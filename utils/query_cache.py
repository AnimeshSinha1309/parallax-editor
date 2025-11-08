"""Caching utilities for DSPy query generators to reduce redundant LLM calls."""

from __future__ import annotations

import hashlib
import json
from functools import wraps
from typing import Any, Callable, Dict, Optional
from collections import OrderedDict


class QueryCache:
    """
    LRU cache for DSPy query generator results.

    Caches results based on input parameters to avoid redundant LLM calls
    for identical queries.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize the query cache.

        Args:
            max_size: Maximum number of entries to store (LRU eviction)
        """
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size

    def _make_key(self, *args, **kwargs) -> str:
        """
        Create a cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash string representing the unique combination of inputs
        """
        # Combine args and kwargs into a stable representation
        key_data = {
            "args": args,
            "kwargs": {k: v for k, v in sorted(kwargs.items())}
        }
        # Use JSON serialization for stable string representation
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        # Hash for efficient storage
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if present, None otherwise
        """
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to store
        """
        if key in self._cache:
            # Update existing entry and mark as recently used
            self._cache.move_to_end(key)
        else:
            # Add new entry
            self._cache[key] = value
            # Evict oldest entry if cache is full
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return the number of entries in the cache."""
        return len(self._cache)


# Global cache instances for different query types
_rg_query_cache = QueryCache(max_size=100)
_web_query_cache = QueryCache(max_size=100)


def cached_predictor(cache: QueryCache) -> Callable:
    """
    Decorator to cache DSPy predictor calls.

    Args:
        cache: QueryCache instance to use for caching

    Returns:
        Decorator function

    Example:
        >>> predictor = dspy.Predict(RGQueryGenerator)
        >>> cached_predictor = cached_predictor(_rg_query_cache)(predictor)
        >>> result = cached_predictor(current_document=doc, repo_summary=summary)
    """
    def decorator(predictor_func: Callable) -> Callable:
        @wraps(predictor_func)
        def wrapper(*args, **kwargs):
            # Generate cache key from inputs
            cache_key = cache._make_key(*args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Call the actual predictor
            result = predictor_func(*args, **kwargs)

            # Store in cache
            cache.put(cache_key, result)

            return result

        return wrapper
    return decorator


def get_rg_query_cache() -> QueryCache:
    """Get the global RGQueryGenerator cache instance."""
    return _rg_query_cache


def get_web_query_cache() -> QueryCache:
    """Get the global WebQueryGenerator cache instance."""
    return _web_query_cache


def clear_all_caches() -> None:
    """Clear all query caches."""
    _rg_query_cache.clear()
    _web_query_cache.clear()


__all__ = [
    "QueryCache",
    "cached_predictor",
    "get_rg_query_cache",
    "get_web_query_cache",
    "clear_all_caches",
]
