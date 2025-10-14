"""Utilities to derive deterministic Cardano DIDs from biometric digests."""
from __future__ import annotations

import base64
import base58
import logging
import warnings
from hashlib import blake2b
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def _encode_digest(digest: bytes) -> str:
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def build_did(
    wallet_address: str,
    digest: bytes,
    *,
    deterministic: bool = True,
    network: str = "mainnet"
) -> str:
    """
    Generate a DID from wallet address and biometric digest.

    Args:
        wallet_address: Cardano wallet address (bech32 format)
        digest: Biometric digest (32 bytes)
        deterministic: If True (default), uses deterministic generation (RECOMMENDED).
                      If False, uses legacy wallet-based format (DEPRECATED).
        network: Network for deterministic DIDs ("mainnet", "testnet", or "preprod")

    Returns:
        DID string

    Note:
        The deterministic format is STRONGLY RECOMMENDED for production use.
        It provides Sybil resistance (one person = one DID) and better privacy.

        Legacy wallet-based format is DEPRECATED and will be removed in v2.0.

    Examples:
        >>> # RECOMMENDED: Deterministic DID (Sybil-resistant)
        >>> did = build_did("addr1...", digest, deterministic=True)
        >>> # Output: did:cardano:mainnet:zQmXyZ...

        >>> # DEPRECATED: Wallet-based DID (vulnerable to Sybil attacks)
        >>> did = build_did("addr1...", digest, deterministic=False)
        >>> # Output: did:cardano:addr1...#AQID...
    """
    if not deterministic:
        # Legacy wallet-based format (DEPRECATED)
        warnings.warn(
            "Wallet-based DID format (deterministic=False) is DEPRECATED and will be "
            "removed in v2.0. It is vulnerable to Sybil attacks (one person can create "
            "multiple DIDs with different wallets) and exposes wallet addresses. "
            "Use deterministic=True (default) for production deployments. "
            "See docs/MIGRATION-GUIDE.md for details.",
            DeprecationWarning,
            stacklevel=2
        )
        if not wallet_address:
            raise ValueError(
                "wallet_address must be provided for legacy format")
        fingerprint = _encode_digest(digest)
        return f"did:cardano:{wallet_address}#{fingerprint}"

    # Deterministic DID format (RECOMMENDED)
    # Use digest as commitment for backward compatibility
    # In production, pass the actual fuzzy commitment from the extractor
    commitment = digest
    return generate_deterministic_did(commitment, network)


def build_metadata_payload(
    wallet_address: str,
    digest: bytes,
    helper_map: Optional[Dict[str, Dict[str, object]]] = None,
    *,
    version: str = "1.1",
    helper_storage: str = "inline",
    helper_uri: Optional[str] = None,
    controllers: Optional[list[str]] = None,
    enrollment_timestamp: Optional[str] = None,
    revoked: bool = False,
    revoked_at: Optional[str] = None,
) -> Dict[str, object]:
    """
    Build metadata payload for Cardano transaction.

    Args:
        wallet_address: Primary controller wallet address
        digest: Biometric digest
        helper_map: Helper data for each finger
        version: Metadata schema version ("1.0" or "1.1", default "1.1")
        helper_storage: Storage mode ("inline" or "external")
        helper_uri: URI for external helper storage
        controllers: List of controller wallet addresses (v1.1+)
        enrollment_timestamp: ISO 8601 timestamp (v1.1+)
        revoked: Whether DID is revoked (v1.1+)
        revoked_at: Revocation timestamp (v1.1+)

    Returns:
        Metadata dictionary ready for Cardano transaction

    Note:
        Schema v1.1 is RECOMMENDED for new deployments. It supports:
        - Multi-controller (multiple wallets controlling same DID)
        - Enrollment timestamps
        - Revocation mechanism

        Schema v1.0 is for backward compatibility only.
    """
    biometric: Dict[str, object] = {
        "idHash": _encode_digest(digest),
        "helperStorage": helper_storage,
    }
    if helper_uri:
        biometric["helperUri"] = helper_uri
    if helper_map is not None:
        biometric["helperData"] = helper_map

    # Build payload based on schema version
    if version == "1.0":
        # Legacy v1.0 schema (single controller)
        warnings.warn(
            "Metadata schema v1.0 is deprecated. Use v1.1 for multi-controller "
            "support, revocation, and enrollment timestamps.",
            DeprecationWarning,
            stacklevel=2
        )
        return {
            "version": 1,  # Numeric version for v1.0
            "walletAddress": wallet_address,
            "biometric": biometric,
        }

    # v1.1 schema (RECOMMENDED)
    payload: Dict[str, object] = {
        "version": version,
        "controllers": controllers or [wallet_address],
        "biometric": biometric,
    }

    # Add optional v1.1 fields
    if enrollment_timestamp:
        payload["enrollmentTimestamp"] = enrollment_timestamp
    if revoked:
        payload["revoked"] = revoked
        if revoked_at:
            payload["revokedAt"] = revoked_at

    return payload


