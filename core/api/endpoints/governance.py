"""FastAPI endpoints for governance operations.

Provides REST API for querying DReps, proposals, votes, and voting power.
Implements CIP-1694 Voltaire governance features.
"""

import sys
from pathlib import Path

# Ensure SDK imports resolve
sdk_path = Path(__file__).parent.parent.parent.parent / "sdk" / "src"
sys.path.insert(0, str(sdk_path))

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from decentralized_did.cardano.governance import (
    GovernanceService,
    DRep,
    Proposal,
    Vote,
    VotingPower,
    KoiosError,
)
from decentralized_did.cardano.koios_client import KoiosClient
from decentralized_did.cardano.cache import TTLCache

# Create router
router = APIRouter(prefix="/api/governance", tags=["governance"])

# Global Koios client (shared across requests)
koios_client = KoiosClient(cache=TTLCache(ttl_seconds=300, max_size=1000))


# Response models
class DRepResponse(BaseModel):
    """DRep API response model."""
    
    drep_id: str
    drep_hash: Optional[str] = None
    has_script: bool
    registered: bool
    url: Optional[str] = None
    metadata_hash: Optional[str] = None
    voting_power: str
    voting_power_ada: str
    delegators: int
    votes_cast: int
    last_vote_epoch: Optional[int] = None


class ProposalResponse(BaseModel):
    """Proposal API response model."""
    
    proposal_id: str
    proposal_type: str
    epoch: int
    title: Optional[str] = None
    abstract: Optional[str] = None
    motivation: Optional[str] = None
    rationale: Optional[str] = None
    yes_votes: str
    yes_votes_ada: str
    no_votes: str
    no_votes_ada: str
    abstain_votes: str
    total_votes: str
    approval_percentage: float
    status: str
    expiration_epoch: Optional[int] = None
    metadata_url: Optional[str] = None
    metadata_hash: Optional[str] = None


class VoteResponse(BaseModel):
    """Vote API response model."""
    
    proposal_id: str
    voter: str
    vote: str
    voting_power: str
    voting_power_ada: str
    epoch: int
    tx_hash: Optional[str] = None


class VotingPowerResponse(BaseModel):
    """Voting power API response model."""
    
    stake_address: str
    voting_power: str
    voting_power_ada: str
    delegated_drep: Optional[str] = None
    is_drep: bool


# Utility functions
def drep_to_response(drep: DRep) -> DRepResponse:
    """Convert DRep to API response."""
    return DRepResponse(
        drep_id=drep.drep_id,
        drep_hash=drep.drep_hash,
        has_script=drep.has_script,
        registered=drep.registered,
        url=drep.url,
        metadata_hash=drep.metadata_hash,
        voting_power=drep.voting_power,
        voting_power_ada=drep.voting_power_ada,
        delegators=drep.delegators,
        votes_cast=drep.votes_cast,
        last_vote_epoch=drep.last_vote_epoch,
    )


def proposal_to_response(proposal: Proposal) -> ProposalResponse:
    """Convert Proposal to API response."""
    return ProposalResponse(
        proposal_id=proposal.proposal_id,
        proposal_type=proposal.proposal_type,
        epoch=proposal.epoch,
        title=proposal.title,
        abstract=proposal.abstract,
        motivation=proposal.motivation,
        rationale=proposal.rationale,
        yes_votes=proposal.yes_votes,
        yes_votes_ada=proposal.yes_votes_ada,
        no_votes=proposal.no_votes,
        no_votes_ada=proposal.no_votes_ada,
        abstain_votes=proposal.abstain_votes,
        total_votes=proposal.total_votes,
        approval_percentage=proposal.approval_percentage,
        status=proposal.status,
        expiration_epoch=proposal.expiration_epoch,
        metadata_url=proposal.metadata_url,
        metadata_hash=proposal.metadata_hash,
    )


def vote_to_response(vote: Vote) -> VoteResponse:
    """Convert Vote to API response."""
    return VoteResponse(
        proposal_id=vote.proposal_id,
        voter=vote.voter,
        vote=vote.vote,
        voting_power=vote.voting_power,
        voting_power_ada=vote.voting_power_ada,
        epoch=vote.epoch,
        tx_hash=vote.tx_hash,
    )


def voting_power_to_response(vp: VotingPower) -> VotingPowerResponse:
    """Convert VotingPower to API response."""
    return VotingPowerResponse(
        stake_address=vp.stake_address,
        voting_power=vp.voting_power,
        voting_power_ada=vp.voting_power_ada,
        delegated_drep=vp.delegated_drep,
        is_drep=vp.is_drep,
    )


