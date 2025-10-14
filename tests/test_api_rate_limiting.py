"""
Tests for Advanced Rate Limiting Module

Test Coverage:
- InMemoryBackend (sliding window, thread safety, cleanup)
- RateLimiter (single limits, multiple limits, exemptions)
- RateLimitConfig (configuration values)
- Helper functions (key generation, error formatting)
"""

import pytest
import time
from threading import Thread
from src.decentralized_did.api.rate_limiter import (
    InMemoryBackend,
    RateLimiter,
    RateLimitConfig,
    get_rate_limit_key,
    format_rate_limit_error,
    create_test_limiter,
)


# ============================================================================
# InMemoryBackend Tests
# ============================================================================

def test_inmemory_backend_basic_increment():
    """Test basic counter increment"""
    backend = InMemoryBackend()

    count1 = backend.increment("test_key", window_seconds=60)
    count2 = backend.increment("test_key", window_seconds=60)
    count3 = backend.increment("test_key", window_seconds=60)

    assert count1 == 1
    assert count2 == 2
    assert count3 == 3


def test_inmemory_backend_sliding_window():
    """Test sliding window expiration"""
    backend = InMemoryBackend()

    # Add 3 requests
    backend.increment("test_key", window_seconds=1)
    backend.increment("test_key", window_seconds=1)
    backend.increment("test_key", window_seconds=1)

    assert backend.get_count("test_key") == 3

    # Wait for window to expire
    time.sleep(1.1)

    # Next increment should reset window
    count = backend.increment("test_key", window_seconds=1)
    assert count == 1


def test_inmemory_backend_reset():
    """Test counter reset"""
    backend = InMemoryBackend()

    backend.increment("test_key", window_seconds=60)
    backend.increment("test_key", window_seconds=60)

    assert backend.get_count("test_key") == 2

    backend.reset("test_key")

    assert backend.get_count("test_key") == 0


def test_inmemory_backend_multiple_keys():
    """Test multiple independent keys"""
    backend = InMemoryBackend()

    backend.increment("key1", window_seconds=60)
    backend.increment("key1", window_seconds=60)
    backend.increment("key2", window_seconds=60)

    assert backend.get_count("key1") == 2
    assert backend.get_count("key2") == 1


