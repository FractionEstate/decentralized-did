"""
DID Generation and Metadata Encoding for Biometric DIDs (v2)

Implements Cardano DID generation with multi-finger biometric support,
comprehensive metadata encoding, and flexible helper data storage strategies.

Integrates with:
- aggregator_v2: Multi-finger XOR aggregation
- fuzzy_extractor_v2: BCH-based fuzzy extraction
- Cardano metadata standards (CIP-30, transaction metadata)

Phase 2, Task 4 - DID Generation and Metadata Encoding

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Any
from urllib.parse import urlparse


# ============================================================================
# CONSTANTS
# ============================================================================

# DID Method
DID_METHOD = "cardano"
DID_VERSION = 1

# Metadata Labels
DEFAULT_METADATA_LABEL = 1990  # Reserved for biometric DIDs

# Size Limits (Cardano transaction metadata)
MAX_METADATA_SIZE_BYTES = 16_384  # 16 KB hard limit
RECOMMENDED_METADATA_SIZE_BYTES = 8_192  # 8 KB recommended for reliability

# Helper Storage Modes
HELPER_STORAGE_INLINE = "inline"
HELPER_STORAGE_EXTERNAL = "external"

# Supported URI schemes for external helper data
SUPPORTED_URI_SCHEMES = {"http", "https", "ipfs"}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class HelperDataEntry:
    """
    Helper data for a single finger.

    Contains fuzzy extractor helper data (BCH syndrome, salt, personalization).
    """
    finger_id: str
    version: int
    salt: str  # Base64url-encoded
    personalization: str  # Base64url-encoded
    bch_syndrome: str  # Base64url-encoded
    hmac: str  # Base64url-encoded

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "fingerId": self.finger_id,
            "version": self.version,
            "salt": self.salt,
            "personalization": self.personalization,
            "bchSyndrome": self.bch_syndrome,
            "hmac": self.hmac,
        }

    @classmethod
    def from_fuzzy_helper_data(cls, finger_id: str, helper_data: Any) -> HelperDataEntry:
        """
        Create from fuzzy extractor HelperData object.

        Args:
            finger_id: Finger identifier (e.g., "left_thumb")
            helper_data: HelperData object from fuzzy_extractor_v2

        Returns:
            HelperDataEntry instance
        """
        return cls(
            finger_id=finger_id,
            version=helper_data.version,
            salt=_encode_bytes(helper_data.salt),
            personalization=_encode_bytes(helper_data.personalization),
            bch_syndrome=_encode_bytes(helper_data.bch_syndrome),
            hmac=_encode_bytes(helper_data.hmac),
        )


@dataclass
class BiometricMetadata:
    """
    Biometric metadata payload for Cardano transaction metadata.

    Supports inline and external helper data storage.
    """
    version: int
    wallet_address: str
    id_hash: str  # Base64url-encoded master key hash
    helper_storage: Literal["inline", "external"]
    helper_uri: Optional[str] = None
    helper_data: Optional[List[HelperDataEntry]] = None
    fingerprint_count: Optional[int] = None
    aggregation_mode: Optional[str] = None  # "4/4", "3/4", "2/4"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        payload: Dict[str, Any] = {
            "version": self.version,
            "walletAddress": self.wallet_address,
            "biometric": {
                "idHash": self.id_hash,
                "helperStorage": self.helper_storage,
            }
        }

        if self.helper_uri:
            payload["biometric"]["helperUri"] = self.helper_uri

        if self.helper_data and self.helper_storage == HELPER_STORAGE_INLINE:
            payload["biometric"]["helperData"] = [
                hd.to_dict() for hd in self.helper_data
            ]

        if self.fingerprint_count:
            payload["biometric"]["fingerprintCount"] = self.fingerprint_count

        if self.aggregation_mode:
            payload["biometric"]["aggregationMode"] = self.aggregation_mode

        return payload

    def size_bytes(self) -> int:
        """Estimate payload size in bytes (JSON-encoded)."""
        return len(json.dumps(self.to_dict(), separators=(',', ':')))

    def validate(self) -> None:
        """
        Validate metadata payload.

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        if not self.wallet_address:
            raise ValueError("wallet_address is required")

        if not self.id_hash:
            raise ValueError("id_hash is required")

        # Validate helper storage mode
        if self.helper_storage not in {HELPER_STORAGE_INLINE, HELPER_STORAGE_EXTERNAL}:
            raise ValueError(
                f"Invalid helper_storage: {self.helper_storage}, "
                f"must be '{HELPER_STORAGE_INLINE}' or '{HELPER_STORAGE_EXTERNAL}'"
            )

        # Validate inline mode
        if self.helper_storage == HELPER_STORAGE_INLINE:
            if not self.helper_data:
                raise ValueError(
                    "helper_data required for inline storage mode")
            if self.helper_uri:
                raise ValueError(
                    "helper_uri not allowed for inline storage mode")

        # Validate external mode
        if self.helper_storage == HELPER_STORAGE_EXTERNAL:
            if not self.helper_uri:
                raise ValueError(
                    "helper_uri required for external storage mode")
            if self.helper_data:
                raise ValueError(
                    "helper_data not allowed for external storage mode")
            _validate_helper_uri(self.helper_uri)

        # Validate size
        size = self.size_bytes()
        if size > MAX_METADATA_SIZE_BYTES:
            raise ValueError(
                f"Metadata size {size} bytes exceeds maximum {MAX_METADATA_SIZE_BYTES} bytes. "
                f"Use external helper storage mode to reduce size."
            )

        if size > RECOMMENDED_METADATA_SIZE_BYTES:
            import warnings
            warnings.warn(
                f"Metadata size {size} bytes exceeds recommended {RECOMMENDED_METADATA_SIZE_BYTES} bytes. "
                f"Consider using external helper storage mode.",
                UserWarning
            )


