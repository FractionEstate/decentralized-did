"""High-level helpers to prepare Cardano metadata bundles for wallet providers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .metadata_encoder import DEFAULT_METADATA_LABEL, to_wallet_metadata
from ..did.generator import build_did, build_metadata_payload


MetadataFormat = str


@dataclass(frozen=True, slots=True)
class WalletMetadataBundle:
    """Container with DID metadata variants for Cardano wallets."""

    did: str
    payload: Dict[str, Any]
    label: int

    def as_wallet_metadata(self) -> Dict[str, Any]:
        """Return metadata keyed by the label as expected by most wallet SDKs."""

        return to_wallet_metadata(self.payload, self.label)

    def as_cip30_request(self) -> Dict[str, Any]:
        """Return a structure tailored for CIP-30 wallet API usage."""

        return {
            "did": self.did,
            "metadata": [(self.label, self.payload)],
        }

    def metadata_for_format(self, fmt: MetadataFormat) -> Dict[str, Any]:
        if fmt == "wallet":
            return self.as_wallet_metadata()
        if fmt == "cip30":
            return self.as_cip30_request()
        raise ValueError(f"unknown metadata format: {fmt}")

    def to_json(self, *, fmt: MetadataFormat = "wallet", pretty: bool = False) -> str:
        """Serialise the metadata bundle to JSON for convenience."""

        indent = 2 if pretty else None
        sort_keys = pretty and fmt == "wallet"
        return json.dumps(self.metadata_for_format(fmt), indent=indent, sort_keys=sort_keys)

    def write_json(
        self,
        destination: Path,
        *,
        fmt: MetadataFormat = "wallet",
        pretty: bool = True,
        create_dirs: bool = True,
    ) -> None:
        """Write the metadata bundle to disk."""

        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_json(
            fmt=fmt, pretty=pretty), encoding="utf-8")


def build_wallet_metadata_bundle(
    wallet_address: str,
    digest: bytes,
    helper_map: Optional[Dict[str, Dict[str, Any]]],
    *,
    label: int = DEFAULT_METADATA_LABEL,
    helper_storage: str = "inline",
    helper_uri: Optional[str] = None,
    version: str = "1.1",
) -> WalletMetadataBundle:
    """Create a metadata bundle ready for wallet integration.

    Args:
        wallet_address: Bech32-encoded Cardano address
        digest: 32-byte biometric digest
        helper_map: Helper data dictionary (or None for external storage)
        label: Cardano metadata label (default: 674 for biometric DIDs)
        helper_storage: "inline" or "external"
        helper_uri: URI for external helper storage (IPFS, etc.)
        version: Metadata schema version ("1.1" or "1.0", default: "1.1")

    Returns:
        WalletMetadataBundle with metadata payload and DID
    """

    payload = build_metadata_payload(
        wallet_address,
        digest,
        helper_map,
        version=version,
        helper_storage=helper_storage,
        helper_uri=helper_uri,
    )
    did = build_did(wallet_address, digest)
    return WalletMetadataBundle(did=did, payload=payload, label=label)
