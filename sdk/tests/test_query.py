import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from src.decentralized_did.cardano.blockfrost import BlockfrostClient
from src.decentralized_did.cardano.query import CardanoQuery


@pytest.fixture
def mock_blockfrost_client():
    client = MagicMock(spec=BlockfrostClient)
    client.check_did_exists = AsyncMock()
    client.get_transactions_by_metadata_label = AsyncMock()
    client.get_transaction_metadata = AsyncMock()
    return client


@pytest.fixture
def cardano_query(mock_blockfrost_client):
    return CardanoQuery(mock_blockfrost_client)


@pytest.mark.asyncio
async def test_resolve_did_found(cardano_query, mock_blockfrost_client):
    did = "did:cardano:testnet:zQm..."
    metadata = {"did": did, "data": "some_data"}
    mock_blockfrost_client.check_did_exists.return_value = metadata

    result = await cardano_query.resolve_did(did)

    assert result == metadata
    mock_blockfrost_client.check_did_exists.assert_awaited_once_with(did)


@pytest.mark.asyncio
async def test_resolve_did_not_found(cardano_query, mock_blockfrost_client):
    did = "did:cardano:testnet:zQm..."
    mock_blockfrost_client.check_did_exists.return_value = None

    result = await cardano_query.resolve_did(did)

    assert result is None
    mock_blockfrost_client.check_did_exists.assert_awaited_once_with(did)


@pytest.mark.asyncio
async def test_get_enrollment_history(cardano_query, mock_blockfrost_client):
    did = "did:cardano:testnet:zQm..."
    txs = [{"tx_hash": "tx1"}, {"tx_hash": "tx2"}]
    metadata1 = [{"label": "674", "json_metadata": {
        "did": did, "version": "1.0"}}]
    metadata2 = [{"label": "674", "json_metadata": {"did": "did:other", "version": "1.0"}}, {
        "label": "674", "json_metadata": {"did": did, "version": "1.1"}}]

    mock_blockfrost_client.get_transactions_by_metadata_label.return_value = txs
    mock_blockfrost_client.get_transaction_metadata.side_effect = [
        metadata1, metadata2]

    history = await cardano_query.get_enrollment_history(did)

    assert len(history) == 2
    assert history[0]["version"] == "1.0"
    assert history[1]["version"] == "1.1"
    mock_blockfrost_client.get_transactions_by_metadata_label.assert_awaited_once_with(
        674)
    assert mock_blockfrost_client.get_transaction_metadata.await_count == 2
    mock_blockfrost_client.get_transaction_metadata.assert_any_await("tx1")
    mock_blockfrost_client.get_transaction_metadata.assert_any_await("tx2")
