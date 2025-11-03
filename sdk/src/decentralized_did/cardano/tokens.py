"""Token management service for Cardano using Koios API.

Provides functions for querying ADA balances, native assets, NFTs, and transaction history.
Supports CIP-25 (NFT metadata) and CIP-68 (reference NFT metadata) standards.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from .koios_client import KoiosClient, KoiosError

logger = logging.getLogger(__name__)

# Constants for Cardano
LOVELACE_PER_ADA = 1_000_000


@dataclass
class Asset:
    """Represents a native asset on Cardano."""
    
    policy_id: str
    asset_name: str
    asset_name_ascii: Optional[str] = None
    fingerprint: Optional[str] = None
    quantity: str = "0"
    decimals: int = 0
    
    @property
    def full_name(self) -> str:
        """Return policy_id.asset_name format."""
        return f"{self.policy_id}.{self.asset_name}"
    
    @property
    def display_quantity(self) -> str:
        """Return quantity with decimal formatting."""
        if self.decimals == 0:
            return self.quantity
        qty = Decimal(self.quantity)
        divisor = Decimal(10 ** self.decimals)
        return str(qty / divisor)


@dataclass
class NFTMetadata:
    """NFT metadata following CIP-25 standard."""
    
    name: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    media_type: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None
    attributes: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_onchain_metadata(cls, metadata: Dict[str, Any]) -> "NFTMetadata":
        """Parse CIP-25 metadata from on-chain JSON."""
        return cls(
            name=metadata.get("name"),
            image=metadata.get("image"),
            description=metadata.get("description"),
            media_type=metadata.get("mediaType"),
            files=metadata.get("files"),
            attributes=metadata.get("attributes"),
        )


@dataclass
class NFT:
    """Represents an NFT with metadata."""
    
    asset: Asset
    metadata: Optional[NFTMetadata] = None
    is_cip68: bool = False
    reference_nft: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Return display name (metadata name or asset name)."""
        if self.metadata and self.metadata.name:
            return self.metadata.name
        if self.asset.asset_name_ascii:
            return self.asset.asset_name_ascii
        return self.asset.asset_name[:16] + "..." if len(self.asset.asset_name) > 16 else self.asset.asset_name


@dataclass
class Balance:
    """Represents wallet balance with ADA and native assets."""
    
    ada_lovelace: str
    assets: List[Asset]
    
    @property
    def ada_amount(self) -> str:
        """Return ADA amount as decimal string."""
        lovelace = Decimal(self.ada_lovelace)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)
    
    @property
    def total_assets(self) -> int:
        """Return total number of native assets."""
        return len(self.assets)


@dataclass
class Transaction:
    """Represents a transaction from history."""
    
    tx_hash: str
    block_time: Optional[int] = None
    block_height: Optional[int] = None
    epoch: Optional[int] = None
    fee: Optional[str] = None
    inputs: Optional[List[Dict[str, Any]]] = None
    outputs: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def fee_ada(self) -> Optional[str]:
        """Return fee in ADA."""
        if self.fee is None:
            return None
        lovelace = Decimal(self.fee)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)


