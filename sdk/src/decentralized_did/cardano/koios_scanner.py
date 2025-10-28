"""Asynchronous helpers for querying Cardano metadata via Koios.

This module provides a minimal client focused on metadata label scans so we can
resolve biometric DID enrollments without relying on Blockfrost. The client is
intentionally lightweight: it only fetches paginated block summaries and the
associated transaction metadata for selected blocks.

Usage example:

    scanner = KoiosMetadataScanner()
    record = await scanner.find_did("did:cardano:mainnet:...")
    await scanner.aclose()

The implementation only depends on the public Koios REST API and does not
require API keys or paid services, keeping parity with the repository's
open-source constraint.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.koios.rest/api/v1"
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_BLOCK_PAGE_LIMIT = 25
DEFAULT_BLOCK_TX_CHUNK = 10
DEFAULT_METADATA_LABEL = "674"


class KoiosError(Exception):
    """Base exception for Koios client errors."""


class KoiosAPIError(KoiosError):
    """Raised when Koios responds with a non-success status code."""


class KoiosRateLimitError(KoiosError):
    """Raised when Koios signals that the public rate limit was exceeded."""


class KoiosTransportError(KoiosError):
    """Raised when an HTTP or network level error occurs."""


@dataclass(frozen=True)
class KoiosMetadataRecord:
    """Metadata entry pulled from the blockchain for a specific label."""

    label: str
    tx_hash: str
    block_hash: Optional[str]
    block_height: Optional[int]
    tx_timestamp: Optional[int]
    metadata: Dict[str, Any]


def _chunked(sequence: Iterable[str], size: int) -> Iterable[List[str]]:
    """Yield fixed-size chunks from *sequence* preserving order."""

    chunk: List[str] = []
    for item in sequence:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


class KoiosMetadataScanner:
    """Minimal Koios helper that searches metadata labels across recent blocks."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        block_page_limit: int = DEFAULT_BLOCK_PAGE_LIMIT,
        block_tx_chunk: int = DEFAULT_BLOCK_TX_CHUNK,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if block_page_limit <= 0:
            raise ValueError("block_page_limit must be positive")
        if block_tx_chunk <= 0:
            raise ValueError("block_tx_chunk must be positive")

        self.base_url = base_url.rstrip("/")
        self.block_page_limit = block_page_limit
        self.block_tx_chunk = block_tx_chunk
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": "decentralized-did-koios-scanner/1.0"},
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP client if this instance owns it."""

        if self._owns_client:
            await self._client.aclose()

    async def find_did(
        self,
        did: str,
        *,
        label: str = DEFAULT_METADATA_LABEL,
        max_blocks: int = 1_000,
        offset: int = 0,
    ) -> Optional[KoiosMetadataRecord]:
        """Search the blockchain for a DID enrollment metadata entry.

        Args:
            did: Deterministic DID we are searching for.
            label: Metadata label to inspect (defaults to 674).
            max_blocks: Maximum number of recent blocks to scan.
            offset: Initial pagination offset in the blocks list.

        Returns:
            A :class:`KoiosMetadataRecord` when the DID is found, otherwise
            ``None``.
        """

        if max_blocks <= 0:
            return None

        async for record in self.iter_label_entries(
            label=label,
            max_blocks=max_blocks,
            offset=offset,
        ):
            payload = record.metadata
            if isinstance(payload, dict) and payload.get("did") == did:
                logger.info(
                    "Found DID %s in transaction %s (block %s)",
                    did,
                    record.tx_hash,
                    record.block_height,
                )
                return record

        return None

    async def iter_label_entries(
        self,
        *,
        label: str = DEFAULT_METADATA_LABEL,
        max_blocks: int = 1_000,
        offset: int = 0,
    ) -> AsyncIterator[KoiosMetadataRecord]:
        """Yield metadata entries for *label* scanning up to *max_blocks*.

        This generator walks blocks in reverse chronological order (Koios
        default ordering) and fetches full transaction metadata for blocks that
        contain transactions. It yields records only when the metadata payload
        for the desired label is a JSON object.
        """

        remaining = max_blocks
        current_offset = max(offset, 0)
        label_str = str(label)

        while remaining > 0:
            page_limit = min(self.block_page_limit, remaining)
            blocks = await self._get_blocks(limit=page_limit, offset=current_offset)
            if not blocks:
                break

            current_offset += len(blocks)
            remaining -= len(blocks)

            block_hashes = [
                block["hash"]
                for block in blocks
                if isinstance(block, dict) and block.get("tx_count", 0) > 0
            ]

            if not block_hashes:
                continue

            for chunk in _chunked(block_hashes, self.block_tx_chunk):
                tx_entries = await self._get_block_tx_info(chunk)
                for entry in tx_entries:
                    if not isinstance(entry, dict):
                        continue
                    metadata = entry.get("metadata")
                    if not isinstance(metadata, dict):
                        continue
                    payload = metadata.get(label_str)
                    if not isinstance(payload, dict):
                        continue
                    yield KoiosMetadataRecord(
                        label=label_str,
                        tx_hash=str(entry.get("tx_hash", "")),
                        block_hash=str(entry.get("block_hash"))
                        if entry.get("block_hash")
                        else None,
                        block_height=entry.get("block_height"),
                        tx_timestamp=entry.get("tx_timestamp"),
                        metadata=payload,
                    )

    async def _get_blocks(
        self,
        *,
        limit: int,
        offset: int,
    ) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset}
        data = await self._request("GET", "/blocks", params=params)
        if not isinstance(data, list):
            raise KoiosAPIError("Unexpected response for /blocks")
        return data

    async def _get_block_tx_info(
        self,
        block_hashes: List[str],
    ) -> List[Dict[str, Any]]:
        if not block_hashes:
            return []
        body = {"_block_hashes": block_hashes, "_metadata": True}
        data = await self._request("POST", "/block_tx_info", json=body)
        if not isinstance(data, list):
            raise KoiosAPIError("Unexpected response for /block_tx_info")
        return data

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Any:
        url = path if path.startswith("/") else f"/{path}"
        try:
            response = await self._client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise KoiosTransportError(f"Koios request failed: {exc}") from exc

        if response.status_code == 429:
            raise KoiosRateLimitError("Koios public tier rate limit exceeded")
        if response.status_code >= 400:
            message: str
            try:
                payload = response.json()
                message = payload.get("message") or payload.get("error") or ""
            except ValueError:
                message = response.text
            raise KoiosAPIError(
                f"Koios error {response.status_code}: {message or 'unknown error'}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise KoiosAPIError("Koios returned invalid JSON") from exc

