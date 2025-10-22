"""Tests for BlockfrostClient caching functionality."""

import pytest
from unittest.mock import AsyncMock

from src.decentralized_did.cardano.blockfrost import BlockfrostClient
from src.decentralized_did.cardano.cache import TTLCache


@pytest.mark.asyncio
async def test_get_request_caching():
    cache = TTLCache(default_ttl=60)
    client = BlockfrostClient(api_key="test_api_key", cache=cache)
    try:
        client._http_request = AsyncMock(return_value={"data": "test"})

        await client._request("GET", "/test")
        await client._request("GET", "/test")

        client._http_request.assert_awaited_once()
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_post_request_not_cached():
    cache = TTLCache(default_ttl=60)
    client = BlockfrostClient(api_key="test_api_key", cache=cache)
    try:
        client._http_request = AsyncMock(return_value={"data": "test"})

        await client._request("POST", "/test")
        await client._request("POST", "/test")

        assert client._http_request.await_count == 2
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_cache_key_uniqueness():
    cache = TTLCache(default_ttl=60)
    client = BlockfrostClient(api_key="test_api_key", cache=cache)
    try:
        client._http_request = AsyncMock(return_value={"data": "test"})

        await client._request("GET", "/test1")
        await client._request("GET", "/test2")

        assert client._http_request.await_count == 2
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_metrics_track_cache_usage():
    cache = TTLCache(default_ttl=60)
    client = BlockfrostClient(api_key="test_api_key", cache=cache)
    try:
        client._http_request = AsyncMock(return_value={"data": "test"})

        await client._request("GET", "/metrics")  # miss
        await client._request("GET", "/metrics")  # hit

        assert client.metrics.total_requests == 2
        assert client.metrics.cache_misses == 1
        assert client.metrics.cache_hits == 1
    finally:
        await client.close()
