"""
Advanced Rate Limiting Module for API Security

Features:
- Per-IP rate limiting (prevent single-source attacks)
- Per-wallet rate limiting (prevent distributed attacks)
- Per-endpoint limits (different limits for different operations)
- Sliding window algorithm (more accurate than fixed window)
- Redis backend support (for distributed systems)
- In-memory backend (for single-server deployments)
- Rate limit bypass for testing (admin API keys)

License: Open-source (MIT)
Dependencies: slowapi (MIT), redis (optional, BSD)
"""

from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
import time


class RateLimitBackend:
    """Abstract base class for rate limit storage backends"""

    def increment(self, key: str, window_seconds: int) -> int:
        """
        Increment counter for key within time window

        Args:
            key: Unique identifier (e.g., "ip:192.168.1.1" or "wallet:addr1...")
            window_seconds: Time window in seconds

        Returns:
            Current count within window
        """
        raise NotImplementedError

    def reset(self, key: str):
        """Reset counter for key"""
        raise NotImplementedError

    def get_count(self, key: str) -> int:
        """Get current count for key"""
        raise NotImplementedError


class InMemoryBackend(RateLimitBackend):
    """
    In-memory rate limit storage (single-server deployment)

    Uses sliding window algorithm for accurate rate limiting.
    Thread-safe with locks.
    """

    def __init__(self):
        self.counters: Dict[str, list] = defaultdict(list)
        self.lock = Lock()

    def increment(self, key: str, window_seconds: int) -> int:
        """Increment counter using sliding window"""
        now = time.time()
        cutoff = now - window_seconds

        with self.lock:
            # Remove expired entries
            self.counters[key] = [
                ts for ts in self.counters[key] if ts > cutoff]

            # Add new entry
            self.counters[key].append(now)

            return len(self.counters[key])

    def reset(self, key: str):
        """Reset counter for key"""
        with self.lock:
            if key in self.counters:
                del self.counters[key]

    def get_count(self, key: str) -> int:
        """Get current count for key"""
        with self.lock:
            return len(self.counters.get(key, []))

    def cleanup_expired(self, max_age_seconds: int = 3600):
        """
        Cleanup expired entries (run periodically)

        Args:
            max_age_seconds: Maximum age to keep entries (default 1 hour)
        """
        cutoff = time.time() - max_age_seconds

        with self.lock:
            keys_to_delete = []
            for key, timestamps in self.counters.items():
                # Remove expired timestamps
                self.counters[key] = [ts for ts in timestamps if ts > cutoff]

                # Mark empty keys for deletion
                if not self.counters[key]:
                    keys_to_delete.append(key)

            # Delete empty keys
            for key in keys_to_delete:
                del self.counters[key]