class TokenService:
    """Service for managing Cardano tokens using Koios API."""
    
    def __init__(self, koios_client: KoiosClient):
        """Initialize token service with Koios client.
        
        Args:
            koios_client: Configured KoiosClient instance
        """
        self.koios = koios_client
    
    async def get_address_balance(self, address: str) -> Balance:
        """Get balance for a Cardano address.
        
        Args:
            address: Cardano payment or stake address
            
        Returns:
            Balance object with ADA and native assets
            
        Raises:
            KoiosError: If API request fails
        """
        try:
            # Call Koios /address_info endpoint
            response = await self.koios._request(
                "POST",
                "/address_info",
                json={"_addresses": [address]}
            )
            
            if not response or not isinstance(response, list) or len(response) == 0:
                # Address not found or has no UTXOs
                return Balance(ada_lovelace="0", assets=[])
            
            addr_info = response[0]
            
            # Extract balance
            balance_str = addr_info.get("balance", "0")
            
            # Extract native assets
            assets = []
            utxo_set = addr_info.get("utxo_set", [])
            
            # Aggregate assets from all UTXOs
            asset_totals: Dict[str, Tuple[str, int]] = {}  # (policy_id.asset_name) -> (quantity, decimals)
            
            for utxo in utxo_set:
                asset_list = utxo.get("asset_list", [])
                for asset_data in asset_list:
                    policy_id = asset_data.get("policy_id", "")
                    asset_name = asset_data.get("asset_name", "")
                    quantity = asset_data.get("quantity", "0")
                    decimals = asset_data.get("decimals", 0)
                    
                    key = f"{policy_id}.{asset_name}"
                    if key in asset_totals:
                        current_qty, _ = asset_totals[key]
                        asset_totals[key] = (str(int(current_qty) + int(quantity)), decimals)
                    else:
                        asset_totals[key] = (quantity, decimals)
            
            # Convert to Asset objects
            for key, (quantity, decimals) in asset_totals.items():
                policy_id, asset_name = key.split(".", 1)
                assets.append(Asset(
                    policy_id=policy_id,
                    asset_name=asset_name,
                    quantity=quantity,
                    decimals=decimals
                ))
            
            return Balance(ada_lovelace=balance_str, assets=assets)
            
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            raise KoiosError(f"Failed to get address balance: {e}")
    
    async def get_asset_metadata(self, policy_id: str, asset_name: str) -> Optional[NFTMetadata]:
        """Get metadata for a specific asset (CIP-25/CIP-68).
        
        Args:
            policy_id: Asset policy ID
            asset_name: Asset name (hex)
            
        Returns:
            NFTMetadata if found, None otherwise
        """
        try:
            # Call Koios /asset_info endpoint
            asset_full = f"{policy_id}{asset_name}"
            response = await self.koios._request(
                "POST",
                "/asset_info",
                json={"_asset_list": [[policy_id, asset_name]]}
            )
            
            if not response or not isinstance(response, list) or len(response) == 0:
                return None
            
            asset_info = response[0]
            minting_tx_metadata = asset_info.get("minting_tx_metadata", {})
            
            # Try to parse CIP-25 metadata (label "721")
            if "721" in minting_tx_metadata:
                metadata_721 = minting_tx_metadata["721"]
                if policy_id in metadata_721:
                    policy_metadata = metadata_721[policy_id]
                    if asset_name in policy_metadata:
                        nft_metadata = policy_metadata[asset_name]
                        return NFTMetadata.from_onchain_metadata(nft_metadata)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get metadata for {policy_id}.{asset_name}: {e}")
            return None
    
    async def get_nfts(self, address: str) -> List[NFT]:
        """Get all NFTs owned by an address.
        
        Args:
            address: Cardano address
            
        Returns:
            List of NFT objects with metadata
        """
        try:
            # Get balance first
            balance = await self.get_address_balance(address)
            
            # Filter for NFTs (quantity == 1, no decimals)
            nft_assets = [
                asset for asset in balance.assets
                if asset.quantity == "1" and asset.decimals == 0
            ]
            
            # Fetch metadata for each NFT
            nfts = []
            for asset in nft_assets:
                metadata = await self.get_asset_metadata(asset.policy_id, asset.asset_name)
                nfts.append(NFT(asset=asset, metadata=metadata))
            
            return nfts
            
        except Exception as e:
            logger.error(f"Failed to get NFTs for {address}: {e}")
            raise KoiosError(f"Failed to get NFTs: {e}")
    
    async def get_transaction_history(
        self,
        address: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        """Get transaction history for an address.
        
        Args:
            address: Cardano address
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of Transaction objects
        """
        try:
            # Call Koios /address_txs endpoint
            response = await self.koios._request(
                "POST",
                "/address_txs",
                json={
                    "_addresses": [address],
                    "_after_block_height": 0
                },
                params={
                    "limit": limit,
                    "offset": offset
                }
            )
            
            if not response or not isinstance(response, list):
                return []
            
            transactions = []
            for tx_data in response:
                tx = Transaction(
                    tx_hash=tx_data.get("tx_hash", ""),
                    block_time=tx_data.get("block_time"),
                    block_height=tx_data.get("block_height"),
                    epoch=tx_data.get("epoch_no"),
                    fee=tx_data.get("fee")
                )
                transactions.append(tx)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transaction history for {address}: {e}")
            raise KoiosError(f"Failed to get transaction history: {e}")


# Convenience functions for common operations
async def get_balance(address: str, koios_client: Optional[KoiosClient] = None) -> Balance:
    """Get balance for an address (convenience function).
    
    Args:
        address: Cardano address
        koios_client: Optional pre-configured client (creates new if None)
        
    Returns:
        Balance object
    """
    client = koios_client or KoiosClient()
    try:
        service = TokenService(client)
        return await service.get_address_balance(address)
    finally:
        if koios_client is None:
            await client.close()


async def get_nfts_for_address(address: str, koios_client: Optional[KoiosClient] = None) -> List[NFT]:
    """Get NFTs for an address (convenience function).
    
    Args:
        address: Cardano address
        koios_client: Optional pre-configured client
        
    Returns:
        List of NFTs
    """
    client = koios_client or KoiosClient()
    try:
        service = TokenService(client)
        return await service.get_nfts(address)
    finally:
        if koios_client is None:
            await client.close()