def test_inmemory_backend_thread_safety():
    """Test thread-safe counter increment"""
    backend = InMemoryBackend()

    def increment_many():
        for _ in range(100):
            backend.increment("concurrent_key", window_seconds=60)

    # Run 5 threads concurrently
    threads = [Thread(target=increment_many) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have exactly 500 increments (5 threads × 100)
    assert backend.get_count("concurrent_key") == 500


def test_inmemory_backend_cleanup():
    """Test expired entry cleanup"""
    backend = InMemoryBackend()

    # Add old entry first
    backend.increment("old_key", window_seconds=1)

    # Wait for it to expire
    time.sleep(1.1)

    # Add recent entry AFTER old one expired
    backend.increment("recent_key", window_seconds=60)

    # Cleanup expired entries (max_age=1 second)
    backend.cleanup_expired(max_age_seconds=1)

    # Recent key should still exist, old key should be gone
    assert backend.get_count("recent_key") == 1
    assert backend.get_count("old_key") == 0
# ============================================================================
# RateLimiter Tests
# ============================================================================


def test_rate_limiter_basic_check():
    """Test basic rate limit check"""
    limiter = create_test_limiter()

    # First 3 requests should pass (limit=3, window=60s)
    allowed1, count1, retry1 = limiter.check_limit(
        "test_key", limit=3, window_seconds=60)
    allowed2, count2, retry2 = limiter.check_limit(
        "test_key", limit=3, window_seconds=60)
    allowed3, count3, retry3 = limiter.check_limit(
        "test_key", limit=3, window_seconds=60)

    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is True
    assert count1 == 1
    assert count2 == 2
    assert count3 == 3

    # 4th request should fail
    allowed4, count4, retry4 = limiter.check_limit(
        "test_key", limit=3, window_seconds=60)

    assert allowed4 is False
    assert count4 == 4
    assert retry4 == 60  # Retry after 60 seconds


def test_rate_limiter_exemptions():
    """Test rate limit exemptions (admin bypass)"""
    limiter = create_test_limiter()

    exempt_keys = {"admin_key"}

    # Admin key should bypass limits
    for _ in range(100):
        allowed, count, retry = limiter.check_limit(
            "admin_key",
            limit=3,
            window_seconds=60,
            exempt_keys=exempt_keys
        )
        assert allowed is True
        assert count == 0  # Count should be 0 for exempt keys


def test_rate_limiter_multiple_limits():
    """Test multiple simultaneous rate limits"""
    limiter = create_test_limiter()

    # Check per-IP and per-wallet limits
    limits = [
        ("ip:192.168.1.1", 5, 60),  # 5 per minute
        ("wallet:addr1xxx", 3, 3600),  # 3 per hour
    ]

    # First 3 requests pass both limits
    for _ in range(3):
        allowed, violated_key, count, retry = limiter.check_multiple_limits(
            limits)
        assert allowed is True
        assert violated_key is None

    # 4th request violates wallet limit
    allowed, violated_key, count, retry = limiter.check_multiple_limits(limits)

    assert allowed is False
    assert violated_key == "wallet:addr1xxx"
    assert count == 4
    assert retry == 3600


def test_rate_limiter_reset():
    """Test manual rate limit reset"""
    limiter = create_test_limiter()

    # Hit limit
    for _ in range(3):
        limiter.check_limit("test_key", limit=3, window_seconds=60)

    # Next request should fail
    allowed1, _, _ = limiter.check_limit(
        "test_key", limit=3, window_seconds=60)
    assert allowed1 is False

    # Reset limit
    limiter.reset_limit("test_key")

    # Next request should pass
    allowed2, count2, _ = limiter.check_limit(
        "test_key", limit=3, window_seconds=60)
    assert allowed2 is True
    assert count2 == 1


# ============================================================================
# RateLimitConfig Tests
# ============================================================================

def test_rate_limit_config_health_check():
    """Test health check rate limit configuration"""
    config = RateLimitConfig.HEALTH_CHECK

    assert config["per_ip_limit"] == 60
    assert config["per_ip_window"] == 60


def test_rate_limit_config_enrollment():
    """Test enrollment rate limit configuration"""
    config = RateLimitConfig.ENROLLMENT

    assert config["per_ip_limit"] == 5
    assert config["per_ip_window"] == 60
    assert config["per_wallet_limit"] == 3
    assert config["per_wallet_window"] == 3600
    assert config["global_limit"] == 100
    assert config["global_window"] == 60


def test_rate_limit_config_verification():
    """Test verification rate limit configuration"""
    config = RateLimitConfig.VERIFICATION

    assert config["per_ip_limit"] == 20
    assert config["per_ip_window"] == 60
    assert config["per_wallet_limit"] == 100
    assert config["per_wallet_window"] == 3600


def test_rate_limit_config_auth():
    """Test authentication rate limit configuration"""
    config = RateLimitConfig.AUTH

    assert config["per_ip_limit"] == 10
    assert config["per_ip_window"] == 60


# ============================================================================
# Helper Function Tests
# ============================================================================

def test_get_rate_limit_key():
    """Test rate limit key generation"""
    key1 = get_rate_limit_key("ip", "192.168.1.1")
    key2 = get_rate_limit_key("wallet", "addr1xxx")
    key3 = get_rate_limit_key("global", "enrollment")

    assert key1 == "ratelimit:ip:192.168.1.1"
    assert key2 == "ratelimit:wallet:addr1xxx"
    assert key3 == "ratelimit:global:enrollment"


def test_format_rate_limit_error():
    """Test rate limit error formatting"""
    error = format_rate_limit_error(
        limit=5,
        window_seconds=60,
        current_count=6,
        retry_after=30
    )

    assert error["error"] == "Rate limit exceeded"
    assert error["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert error["current_count"] == 6
    assert error["limit"] == 5
    assert error["window_seconds"] == 60
    assert error["retry_after_seconds"] == 30
    assert "Too many requests" in error["message"]


# ============================================================================
# Integration Tests
# ============================================================================

def test_enrollment_rate_limiting_scenario():
    """Test realistic enrollment rate limiting scenario"""
    limiter = create_test_limiter()
    config = RateLimitConfig.ENROLLMENT

    ip = "192.168.1.100"
    wallet = "addr1qxyz"

    # Simulate 5 enrollment requests (at per-IP limit)
    for i in range(5):
        limits = [
            (get_rate_limit_key("ip", ip),
             config["per_ip_limit"], config["per_ip_window"]),
            (get_rate_limit_key("wallet", wallet),
             config["per_wallet_limit"], config["per_wallet_window"]),
        ]

        allowed, violated_key, count, retry = limiter.check_multiple_limits(
            limits)

        # First 3 pass wallet limit, next 2 violate wallet limit
        if i < 3:
            assert allowed is True
        else:
            assert allowed is False
            assert violated_key is not None and "wallet" in violated_key


def test_verification_rate_limiting_scenario():
    """Test realistic verification rate limiting scenario"""
    limiter = create_test_limiter()
    config = RateLimitConfig.VERIFICATION

    ip = "192.168.1.200"
    wallet = "addr1qabc"

    # Simulate 20 verification requests (at per-IP limit)
    limits = []  # Initialize variable
    for i in range(20):
        limits = [
            (get_rate_limit_key("ip", ip),
             config["per_ip_limit"], config["per_ip_window"]),
            (get_rate_limit_key("wallet", wallet),
             config["per_wallet_limit"], config["per_wallet_window"]),
        ]

        allowed, violated_key, count, retry = limiter.check_multiple_limits(
            limits)

        assert allowed is True  # All should pass (under both limits)

    # 21st request should violate IP limit
    allowed, violated_key, count, retry = limiter.check_multiple_limits(limits)
    assert allowed is False
    assert violated_key is not None and "ip" in violated_key


def test_distributed_attack_prevention():
    """Test prevention of distributed attack (multiple IPs, same wallet)"""
    limiter = create_test_limiter()
    config = RateLimitConfig.ENROLLMENT

    wallet = "addr1attacker"

    # Attacker uses 3 different IPs to bypass per-IP limit
    for i in range(3):
        ip = f"192.168.1.{100 + i}"

        limits = [
            (get_rate_limit_key("ip", ip),
             config["per_ip_limit"], config["per_ip_window"]),
            (get_rate_limit_key("wallet", wallet),
             config["per_wallet_limit"], config["per_wallet_window"]),
        ]

        allowed, violated_key, count, retry = limiter.check_multiple_limits(
            limits)
        assert allowed is True

    # 4th request from new IP should still fail (wallet limit reached)
    ip = "192.168.1.103"
    limits = [
        (get_rate_limit_key("ip", ip),
         config["per_ip_limit"], config["per_ip_window"]),
        (get_rate_limit_key("wallet", wallet),
         config["per_wallet_limit"], config["per_wallet_window"]),
    ]

    allowed, violated_key, count, retry = limiter.check_multiple_limits(limits)
    assert allowed is False
    assert violated_key is not None and "wallet" in violated_key


# ============================================================================
# Performance Tests
# ============================================================================

def test_rate_limiter_performance():
    """Test rate limiter performance (should handle 1000 checks < 100ms)"""
    limiter = create_test_limiter()

    start_time = time.time()

    for i in range(1000):
        limiter.check_limit(f"key_{i}", limit=10, window_seconds=60)

    elapsed = time.time() - start_time

    # Should complete in < 100ms
    assert elapsed < 0.1, f"Performance too slow: {elapsed:.3f}s for 1000 checks"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