class RedisBackend(RateLimitBackend):
    """
    Redis-based rate limit storage (distributed deployment)

    Uses sorted sets for sliding window.
    Requires redis library (optional dependency).
    """

    def __init__(self, redis_client):
        """
        Initialize Redis backend

        Args:
            redis_client: redis.Redis instance
        """
        self.redis = redis_client

    def increment(self, key: str, window_seconds: int) -> int:
        """Increment counter using Redis sorted set"""
        now = time.time()
        cutoff = now - window_seconds

        pipe = self.redis.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, cutoff)

        # Add new entry
        pipe.zadd(key, {str(now): now})

        # Count entries in window
        pipe.zcount(key, cutoff, now)

        # Set expiration
        pipe.expire(key, window_seconds * 2)

        results = pipe.execute()

        return results[2]  # Count result

    def reset(self, key: str):
        """Reset counter for key"""
        self.redis.delete(key)

    def get_count(self, key: str) -> int:
        """Get current count for key"""
        return self.redis.zcard(key)


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies

    Supports:
    - Per-IP limiting
    - Per-wallet limiting
    - Per-endpoint limiting
    - Global limiting
    - Admin bypass
    """

    def __init__(self, backend: Optional[RateLimitBackend] = None):
        """
        Initialize rate limiter

        Args:
            backend: Storage backend (defaults to InMemoryBackend)
        """
        self.backend = backend or InMemoryBackend()

    def check_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        exempt_keys: Optional[set] = None
    ) -> tuple[bool, int, int]:
        """
        Check if request exceeds rate limit

        Args:
            key: Unique identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            exempt_keys: Set of keys to exempt from rate limiting (admin API keys)

        Returns:
            Tuple of (allowed, current_count, retry_after_seconds)
        """
        # Check exemptions
        if exempt_keys and key in exempt_keys:
            return (True, 0, 0)

        # Get current count
        count = self.backend.increment(key, window_seconds)

        # Check limit
        allowed = count <= limit

        # Calculate retry-after (seconds until window resets)
        retry_after = window_seconds if not allowed else 0

        return (allowed, count, retry_after)

    def check_multiple_limits(
        self,
        limits: list[tuple[str, int, int]],
        exempt_keys: Optional[set] = None
    ) -> tuple[bool, Optional[str], int, int]:
        """
        Check multiple rate limits (e.g., per-IP AND per-wallet)

        Args:
            limits: List of (key, limit, window_seconds) tuples
            exempt_keys: Set of keys to exempt from rate limiting

        Returns:
            Tuple of (allowed, violated_key, current_count, retry_after_seconds)
        """
        for key, limit, window_seconds in limits:
            allowed, count, retry_after = self.check_limit(
                key, limit, window_seconds, exempt_keys
            )

            if not allowed:
                return (False, key, count, retry_after)

        return (True, None, 0, 0)

    def reset_limit(self, key: str):
        """Reset rate limit for key (admin function)"""
        self.backend.reset(key)


# ============================================================================
# Rate Limit Configurations
# ============================================================================

class RateLimitConfig:
    """Rate limit configurations for different endpoints"""

    # Health check (free operation)
    HEALTH_CHECK = {
        "per_ip_limit": 60,  # 60 requests per minute
        "per_ip_window": 60,
    }

    # Enrollment (expensive operation, creates blockchain data)
    ENROLLMENT = {
        "per_ip_limit": 5,  # 5 enrollments per minute
        "per_ip_window": 60,
        "per_wallet_limit": 3,  # 3 enrollments per hour
        "per_wallet_window": 3600,
        "global_limit": 100,  # 100 enrollments per minute (system-wide)
        "global_window": 60,
    }

    # Verification (cheaper operation, read-only)
    VERIFICATION = {
        "per_ip_limit": 20,  # 20 verifications per minute
        "per_ip_window": 60,
        "per_wallet_limit": 100,  # 100 verifications per hour
        "per_wallet_window": 3600,
        "global_limit": 500,  # 500 verifications per minute (system-wide)
        "global_window": 60,
    }

    # Authentication (login, register, refresh)
    AUTH = {
        "per_ip_limit": 10,  # 10 auth requests per minute
        "per_ip_window": 60,
        "per_wallet_limit": 20,  # 20 auth requests per hour
        "per_wallet_window": 3600,
    }

    # API key operations (admin)
    API_KEY_OPS = {
        "per_ip_limit": 5,  # 5 API key operations per minute
        "per_ip_window": 60,
    }


# ============================================================================
# Helper Functions
# ============================================================================

def get_rate_limit_key(prefix: str, identifier: str) -> str:
    """
    Generate rate limit key

    Args:
        prefix: Key prefix (e.g., "ip", "wallet", "global")
        identifier: Unique identifier

    Returns:
        Rate limit key (e.g., "ratelimit:ip:192.168.1.1")
    """
    return f"ratelimit:{prefix}:{identifier}"


def format_rate_limit_error(
    limit: int,
    window_seconds: int,
    current_count: int,
    retry_after: int
) -> Dict:
    """
    Format rate limit error response

    Args:
        limit: Rate limit
        window_seconds: Time window
        current_count: Current request count
        retry_after: Seconds until retry

    Returns:
        Error response dict
    """
    return {
        "error": "Rate limit exceeded",
        "error_code": "RATE_LIMIT_EXCEEDED",
        "message": f"Too many requests. Limit: {limit} per {window_seconds}s",
        "current_count": current_count,
        "limit": limit,
        "window_seconds": window_seconds,
        "retry_after_seconds": retry_after,
        "retry_after": f"{retry_after}s",
    }


# ============================================================================
# Testing Utilities
# ============================================================================

def create_test_limiter() -> RateLimiter:
    """Create rate limiter for testing (in-memory backend)"""
    return RateLimiter(backend=InMemoryBackend())


def create_redis_limiter(redis_url: str) -> RateLimiter:
    """
    Create rate limiter with Redis backend

    Args:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")

    Returns:
        RateLimiter instance

    Raises:
        ImportError: If redis library not installed
    """
    try:
        import redis  # type: ignore[import-untyped] # Optional dependency
    except ImportError:
        raise ImportError(
            "Redis library not installed. Install with: pip install redis"
        )

    redis_client = redis.from_url(redis_url)
    return RateLimiter(backend=RedisBackend(redis_client))
