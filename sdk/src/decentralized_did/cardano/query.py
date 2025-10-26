from typing import Optional, Dict, Any, List

from .koios_client import KoiosClient
from .koios_scanner import (
    DEFAULT_METADATA_LABEL,
    KoiosMetadataRecord,
    KoiosMetadataScanner,
)


class CardanoQuery:
    """Query helper that operates on top of Koios endpoints."""

    def __init__(
        self,
        koios_client: KoiosClient,
        *,
        metadata_label: str = DEFAULT_METADATA_LABEL,
        koios_scanner: Optional[KoiosMetadataScanner] = None,
    ) -> None:
        self.koios_client = koios_client
        self.metadata_label = str(metadata_label)
        self.koios_scanner = koios_scanner or koios_client.metadata_scanner

    async def resolve_did(self, did: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a DID by querying the blockchain for its latest metadata.

        :param did: The DID to resolve.
        :return: The latest metadata document for the DID, or None if not found.
        """
        record = await self.koios_scanner.find_did(did, label=self.metadata_label)
        if record is None:
            return None
        return _koios_record_to_enrollment(record)

    async def get_enrollment_history(self, did: str) -> list[Dict[str, Any]]:
        """
        Retrieves the entire on-chain history of a DID.

        :param did: The DID to retrieve the history for.
        :return: A list of metadata documents, from oldest to newest.
        """
        history = []
        async for record in self.koios_scanner.iter_label_entries(label=self.metadata_label):
            payload = record.metadata
            if payload.get("did") != did:
                continue
            history.append(payload)
        # Koios returns blocks newest first, so reverse for chronological order.
        history.reverse()
        return history


def _koios_record_to_enrollment(record: KoiosMetadataRecord) -> Dict[str, Any]:
    """Convert a Koios metadata record to the enrollment dict format."""

    payload = record.metadata
    controllers = payload.get("controllers") or []
    if not controllers:
        wallet = payload.get("wallet_address")
        if wallet:
            controllers = [wallet]

    return {
        "tx_hash": record.tx_hash,
        "controllers": controllers,
        "enrollment_timestamp": payload.get("enrollment_timestamp", "unknown"),
        "revoked": payload.get("revoked", False),
        "metadata": payload,
    }
