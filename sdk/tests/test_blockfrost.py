"""Async unit tests for the Blockfrost API client."""

from decentralized_did.cardano.blockfrost import (
    BLOCKFROST_MAINNET_URL,
    BLOCKFROST_TESTNET_URL,
    BlockfrostAPIError,
    BlockfrostClient,
    BlockfrostError,
    BlockfrostRateLimitError,
    TransactionStatus,
    UTXOInfo,
    convert_utxo_info_to_input,
    format_lovelace,
)
import json
from contextlib import asynccontextmanager
from typing import Any, Dict, List
from collections.abc import AsyncIterator

import httpx
import pytest
from unittest.mock import AsyncMock


def make_httpx_response(
    status_code: int = 200,
    json_data: Any = None,
    text: str = "",
    headers: Dict[str, str] | None = None,
    method: str = "GET",
) -> httpx.Response:
    """Create an httpx.Response with optional JSON payload for testing."""
    if json_data is not None:
        content = json.dumps(json_data).encode("utf-8")
    else:
        content = text.encode("utf-8")
    request = httpx.Request(method, "https://blockfrost.test/api")
    return httpx.Response(
        status_code=status_code,
        headers=headers or {},
        content=content,
        request=request,
    )


@asynccontextmanager
async def blockfrost_client_context(
    *,
    api_key: str = "test_api_key",
    network: str = "testnet",
    **kwargs: Any,
) -> AsyncIterator[BlockfrostClient]:
    client = BlockfrostClient(api_key=api_key, network=network, **kwargs)
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
def sample_utxo_data() -> List[Dict[str, Any]]:
    return [
        {
            "tx_hash": "a" * 64,
            "output_index": 0,
            "amount": [
                {"unit": "lovelace", "quantity": "5000000"},
                {"unit": "token1", "quantity": "10"},
            ],
            "address": "addr_test1...",
            "block": "block_hash_123",
            "data_hash": None,
        },
        {
            "tx_hash": "b" * 64,
            "output_index": 1,
            "amount": [
                {"unit": "lovelace", "quantity": "10000000"},
            ],
            "address": "addr_test1...",
            "block": "block_hash_456",
            "data_hash": None,
        },
    ]


@pytest.fixture
def sample_tx_status_data() -> Dict[str, Any]:
    return {
        "hash": "a" * 64,
        "block": "block_hash_123",
        "block_height": 12345,
        "block_time": 1634567890,
        "slot": 987654,
        "index": 5,
    }


@pytest.mark.asyncio
async def test_client_initialization_testnet():
    client = BlockfrostClient(api_key="test_key", network="testnet")
    try:
        assert client.api_key == "test_key"
        assert client.network == "testnet"
        assert client.base_url == BLOCKFROST_TESTNET_URL
        assert client.session.headers["project_id"] == "test_key"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_client_initialization_mainnet():
    client = BlockfrostClient(api_key="mainnet_key", network="mainnet")
    try:
        assert client.network == "mainnet"
        assert client.base_url == BLOCKFROST_MAINNET_URL
    finally:
        await client.close()


def test_client_initialization_invalid_network():
    with pytest.raises(ValueError, match="Invalid network"):
        BlockfrostClient(api_key="test_key", network="invalid")


@pytest.mark.asyncio
async def test_get_address_utxos_success(sample_utxo_data):
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(return_value=sample_utxo_data)

        utxos = await blockfrost_client.get_address_utxos("addr_test1...")

        assert len(utxos) == 2
        assert isinstance(utxos[0], UTXOInfo)
        assert utxos[0].tx_hash == "a" * 64
        assert utxos[1].tx_index == 1


@pytest.mark.asyncio
async def test_get_address_utxos_empty():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=BlockfrostAPIError(
                "API error (404): Address not found")
        )

        utxos = await blockfrost_client.get_address_utxos("addr_test1...")
        assert utxos == []


@pytest.mark.asyncio
async def test_get_address_balance(sample_utxo_data):
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(return_value=sample_utxo_data)

        balance = await blockfrost_client.get_address_balance("addr_test1...")

        assert balance == 15_000_000


@pytest.mark.asyncio
async def test_submit_transaction_success():
    tx_hash = "c" * 64
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.session.request = AsyncMock(
            return_value=make_httpx_response(json_data=tx_hash, method="POST")
        )

        result = await blockfrost_client.submit_transaction("84a300")

        assert result == tx_hash
        blockfrost_client.session.request.assert_awaited_once()
        assert blockfrost_client.metrics.total_requests == 1


