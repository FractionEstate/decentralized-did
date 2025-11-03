"""FastAPI endpoints for staking operations.

Provides REST API for querying stake accounts, pools, rewards, and delegation status.
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

from decentralized_did.cardano.staking import (
    StakingService,
    StakeAccount,
    StakePool,
    Reward,
    KoiosError,
)
from decentralized_did.cardano.koios_client import KoiosClient
from decentralized_did.cardano.cache import TTLCache

# Create router
router = APIRouter(prefix="/api/staking", tags=["staking"])

# Global Koios client (shared across requests)
koios_client = KoiosClient(cache=TTLCache(ttl_seconds=300, max_size=1000))


# Response models
class StakeAccountResponse(BaseModel):
    """Stake account API response model."""
    
    stake_address: str
    status: str
    delegated_pool: Optional[str] = None
    total_balance: str
    total_balance_ada: str
    available_rewards: str
    rewards_ada: str
    delegated_amount: str
    is_delegated: bool


class StakePoolResponse(BaseModel):
    """Stake pool API response model."""
    
    pool_id: str
    pool_id_bech32: str
    ticker: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    active_stake: str
    active_stake_ada: str
    live_stake: str
    live_saturation: float
    saturation_percentage: str
    margin: float
    margin_percentage: str
    fixed_cost: str
    fixed_cost_ada: str
    blocks_minted: int
    blocks_epoch: int
    live_delegators: int
    estimated_apy: Optional[float] = None


class RewardResponse(BaseModel):
    """Reward API response model."""
    
    epoch: int
    amount: str
    amount_ada: str
    pool_id: str
    earned_epoch: int


# Utility functions
def stake_account_to_response(account: StakeAccount) -> StakeAccountResponse:
    """Convert StakeAccount to API response."""
    return StakeAccountResponse(
        stake_address=account.stake_address,
        status=account.status,
        delegated_pool=account.delegated_pool,
        total_balance=account.total_balance,
        total_balance_ada=account.total_balance_ada,
        available_rewards=account.available_rewards,
        rewards_ada=account.rewards_ada,
        delegated_amount=account.delegated_amount,
        is_delegated=account.is_delegated,
    )


def stake_pool_to_response(pool: StakePool, apy: Optional[float] = None) -> StakePoolResponse:
    """Convert StakePool to API response."""
    return StakePoolResponse(
        pool_id=pool.pool_id,
        pool_id_bech32=pool.pool_id_bech32,
        ticker=pool.ticker,
        name=pool.name,
        description=pool.description,
        homepage=pool.homepage,
        active_stake=pool.active_stake,
        active_stake_ada=pool.active_stake_ada,
        live_stake=pool.live_stake,
        live_saturation=pool.live_saturation,
        saturation_percentage=pool.saturation_percentage,
        margin=pool.margin,
        margin_percentage=pool.margin_percentage,
        fixed_cost=pool.fixed_cost,
        fixed_cost_ada=pool.fixed_cost_ada,
        blocks_minted=pool.blocks_minted,
        blocks_epoch=pool.blocks_epoch,
        live_delegators=pool.live_delegators,
        estimated_apy=apy,
    )


def reward_to_response(reward: Reward) -> RewardResponse:
    """Convert Reward to API response."""
    return RewardResponse(
        epoch=reward.epoch,
        amount=reward.amount,
        amount_ada=reward.amount_ada,
        pool_id=reward.pool_id,
        earned_epoch=reward.earned_epoch,
    )


# Endpoints
@router.get("/account/{stake_address}", response_model=StakeAccountResponse)
async def get_account_info(
    stake_address: str = Field(..., description="Cardano stake address (stake1...)")
):
    """Get stake account information.
    
    Returns account status, delegated pool, balance, and rewards.
    
    Args:
        stake_address: Cardano stake address
        
    Returns:
        StakeAccountResponse with account details
        
    Raises:
        HTTPException: 400 if address invalid, 500 if service error
    """
    try:
        service = StakingService(koios_client)
        account = await service.get_account_info(stake_address)
        
        return stake_account_to_response(account)
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/pools", response_model=List[StakePoolResponse])
async def get_pool_list(
    limit: int = Query(50, ge=1, le=100, description="Maximum pools to return"),
    offset: int = Query(0, ge=0, description="Number of pools to skip")
):
    """Get list of active stake pools.
    
    Returns pools sorted by active stake (highest first).
    
    Args:
        limit: Maximum number of pools (1-100)
        offset: Pagination offset
        
    Returns:
        List of stake pools with metrics
        
    Raises:
        HTTPException: 500 if service error
    """
    try:
        service = StakingService(koios_client)
        pools = await service.get_pool_list(limit, offset)
        
        return [stake_pool_to_response(pool) for pool in pools]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/pool/{pool_id}", response_model=StakePoolResponse)
async def get_pool_details(
    pool_id: str = Field(..., description="Pool ID (hex or bech32)"),
    include_apy: bool = Query(False, description="Calculate estimated APY")
):
    """Get detailed information for a specific pool.
    
    Returns pool metadata, performance metrics, and optionally estimated APY.
    
    Args:
        pool_id: Pool ID (hex or bech32 format)
        include_apy: Whether to calculate estimated APY
        
    Returns:
        StakePoolResponse with detailed metrics
        
    Raises:
        HTTPException: 404 if pool not found, 500 if service error
    """
    try:
        service = StakingService(koios_client)
        pool = await service.get_pool_metadata(pool_id)
        
        if not pool:
            raise HTTPException(status_code=404, detail="Pool not found")
        
        apy = None
        if include_apy:
            apy = await service.calculate_apy(pool_id)
        
        return stake_pool_to_response(pool, apy)
    except HTTPException:
        raise
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/rewards/{stake_address}", response_model=List[RewardResponse])
async def get_rewards_history(
    stake_address: str = Field(..., description="Cardano stake address"),
    limit: int = Query(20, ge=1, le=100, description="Maximum rewards to return")
):
    """Get rewards history for a stake address.
    
    Returns recent rewards sorted by epoch (newest first).
    
    Args:
        stake_address: Cardano stake address
        limit: Maximum number of rewards (1-100)
        
    Returns:
        List of rewards
        
    Raises:
        HTTPException: 400 if address invalid, 500 if service error
    """
    try:
        service = StakingService(koios_client)
        rewards = await service.get_rewards_history(stake_address, limit)
        
        return [reward_to_response(reward) for reward in rewards]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for staking service."""
    return {"status": "ok", "service": "staking"}
