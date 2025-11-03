"""FastAPI endpoints for token management.

Provides REST API for querying ADA balances, native assets, NFTs, and transaction history.
"""

import sys
from pathlib import Path

# Ensure SDK imports resolve
sdk_path = Path(__file__).parent.parent.parent.parent / "sdk" / "src"
sys.path.insert(0, str(sdk_path))

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

from decentralized_did.cardano.tokens import (
    TokenService,
    Balance,
    Asset,
    NFT,
    NFTMetadata,
    Transaction,
    KoiosError,
)
from decentralized_did.cardano.koios_client import KoiosClient
from decentralized_did.cardano.cache import TTLCache

# Create router
router = APIRouter(prefix="/api/tokens", tags=["tokens"])

# Global Koios client (shared across requests)
koios_client = KoiosClient(cache=TTLCache(ttl_seconds=300, max_size=1000))


# Response models
class AssetResponse(BaseModel):
    """Asset API response model."""
    
    policy_id: str
    asset_name: str
    asset_name_ascii: Optional[str] = None
    fingerprint: Optional[str] = None
    quantity: str
    decimals: int
    display_quantity: str
    full_name: str


class NFTMetadataResponse(BaseModel):
    """NFT metadata API response model."""
    
    name: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    media_type: Optional[str] = None
    attributes: Optional[dict] = None


class NFTResponse(BaseModel):
    """NFT API response model."""
    
    asset: AssetResponse
    metadata: Optional[NFTMetadataResponse] = None
    display_name: str
    is_cip68: bool = False


class BalanceResponse(BaseModel):
    """Balance API response model."""
    
    ada_lovelace: str
    ada_amount: str
    total_assets: int
    assets: List[AssetResponse]


class TransactionResponse(BaseModel):
    """Transaction API response model."""
    
    tx_hash: str
    block_time: Optional[int] = None
    block_height: Optional[int] = None
    epoch: Optional[int] = None
    fee: Optional[str] = None
    fee_ada: Optional[str] = None


# Utility functions
def asset_to_response(asset: Asset) -> AssetResponse:
    """Convert Asset domain object to API response."""
    return AssetResponse(
        policy_id=asset.policy_id,
        asset_name=asset.asset_name,
        asset_name_ascii=asset.asset_name_ascii,
        fingerprint=asset.fingerprint,
        quantity=asset.quantity,
        decimals=asset.decimals,
        display_quantity=asset.display_quantity,
        full_name=asset.full_name,
    )


def nft_to_response(nft: NFT) -> NFTResponse:
    """Convert NFT domain object to API response."""
    metadata_response = None
    if nft.metadata:
        metadata_response = NFTMetadataResponse(
            name=nft.metadata.name,
            image=nft.metadata.image,
            description=nft.metadata.description,
            media_type=nft.metadata.media_type,
            attributes=nft.metadata.attributes,
        )
    
    return NFTResponse(
        asset=asset_to_response(nft.asset),
        metadata=metadata_response,
        display_name=nft.display_name,
        is_cip68=nft.is_cip68,
    )


def transaction_to_response(tx: Transaction) -> TransactionResponse:
    """Convert Transaction domain object to API response."""
    return TransactionResponse(
        tx_hash=tx.tx_hash,
        block_time=tx.block_time,
        block_height=tx.block_height,
        epoch=tx.epoch,
        fee=tx.fee,
        fee_ada=tx.fee_ada,
    )


# Endpoints
@router.get("/balance/{address}", response_model=BalanceResponse)
async def get_balance(
    address: str = Field(..., description="Cardano payment or stake address")
):
    """Get balance for a Cardano address.
    
    Returns ADA balance in lovelace and all native assets held by the address.
    
    Args:
        address: Cardano address (addr1... or stake1...)
        
    Returns:
        BalanceResponse with ADA and native assets
        
    Raises:
        HTTPException: 400 if address invalid, 500 if service error
    """
    try:
        service = TokenService(koios_client)
        balance = await service.get_address_balance(address)
        
        return BalanceResponse(
            ada_lovelace=balance.ada_lovelace,
            ada_amount=balance.ada_amount,
            total_assets=balance.total_assets,
            assets=[asset_to_response(asset) for asset in balance.assets],
        )
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/nfts/{address}", response_model=List[NFTResponse])
async def get_nfts(
    address: str = Field(..., description="Cardano address")
):
    """Get all NFTs owned by an address.
    
    Returns NFTs with metadata (CIP-25/CIP-68 support).
    
    Args:
        address: Cardano address
        
    Returns:
        List of NFTs with metadata
        
    Raises:
        HTTPException: 400 if address invalid, 500 if service error
    """
    try:
        service = TokenService(koios_client)
        nfts = await service.get_nfts(address)
        
        return [nft_to_response(nft) for nft in nfts]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/history/{address}", response_model=List[TransactionResponse])
async def get_transaction_history(
    address: str = Field(..., description="Cardano address"),
    limit: int = Query(50, ge=1, le=100, description="Maximum transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip")
):
    """Get transaction history for an address.
    
    Returns recent transactions sorted by block height (newest first).
    
    Args:
        address: Cardano address
        limit: Maximum number of transactions (1-100)
        offset: Pagination offset
        
    Returns:
        List of transactions
        
    Raises:
        HTTPException: 400 if parameters invalid, 500 if service error
    """
    try:
        service = TokenService(koios_client)
        transactions = await service.get_transaction_history(address, limit, offset)
        
        return [transaction_to_response(tx) for tx in transactions]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for token service."""
    return {"status": "ok", "service": "tokens"}