# ============================================================================
# Deterministic DID Generation (Phase 4.5 - Sybil Resistance)
# ============================================================================


def generate_deterministic_did(
    commitment: bytes,
    network: str = "mainnet"
) -> str:
    """
    Generate deterministic DID from biometric commitment.

    The DID is computed as a BLAKE2b-256 hash of the fuzzy commitment,
    then Base58-encoded for human readability. This ensures:
    1. Same fingerprints always produce the same DID
    2. Different fingerprints produce different DIDs (collision-resistant)
    3. DID reveals nothing about the biometric data (one-way hash)

    DID Format: did:cardano:{network}:{base58_hash}

    Example:
        >>> commitment = b"\\x01\\x02\\x03..." # Fuzzy commitment
        >>> did = generate_deterministic_did(commitment, "mainnet")
        >>> print(did)
        did:cardano:mainnet:zQmXyZ1a2B3c4D5e6F7g8H9i0J

    Args:
        commitment: Fuzzy commitment bytes (stable biometric representation)
        network: "mainnet", "testnet", or "preprod"

    Returns:
        DID string in format: did:cardano:{network}:{hash}

    Raises:
        ValueError: If commitment is empty or network is invalid

    Security Notes:
        - Uses BLAKE2b-256 for cryptographic security
        - 256-bit output provides 128-bit collision resistance
        - One-way: Cannot derive commitment from DID
        - Base58 encoding avoids ambiguous characters (0, O, I, l)
    """
    # Validate inputs
    if not commitment:
        raise ValueError("Commitment cannot be empty")

    if network not in ["mainnet", "testnet", "preprod"]:
        raise ValueError(
            f"Invalid network: {network}. "
            "Must be 'mainnet', 'testnet', or 'preprod'"
        )

    # Normalize network name (preprod → testnet for DID)
    did_network = "testnet" if network == "preprod" else network

    # Hash the commitment with BLAKE2b-256
    did_hash = blake2b(commitment, digest_size=32).digest()

    # Base58 encode for human-readable DID identifier
    did_id = base58.b58encode(did_hash).decode('ascii')

    # Construct full DID
    did = f"did:cardano:{did_network}:{did_id}"

    logger.info(
        f"Generated deterministic DID: {did[:40]}... "
        f"(from {len(commitment)} byte commitment)"
    )

    return did


def verify_did_determinism(
    commitment: bytes,
    expected_did: str,
    network: str = "mainnet"
) -> bool:
    """
    Verify that a DID was correctly generated from a commitment.

    Useful for:
    - Verifying DID ownership (prove you have the commitment)
    - Testing deterministic generation
    - Validating DID resolver results

    Args:
        commitment: Fuzzy commitment bytes
        expected_did: DID to verify
        network: Network parameter used in generation

    Returns:
        True if commitment produces expected_did, False otherwise
    """
    try:
        computed_did = generate_deterministic_did(commitment, network)
        return computed_did == expected_did
    except Exception as e:
        logger.error(f"DID verification failed: {e}")
        return False


def extract_did_hash(did: str) -> Optional[bytes]:
    """
    Extract the Base58-decoded hash from a DID.

    Useful for:
    - Comparing DIDs at the byte level
    - Indexing DIDs in databases
    - Cryptographic operations on DID identifiers

    Args:
        did: DID string (did:cardano:{network}:{hash})

    Returns:
        32-byte hash if valid DID, None otherwise
    """
    try:
        # Parse DID format
        parts = did.split(":")
        if len(parts) != 4:
            logger.warning(f"Invalid DID format: {did}")
            return None

        method, network_part, network, did_id = parts

        if method != "did" or network_part != "cardano":
            logger.warning(f"Not a Cardano DID: {did}")
            return None

        # Base58 decode
        hash_bytes = base58.b58decode(did_id)

        if len(hash_bytes) != 32:
            logger.warning(
                f"Invalid DID hash length: {len(hash_bytes)} "
                "(expected 32 bytes)"
            )
            return None

        return hash_bytes

    except Exception as e:
        logger.error(f"Failed to extract DID hash: {e}")
        return None


def compute_commitment_fingerprint(commitment: bytes) -> str:
    """
    Compute a short fingerprint of a commitment for logging/debugging.

    This is NOT the DID - just a short identifier for development use.

    Args:
        commitment: Fuzzy commitment bytes

    Returns:
        Hex string of first 8 bytes of BLAKE2b hash
    """
    hash_bytes = blake2b(commitment, digest_size=32).digest()
    return hash_bytes[:8].hex()
