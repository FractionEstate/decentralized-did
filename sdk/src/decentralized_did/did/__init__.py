"""DID string helpers and deterministic identifier derivation.

This module provides utilities for building W3C Decentralized Identifier (DID)
strings and Cardano transaction metadata payloads for biometric DIDs.

Components
----------
build_did : function
    Construct a did:cardano identifier from wallet address and digest
build_metadata_payload : function
    Create Cardano transaction metadata payload for DID registration

DID Format
----------
The generated DIDs follow the format:
    did:cardano:{network}:{address}:{digest}

Where:
- network: Cardano network identifier (mainnet, testnet, preprod)
- address: Bech32-encoded Cardano address
- digest: Base64url-encoded biometric digest

Examples
--------
>>> from decentralized_did.did import build_did, build_metadata_payload
>>>
>>> # Build DID from wallet address and biometric digest
>>> wallet_addr = "addr1qx..."
>>> digest = b"\\x01\\x02\\x03..."  # 32-byte biometric digest
>>> did = build_did(wallet_addr, digest)
>>> print(did)
'did:cardano:mainnet:addr1qx...:AQID...'
>>>
>>> # Create metadata payload for Cardano transaction
>>> metadata = build_metadata_payload(
...     did=did,
...     helper_storage={"type": "ipfs", "cid": "Qm..."},
...     timestamp="2025-10-14T12:00:00Z"
... )
>>> print(metadata["674"]["did"])
'did:cardano:mainnet:addr1qx...:AQID...'

See Also
--------
- W3C DID Specification: https://www.w3.org/TR/did-core/
- Cardano Metadata CIPs: CIP-20, CIP-25
"""

from .generator import build_did, build_metadata_payload

__all__ = [
    "build_did",
    "build_metadata_payload",
]
