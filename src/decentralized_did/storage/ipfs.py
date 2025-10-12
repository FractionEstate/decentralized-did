"""
IPFS storage backend.

Stores helper data on IPFS with content addressing and optional pinning.
Uses ipfshttpclient library (MIT license, open-source).
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional

from .base import StorageBackend, StorageReference, StorageError

# IPFS client - optional dependency
try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False


class IPFSStorage(StorageBackend):
    """
    IPFS storage backend for helper data.

    Stores helper data on IPFS (InterPlanetary File System) with:
    - Content addressing (CID-based retrieval)
    - Optional pinning for persistence
    - Gateway fallback for retrieval
    - Timeout handling

    Advantages:
    - Decentralized storage
    - Content-addressed (immutable)
    - Global availability
    - No central point of failure

    Disadvantages:
    - Requires IPFS node or gateway
    - Data may be garbage collected if not pinned
    - Network latency
    - Pinning services may have costs

    Requires:
    - ipfshttpclient library (MIT license)
    - IPFS node or gateway access
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize IPFS storage.

        Config options:
            api_url (str): IPFS API endpoint (default: /ip4/127.0.0.1/tcp/5001)
            gateway (str): IPFS gateway for retrieval (default: http://localhost:8080)
            pin (bool): Pin uploaded content (default: True)
            timeout (int): Request timeout in seconds (default: 30)
        """
        super().__init__(config)

        if not IPFS_AVAILABLE:
            raise StorageError(
                "IPFS storage requires ipfshttpclient library. "
                "Install with: pip install ipfshttpclient",
                backend="ipfs"
            )

        # IPFS configuration
        self.api_url = self.config.get("api_url", "/ip4/127.0.0.1/tcp/5001")
        self.gateway = self.config.get("gateway", "http://localhost:8080")
        self.pin = self.config.get("pin", True)
        self.timeout = self.config.get("timeout", 30)

        # Initialize client
        self.client: Optional[ipfshttpclient.Client] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to IPFS node."""
        try:
            self.client = ipfshttpclient.connect(
                self.api_url,
                timeout=self.timeout
            )
        except Exception as e:
            raise StorageError(
                f"Failed to connect to IPFS node: {e}", backend="ipfs", cause=e)

    def store(self, helper_data: Dict[str, Any]) -> StorageReference:
        """
        Store helper data on IPFS.

        Args:
            helper_data: Helper data dictionary

        Returns:
            StorageReference with IPFS CID

        Raises:
            StorageError: If upload fails
        """
        if not self.client:
            raise StorageError("IPFS client not connected", backend="ipfs")

        try:
            # Serialize to JSON
            json_data = json.dumps(
                helper_data, separators=(',', ':'), sort_keys=True)
            json_bytes = json_data.encode('utf-8')

            # Upload to IPFS
            result = self.client.add_bytes(json_bytes)
            cid = result

            # Pin if requested
            if self.pin:
                self.client.pin.add(cid)

            # Build gateway URL
            gateway_url = f"{self.gateway}/ipfs/{cid}"

            return StorageReference(
                backend="ipfs",
                uri=f"ipfs://{cid}",
                metadata={
                    "cid": cid,
                    "gateway_url": gateway_url,
                    "pinned": self.pin,
                    "size": len(json_bytes),
                }
            )

        except Exception as e:
            raise StorageError(
                f"IPFS upload failed: {e}", backend="ipfs", cause=e)

    def retrieve(self, reference: StorageReference) -> Dict[str, Any]:
        """
        Retrieve helper data from IPFS.

        Args:
            reference: Storage reference with IPFS CID

        Returns:
            Helper data dictionary

        Raises:
            StorageError: If retrieval fails
        """
        if reference.backend != "ipfs":
            raise StorageError(
                f"Invalid backend type: expected 'ipfs', got '{reference.backend}'",
                backend="ipfs"
            )

        if not self.client:
            raise StorageError("IPFS client not connected", backend="ipfs")

        try:
            # Extract CID from URI (ipfs://CID)
            cid = reference.uri.replace("ipfs://", "")

            # Retrieve from IPFS
            data_bytes = self.client.cat(cid)
            json_data = data_bytes.decode('utf-8')

            return json.loads(json_data)

        except json.JSONDecodeError as e:
            raise StorageError(
                f"Invalid JSON in IPFS data: {e}", backend="ipfs", cause=e)
        except Exception as e:
            raise StorageError(
                f"IPFS retrieval failed: {e}", backend="ipfs", cause=e)

    def delete(self, reference: StorageReference) -> bool:
        """
        Unpin helper data from IPFS.

        Note: This only unpins the content, doesn't delete it from IPFS network.
        Content may still be available from other nodes.

        Args:
            reference: Storage reference with IPFS CID

        Returns:
            True if unpinned successfully

        Raises:
            StorageError: If unpin fails
        """
        if reference.backend != "ipfs":
            raise StorageError(
                f"Invalid backend type: expected 'ipfs', got '{reference.backend}'",
                backend="ipfs"
            )

        if not self.client:
            raise StorageError("IPFS client not connected", backend="ipfs")

        try:
            # Extract CID from URI
            cid = reference.uri.replace("ipfs://", "")

            # Unpin (if it was pinned)
            self.client.pin.rm(cid)
            return True

        except Exception as e:
            # May fail if not pinned, which is OK
            return False

    def health_check(self) -> bool:
        """
        Check if IPFS node is operational.

        Returns:
            True if node is reachable and responsive
        """
        try:
            if not self.client:
                self._connect()

            # Try to get node ID
            self.client.id()
            return True

        except Exception:
            return False

    def supports_deletion(self) -> bool:
        """
        IPFS supports unpinning but not true deletion.

        Returns:
            True (supports unpinning)
        """
        return True
