"""Governance service for Cardano using Koios API.

Provides functions for querying DReps, governance proposals, voting power,
and vote history. Supports CIP-1694 Voltaire governance features.

Note: CIP-1694 is relatively new. Some endpoints may have limited data
depending on Koios API implementation status.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from decimal import Decimal

from .koios_client import KoiosClient, KoiosError

logger = logging.getLogger(__name__)

# Constants
LOVELACE_PER_ADA = 1_000_000


@dataclass
class DRep:
    """Represents a Delegated Representative (DRep)."""
    
    drep_id: str
    drep_hash: Optional[str] = None
    has_script: bool = False
    registered: bool = False
    
    # Metadata
    url: Optional[str] = None
    metadata_hash: Optional[str] = None
    
    # Voting power
    voting_power: str = "0"  # Active stake delegated to this DRep
    delegators: int = 0
    
    # Activity
    votes_cast: int = 0
    last_vote_epoch: Optional[int] = None
    
    @property
    def voting_power_ada(self) -> str:
        """Return voting power in ADA (millions)."""
        lovelace = Decimal(self.voting_power)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        millions = ada / Decimal(1_000_000)
        return f"{millions:.2f}M"


@dataclass
class Proposal:
    """Represents a governance proposal."""
    
    proposal_id: str
    proposal_type: str  # "TreasuryWithdrawals", "ParameterChange", "HardForkInitiation", etc.
    epoch: int
    
    # Description
    title: Optional[str] = None
    abstract: Optional[str] = None
    motivation: Optional[str] = None
    rationale: Optional[str] = None
    
    # Voting
    yes_votes: str = "0"  # Voting power in lovelace
    no_votes: str = "0"
    abstain_votes: str = "0"
    
    # Status
    status: str = "active"  # active, passed, rejected, expired
    expiration_epoch: Optional[int] = None
    
    # Metadata
    metadata_url: Optional[str] = None
    metadata_hash: Optional[str] = None
    
    @property
    def yes_votes_ada(self) -> str:
        """Return yes votes in ADA."""
        lovelace = Decimal(self.yes_votes)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)
    
    @property
    def no_votes_ada(self) -> str:
        """Return no votes in ADA."""
        lovelace = Decimal(self.no_votes)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)
    
    @property
    def total_votes(self) -> str:
        """Return total votes in lovelace."""
        total = Decimal(self.yes_votes) + Decimal(self.no_votes) + Decimal(self.abstain_votes)
        return str(total)
    
    @property
    def approval_percentage(self) -> float:
        """Calculate approval percentage."""
        total = Decimal(self.total_votes)
        if total == 0:
            return 0.0
        yes = Decimal(self.yes_votes)
        return float((yes / total) * 100)


@dataclass
class Vote:
    """Represents a vote on a proposal."""
    
    proposal_id: str
    voter: str  # DRep ID or stake address
    vote: str  # "yes", "no", "abstain"
    voting_power: str  # Voting power in lovelace
    epoch: int
    tx_hash: Optional[str] = None
    
    @property
    def voting_power_ada(self) -> str:
        """Return voting power in ADA."""
        lovelace = Decimal(self.voting_power)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)


@dataclass
class VotingPower:
    """Represents voting power for an address."""
    
    stake_address: str
    voting_power: str  # Total voting power in lovelace
    delegated_drep: Optional[str] = None
    is_drep: bool = False
    
    @property
    def voting_power_ada(self) -> str:
        """Return voting power in ADA."""
        lovelace = Decimal(self.voting_power)
        ada = lovelace / Decimal(LOVELACE_PER_ADA)
        return str(ada)


class GovernanceService:
    """Service for managing Cardano governance using Koios API."""
    
    def __init__(self, koios_client: KoiosClient):
        """Initialize governance service with Koios client.
        
        Args:
            koios_client: Configured KoiosClient instance
        """
        self.koios = koios_client
    
    async def get_drep_list(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[DRep]:
        """Get list of registered DReps.
        
        Args:
            limit: Maximum number of DReps to return
            offset: Number of DReps to skip
            
        Returns:
            List of DRep objects
            
        Note:
            This endpoint may have limited availability depending on
            Koios API CIP-1694 implementation status.
        """
        try:
            # Call Koios /drep_list endpoint (CIP-1694)
            # Note: This may not be fully implemented yet
            response = await self.koios._request(
                "GET",
                "/drep_list",
                params={
                    "limit": limit,
                    "offset": offset
                }
            )
            
            if not response or not isinstance(response, list):
                logger.warning("DRep list endpoint returned no data - may not be implemented")
                return []
            
            dreps = []
            for drep_data in response:
                drep = DRep(
                    drep_id=drep_data.get("drep_id", ""),
                    drep_hash=drep_data.get("drep_hash"),
                    has_script=drep_data.get("has_script", False),
                    registered=drep_data.get("registered", False),
                    url=drep_data.get("url"),
                    metadata_hash=drep_data.get("metadata_hash"),
                    voting_power=drep_data.get("voting_power", "0"),
                    delegators=drep_data.get("delegators", 0),
                    votes_cast=drep_data.get("votes_cast", 0),
                    last_vote_epoch=drep_data.get("last_vote_epoch")
                )
                dreps.append(drep)
            
            return dreps
            
        except Exception as e:
            logger.warning(f"Failed to get DRep list (may not be implemented): {e}")
            # Return empty list instead of failing - feature may not be available yet
            return []
    
    async def get_drep_info(self, drep_id: str) -> Optional[DRep]:
        """Get detailed information for a specific DRep.
        
        Args:
            drep_id: DRep identifier
            
        Returns:
            DRep object or None if not found
        """
        try:
            response = await self.koios._request(
                "POST",
                "/drep_info",
                json={"_drep_ids": [drep_id]}
            )
            
            if not response or not isinstance(response, list) or len(response) == 0:
                return None
            
            drep_data = response[0]
            
            return DRep(
                drep_id=drep_data.get("drep_id", drep_id),
                drep_hash=drep_data.get("drep_hash"),
                has_script=drep_data.get("has_script", False),
                registered=drep_data.get("registered", False),
                url=drep_data.get("url"),
                metadata_hash=drep_data.get("metadata_hash"),
                voting_power=drep_data.get("voting_power", "0"),
                delegators=drep_data.get("delegators", 0),
                votes_cast=drep_data.get("votes_cast", 0),
                last_vote_epoch=drep_data.get("last_vote_epoch")
            )
            
        except Exception as e:
            logger.warning(f"Failed to get DRep info for {drep_id}: {e}")
            return None
    
    async def get_proposals(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Proposal]:
        """Get list of governance proposals.
        
        Args:
            status: Filter by status (active, passed, rejected, expired)
            limit: Maximum number of proposals to return
            offset: Number of proposals to skip
            
        Returns:
            List of Proposal objects
        """
        try:
            params = {
                "limit": limit,
                "offset": offset
            }
            if status:
                params["status"] = status
            
            response = await self.koios._request(
                "GET",
                "/proposal_list",
                params=params
            )
            
            if not response or not isinstance(response, list):
                logger.warning("Proposal list endpoint returned no data")
                return []
            
            proposals = []
            for prop_data in response:
                proposal = Proposal(
                    proposal_id=prop_data.get("proposal_id", ""),
                    proposal_type=prop_data.get("proposal_type", "unknown"),
                    epoch=prop_data.get("epoch", 0),
                    title=prop_data.get("title"),
                    abstract=prop_data.get("abstract"),
                    motivation=prop_data.get("motivation"),
                    rationale=prop_data.get("rationale"),
                    yes_votes=prop_data.get("yes_votes", "0"),
                    no_votes=prop_data.get("no_votes", "0"),
                    abstain_votes=prop_data.get("abstain_votes", "0"),
                    status=prop_data.get("status", "active"),
                    expiration_epoch=prop_data.get("expiration_epoch"),
                    metadata_url=prop_data.get("metadata_url"),
                    metadata_hash=prop_data.get("metadata_hash")
                )
                proposals.append(proposal)
            
            return proposals
            
        except Exception as e:
            logger.warning(f"Failed to get proposals: {e}")
            return []
    
    async def get_proposal_votes(
        self,
        proposal_id: str,
        limit: int = 100
    ) -> List[Vote]:
        """Get votes for a specific proposal.
        
        Args:
            proposal_id: Proposal identifier
            limit: Maximum number of votes to return
            
        Returns:
            List of Vote objects
        """
        try:
            response = await self.koios._request(
                "POST",
                "/proposal_votes",
                json={"_proposal_id": proposal_id},
                params={"limit": limit}
            )
            
            if not response or not isinstance(response, list):
                return []
            
            votes = []
            for vote_data in response:
                vote = Vote(
                    proposal_id=proposal_id,
                    voter=vote_data.get("voter", ""),
                    vote=vote_data.get("vote", ""),
                    voting_power=vote_data.get("voting_power", "0"),
                    epoch=vote_data.get("epoch", 0),
                    tx_hash=vote_data.get("tx_hash")
                )
                votes.append(vote)
            
            return votes
            
        except Exception as e:
            logger.warning(f"Failed to get votes for proposal {proposal_id}: {e}")
            return []
    
    async def get_voting_power(self, stake_address: str) -> Optional[VotingPower]:
        """Get voting power for a stake address.
        
        Args:
            stake_address: Cardano stake address
            
        Returns:
            VotingPower object or None if not found
        """
        try:
            # Get account info which includes voting power
            response = await self.koios._request(
                "POST",
                "/account_info",
                json={"_stake_addresses": [stake_address]}
            )
            
            if not response or not isinstance(response, list) or len(response) == 0:
                return None
            
            account_data = response[0]
            
            return VotingPower(
                stake_address=stake_address,
                voting_power=account_data.get("total_balance", "0"),
                delegated_drep=account_data.get("delegated_drep"),
                is_drep=account_data.get("is_drep", False)
            )
            
        except Exception as e:
            logger.error(f"Failed to get voting power for {stake_address}: {e}")
            raise KoiosError(f"Failed to get voting power: {e}")
    
    async def get_vote_history(
        self,
        voter: str,
        limit: int = 20
    ) -> List[Vote]:
        """Get vote history for a DRep or stake address.
        
        Args:
            voter: DRep ID or stake address
            limit: Maximum number of votes to return
            
        Returns:
            List of Vote objects
        """
        try:
            response = await self.koios._request(
                "POST",
                "/voter_history",
                json={"_voter": voter},
                params={"limit": limit}
            )
            
            if not response or not isinstance(response, list):
                return []
            
            votes = []
            for vote_data in response:
                vote = Vote(
                    proposal_id=vote_data.get("proposal_id", ""),
                    voter=voter,
                    vote=vote_data.get("vote", ""),
                    voting_power=vote_data.get("voting_power", "0"),
                    epoch=vote_data.get("epoch", 0),
                    tx_hash=vote_data.get("tx_hash")
                )
                votes.append(vote)
            
            return votes
            
        except Exception as e:
            logger.warning(f"Failed to get vote history for {voter}: {e}")
            return []


# Convenience functions
async def get_dreps(
    limit: int = 50,
    koios_client: Optional[KoiosClient] = None
) -> List[DRep]:
    """Get DRep list (convenience function).
    
    Args:
        limit: Maximum number of DReps
        koios_client: Optional pre-configured client
        
    Returns:
        List of DReps
    """
    client = koios_client or KoiosClient()
    try:
        service = GovernanceService(client)
        return await service.get_drep_list(limit=limit)
    finally:
        if koios_client is None:
            await client.close()


async def get_active_proposals(
    koios_client: Optional[KoiosClient] = None
) -> List[Proposal]:
    """Get active proposals (convenience function).
    
    Args:
        koios_client: Optional pre-configured client
        
    Returns:
        List of active proposals
    """
    client = koios_client or KoiosClient()
    try:
        service = GovernanceService(client)
        return await service.get_proposals(status="active")
    finally:
        if koios_client is None:
            await client.close()
