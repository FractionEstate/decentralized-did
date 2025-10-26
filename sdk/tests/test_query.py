from unittest.mock import MagicMock

import pytest

from src.decentralized_did.cardano.koios_client import KoiosClient
from src.decentralized_did.cardano.koios_scanner import KoiosMetadataRecord
from src.decentralized_did.cardano.query import CardanoQuery


class DummyKoiosScanner:
    def __init__(self, records):
        self.records = records
        self.find_calls = []

    async def find_did(self, did: str, *, label: str = "674", max_blocks: int = 1000, offset: int = 0):
        self.find_calls.append((did, label, max_blocks, offset))
        for record in self.records:
            if record.metadata.get("did") == did:
                return record
        return None

    async def iter_label_entries(self, *, label: str = "674", max_blocks: int = 1000, offset: int = 0):
        for record in self.records:
            yield record


def build_query(scanner: DummyKoiosScanner) -> CardanoQuery:
    client = MagicMock(spec=KoiosClient)
    client.metadata_scanner = scanner
    return CardanoQuery(koios_client=client, koios_scanner=scanner)


@pytest.mark.asyncio
async def test_resolve_did_found():
    did = "did:cardano:testnet:zKoios"
    record = KoiosMetadataRecord(
        label="674",
        tx_hash="tx_hash_1",
        block_hash="block_hash_1",
        block_height=123,
        tx_timestamp=456,
        metadata={
            "did": did,
            "controllers": ["addr_test1"],
            "enrollment_timestamp": "2025-10-25T12:00:00Z",
            "revoked": False,
        },
    )

    query = build_query(DummyKoiosScanner([record]))
    result = await query.resolve_did(did)

    assert result is not None
    assert result["tx_hash"] == "tx_hash_1"
    assert result["metadata"]["did"] == did


@pytest.mark.asyncio
async def test_resolve_did_not_found():
    did = "did:cardano:testnet:zMissing"
    query = build_query(DummyKoiosScanner([]))

    result = await query.resolve_did(did)

    assert result is None


@pytest.mark.asyncio
async def test_get_enrollment_history_chronological():
    did = "did:cardano:testnet:zHistory"
    records = [
        KoiosMetadataRecord(
            label="674",
            tx_hash="tx_hash_new",
            block_hash="block_new",
            block_height=200,
            tx_timestamp=222,
            metadata={"did": did, "controllers": ["addr"], "enrollment_timestamp": "2025"},
        ),
        KoiosMetadataRecord(
            label="674",
            tx_hash="tx_hash_old",
            block_hash="block_old",
            block_height=100,
            tx_timestamp=111,
            metadata={"did": did, "controllers": [], "enrollment_timestamp": "2024"},
        ),
    ]

    query = build_query(DummyKoiosScanner(records))
    history = await query.get_enrollment_history(did)

    assert len(history) == 2
    assert history[0]["enrollment_timestamp"] == "2024"
    assert history[1]["enrollment_timestamp"] == "2025"
