"""
In-memory caching with Time-To-Live (TTL) support.

This module provides a simple in-memory cache to store results from
expensive operations, such as API calls, with a defined expiration time.

Features:
- Thread-safe operations.
- Configurable TTL for cache entries.
- Automatic pruning of expired entries (optional).

License: Apache 2.0
"""

import time
import threading
from typing import Any, Optional, Dict


class TTLCache:
    """
    A simple thread-safe in-memory cache with Time-To-Live (TTL) support.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize the cache.

        Args:
            default_ttl: Default time-to-live for cache entries in seconds.
        """
        self._cache: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}
        self.default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an item from the cache if it exists and has not expired.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The cached item, or None if not found or expired.
        """
        with self._lock:
            if key in self._cache and time.time() < self._ttl.get(key, 0):
                return self._cache[key]

            # Clean up expired key if it exists
            if key in self._cache:
                del self._cache[key]
                del self._ttl[key]

            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Add an item to the cache with a specific TTL.

        Args:
            key: The key of the item to add.
            value: The item to cache.
            ttl: The time-to-live for this item in seconds. If None, the
                 default TTL is used.
        """
        with self._lock:
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            self._cache[key] = value
            self._ttl[key] = time.time() + ttl_seconds

    def clear(self):
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            self._ttl.clear()

    def prune_expired(self):
        """Remove all expired items from the cache."""
        with self._lock:
            now = time.time()
            expired_keys = [key for key,
                            expiry in self._ttl.items() if now >= expiry]
            for key in expired_keys:
                del self._cache[key]
                del self._ttl[key]