@dataclass
class CardanoDID:
    """
    Cardano DID identifier.

    Format: did:cardano:{wallet_address}#{fingerprint}
    """
    method: str
    wallet_address: str
    fingerprint: str

    def __str__(self) -> str:
        """Return full DID string."""
        return f"did:{self.method}:{self.wallet_address}#{self.fingerprint}"

    @classmethod
    def from_master_key(cls, wallet_address: str, master_key: bytes) -> CardanoDID:
        """
        Create DID from master key.

        Args:
            wallet_address: Cardano wallet address
            master_key: 32-byte master key from aggregator

        Returns:
            CardanoDID instance
        """
        if len(master_key) != 32:
            raise ValueError(
                f"master_key must be 32 bytes, got {len(master_key)}")

        # Fingerprint = base64url(SHA256(master_key))
        fingerprint_hash = hashlib.sha256(master_key).digest()
        fingerprint = _encode_bytes(fingerprint_hash)

        return cls(
            method=DID_METHOD,
            wallet_address=wallet_address,
            fingerprint=fingerprint,
        )

    @classmethod
    def parse(cls, did_string: str) -> CardanoDID:
        """
        Parse DID string.

        Args:
            did_string: DID string (e.g., "did:cardano:addr1...#abc123")

        Returns:
            CardanoDID instance

        Raises:
            ValueError: If DID string is invalid
        """
        if not did_string.startswith("did:"):
            raise ValueError(
                f"Invalid DID: must start with 'did:', got {did_string}")

        parts = did_string.split(":")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid DID: expected 'did:method:identifier', got {did_string}")

        method = parts[1]
        identifier = ":".join(parts[2:])

        if method != DID_METHOD:
            raise ValueError(
                f"Invalid DID method: expected '{DID_METHOD}', got {method}")

        if "#" not in identifier:
            raise ValueError(
                f"Invalid DID: missing fragment '#fingerprint', got {did_string}")

        wallet_address, fingerprint = identifier.split("#", 1)

        return cls(
            method=method,
            wallet_address=wallet_address,
            fingerprint=fingerprint,
        )


@dataclass
class WalletMetadataBundle:
    """
    Complete metadata bundle for Cardano wallets.

    Includes DID, metadata payload, and optional helper data for external storage.
    """
    did: CardanoDID
    metadata: BiometricMetadata
    metadata_label: int = DEFAULT_METADATA_LABEL
    helper_data_json: Optional[Dict[str, Any]] = None

    def to_wallet_format(self) -> Dict[str, Any]:
        """
        Convert to wallet format (transaction metadata JSON).

        Returns:
            {label: payload} mapping
        """
        return {
            str(self.metadata_label): self.metadata.to_dict()
        }

    def to_cip30_format(self) -> Dict[str, Any]:
        """
        Convert to CIP-30 format.

        Returns:
            {did, metadata: [[label, payload]]} mapping
        """
        return {
            "did": str(self.did),
            "metadata": [[self.metadata_label, self.metadata.to_dict()]]
        }

    def to_json(self, format: Literal["wallet", "cip30"] = "wallet") -> str:
        """
        Convert to JSON string.

        Args:
            format: Output format ("wallet" or "cip30")

        Returns:
            JSON string
        """
        if format == "wallet":
            return json.dumps(self.to_wallet_format(), indent=2)
        elif format == "cip30":
            return json.dumps(self.to_cip30_format(), indent=2)
        else:
            raise ValueError(
                f"Invalid format: {format}, must be 'wallet' or 'cip30'")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _encode_bytes(data: bytes) -> str:
    """
    Encode bytes to base64url (URL-safe, no padding).

    Args:
        data: Bytes to encode

    Returns:
        Base64url-encoded string
    """
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _decode_bytes(encoded: str) -> bytes:
    """
    Decode base64url string to bytes.

    Args:
        encoded: Base64url-encoded string

    Returns:
        Decoded bytes
    """
    # Add padding if needed
    padding = (4 - len(encoded) % 4) % 4
    encoded_padded = encoded + ("=" * padding)
    return base64.urlsafe_b64decode(encoded_padded)


