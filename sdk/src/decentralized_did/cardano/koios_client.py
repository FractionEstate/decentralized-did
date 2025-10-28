"""Utilities for interacting with the Cardano blockchain via Koios."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from .cache import TTLCache
from .koios_scanner import (
    DEFAULT_METADATA_LABEL as SCANNER_DEFAULT_LABEL,
    KoiosMetadataRecord,
    KoiosMetadataScanner,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.koios.rest/api/v1"
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
DEFAULT_METADATA_SCAN_LIMIT = 1_000


@dataclass
class KoiosMetrics:
    """Basic performance counters for Koios requests."""

    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    network_requests: int = 0
    network_errors: int = 0
    total_network_latency: float = 0.0
    max_network_latency: float = 0.0

    def record_cache_hit(self) -> None:
        self.total_requests += 1
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.total_requests += 1
        self.cache_misses += 1

    def record_direct_request(self) -> None:
        self.total_requests += 1

    def record_network_attempt(self, duration: float, *, success: bool) -> None:
        self.network_requests += 1
        self.total_network_latency += duration
        if duration > self.max_network_latency:
            self.max_network_latency = duration
        if not success:
            self.network_errors += 1

    @property
    def average_network_latency(self) -> float:
        if not self.network_requests:
            return 0.0
        return self.total_network_latency / self.network_requests

    def reset(self) -> None:
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.network_requests = 0
        self.network_errors = 0
        self.total_network_latency = 0.0
        self.max_network_latency = 0.0


@dataclass
class UTXOInfo:
    """Simplified representation of a UTXO returned by Koios."""

    tx_hash: str
    tx_index: int
    amount: List[Dict[str, Any]]
    address: str
    block: Optional[str] = None
    data_hash: Optional[str] = None


@dataclass
class TransactionStatus:
    """High level transaction confirmation status."""

    tx_hash: str
    confirmed: bool
    block_height: Optional[int] = None
    block_time: Optional[int] = None
    slot: Optional[int] = None
    confirmations: Optional[int] = None
    block_hash: Optional[str] = None


class KoiosError(Exception):
    """Base exception for Koios client errors."""


class KoiosAPIError(KoiosError):
    """Raised when Koios returns an error response."""


class KoiosRateLimitError(KoiosError):
    """Raised when Koios throttles requests."""


class KoiosTransportError(KoiosError):
    """Raised when an HTTP transport error occurs."""


class DIDAlreadyExistsError(KoiosError):
    """Raised when duplicate DID enrollment is detected."""

    def __init__(self, did: str, tx_hash: str, enrollment_data: Optional[Dict[str, Any]] = None) -> None:
        self.did = did
        self.tx_hash = tx_hash
        self.enrollment_data = enrollment_data or {}
        message = (
            f"DID already exists: {did}\n"
            f"Original enrollment transaction: {tx_hash}\n"
            "This biometric identity has already been enrolled on the blockchain."
        )
        super().__init__(message)


class KoiosClient:
    """Asynchronous helper for Cardano blockchain operations via Koios."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        cache: Optional[TTLCache] = None,
        metrics: Optional[KoiosMetrics] = None,
        metadata_scan_limit: int = DEFAULT_METADATA_SCAN_LIMIT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache = cache
        self.metrics = metrics or KoiosMetrics()
        self.metadata_scan_limit = metadata_scan_limit

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"User-Agent": "decentralized-did-koios-client/1.0"},
        )
        self._metadata_scanner = KoiosMetadataScanner(
            base_url=self.base_url,
            client=self._client,
            block_page_limit=50,
        )

    @property
    def metadata_scanner(self) -> KoiosMetadataScanner:
        return self._metadata_scanner

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, *, use_cache: bool = True, **kwargs: Any) -> Any:
        method_upper = method.upper()
        cache_key = None
        if use_cache and self.cache and method_upper == "GET":
            params = kwargs.get("params") or {}
            sorted_params = tuple(sorted(params.items()))
            cache_key = (method_upper, path, sorted_params)
            cached = self.cache.get(str(cache_key))
            if cached is not None:
                logger.debug("Koios cache HIT for %s", cache_key)
                self.metrics.record_cache_hit()
                return cached
            logger.debug("Koios cache MISS for %s", cache_key)
            self.metrics.record_cache_miss()
            data = await self._http_request(method_upper, path, **kwargs)
            self.cache.set(str(cache_key), data)
            return data

        self.metrics.record_direct_request()
        return await self._http_request(method_upper, path, **kwargs)

    async def _http_request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = path if path.startswith("/") else f"/{path}"
        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= self.max_retries:
            attempt_start = time.perf_counter()
            try:
                response = await self._client.request(method, url, **kwargs)
                duration = time.perf_counter() - attempt_start

                if response.status_code == 429:
                    self.metrics.record_network_attempt(duration, success=False)
                    raise KoiosRateLimitError("Koios rate limit exceeded")

                if response.status_code >= 400:
                    message: str
                    try:
                        payload = response.json()
                        message = (
                            payload.get("message")
                            or payload.get("error")
                            or payload.get("detail")
                            or ""
                        )
                    except ValueError:
                        message = response.text

                    if response.status_code >= 500 and attempt < self.max_retries:
                        backoff = 2 ** attempt
                        logger.warning(
                            "Koios server error (%s); retrying in %ss",
                            response.status_code,
                            backoff,
                        )
                        self.metrics.record_network_attempt(duration, success=False)
                        await asyncio.sleep(backoff)
                        attempt += 1
                        continue

                    self.metrics.record_network_attempt(duration, success=False)
                    raise KoiosAPIError(
                        f"Koios error {response.status_code}: {message or 'unknown error'}"
                    )

                self.metrics.record_network_attempt(duration, success=True)

                if response.headers.get("Content-Type", "").startswith("application/json"):
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise KoiosAPIError("Koios returned invalid JSON") from exc

                return response.text

            except (httpx.RequestError, KoiosRateLimitError, KoiosAPIError) as exc:
                last_error = exc
                if isinstance(exc, KoiosRateLimitError) and attempt < self.max_retries:
                    backoff = 2 ** attempt
                    logger.warning("Koios rate limited request; retrying in %ss", backoff)
                    await asyncio.sleep(backoff)
                    attempt += 1
                    continue
                if isinstance(exc, httpx.RequestError):
                    duration = time.perf_counter() - attempt_start
                    self.metrics.record_network_attempt(duration, success=False)
                    if attempt < self.max_retries:
                        backoff = 2 ** attempt
                        logger.warning("Koios transport error; retrying in %ss", backoff)
                        await asyncio.sleep(backoff)
                        attempt += 1
                        continue
                    raise KoiosTransportError(f"Koios request failed: {exc}") from exc
                raise

        raise KoiosError(
            f"Koios request failed after {self.max_retries + 1} attempts: {method} {path}; last error: {last_error}"
        )

    async def get_address_utxos(self, address: str) -> List[UTXOInfo]:
        body = {"_addresses": [address]}
        data = await self._request("POST", "/address_utxos", use_cache=False, json=body)
        if not isinstance(data, list):
            raise KoiosAPIError("Unexpected response for /address_utxos")

        utxos: List[UTXOInfo] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            amount: List[Dict[str, Any]] = [
                {"unit": "lovelace", "quantity": str(entry.get("value", "0"))}
            ]
            asset_list = entry.get("asset_list")
            if isinstance(asset_list, list):
                for asset in asset_list:
                    if not isinstance(asset, dict):
                        continue
                    policy_id = asset.get("policy_id", "") or ""
                    asset_name = asset.get("asset_name", "") or ""
                    unit = f"{policy_id}{asset_name}"
                    amount.append(
                        {
                            "unit": unit,
                            "quantity": str(asset.get("quantity", "0")),
                        }
                    )
            utxos.append(
                UTXOInfo(
                    tx_hash=str(entry.get("tx_hash", "")),
                    tx_index=int(entry.get("tx_index", 0)),
                    amount=amount,
                    address=str(entry.get("address", address)),
                    block=str(entry.get("block_height")) if entry.get("block_height") else None,
                    data_hash=str(entry.get("datum_hash")) if entry.get("datum_hash") else None,
                )
            )
        return utxos

    async def get_address_balance(self, address: str) -> int:
        utxos = await self.get_address_utxos(address)
        total = 0
        for utxo in utxos:
            for asset in utxo.amount:
                if asset.get("unit") == "lovelace":
                    try:
                        total += int(asset.get("quantity", "0"))
                    except (ValueError, TypeError):
                        continue
        return total

    async def submit_transaction(self, tx_cbor_hex: str) -> str:
        try:
            tx_bytes = bytes.fromhex(tx_cbor_hex)
        except ValueError as exc:
            raise KoiosError(f"Invalid CBOR hex: {exc}") from exc

        result = await self._request(
            "POST",
            "/submittx",
            use_cache=False,
            content=tx_bytes,
            headers={"Content-Type": "application/cbor"},
        )
        if isinstance(result, str):
            return result.strip() or tx_cbor_hex
        raise KoiosAPIError("Unexpected response from /submittx")

    async def get_transaction_status(self, tx_hash: str) -> TransactionStatus:
        status_body = {"_tx_hashes": [tx_hash]}
        status_data = await self._request(
            "POST", "/tx_status", use_cache=False, json=status_body
        )
        confirmations: Optional[int] = None
        if isinstance(status_data, list) and status_data:
            entry = status_data[0]
            if isinstance(entry, dict):
                value = entry.get("num_confirmations")
                if isinstance(value, int):
                    confirmations = value
                elif isinstance(value, str) and value.isdigit():
                    confirmations = int(value)

        info_data = await self._request(
            "POST", "/tx_info", use_cache=False, json=status_body
        )
        block_height = None
        block_time = None
        slot = None
        block = None
        if isinstance(info_data, list) and info_data:
            entry = info_data[0]
            if isinstance(entry, dict):
                block_height = entry.get("block_height")
                block_time = entry.get("tx_timestamp")
                slot = entry.get("absolute_slot")
                block = entry.get("block_hash")

        confirmed = (confirmations or 0) > 0
        return TransactionStatus(
            tx_hash=tx_hash,
            confirmed=confirmed,
            block_height=block_height,
            block_time=block_time,
            slot=slot,
            confirmations=confirmations,
            block_hash=block,
        )

    async def wait_for_confirmation(
        self,
        tx_hash: str,
        *,
        max_wait: int = 300,
        poll_interval: int = 10,
    ) -> TransactionStatus:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status = await self.get_transaction_status(tx_hash)
            if status.confirmed:
                return status
            await asyncio.sleep(poll_interval)
        raise KoiosError(f"Transaction not confirmed within {max_wait}s")

    async def get_latest_block(self) -> Dict[str, Any]:
        tip = await self._request("GET", "/tip", params={}, use_cache=True)
        if isinstance(tip, list) and tip:
            entry = tip[0]
            if isinstance(entry, dict):
                return entry
        raise KoiosAPIError("Unexpected response for /tip")

    async def get_network_info(self) -> Dict[str, Any]:
        tip = await self.get_latest_block()
        totals = await self._request("GET", "/totals", params={}, use_cache=True)
        latest_totals: Optional[Dict[str, Any]] = None
        if isinstance(totals, list) and totals:
            entry = totals[0]
            if isinstance(entry, dict):
                latest_totals = entry
        genesis = await self._request("GET", "/genesis", params={}, use_cache=True)
        return {
            "tip": tip,
            "totals": latest_totals,
            "genesis": genesis,
        }

    async def get_transaction_metadata(self, tx_hash: str) -> List[Dict[str, Any]]:
        body = {"_tx_hashes": [tx_hash]}
        data = await self._request(
            "POST", "/tx_metadata", use_cache=False, json=body
        )
        if not isinstance(data, list):
            raise KoiosAPIError("Unexpected response for /tx_metadata")

        results: List[Dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            metadata = entry.get("metadata")
            if not isinstance(metadata, dict):
                continue
            for label, payload in metadata.items():
                results.append(
                    {
                        "label": str(label),
                        "json_metadata": payload,
                    }
                )
        return results

    async def get_transactions_by_metadata_label(
        self,
        label: str | int,
        *,
        max_blocks: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        label_str = str(label)
        limit = max_blocks or self.metadata_scan_limit
        transactions: List[Dict[str, Any]] = []
        async for record in self._metadata_scanner.iter_label_entries(
            label=label_str,
            max_blocks=limit,
        ):
            transactions.append({"tx_hash": record.tx_hash, "metadata": record.metadata})
        return transactions

    async def check_did_exists(
        self,
        did: str,
        *,
        label: str = SCANNER_DEFAULT_LABEL,
        max_blocks: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        record = await self._metadata_scanner.find_did(
            did,
            label=label,
            max_blocks=max_blocks or self.metadata_scan_limit,
        )
        if record is None:
            return None
        enrollment = _record_to_enrollment(record)
        return enrollment

    def metrics_snapshot(self) -> Dict[str, Any]:
        cache_queries = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_ratio = (
            self.metrics.cache_hits / cache_queries if cache_queries else 0.0
        )
        error_rate = (
            self.metrics.network_errors / self.metrics.network_requests
            if self.metrics.network_requests
            else 0.0
        )
        return {
            "timestamp": time.time(),
            "total_requests": self.metrics.total_requests,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "cache_hit_ratio": cache_hit_ratio,
            "network_requests": self.metrics.network_requests,
            "network_errors": self.metrics.network_errors,
            "error_rate": error_rate,
            "total_network_latency": self.metrics.total_network_latency,
            "average_network_latency": self.metrics.average_network_latency,
            "max_network_latency": self.metrics.max_network_latency,
        }

    def reset_metrics(self) -> None:
        self.metrics.reset()


def _record_to_enrollment(record: KoiosMetadataRecord) -> Dict[str, Any]:
    metadata = record.metadata
    controllers = metadata.get("controllers") or []
    if not controllers:
        wallet = metadata.get("wallet_address")
        if wallet:
            controllers = [wallet]
    return {
        "tx_hash": record.tx_hash,
        "controllers": controllers,
        "enrollment_timestamp": metadata.get("enrollment_timestamp", "unknown"),
        "revoked": metadata.get("revoked", False),
        "metadata": metadata,
    }


def convert_utxo_info_to_input(utxo: UTXOInfo) -> Dict[str, Any]:
    lovelace_amount = 0
    for asset in utxo.amount:
        if asset.get("unit") == "lovelace":
            try:
                lovelace_amount = int(asset.get("quantity", "0"))
            except (TypeError, ValueError):
                lovelace_amount = 0
            break
    return {
        "tx_hash": utxo.tx_hash,
        "tx_index": utxo.tx_index,
        "amount_lovelace": lovelace_amount,
        "address": utxo.address,
    }


def format_lovelace(lovelace: int) -> str:
    ada = lovelace / 1_000_000
    return f"{ada:.6f} ADA"