@pytest.mark.asyncio
async def test_submit_transaction_failure():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.session.request = AsyncMock(
            return_value=make_httpx_response(
                status_code=400,
                json_data={"message": "Invalid transaction"},
                method="POST",
            )
        )

        with pytest.raises(BlockfrostAPIError, match="Invalid transaction"):
            await blockfrost_client.submit_transaction("84a300")

        assert blockfrost_client.metrics.total_requests == 1


@pytest.mark.asyncio
async def test_submit_transaction_invalid_hex():
    async with blockfrost_client_context() as blockfrost_client:
        with pytest.raises(BlockfrostError, match="Invalid CBOR hex"):
            await blockfrost_client.submit_transaction("not_valid_hex!")


@pytest.mark.asyncio
async def test_get_transaction_status_confirmed(sample_tx_status_data):
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            return_value=sample_tx_status_data)

        status = await blockfrost_client.get_transaction_status("a" * 64)

        assert isinstance(status, TransactionStatus)
        assert status.confirmed is True
        assert status.block_height == 12345


@pytest.mark.asyncio
async def test_get_transaction_status_pending():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=BlockfrostAPIError(
                "API error (404): Transaction not found")
        )

        status = await blockfrost_client.get_transaction_status("a" * 64)

        assert status.confirmed is False
        assert status.block_height is None


@pytest.mark.asyncio
async def test_wait_for_confirmation_success():
    pending_status = TransactionStatus(tx_hash="tx", confirmed=False)
    confirmed_status = TransactionStatus(
        tx_hash="tx", confirmed=True, block_height=10)

    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.get_transaction_status = AsyncMock(
            side_effect=[pending_status, confirmed_status]
        )

        status = await blockfrost_client.wait_for_confirmation(
            "tx",
            max_wait=5,
            poll_interval=0,
        )

        assert status.confirmed is True
        assert blockfrost_client.get_transaction_status.await_count == 2


@pytest.mark.asyncio
async def test_wait_for_confirmation_timeout():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.get_transaction_status = AsyncMock(
            return_value=TransactionStatus(tx_hash="tx", confirmed=False)
        )

        with pytest.raises(BlockfrostError, match="not confirmed within"):
            await blockfrost_client.wait_for_confirmation("tx", max_wait=0, poll_interval=0)


@pytest.mark.asyncio
async def test_rate_limit_error():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._http_request = AsyncMock(
            side_effect=BlockfrostRateLimitError(
                "Rate limit exceeded. Retry after 60 seconds.")
        )

        with pytest.raises(BlockfrostRateLimitError):
            await blockfrost_client.get_address_utxos("addr_test1...")


@pytest.mark.asyncio
async def test_api_error_handling():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._http_request = AsyncMock(
            side_effect=BlockfrostAPIError(
                "API error (500): Internal server error")
        )

        with pytest.raises(BlockfrostAPIError):
            await blockfrost_client.get_address_utxos("addr_test1...")


@pytest.mark.asyncio
async def test_timeout_error():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.max_retries = 0
        blockfrost_client.session.request = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )

        with pytest.raises(BlockfrostError, match="Request timeout"):
            await blockfrost_client._http_request("GET", "/test")


@pytest.mark.asyncio
async def test_connection_error():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.max_retries = 0
        blockfrost_client.session.request = AsyncMock(
            side_effect=httpx.NetworkError("connection failure")
        )

        with pytest.raises(BlockfrostError, match="Request failed"):
            await blockfrost_client._http_request("GET", "/test")


@pytest.mark.asyncio
async def test_http_retry_on_server_error():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.session.request = AsyncMock(
            side_effect=[
                make_httpx_response(
                    status_code=500,
                    json_data={"message": "Internal"},
                ),
                make_httpx_response(json_data={"ok": True}),
            ]
        )

        result = await blockfrost_client._http_request("GET", "/test")

        assert result == {"ok": True}
        assert blockfrost_client.session.request.await_count == 2


@pytest.mark.asyncio
async def test_get_latest_block():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            return_value={"height": 12345, "slot": 987654}
        )

        block = await blockfrost_client.get_latest_block()

        assert block["height"] == 12345


@pytest.mark.asyncio
async def test_get_network_info():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            return_value={"stake": {"live": {"stake": 1_000_000}}}
        )

        network_info = await blockfrost_client.get_network_info()

        assert network_info["stake"]["live"]["stake"] == 1_000_000


