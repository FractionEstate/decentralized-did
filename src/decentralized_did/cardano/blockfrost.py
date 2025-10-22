"""
Blockfrost API Client for Cardano Blockchain Interaction

This module provides a wrapper around the Blockfrost API for querying
UTXOs, submitting transactions, and tracking transaction status.

Features:
- UTXO querying by address
- Transaction submission
- Transaction status tracking
- DID duplicate detection (Sybil attack prevention)
- Metadata querying by label
- Rate limit handling
- Error handling and retries
- Both testnet and mainnet support

License: Apache 2.0
"""

import logging
import time
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import httpx
from urllib.parse import urlencode

from .cache import TTLCache

logger = logging.getLogger(__name__)


# Constants
BLOCKFROST_TESTNET_URL = "https://cardano-preprod.blockfrost.io/api/v0"
BLOCKFROST_MAINNET_URL = "https://cardano-mainnet.blockfrost.io/api/v0"
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3


@dataclass
class BlockfrostMetrics:
    """Lightweight performance counters for Blockfrost requests."""

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
    """UTXO information from Blockfrost API"""

    tx_hash: str
    tx_index: int
    # [{"unit": "lovelace", "quantity": "1000000"}]
    amount: List[Dict[str, Any]]
    address: str
    block: str
    data_hash: Optional[str] = None


@dataclass
class TransactionStatus:
    """Transaction status information"""

    tx_hash: str
    confirmed: bool
    block_height: Optional[int] = None
    block_time: Optional[int] = None
    slot: Optional[int] = None
    index: Optional[int] = None


class BlockfrostError(Exception):
    """Base exception for Blockfrost API errors"""
    pass


class BlockfrostRateLimitError(BlockfrostError):
    """Rate limit exceeded"""
    pass


class BlockfrostAPIError(BlockfrostError):
    """API returned an error"""
    pass


class DIDAlreadyExistsError(BlockfrostError):
    """DID already exists on blockchain"""

    def __init__(self, did: str, tx_hash: str, enrollment_data: Optional[Dict[str, Any]] = None):
        self.did = did
        self.tx_hash = tx_hash
        self.enrollment_data = enrollment_data or {}

        message = (
            f"DID already exists: {did}\n"
            f"Original enrollment transaction: {tx_hash}\n"
            f"This biometric identity has already been enrolled on the blockchain.\n"
            f"If you control this identity, you can add a new controller wallet instead of re-enrolling."
        )
        super().__init__(message)