# Endpoints
@router.get("/dreps", response_model=List[DRepResponse])
async def get_drep_list(
    limit: int = Query(50, ge=1, le=100, description="Maximum DReps to return"),
    offset: int = Query(0, ge=0, description="Number of DReps to skip")
):
    """Get list of registered DReps.
    
    Returns DReps sorted by voting power (highest first).
    
    Args:
        limit: Maximum number of DReps (1-100)
        offset: Pagination offset
        
    Returns:
        List of DReps with voting power and metadata
        
    Raises:
        HTTPException: 500 if service error
        
    Note:
        CIP-1694 is relatively new. This endpoint may return empty data
        if not yet implemented in Koios API.
    """
    try:
        service = GovernanceService(koios_client)
        dreps = await service.get_drep_list(limit, offset)
        
        return [drep_to_response(drep) for drep in dreps]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/drep/{drep_id}", response_model=DRepResponse)
async def get_drep_details(
    drep_id: str = Field(..., description="DRep identifier")
):
    """Get detailed information for a specific DRep.
    
    Args:
        drep_id: DRep identifier
        
    Returns:
        DRep with full details and metadata
        
    Raises:
        HTTPException: 404 if DRep not found, 500 if service error
    """
    try:
        service = GovernanceService(koios_client)
        drep = await service.get_drep_info(drep_id)
        
        if not drep:
            raise HTTPException(status_code=404, detail="DRep not found")
        
        return drep_to_response(drep)
    except HTTPException:
        raise
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/proposals", response_model=List[ProposalResponse])
async def get_proposal_list(
    status: Optional[str] = Query(None, description="Filter by status (active, passed, rejected, expired)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum proposals to return"),
    offset: int = Query(0, ge=0, description="Number of proposals to skip")
):
    """Get list of governance proposals.
    
    Returns proposals with voting statistics.
    
    Args:
        status: Filter by proposal status
        limit: Maximum number of proposals (1-100)
        offset: Pagination offset
        
    Returns:
        List of proposals with vote counts
        
    Raises:
        HTTPException: 500 if service error
    """
    try:
        service = GovernanceService(koios_client)
        proposals = await service.get_proposals(status, limit, offset)
        
        return [proposal_to_response(proposal) for proposal in proposals]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/proposal/{proposal_id}/votes", response_model=List[VoteResponse])
async def get_proposal_votes(
    proposal_id: str = Field(..., description="Proposal identifier"),
    limit: int = Query(100, ge=1, le=200, description="Maximum votes to return")
):
    """Get votes for a specific proposal.
    
    Args:
        proposal_id: Proposal identifier
        limit: Maximum number of votes (1-200)
        
    Returns:
        List of votes with voting power
        
    Raises:
        HTTPException: 500 if service error
    """
    try:
        service = GovernanceService(koios_client)
        votes = await service.get_proposal_votes(proposal_id, limit)
        
        return [vote_to_response(vote) for vote in votes]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/voting-power/{stake_address}", response_model=VotingPowerResponse)
async def get_voting_power(
    stake_address: str = Field(..., description="Cardano stake address")
):
    """Get voting power for a stake address.
    
    Args:
        stake_address: Cardano stake address
        
    Returns:
        Voting power and DRep delegation status
        
    Raises:
        HTTPException: 404 if address not found, 500 if service error
    """
    try:
        service = GovernanceService(koios_client)
        vp = await service.get_voting_power(stake_address)
        
        if not vp:
            raise HTTPException(status_code=404, detail="Stake address not found")
        
        return voting_power_to_response(vp)
    except HTTPException:
        raise
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/vote-history/{voter}", response_model=List[VoteResponse])
async def get_vote_history(
    voter: str = Field(..., description="DRep ID or stake address"),
    limit: int = Query(20, ge=1, le=100, description="Maximum votes to return")
):
    """Get vote history for a DRep or stake address.
    
    Args:
        voter: DRep ID or stake address
        limit: Maximum number of votes (1-100)
        
    Returns:
        List of historical votes
        
    Raises:
        HTTPException: 500 if service error
    """
    try:
        service = GovernanceService(koios_client)
        votes = await service.get_vote_history(voter, limit)
        
        return [vote_to_response(vote) for vote in votes]
    except KoiosError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for governance service."""
    return {"status": "ok", "service": "governance", "note": "CIP-1694 endpoints may have limited data"}
