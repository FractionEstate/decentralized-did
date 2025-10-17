from typing import Optional, Dict, Any
from .blockfrost import BlockfrostClient


class CardanoQuery:
    """
    A class to query the Cardano blockchain for DID-related information.
    """

    def __init__(self, blockfrost_client: BlockfrostClient):
        self.blockfrost_client = blockfrost_client

    def resolve_did(self, did: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a DID by querying the blockchain for its latest metadata.

        :param did: The DID to resolve.
        :return: The latest metadata document for the DID, or None if not found.
        """
        return self.blockfrost_client.check_did_exists(did)

    def get_enrollment_history(self, did: str) -> list[Dict[str, Any]]:
        """
        Retrieves the entire on-chain history of a DID.

        :param did: The DID to retrieve the history for.
        :return: A list of metadata documents, from oldest to newest.
        """
        # This is a simplified implementation. A real implementation would need
        # to handle pagination and potentially multiple transactions in the same slot.
        transactions = self.blockfrost_client.get_transactions_by_metadata_label(
            674
        )
        history = []
        for tx_info in transactions:
            tx_hash = tx_info.get("tx_hash")
            if not tx_hash:
                continue

            metadata_list = self.blockfrost_client.get_transaction_metadata(
                tx_hash)
            for metadata_entry in metadata_list:
                if metadata_entry.get("label") == "674":
                    json_metadata = metadata_entry.get("json_metadata")
                    if isinstance(json_metadata, dict) and json_metadata.get('did') == did:
                        history.append(json_metadata)
        return history