class BlockfrostClient:
    """
    Blockfrost API client for Cardano blockchain interaction.

    This client provides methods to:
    - Query UTXOs by address
    - Submit transactions
    - Track transaction status
    - Check for duplicate DIDs (Sybil attack prevention)
    - Query metadata by label
    - Handle rate limits and errors

    Usage:
        >>> client = BlockfrostClient(
        ...     api_key="your_blockfrost_key",
        ...     network="testnet"
        ... )
        >>> # Query UTXOs
    >>> utxos = await client.get_address_utxos("addr_test1...")
        >>>
        >>> # Check for duplicate DID before enrollment
    >>> existing = await client.check_did_exists("did:cardano:mainnet:zQm...")
        >>> if existing:
        ...     print(f"DID already enrolled at: {existing['enrollment_timestamp']}")
        >>>
        >>> # Submit transaction
    >>> tx_hash = await client.submit_transaction(tx_cbor)
    >>> status = await client.get_transaction_status(tx_hash)
    """

    def __init__(
        self,
        api_key: str,
        network: str = "testnet",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        cache: Optional[TTLCache] = None,
        metrics: Optional[BlockfrostMetrics] = None,
    ):
        """
        Initialize Blockfrost client.

        Args:
            api_key: Blockfrost project API key
            network: "testnet" or "mainnet"
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            cache: Optional TTLCache instance for caching results
            metrics: Optional BlockfrostMetrics instance for instrumentation
        """
        self.api_key = api_key
        self.network = network
        self.timeout = timeout
        self.cache = cache
        self.metrics = metrics or BlockfrostMetrics()

        # Set base URL based on network
        if network == "testnet":
            self.base_url = BLOCKFROST_TESTNET_URL
        elif network == "mainnet":
            self.base_url = BLOCKFROST_MAINNET_URL
        else:
            raise ValueError(
                f"Invalid network: {network}. Use 'testnet' or 'mainnet'")

        # Setup session
        self.session = httpx.AsyncClient(
            headers={
                "project_id": api_key,
                "Content-Type": "application/json"
            },
            timeout=self.timeout,
        )
        self.max_retries = max_retries

        logger.info(
            f"BlockfrostClient initialized: network={network}, cache={'enabled' if cache else 'disabled'}")

    async def close(self):
        """Close the underlying HTTP client session."""
        await self.session.aclose()

    def metrics_snapshot(self) -> Dict[str, Any]:
        """Return a point-in-time snapshot of client performance metrics."""

        cache_lookups = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_ratio = (
            self.metrics.cache_hits / cache_lookups if cache_lookups else 0.0
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
        """Reset all collected metrics counters back to zero."""

        self.metrics.reset()

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Any:
        """
        Make HTTP request to Blockfrost API, with caching support for GET requests.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/addresses/{address}/utxos")
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON data
        """
        method_upper = method.upper()

        # Only cache GET requests
        if self.cache and method_upper == "GET":
            # Create a unique cache key from the endpoint and query parameters
            params = kwargs.get("params", {})
            # Sort params for consistent key generation
            sorted_params = sorted(params.items())
            cache_key = f"{endpoint}?{urlencode(sorted_params)}"

            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache HIT for {cache_key}")
                self.metrics.record_cache_hit()
                return cached_data

            logger.debug(f"Cache MISS for {cache_key}")
            self.metrics.record_cache_miss()
            # If not in cache, make the actual HTTP request
            data = await self._http_request(method, endpoint, **kwargs)
            # Store the successful result in the cache
            self.cache.set(cache_key, data)
            return data

        # For non-GET requests or if cache is disabled, make a direct request
        self.metrics.record_direct_request()
        return await self._http_request(method, endpoint, **kwargs)

    async def _http_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Blockfrost API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/addresses/{address}/utxos")
            **kwargs: Additional arguments for requests

        Returns:
            Response JSON data

        Raises:
            BlockfrostRateLimitError: Rate limit exceeded
            BlockfrostAPIError: API error occurred
            BlockfrostError: Other errors
        """
        url = f"{self.base_url}{endpoint}"

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= self.max_retries:
            attempt_start = time.perf_counter()
            try:
                response = await self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                duration = time.perf_counter() - attempt_start

                if response.status_code == 429:
                    retry_after_raw = response.headers.get("Retry-After")
                    retry_after = int(
                        retry_after_raw) if retry_after_raw else 60
                    message = (
                        "Rate limit exceeded. Retry after "
                        f"{retry_after} seconds."
                    )
                    if attempt < self.max_retries:
                        logger.warning(
                            "Rate limited by Blockfrost, retrying in %ss",
                            retry_after,
                        )
                        self.metrics.record_network_attempt(
                            duration, success=False)
                        await asyncio.sleep(retry_after)
                        attempt += 1
                        continue
                    self.metrics.record_network_attempt(
                        duration, success=False)
                    raise BlockfrostRateLimitError(message)

                if response.status_code >= 400:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            error_msg = error_data.get("message", error_msg)
                    except Exception:  # pragma: no cover - fallback when JSON parsing fails
                        pass

                    logger.error(
                        "Blockfrost API error (%s): %s", response.status_code, error_msg
                    )

                    if response.status_code >= 500 and attempt < self.max_retries:
                        backoff = 2 ** attempt
                        logger.warning(
                            "Server error from Blockfrost, retrying in %ss", backoff
                        )
                        self.metrics.record_network_attempt(
                            duration, success=False)
                        await asyncio.sleep(backoff)
                        attempt += 1
                        continue

                    self.metrics.record_network_attempt(
                        duration, success=False)
                    raise BlockfrostAPIError(
                        f"API error ({response.status_code}): {error_msg}"
                    )

                try:
                    data = response.json()
                except ValueError as exc:  # pragma: no cover - unexpected non-JSON payload
                    logger.error(
                        "Invalid JSON response from Blockfrost: %s", exc)
                    self.metrics.record_network_attempt(
                        duration, success=False)
                    raise BlockfrostError(
                        "Invalid JSON response from Blockfrost") from exc

                self.metrics.record_network_attempt(duration, success=True)
                return data

            except httpx.TimeoutException as exc:
                duration = time.perf_counter() - attempt_start
                last_error = exc
                if attempt < self.max_retries:
                    backoff = 2 ** attempt
                    logger.warning(
                        "Blockfrost request timed out (%s); retrying in %ss",
                        url,
                        backoff,
                    )
                    self.metrics.record_network_attempt(
                        duration, success=False)
                    await asyncio.sleep(backoff)
                    attempt += 1
                    continue

                logger.error("Request timeout: %s", url)
                self.metrics.record_network_attempt(duration, success=False)
                raise BlockfrostError(
                    f"Request timeout after {self.timeout}s") from exc

            except httpx.RequestError as exc:
                duration = time.perf_counter() - attempt_start
                last_error = exc
                if attempt < self.max_retries:
                    backoff = 2 ** attempt
                    logger.warning(
                        "Blockfrost request error (%s); retrying in %ss",
                        exc,
                        backoff,
                    )
                    self.metrics.record_network_attempt(
                        duration, success=False)
                    await asyncio.sleep(backoff)
                    attempt += 1
                    continue

                logger.error("Request failed: %s", exc)
                self.metrics.record_network_attempt(duration, success=False)
                raise BlockfrostError(f"Request failed: {exc}") from exc

        if last_error:
            raise BlockfrostError(
                f"Request failed after {self.max_retries + 1} attempts: {last_error}")

        raise BlockfrostError(
            f"Request failed after {self.max_retries + 1} attempts: {method} {endpoint}"
        )

    async def get_address_utxos(
        self,
        address: str,
        count: int = 100,
        page: int = 1,
    ) -> List[UTXOInfo]:
        """
        Get UTXOs for a given address.

        Args:
            address: Cardano address
            count: Number of results per page (max 100)
            page: Page number (starts at 1)

        Returns:
            List of UTXOInfo objects

        Example:
            >>> utxos = await client.get_address_utxos("addr_test1...")
            >>> for utxo in utxos:
            ...     print(f"{utxo.tx_hash}#{utxo.tx_index}: {utxo.amount}")
        """
        endpoint = f"/addresses/{address}/utxos"
        params = {"count": min(count, 100), "page": page}

        logger.debug(f"Querying UTXOs for address: {address}")

        try:
            data = await self._request("GET", endpoint, params=params)

            # Type assertion: data is a list of dictionaries
            if not isinstance(data, list):
                raise BlockfrostAPIError(
                    f"Unexpected response format: {type(data)}")

            utxos: List[UTXOInfo] = []
            for utxo in data:
                if not isinstance(utxo, dict):
                    continue

                utxos.append(UTXOInfo(
                    tx_hash=str(utxo.get("tx_hash", "")),
                    tx_index=int(utxo.get("output_index", 0)),
                    amount=utxo.get("amount", []) if isinstance(
                        utxo.get("amount"), list) else [],
                    address=str(utxo.get("address", "")),
                    block=str(utxo.get("block", "")),
                    data_hash=str(utxo.get("data_hash")) if utxo.get(
                        "data_hash") else None,
                ))

            logger.info(
                f"Found {len(utxos)} UTXOs for address {address[:20]}...")
            return utxos

        except BlockfrostAPIError as e:
            if "404" in str(e):
                # Address has no UTXOs
                logger.info(f"No UTXOs found for address {address[:20]}...")
                return []
            raise

    async def get_address_balance(self, address: str) -> int:
        """
        Get total lovelace balance for an address.

        Args:
            address: Cardano address

        Returns:
            Total balance in lovelace
        """
        utxos = await self.get_address_utxos(address)

        total_lovelace = 0
        for utxo in utxos:
            for asset in utxo.amount:
                if asset["unit"] == "lovelace":
                    total_lovelace += int(asset["quantity"])

        logger.info(
            f"Address balance: {total_lovelace} lovelace "
            f"({total_lovelace / 1_000_000:.6f} ADA)"
        )

        return total_lovelace

    async def submit_transaction(self, tx_cbor: str) -> str:
        """
        Submit a transaction to the blockchain.

        Args:
            tx_cbor: Transaction in CBOR hex format

        Returns:
            Transaction hash

        Raises:
            BlockfrostAPIError: If submission fails

        Example:
            >>> tx_hash = await client.submit_transaction(tx.to_cbor().hex())
            >>> print(f"Transaction submitted: {tx_hash}")
        """
        endpoint = "/tx/submit"

        # Blockfrost expects raw CBOR bytes
        headers = {"Content-Type": "application/cbor"}

        logger.info("Submitting transaction to blockchain...")

        try:
            # Convert hex to bytes
            tx_bytes = bytes.fromhex(tx_cbor)
            result = await self._request(
                "POST",
                endpoint,
                content=tx_bytes,
                headers=headers,
            )

            tx_hash = str(result)

            logger.info(f"Transaction submitted successfully: {tx_hash}")
            return tx_hash

        except ValueError as e:
            logger.error(f"Invalid CBOR hex: {e}")
            raise BlockfrostError(f"Invalid CBOR hex: {e}")

    async def get_transaction_status(self, tx_hash: str) -> TransactionStatus:
        """
        Get transaction status and confirmation details.

        Args:
            tx_hash: Transaction hash

        Returns:
            TransactionStatus object

        Example:
            >>> status = await client.get_transaction_status(tx_hash)
            >>> if status.confirmed:
            ...     print(f"Confirmed in block {status.block_height}")
            ... else:
            ...     print("Transaction pending...")
        """
        endpoint = f"/txs/{tx_hash}"

        logger.debug(f"Checking transaction status: {tx_hash}")

        try:
            data = await self._request("GET", endpoint)

            confirmed = data.get("block") is not None

            status = TransactionStatus(
                tx_hash=tx_hash,
                confirmed=confirmed,
                block_height=data.get("block_height"),
                block_time=data.get("block_time"),
                slot=data.get("slot"),
                index=data.get("index"),
            )

            if confirmed:
                logger.info(
                    f"Transaction confirmed: block {status.block_height}, "
                    f"slot {status.slot}"
                )
            else:
                logger.info("Transaction pending confirmation")

            return status

        except BlockfrostAPIError as e:
            if "404" in str(e):
                # Transaction not found (might be very recent)
                logger.info("Transaction not yet visible in mempool/chain")
                return TransactionStatus(
                    tx_hash=tx_hash,
                    confirmed=False
                )
            raise

    async def wait_for_confirmation(
        self,
        tx_hash: str,
        max_wait: int = 300,
        poll_interval: int = 10,
    ) -> TransactionStatus:
        """
        Wait for transaction confirmation.

        Args:
            tx_hash: Transaction hash
            max_wait: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            TransactionStatus (confirmed=True)

        Raises:
            BlockfrostError: If transaction not confirmed within max_wait

        Example:
            >>> status = await client.wait_for_confirmation(tx_hash, max_wait=600)
            >>> print(f"Confirmed in block {status.block_height}")
        """
        logger.info(f"Waiting for transaction confirmation: {tx_hash}")

        start_time = time.time()

        while time.time() - start_time < max_wait:
            status = await self.get_transaction_status(tx_hash)

            if status.confirmed:
                elapsed = time.time() - start_time
                logger.info(f"Transaction confirmed after {elapsed:.1f}s")
                return status

            logger.debug(f"Transaction pending, waiting {poll_interval}s...")
            await asyncio.sleep(poll_interval)

        raise BlockfrostError(
            f"Transaction not confirmed within {max_wait}s"
        )

    async def get_latest_block(self) -> Dict[str, Any]:
        """
        Get information about the latest block.

        Returns:
            Block information dictionary
        """
        endpoint = "/blocks/latest"

        logger.debug("Fetching latest block info")

        data = await self._request("GET", endpoint)

        logger.info(
            f"Latest block: height={data.get('height')}, "
            f"slot={data.get('slot')}, hash={data.get('hash', '')[:16]}..."
        )

        return data

    async def get_network_info(self) -> Dict[str, Any]:
        """
        Get network information.

        Returns:
            Network information dictionary
        """
        endpoint = "/network"

        logger.debug("Fetching network info")

        data = await self._request("GET", endpoint)

        logger.info(
            f"Network info: supply={data.get('supply')}, stake={data.get('stake')}")

        return data

    async def get_transactions_by_metadata_label(
        self,
        label: int,
        count: int = 100,
        page: int = 1,
        order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """
        Get transactions containing metadata with a specific label.

        Args:
            label: Metadata label (e.g., 674)
            count: Number of results per page
            page: Page number
            order: "asc" or "desc"

        Returns:
            List of transaction metadata objects
        """
        endpoint = f"/metadata/txs/labels/{label}"
        params = {"count": count, "page": page, "order": order}

        logger.debug(f"Querying transactions with metadata label: {label}")

        try:
            data = await self._request("GET", endpoint, params=params)
            if not isinstance(data, list):
                raise BlockfrostAPIError(
                    f"Unexpected response format: {type(data)}")
            return data
        except BlockfrostAPIError as e:
            if "404" in str(e):
                logger.info(
                    f"No transactions found with metadata label {label}")
                return []
            raise

    async def get_transaction_metadata(
        self,
        tx_hash: str,
    ) -> List[Dict[str, Any]]:
        """
        Get metadata for a specific transaction.

        Args:
            tx_hash: Transaction hash

        Returns:
            List of metadata objects, each with 'label' and 'json_metadata'
        """
        endpoint = f"/txs/{tx_hash}/metadata"

        logger.debug(f"Querying metadata for transaction: {tx_hash}")

        try:
            data = await self._request("GET", endpoint)
            if not isinstance(data, list):
                raise BlockfrostAPIError(
                    f"Unexpected response format: {type(data)}")
            return data
        except BlockfrostAPIError as e:
            if "404" in str(e):
                logger.info(f"No metadata found for transaction {tx_hash}")
                return []
            raise

    async def check_did_exists(self, did: str) -> Optional[Dict[str, Any]]:
        """
        Check if a DID exists on the blockchain by searching transaction metadata.

        This method queries the blockchain for transactions with metadata label 674
        (biometric DID standard) and searches for the specified DID. This enables
        duplicate detection and prevents Sybil attacks.

        Args:
            did: DID to search for (e.g., "did:cardano:mainnet:zQm...")

        Returns:
            Enrollment data dict if DID exists, None otherwise.
            Dict contains:
                - tx_hash: Transaction hash of original enrollment
                - controllers: List of wallet addresses controlling this DID
                - enrollment_timestamp: ISO 8601 timestamp of enrollment
                - revoked: Whether DID has been revoked
                - metadata: Full metadata from blockchain

        Raises:
            BlockfrostAPIError: API error occurred
            BlockfrostRateLimitError: Rate limit exceeded

        Example:
            >>> existing = await client.check_did_exists("did:cardano:mainnet:zQm...")
            >>> if existing:
            ...     print(f"DID enrolled at: {existing['enrollment_timestamp']}")
            ...     print(f"Controllers: {existing['controllers']}")
            ... else:
            ...     print("DID available for enrollment")
        """
        endpoint = "/metadata/txs/labels/674"  # Biometric DID metadata label

        logger.debug(f"Checking if DID exists: {did}")

        try:
            # Query transactions with biometric DID metadata label
            # Blockfrost returns paginated results (default 100 per page)
            page = 1
            max_pages = 10  # Prevent infinite loops

            while page <= max_pages:
                params = {"page": page, "count": 100, "order": "desc"}
                data = await self._request("GET", endpoint, params=params)

                if not isinstance(data, list) or len(data) == 0:
                    # No more results
                    break

                # Search through transactions for matching DID
                for tx_metadata in data:
                    if not isinstance(tx_metadata, dict):
                        continue
                    tx_hash = tx_metadata.get("tx_hash")
                    if not tx_hash:
                        continue

                    # Get transaction metadata details
                    try:
                        tx_detail_endpoint = f"/txs/{tx_hash}/metadata"
                        tx_details = await self._request("GET", tx_detail_endpoint)

                        # Search for our metadata label
                        for metadata_entry in tx_details:
                            if not isinstance(metadata_entry, dict):
                                continue
                            if metadata_entry.get("label") != "674":
                                continue

                            json_metadata = metadata_entry.get(
                                "json_metadata", {})
                            if not isinstance(json_metadata, dict):
                                continue

                            # Check if this metadata contains our DID
                            metadata_did = json_metadata.get("did")
                            if metadata_did == did:
                                # Found it! Extract enrollment data
                                logger.info(
                                    f"DID already exists: {did[:50]}... "
                                    f"(tx: {tx_hash[:16]}...)"
                                )

                                # Extract v1.1 metadata fields
                                controllers = json_metadata.get(
                                    "controllers", [])
                                if not controllers:
                                    # Fallback to v1.0 format (wallet_address)
                                    wallet = json_metadata.get(
                                        "wallet_address")
                                    controllers = [wallet] if wallet else []

                                enrollment_data = {
                                    "tx_hash": tx_hash,
                                    "controllers": controllers,
                                    "enrollment_timestamp": json_metadata.get(
                                        "enrollment_timestamp", "unknown"
                                    ),
                                    "revoked": json_metadata.get("revoked", False),
                                    "metadata": json_metadata,
                                }

                                return enrollment_data

                    except BlockfrostAPIError as e:
                        # Skip transactions we can't read
                        logger.debug(
                            f"Could not read metadata for tx {tx_hash[:16]}...: {e}"
                        )
                        continue

                # Move to next page
                page += 1
                if len(data) < 100:
                    # Last page
                    break

            # DID not found after searching all pages
            logger.info(f"DID not found on blockchain: {did[:50]}...")
            return None

        except BlockfrostAPIError as e:
            if "404" in str(e):
                # No transactions with this label yet
                logger.info(
                    "No biometric DID transactions found on blockchain")
                return None
            raise


# Utility functions

def convert_utxo_info_to_input(utxo: UTXOInfo) -> Dict[str, Any]:
    """
    Convert UTXOInfo to transaction input format.

    Args:
        utxo: UTXOInfo from Blockfrost

    Returns:
        Dictionary suitable for transaction building
    """
    lovelace_amount = 0
    for asset in utxo.amount:
        if asset["unit"] == "lovelace":
            lovelace_amount = int(asset["quantity"])
            break

    return {
        "tx_hash": utxo.tx_hash,
        "tx_index": utxo.tx_index,
        "amount_lovelace": lovelace_amount,
        "address": utxo.address,
    }


def format_lovelace(lovelace: int) -> str:
    """
    Format lovelace amount as ADA string.

    Args:
        lovelace: Amount in lovelace

    Returns:
        Formatted string (e.g., "5.000000 ADA")
    """
    ada = lovelace / 1_000_000
    return f"{ada:.6f} ADA"
