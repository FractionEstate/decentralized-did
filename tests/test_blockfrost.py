"""
Unit tests for Blockfrost API client.

Tests cover:
- UTXO querying
- Transaction submission
- Transaction status tracking
- Rate limit handling
- Error handling
- Network configuration

Run: pytest tests/test_blockfrost.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from decentralized_did.cardano.blockfrost import (
    BlockfrostClient,
    UTXOInfo,
    TransactionStatus,
    BlockfrostError,
    BlockfrostRateLimitError,
    BlockfrostAPIError,
    convert_utxo_info_to_input,
    format_lovelace,
    BLOCKFROST_TESTNET_URL,
    BLOCKFROST_MAINNET_URL,
)


# Test fixtures

@pytest.fixture
def mock_response():
    """Mock requests.Response object."""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.headers = {}
    return response


@pytest.fixture
def blockfrost_client():
    """BlockfrostClient instance for testing."""
    return BlockfrostClient(
        api_key="test_api_key",
        network="testnet"
    )


@pytest.fixture
def sample_utxo_data():
    """Sample UTXO data from Blockfrost API."""
    return [
        {
            "tx_hash": "a" * 64,
            "output_index": 0,
            "amount": [
                {"unit": "lovelace", "quantity": "5000000"}
            ],
            "address": "addr_test1...",
            "block": "block_hash_123",
            "data_hash": None
        },
        {
            "tx_hash": "b" * 64,
            "output_index": 1,
            "amount": [
                {"unit": "lovelace", "quantity": "10000000"}
            ],
            "address": "addr_test1...",
            "block": "block_hash_456",
            "data_hash": None
        }
    ]


@pytest.fixture
def sample_tx_status_data():
    """Sample transaction status data from Blockfrost API."""
    return {
        "hash": "a" * 64,
        "block": "block_hash_123",
        "block_height": 12345,
        "block_time": 1634567890,
        "slot": 987654,
        "index": 5
    }


# Client Initialization Tests

def test_client_initialization_testnet():
    """Test client initialization with testnet."""
    client = BlockfrostClient(
        api_key="test_key",
        network="testnet"
    )

    assert client.api_key == "test_key"
    assert client.network == "testnet"
    assert client.base_url == BLOCKFROST_TESTNET_URL
    assert "project_id" in client.session.headers
    assert client.session.headers["project_id"] == "test_key"


def test_client_initialization_mainnet():
    """Test client initialization with mainnet."""
    client = BlockfrostClient(
        api_key="mainnet_key",
        network="mainnet"
    )

    assert client.network == "mainnet"
    assert client.base_url == BLOCKFROST_MAINNET_URL


def test_client_initialization_invalid_network():
    """Test client initialization with invalid network."""
    with pytest.raises(ValueError, match="Invalid network"):
        BlockfrostClient(
            api_key="test_key",
            network="invalid"
        )


# UTXO Query Tests

@patch('requests.Session.request')
def test_get_address_utxos_success(mock_request, blockfrost_client, sample_utxo_data, mock_response):
    """Test successful UTXO query."""
    mock_response.json.return_value = sample_utxo_data
    mock_request.return_value = mock_response

    utxos = blockfrost_client.get_address_utxos("addr_test1...")

    assert len(utxos) == 2
    assert isinstance(utxos[0], UTXOInfo)
    assert utxos[0].tx_hash == "a" * 64
    assert utxos[0].tx_index == 0
    assert utxos[1].tx_hash == "b" * 64
    assert utxos[1].tx_index == 1


@patch('requests.Session.request')
def test_get_address_utxos_empty(mock_request, blockfrost_client, mock_response):
    """Test UTXO query for address with no UTXOs."""
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Address not found"}
    mock_request.return_value = mock_response

    utxos = blockfrost_client.get_address_utxos("addr_test1...")

    assert len(utxos) == 0


@patch('requests.Session.request')
def test_get_address_balance(mock_request, blockfrost_client, sample_utxo_data, mock_response):
    """Test address balance calculation."""
    mock_response.json.return_value = sample_utxo_data
    mock_request.return_value = mock_response

    balance = blockfrost_client.get_address_balance("addr_test1...")

    # 5,000,000 + 10,000,000 = 15,000,000 lovelace
    assert balance == 15_000_000


# Transaction Submission Tests

@patch('requests.Session.post')
def test_submit_transaction_success(mock_post, blockfrost_client, mock_response):
    """Test successful transaction submission."""
    tx_hash = "c" * 64
    mock_response.json.return_value = tx_hash
    mock_post.return_value = mock_response

    tx_cbor = "84a300818258200000000000000000000000000000000000000000000000000000000000000000000182825839000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001a000f4240021a0002b5b5a0f5f6"

    result = blockfrost_client.submit_transaction(tx_cbor)

    assert result == tx_hash
    mock_post.assert_called_once()


@patch('requests.Session.post')
def test_submit_transaction_failure(mock_post, blockfrost_client, mock_response):
    """Test failed transaction submission."""
    mock_response.status_code = 400
    mock_response.text = "Invalid transaction"
    mock_response.json.return_value = {"message": "Invalid transaction"}
    mock_post.return_value = mock_response

    # Use valid hex that will trigger API error (not hex parsing error)
    valid_hex = "84a300"
    with pytest.raises(BlockfrostAPIError, match="Invalid transaction"):
        blockfrost_client.submit_transaction(valid_hex)


@patch('requests.Session.post')
def test_submit_transaction_invalid_hex(mock_post, blockfrost_client):
    """Test transaction submission with invalid hex."""
    with pytest.raises(BlockfrostError, match="Invalid CBOR hex"):
        blockfrost_client.submit_transaction("not_valid_hex!")


# Transaction Status Tests

@patch('requests.Session.request')
def test_get_transaction_status_confirmed(mock_request, blockfrost_client, sample_tx_status_data, mock_response):
    """Test getting status of confirmed transaction."""
    mock_response.json.return_value = sample_tx_status_data
    mock_request.return_value = mock_response

    status = blockfrost_client.get_transaction_status("a" * 64)

    assert isinstance(status, TransactionStatus)
    assert status.confirmed is True
    assert status.block_height == 12345
    assert status.slot == 987654


@patch('requests.Session.request')
def test_get_transaction_status_pending(mock_request, blockfrost_client, mock_response):
    """Test getting status of pending transaction."""
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Transaction not found"}
    mock_request.return_value = mock_response

    status = blockfrost_client.get_transaction_status("a" * 64)

    assert status.confirmed is False
    assert status.block_height is None


@patch('requests.Session.request')
def test_wait_for_confirmation_success(mock_request, blockfrost_client, sample_tx_status_data, mock_response):
    """Test waiting for transaction confirmation."""
    mock_response.json.return_value = sample_tx_status_data
    mock_request.return_value = mock_response

    status = blockfrost_client.wait_for_confirmation(
        "a" * 64,
        max_wait=5,
        poll_interval=1
    )

    assert status.confirmed is True


@patch('requests.Session.request')
def test_wait_for_confirmation_timeout(mock_request, blockfrost_client, mock_response):
    """Test waiting for confirmation times out."""
    # Always return pending status
    pending_data = {"hash": "a" * 64, "block": None}
    mock_response.json.return_value = pending_data
    mock_request.return_value = mock_response

    with pytest.raises(BlockfrostError, match="not confirmed within"):
        blockfrost_client.wait_for_confirmation(
            "a" * 64,
            max_wait=2,
            poll_interval=1
        )


# Error Handling Tests

@patch('requests.Session.request')
def test_rate_limit_error(mock_request, blockfrost_client, mock_response):
    """Test rate limit error handling."""
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "60"}
    mock_request.return_value = mock_response

    with pytest.raises(BlockfrostRateLimitError, match="Rate limit exceeded"):
        blockfrost_client.get_address_utxos("addr_test1...")


@patch('requests.Session.request')
def test_api_error_handling(mock_request, blockfrost_client, mock_response):
    """Test API error handling."""
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    mock_response.json.return_value = {"message": "Internal server error"}
    mock_request.return_value = mock_response

    with pytest.raises(BlockfrostAPIError, match="Internal server error"):
        blockfrost_client.get_address_utxos("addr_test1...")


@patch('requests.Session.request')
def test_timeout_error(mock_request, blockfrost_client):
    """Test timeout error handling."""
    mock_request.side_effect = requests.exceptions.Timeout()

    with pytest.raises(BlockfrostError, match="Request timeout"):
        blockfrost_client.get_address_utxos("addr_test1...")


@patch('requests.Session.request')
def test_connection_error(mock_request, blockfrost_client):
    """Test connection error handling."""
    mock_request.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(BlockfrostError, match="Request failed"):
        blockfrost_client.get_address_utxos("addr_test1...")


# Network Info Tests

@patch('requests.Session.request')
def test_get_latest_block(mock_request, blockfrost_client, mock_response):
    """Test getting latest block info."""
    block_data = {
        "hash": "block_hash_123",
        "height": 12345,
        "slot": 987654,
        "time": 1634567890
    }
    mock_response.json.return_value = block_data
    mock_request.return_value = mock_response

    block = blockfrost_client.get_latest_block()

    assert block["height"] == 12345
    assert block["slot"] == 987654


@patch('requests.Session.request')
def test_get_network_info(mock_request, blockfrost_client, mock_response):
    """Test getting network info."""
    network_data = {
        "supply": {"circulating": "35000000000000000"},
        "stake": {"active": "25000000000000000"}
    }
    mock_response.json.return_value = network_data
    mock_request.return_value = mock_response

    info = blockfrost_client.get_network_info()

    assert "supply" in info
    assert "stake" in info


# Utility Function Tests

def test_convert_utxo_info_to_input():
    """Test converting UTXOInfo to transaction input format."""
    utxo = UTXOInfo(
        tx_hash="a" * 64,
        tx_index=0,
        amount=[{"unit": "lovelace", "quantity": "5000000"}],
        address="addr_test1...",
        block="block_hash"
    )

    input_dict = convert_utxo_info_to_input(utxo)

    assert input_dict["tx_hash"] == "a" * 64
    assert input_dict["tx_index"] == 0
    assert input_dict["amount_lovelace"] == 5_000_000
    assert input_dict["address"] == "addr_test1..."


def test_format_lovelace():
    """Test lovelace formatting."""
    assert format_lovelace(1_000_000) == "1.000000 ADA"
    assert format_lovelace(5_500_000) == "5.500000 ADA"
    assert format_lovelace(123_456_789) == "123.456789 ADA"


def test_format_lovelace_zero():
    """Test formatting zero lovelace."""
    assert format_lovelace(0) == "0.000000 ADA"


def test_format_lovelace_large():
    """Test formatting large amounts."""
    assert format_lovelace(1_000_000_000_000) == "1000000.000000 ADA"


# Integration Tests

@patch('requests.Session.request')
@patch('requests.Session.post')
def test_full_transaction_flow(mock_post, mock_request, blockfrost_client, sample_utxo_data, mock_response):
    """Test full transaction flow: query UTXOs, submit, check status."""
    # Mock UTXO query
    utxo_response = Mock(spec=requests.Response)
    utxo_response.status_code = 200
    utxo_response.json.return_value = sample_utxo_data

    # Mock transaction submission
    submit_response = Mock(spec=requests.Response)
    submit_response.status_code = 200
    submit_response.json.return_value = "tx_hash_123"

    # Mock status query
    status_response = Mock(spec=requests.Response)
    status_response.status_code = 200
    status_response.json.return_value = {
        "hash": "tx_hash_123",
        "block": "block_hash",
        "block_height": 12345
    }

    mock_request.return_value = utxo_response
    mock_post.return_value = submit_response

    # 1. Query UTXOs
    utxos = blockfrost_client.get_address_utxos("addr_test1...")
    assert len(utxos) == 2

    # 2. Submit transaction (use valid hex)
    valid_tx_hex = "84a30081825820" + ("0" * 56) + "00018258390000"
    tx_hash = blockfrost_client.submit_transaction(valid_tx_hex)
    assert tx_hash == "tx_hash_123"    # 3. Check status
    mock_request.return_value = status_response
    status = blockfrost_client.get_transaction_status(tx_hash)
    assert status.confirmed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