def _validate_helper_uri(uri: str) -> None:
    """
    Validate helper data URI.

    Args:
        uri: URI string

    Raises:
        ValueError: If URI is invalid
    """
    if not uri:
        raise ValueError("helper_uri cannot be empty")

    parsed = urlparse(uri)

    if not parsed.scheme:
        raise ValueError(f"Invalid helper_uri: missing scheme, got {uri}")

    if parsed.scheme not in SUPPORTED_URI_SCHEMES:
        raise ValueError(
            f"Invalid helper_uri scheme: {parsed.scheme}, "
            f"must be one of {SUPPORTED_URI_SCHEMES}"
        )

    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        raise ValueError(
            f"Invalid helper_uri: missing netloc for {parsed.scheme}, got {uri}")


def _validate_wallet_address(address: str) -> None:
    """
    Validate Cardano wallet address format.

    Args:
        address: Wallet address string

    Raises:
        ValueError: If address is invalid
    """
    if not address:
        raise ValueError("wallet_address cannot be empty")

    # Basic validation: Cardano addresses start with addr1 (mainnet) or addr_test1 (testnet)
    # followed by alphanumeric Bech32 characters
    if not re.match(r"^addr(_test)?1[a-z0-9]{50,}$", address):
        raise ValueError(
            f"Invalid wallet_address format: {address}, "
            f"expected 'addr1...' (mainnet) or 'addr_test1...' (testnet)"
        )


# ============================================================================
# MAIN API
# ============================================================================

def build_did_from_master_key(
    wallet_address: str,
    master_key: bytes
) -> CardanoDID:
    """
    Build Cardano DID from master key.

    Args:
        wallet_address: Cardano wallet address (e.g., "addr1...")
        master_key: 32-byte master key from aggregator_v2

    Returns:
        CardanoDID instance

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> from src.biometrics.aggregator_v2 import aggregate_finger_keys, FingerKey
        >>> # ... enrollment and aggregation ...
        >>> result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)
        >>> did = build_did_from_master_key("addr1xyz...", result.master_key)
        >>> print(did)
        did:cardano:addr1xyz...#a3K9...
    """
    _validate_wallet_address(wallet_address)
    return CardanoDID.from_master_key(wallet_address, master_key)


def build_metadata(
    wallet_address: str,
    master_key: bytes,
    helper_data_entries: List[HelperDataEntry],
    *,
    helper_storage: Literal["inline", "external"] = "inline",
    helper_uri: Optional[str] = None,
    fingerprint_count: Optional[int] = None,
    aggregation_mode: Optional[str] = None,
    version: int = DID_VERSION,
) -> BiometricMetadata:
    """
    Build biometric metadata payload.

    Args:
        wallet_address: Cardano wallet address
        master_key: 32-byte master key from aggregator
        helper_data_entries: List of HelperDataEntry objects (one per finger)
        helper_storage: Storage mode ("inline" or "external")
        helper_uri: URI for external helper data (required if helper_storage="external")
        fingerprint_count: Number of fingerprints enrolled
        aggregation_mode: Aggregation mode (e.g., "4/4", "3/4")
        version: Metadata version

    Returns:
        BiometricMetadata instance

    Raises:
        ValueError: If inputs are invalid or size limits exceeded

    Example:
        >>> # Inline mode (helper data embedded)
        >>> metadata = build_metadata(
        ...     wallet_address="addr1xyz...",
        ...     master_key=master_key,
        ...     helper_data_entries=helper_entries,
        ...     helper_storage="inline",
        ...     fingerprint_count=4,
        ...     aggregation_mode="4/4"
        ... )
        >>>
        >>> # External mode (helper data stored separately)
        >>> metadata = build_metadata(
        ...     wallet_address="addr1xyz...",
        ...     master_key=master_key,
        ...     helper_data_entries=[],  # Empty for external
        ...     helper_storage="external",
        ...     helper_uri="ipfs://QmXyz..."
        ... )
    """
    _validate_wallet_address(wallet_address)

    if len(master_key) != 32:
        raise ValueError(f"master_key must be 32 bytes, got {len(master_key)}")

    # Generate ID hash from master key
    id_hash = _encode_bytes(hashlib.sha256(master_key).digest())

    # Create metadata
    metadata = BiometricMetadata(
        version=version,
        wallet_address=wallet_address,
        id_hash=id_hash,
        helper_storage=helper_storage,
        helper_uri=helper_uri,
        helper_data=helper_data_entries if helper_storage == HELPER_STORAGE_INLINE else None,
        fingerprint_count=fingerprint_count,
        aggregation_mode=aggregation_mode,
    )

    # Validate
    metadata.validate()

    return metadata


