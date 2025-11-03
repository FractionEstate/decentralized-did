"""Staking service for Cardano using Koios API.

Provides functions for querying stake accounts, pool information, rewards history,
and delegation status. Supports Cardano staking operations including pool selection,
delegation tracking, and reward calculations.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from decimal import Decimal

from .koios_client import KoiosClient, KoiosError

logger = logging.getLogger(__name__)

# Constants
LOVELACE_PER_ADA = 1_000_000
EPOCH_DURATION_DAYS = 5  # Approximate Cardano epoch duration


@dataclass
class StakeAccount:
    """Represents a Cardano stake account."""
    
    stake_address: str
    status: str  # "registered", "not registered"
    delegated_pool: Optional[str] = None
    total_balance: str = "0"  # Total balance in lovelace
    available_rewards: str = "0"  # Available rewards in lovelace
    delegated_amount: str = "0"  # Amount delegated in lovelace
    
    @property
    def total_balance_ada(self) -> str:
        """Return total balance in ADA."""
        lovelace = Decimal(self.total_balance)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)
    
    @property
    def rewards_ada(self) -> str:
        """Return rewards in ADA."""
        lovelace = Decimal(self.available_rewards)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)
    
    @property
    def is_delegated(self) -> bool:
        """Return whether account is currently delegated."""
        return self.delegated_pool is not None


@dataclass
class StakePool:
    """Represents a Cardano stake pool."""
    
    pool_id: str
    pool_id_bech32: str  # Bech32 format pool ID
    ticker: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    
    # Pool metrics
    active_stake: str = "0"  # Total active stake in lovelace
    live_stake: str = "0"  # Current live stake in lovelace
    live_saturation: float = 0.0  # Saturation percentage (0-1)
    
    # Pool parameters
    margin: float = 0.0  # Pool margin (0-1)
    fixed_cost: str = "0"  # Fixed cost in lovelace
    
    # Performance metrics
    blocks_minted: int = 0  # Lifetime blocks minted
    blocks_epoch: int = 0  # Blocks minted in current epoch
    live_delegators: int = 0  # Current number of delegators
    
    @property
    def active_stake_ada(self) -> str:
        """Return active stake in ADA (millions)."""
        lovelace = Decimal(self.active_stake)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        millions = ada / Decimal(1_000_000)
        return f"{millions:.2f}M"
    
    @property
    def fixed_cost_ada(self) -> str:
        """Return fixed cost in ADA."""
        lovelace = Decimal(self.fixed_cost)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)
    
    @property
    def margin_percentage(self) -> str:
        """Return margin as percentage."""
        return f"{self.margin * 100:.2f}%"
    
    @property
    def saturation_percentage(self) -> str:
        """Return saturation as percentage."""
        return f"{self.live_saturation * 100:.2f}%"


@dataclass
class Reward:
    """Represents a staking reward."""
    
    epoch: int
    amount: str  # Reward amount in lovelace
    pool_id: str
    earned_epoch: int  # Epoch when reward was earned
    
    @property
    def amount_ada(self) -> str:
        """Return reward amount in ADA."""
        lovelace = Decimal(self.amount)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)


@dataclass
class PoolPerformance:
    """Pool performance metrics for APY calculation."""
    
    pool_id: str
    epoch: int
    blocks_expected: int
    blocks_minted: int
    luck: float  # Performance luck factor
    
    @property
    def performance_percentage(self) -> str:
        """Return performance as percentage."""
        if self.blocks_expected == 0:
            return "0.00%"
        performance = (self.blocks_minted / self.blocks_expected) * 100
        return f"{performance:.2f}%"


class StakingService:
    """Service for managing Cardano staking using Koios API."""
    
    def __init__(self, koios_client: KoiosClient):
        """Initialize staking service with Koios client.
        
        Args:
            koios_client: Configured KoiosClient instance
        """
        self.koios = koios_client
    
    async def get_account_info(self, stake_address: str) -> StakeAccount:
        """Get stake account information.
        
        Args:
            stake_address: Cardano stake address (stake1...)
            
        Returns:
            StakeAccount object with current status and balance
            
        Raises:
            KoiosError: If API request fails
        """
        try:
            # Call Koios /account_info endpoint
            response = await self.koios._request(
                "POST",
                "/account_info",
                json={"_stake_addresses": [stake_address]}
            )
            
            if not response or not isinstance(response, list) or len(response) == 0:
                # Account not found or not registered
                return StakeAccount(
                    stake_address=stake_address,
                    status="not registered"
                )
            
            account_info = response[0]
            
            # Extract account data
            status = account_info.get("status", "not registered")
            delegated_pool = account_info.get("delegated_pool")
            total_balance = account_info.get("total_balance", "0")
            available_rewards = account_info.get("rewards_available", "0")
            
            return StakeAccount(
                stake_address=stake_address,
                status=status,
                delegated_pool=delegated_pool,
                total_balance=total_balance,
                available_rewards=available_rewards,
                delegated_amount=total_balance if delegated_pool else "0"
            )
            
        except Exception as e:
            logger.error(f"Failed to get account info for {stake_address}: {e}")
            raise KoiosError(f"Failed to get stake account info: {e}")
    
    async def get_pool_list(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[StakePool]:
        """Get list of active stake pools.
        
        Args:
            limit: Maximum number of pools to return
            offset: Number of pools to skip
            
        Returns:
            List of StakePool objects
        """
        try:
            # Call Koios /pool_list endpoint
            response = await self.koios._request(
                "GET",
                "/pool_list",
                params={
                    "limit": limit,
                    "offset": offset
                }
            )
            
            if not response or not isinstance(response, list):
                return []
            
            pools = []
            for pool_data in response:
                pool = StakePool(
                    pool_id=pool_data.get("pool_id_hex", ""),
                    pool_id_bech32=pool_data.get("pool_id_bech32", ""),
                    ticker=pool_data.get("ticker"),
                    active_stake=pool_data.get("active_stake", "0"),
                    live_stake=pool_data.get("live_stake", "0"),
                    live_saturation=pool_data.get("live_saturation", 0.0),
                    blocks_minted=pool_data.get("block_count", 0),
                    live_delegators=pool_data.get("live_delegators", 0)
                )
                pools.append(pool)
            
            return pools
            
        except Exception as e:
            logger.error(f"Failed to get pool list: {e}")
            raise KoiosError(f"Failed to get pool list: {e}")
    
    async def get_pool_metadata(self, pool_id: str) -> Optional[StakePool]:
        """Get detailed metadata for a specific pool.
        
        Args:
            pool_id: Pool ID (hex or bech32)
            
        Returns:
            StakePool with detailed metadata, or None if not found
        """
        try:
            # Call Koios /pool_info endpoint
            response = await self.koios._request(
                "POST",
                "/pool_info",
                json={"_pool_bech32_ids": [pool_id]}
            )
            
            if not response or not isinstance(response, list) or len(response) == 0:
                return None
            
            pool_data = response[0]
            
            # Parse pool metadata
            metadata = pool_data.get("meta_json", {}) or {}
            
            return StakePool(
                pool_id=pool_data.get("pool_id_hex", ""),
                pool_id_bech32=pool_data.get("pool_id_bech32", ""),
                ticker=metadata.get("ticker"),
                name=metadata.get("name"),
                description=metadata.get("description"),
                homepage=metadata.get("homepage"),
                active_stake=pool_data.get("active_stake", "0"),
                live_stake=pool_data.get("live_stake", "0"),
                live_saturation=pool_data.get("live_saturation", 0.0),
                margin=pool_data.get("margin", 0.0),
                fixed_cost=pool_data.get("fixed_cost", "0"),
                blocks_minted=pool_data.get("block_count", 0),
                blocks_epoch=pool_data.get("blocks_epoch", 0),
                live_delegators=pool_data.get("live_delegators", 0)
            )
            
        except Exception as e:
            logger.warning(f"Failed to get pool metadata for {pool_id}: {e}")
            return None
    
    async def get_rewards_history(
        self,
        stake_address: str,
        limit: int = 20
    ) -> List[Reward]:
        """Get rewards history for a stake address.
        
        Args:
            stake_address: Cardano stake address
            limit: Maximum number of rewards to return
            
        Returns:
            List of Reward objects
        """
        try:
            # Call Koios /account_rewards endpoint
            response = await self.koios._request(
                "POST",
                "/account_rewards",
                json={"_stake_addresses": [stake_address]},
                params={"limit": limit}
            )
            
            if not response or not isinstance(response, list):
                return []
            
            rewards = []
            for reward_data in response:
                reward = Reward(
                    epoch=reward_data.get("epoch_no", 0),
                    amount=reward_data.get("amount", "0"),
                    pool_id=reward_data.get("pool_id", ""),
                    earned_epoch=reward_data.get("earned_epoch", 0)
                )
                rewards.append(reward)
            
            return rewards
            
        except Exception as e:
            logger.error(f"Failed to get rewards history for {stake_address}: {e}")
            raise KoiosError(f"Failed to get rewards history: {e}")
    
    async def calculate_apy(
        self,
        pool_id: str,
        epochs: int = 10
    ) -> Optional[float]:
        """Calculate estimated APY for a pool.
        
        This is a simplified calculation based on recent performance.
        Real APY depends on many factors including stake amount, pool luck, etc.
        
        Args:
            pool_id: Pool ID
            epochs: Number of epochs to consider
            
        Returns:
            Estimated APY as decimal (e.g., 0.05 = 5%), or None if cannot calculate
        """
        try:
            # Get pool info for active stake and margin
            pool_info = await self.get_pool_metadata(pool_id)
            if not pool_info:
                return None
            
            # Simplified APY calculation
            # Cardano average APY is around 4-5%
            # Adjust based on pool saturation and margin
            base_apy = 0.045  # 4.5% base
            
            # Penalty for high saturation (over 70%)
            if pool_info.live_saturation > 0.7:
                saturation_penalty = (pool_info.live_saturation - 0.7) * 0.1
                base_apy -= saturation_penalty
            
            # Adjust for pool margin
            apy = base_apy * (1 - pool_info.margin)
            
            return max(0.0, apy)  # Ensure non-negative
            
        except Exception as e:
            logger.warning(f"Failed to calculate APY for {pool_id}: {e}")
            return None


# Convenience functions
async def get_stake_account(
    stake_address: str,
    koios_client: Optional[KoiosClient] = None
) -> StakeAccount:
    """Get stake account info (convenience function).
    
    Args:
        stake_address: Cardano stake address
        koios_client: Optional pre-configured client
        
    Returns:
        StakeAccount object
    """
    client = koios_client or KoiosClient()
    try:
        service = StakingService(client)
        return await service.get_account_info(stake_address)
    finally:
        if koios_client is None:
            await client.close()


async def get_active_pools(
    limit: int = 50,
    koios_client: Optional[KoiosClient] = None
) -> List[StakePool]:
    """Get active stake pools (convenience function).
    
    Args:
        limit: Maximum number of pools
        koios_client: Optional pre-configured client
        
    Returns:
        List of StakePool objects
    """
    client = koios_client or KoiosClient()
    try:
        service = StakingService(client)
        return await service.get_pool_list(limit=limit)
    finally:
        if koios_client is None:
            await client.close()
