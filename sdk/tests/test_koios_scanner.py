import json
from typing import List

import httpx
import pytest

from src.decentralized_did.cardano.koios_scanner import (
    KoiosMetadataRecord,
    KoiosMetadataScanner,
)


BLOCKS_FIXTURE = [
    {"hash": "block0", "tx_count": 1},
    {"hash": "block1", "tx_count": 0},
    {"hash": "block2", "tx_count": 1},
    {"hash": "block3", "tx_count": 2},
]

BLOCK_TX_INFO_FIXTURE = {
    "block0": [
        {
            "tx_hash": "tx_block0",
            "block_hash": "block0",
            "block_height": 10,
            "tx_timestamp": 111,
            "metadata": {"123": {"foo": "bar"}},
        }
    ],
    "block2": [
        {
            "tx_hash": "tx_block2",
            "block_hash": "block2",
            "block_height": 30,
            "tx_timestamp": 222,
            "metadata": {
                "674": {
                    "did": "did:cardano:testnet:one",
                    "controllers": ["addr_test1"],
                    "enrollment_timestamp": "2025",
                }
            },
        }
    ],
    "block3": [
        {
            "tx_hash": "tx_block3_a",
            "block_hash": "block3",
            "block_height": 40,
            "tx_timestamp": 333,
            "metadata": {
                "674": {
                    "did": "did:cardano:testnet:two",
                    "controllers": [],
                    "enrollment_timestamp": "2024",
                }
            },
        },
        {
            "tx_hash": "tx_block3_b",
            "block_hash": "block3",
            "block_height": 40,
            "tx_timestamp": 334,
            "metadata": {
                "999": {"skip": True}
            },
        },
    ],
}


def _mock_transport(call_log: List[str]) -> httpx.MockTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        call_log.append(f"{request.method} {request.url.path}")
        if request.url.path.endswith("/blocks"):
            offset = int(request.url.params.get("offset", "0"))
            limit = int(request.url.params.get("limit", "25"))
            payload = BLOCKS_FIXTURE[offset : offset + limit]
            return httpx.Response(200, json=payload)

        if request.url.path.endswith("/block_tx_info"):
            body = json.loads(request.content.decode("utf-8"))
            payload = []
            for block_hash in body.get("_block_hashes", []):
                payload.extend(BLOCK_TX_INFO_FIXTURE.get(block_hash, []))
            return httpx.Response(200, json=payload)

        return httpx.Response(404, json={"error": "not found"})

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_find_did_returns_record():
    call_log: List[str] = []
    transport = _mock_transport(call_log)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://api.koios.rest/api/v1"
    ) as client:
        scanner = KoiosMetadataScanner(
            client=client,
            block_page_limit=2,
            block_tx_chunk=1,
        )

        record = await scanner.find_did("did:cardano:testnet:one", max_blocks=4)
        await scanner.aclose()

    assert record is not None
    assert record.tx_hash == "tx_block2"
    assert record.metadata["did"] == "did:cardano:testnet:one"
    assert call_log[0] == "GET /api/v1/blocks"


@pytest.mark.asyncio
async def test_find_did_returns_none_for_unknown_did():
    transport = _mock_transport([])
    async with httpx.AsyncClient(
        transport=transport, base_url="https://api.koios.rest/api/v1"
    ) as client:
        scanner = KoiosMetadataScanner(client=client, block_page_limit=2)
        result = await scanner.find_did("did:cardano:testnet:missing", max_blocks=3)
        await scanner.aclose()

    assert result is None


@pytest.mark.asyncio
async def test_iter_label_entries_yields_chronological_records():
    transport = _mock_transport([])
    async with httpx.AsyncClient(
        transport=transport, base_url="https://api.koios.rest/api/v1"
    ) as client:
        scanner = KoiosMetadataScanner(client=client, block_page_limit=3)

        entries = []
        async for record in scanner.iter_label_entries(max_blocks=4):
            entries.append(record)
        await scanner.aclose()

    assert len(entries) == 2
    assert isinstance(entries[0], KoiosMetadataRecord)
    # Results come back newest-first; verify ordering before downstream reversal
    assert [entry.metadata["did"] for entry in entries] == [
        "did:cardano:testnet:one",
        "did:cardano:testnet:two",
    ]


def test_scanner_invalid_configuration():
    with pytest.raises(ValueError):
        KoiosMetadataScanner(block_page_limit=0)
    with pytest.raises(ValueError):
        KoiosMetadataScanner(block_tx_chunk=0)
