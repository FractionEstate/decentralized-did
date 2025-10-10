"""Utilities to derive deterministic Cardano DIDs from biometric digests."""
from __future__ import annotations

import base64
from typing import Dict, Optional


def _encode_digest(digest: bytes) -> str:
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def build_did(wallet_address: str, digest: bytes) -> str:
    if not wallet_address:
        raise ValueError("wallet_address must be provided")
    fingerprint = _encode_digest(digest)
    return f"did:cardano:{wallet_address}#{fingerprint}"


def build_metadata_payload(
    wallet_address: str,
    digest: bytes,
    helper_map: Optional[Dict[str, Dict[str, object]]] = None,
    *,
    version: int = 1,
    helper_storage: str = "inline",
    helper_uri: Optional[str] = None,
) -> Dict[str, object]:
    biometric: Dict[str, object] = {
        "idHash": _encode_digest(digest),
        "helperStorage": helper_storage,
    }
    if helper_uri:
        biometric["helperUri"] = helper_uri
    if helper_map is not None:
        biometric["helperData"] = helper_map
    return {
        "version": version,
        "walletAddress": wallet_address,
        "biometric": biometric,
    }