@pytest.mark.asyncio
async def test_check_did_exists_found():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=[
                [{"tx_hash": "tx1"}],
                [
                    {
                        "label": "674",
                        "json_metadata": {
                            "did": "did:cardano:...",
                            "controllers": ["addr_test1..."],
                            "enrollment_timestamp": "2024-01-01T00:00:00Z",
                            "revoked": False,
                        },
                    }
                ],
            ]
        )

        enrollment = await blockfrost_client.check_did_exists("did:cardano:...")

        assert enrollment is not None
        assert enrollment["tx_hash"] == "tx1"
        assert enrollment["controllers"] == ["addr_test1..."]


@pytest.mark.asyncio
async def test_check_did_exists_not_found():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=[
                [{"tx_hash": "tx1"}],
                [
                    {
                        "label": "674",
                        "json_metadata": {
                            "did": "did:cardano:other",
                        },
                    }
                ],
                [],
            ]
        )

        enrollment = await blockfrost_client.check_did_exists("did:cardano:...")

        assert enrollment is None


@pytest.mark.asyncio
async def test_check_did_exists_rate_limited():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=BlockfrostRateLimitError(
                "Rate limit exceeded. Retry after 30 seconds.")
        )

        with pytest.raises(BlockfrostRateLimitError):
            await blockfrost_client.check_did_exists("did:cardano:...")


@pytest.mark.asyncio
async def test_check_did_exists_unexpected_error():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=BlockfrostAPIError(
                "API error (500): Internal server error")
        )

        with pytest.raises(BlockfrostAPIError):
            await blockfrost_client.check_did_exists("did:cardano:...")


@pytest.mark.asyncio
async def test_check_did_exists_unexpected_structure():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client._request = AsyncMock(
            side_effect=[
                [{"tx_hash": "tx1"}],
                [
                    {
                        "label": "674",
                        "json_metadata": "not-a-dict",
                    }
                ],
                [],
            ]
        )

        enrollment = await blockfrost_client.check_did_exists("did:cardano:...")

        assert enrollment is None


@pytest.mark.asyncio
async def test_convert_utxo_info_to_input(sample_utxo_data):
    utxo = UTXOInfo(
        tx_hash=sample_utxo_data[0]["tx_hash"],
        tx_index=sample_utxo_data[0]["output_index"],
        amount=sample_utxo_data[0]["amount"],
        address=sample_utxo_data[0]["address"],
        block=sample_utxo_data[0]["block"],
        data_hash=sample_utxo_data[0]["data_hash"],
    )

    tx_input = convert_utxo_info_to_input(utxo)

    assert tx_input["tx_hash"] == "a" * 64
    assert tx_input["tx_index"] == 0
    assert tx_input["amount_lovelace"] == 5_000_000
    assert tx_input["address"] == "addr_test1..."


@pytest.mark.asyncio
async def test_format_lovelace():
    assert format_lovelace(0) == "0.000000 ADA"
    assert format_lovelace(1_000_000) == "1.000000 ADA"
    assert format_lovelace(1_234_567) == "1.234567 ADA"


@pytest.mark.asyncio
async def test_close():
    client = BlockfrostClient(api_key="key", network="testnet")
    client.session.aclose = AsyncMock()
    await client.close()
    client.session.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_metrics_capture_network_success():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.session.request = AsyncMock(
            return_value=make_httpx_response(json_data={"ok": True})
        )

        data = await blockfrost_client._http_request("GET", "/metrics")

        assert data == {"ok": True}
        assert blockfrost_client.metrics.network_requests == 1
        assert blockfrost_client.metrics.network_errors == 0
        assert blockfrost_client.metrics.total_network_latency >= 0.0
        assert (
            blockfrost_client.metrics.max_network_latency
            == blockfrost_client.metrics.total_network_latency
        )


@pytest.mark.asyncio
async def test_metrics_capture_network_error():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.max_retries = 0
        blockfrost_client.session.request = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )

        with pytest.raises(BlockfrostError, match="Request timeout"):
            await blockfrost_client._http_request("GET", "/metrics")

        assert blockfrost_client.metrics.network_requests == 1
        assert blockfrost_client.metrics.network_errors == 1


@pytest.mark.asyncio
async def test_metrics_snapshot_and_reset():
    async with blockfrost_client_context() as blockfrost_client:
        blockfrost_client.session.request = AsyncMock(
            return_value=make_httpx_response(json_data={"ok": True})
        )

        await blockfrost_client._request("GET", "/snapshot")

        snapshot = blockfrost_client.metrics_snapshot()

        assert snapshot["total_requests"] == 1
        assert snapshot["network_requests"] == 1
        assert "average_network_latency" in snapshot
        assert snapshot["cache_hit_ratio"] == 0.0

        blockfrost_client.reset_metrics()

        assert blockfrost_client.metrics.total_requests == 0
        assert blockfrost_client.metrics.network_requests == 0