def build_wallet_bundle(
    wallet_address: str,
    master_key: bytes,
    helper_data_entries: List[HelperDataEntry],
    *,
    helper_storage: Literal["inline", "external"] = "inline",
    helper_uri: Optional[str] = None,
    fingerprint_count: Optional[int] = None,
    aggregation_mode: Optional[str] = None,
    metadata_label: int = DEFAULT_METADATA_LABEL,
) -> WalletMetadataBundle:
    """
    Build complete wallet metadata bundle (DID + metadata + helper data).

    Args:
        wallet_address: Cardano wallet address
        master_key: 32-byte master key from aggregator
        helper_data_entries: List of HelperDataEntry objects
        helper_storage: Storage mode ("inline" or "external")
        helper_uri: URI for external helper data
        fingerprint_count: Number of fingerprints enrolled
        aggregation_mode: Aggregation mode (e.g., "4/4")
        metadata_label: Cardano metadata label (default: 1990)

    Returns:
        WalletMetadataBundle instance

    Example:
        >>> bundle = build_wallet_bundle(
        ...     wallet_address="addr1xyz...",
        ...     master_key=master_key,
        ...     helper_data_entries=helper_entries,
        ...     helper_storage="inline",
        ...     fingerprint_count=4,
        ...     aggregation_mode="4/4"
        ... )
        >>>
        >>> # Export for wallet
        >>> wallet_json = bundle.to_json(format="wallet")
        >>>
        >>> # Export for CIP-30
        >>> cip30_json = bundle.to_json(format="cip30")
    """
    # Build DID
    did = build_did_from_master_key(wallet_address, master_key)

    # Build metadata
    metadata = build_metadata(
        wallet_address=wallet_address,
        master_key=master_key,
        helper_data_entries=helper_data_entries,
        helper_storage=helper_storage,
        helper_uri=helper_uri,
        fingerprint_count=fingerprint_count,
        aggregation_mode=aggregation_mode,
    )

    # Build helper data JSON (for external storage)
    helper_data_json = None
    if helper_storage == HELPER_STORAGE_EXTERNAL and helper_data_entries:
        helper_data_json = {
            "version": metadata.version,
            "did": str(did),
            "helperData": [hd.to_dict() for hd in helper_data_entries]
        }

    return WalletMetadataBundle(
        did=did,
        metadata=metadata,
        metadata_label=metadata_label,
        helper_data_json=helper_data_json,
    )


def estimate_metadata_size(
    helper_data_entries: List[HelperDataEntry],
    helper_storage: Literal["inline", "external"] = "inline",
) -> Dict[str, int]:
    """
    Estimate metadata payload size.

    Args:
        helper_data_entries: List of HelperDataEntry objects
        helper_storage: Storage mode

    Returns:
        Dictionary with size estimates:
            - "payload_bytes": Total payload size
            - "per_finger_bytes": Average size per finger
            - "helper_data_bytes": Helper data size
            - "overhead_bytes": Fixed overhead (wallet address, version, etc.)

    Example:
        >>> sizes = estimate_metadata_size(helper_entries, helper_storage="inline")
        >>> print(f"Total: {sizes['payload_bytes']} bytes")
        >>> if sizes['payload_bytes'] > 8192:
        ...     print("Consider external storage mode!")
    """
    # Create dummy metadata for size estimation
    dummy_wallet = "addr1" + ("x" * 100)  # Typical address length
    dummy_master_key = b'\x00' * 32

    metadata = build_metadata(
        wallet_address=dummy_wallet,
        master_key=dummy_master_key,
        helper_data_entries=helper_data_entries if helper_storage == HELPER_STORAGE_INLINE else [],
        helper_storage=helper_storage,
        helper_uri="https://example.com/helpers.json" if helper_storage == HELPER_STORAGE_EXTERNAL else None,
        fingerprint_count=len(helper_data_entries),
    )

    total_bytes = metadata.size_bytes()

    # Estimate helper data size
    if helper_storage == HELPER_STORAGE_INLINE and helper_data_entries:
        helper_json = json.dumps(
            [hd.to_dict() for hd in helper_data_entries], separators=(',', ':'))
        helper_bytes = len(helper_json)
    else:
        helper_bytes = 0

    # Estimate overhead (everything except helper data)
    overhead_bytes = total_bytes - helper_bytes

    per_finger_bytes = helper_bytes // len(
        helper_data_entries) if helper_data_entries else 0

    return {
        "payload_bytes": total_bytes,
        "per_finger_bytes": per_finger_bytes,
        "helper_data_bytes": helper_bytes,
        "overhead_bytes": overhead_bytes,
    }
