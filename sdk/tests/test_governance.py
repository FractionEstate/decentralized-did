"""Tests for governance service."""

import pytest
from unittest.mock import AsyncMock, Mock

from decentralized_did.cardano.governance import (
    GovernanceService,
    DRep,
    Proposal,
    Vote,
    VotingPower,
    get_dreps,
    get_active_proposals,
)
from decentralized_did.cardano.koios_client import KoiosClient, KoiosError


# Mock data
MOCK_DREP_ID = "drep1abc123def456"
MOCK_STAKE_ADDRESS = "stake1u80jysjtdzqt8qz8xq9y6dtj0rqh8kqwj5qjkqzqxqz0qg6q6q6"
MOCK_PROPOSAL_ID = "prop_treasury_001"


@pytest.fixture
def mock_koios_client():
    """Create mock Koios client."""
    client = Mock(spec=KoiosClient)
    client._request = AsyncMock()
    return client


@pytest.fixture
def governance_service(mock_koios_client):
    """Create governance service with mock client."""
    return GovernanceService(mock_koios_client)


class TestDRep:
    """Test DRep dataclass."""
    
    def test_drep_voting_power_conversion(self):
        """Test voting power conversion to ADA millions."""
        drep = DRep(
            drep_id=MOCK_DREP_ID,
            voting_power="50000000000000"  # 50M ADA
        )
        assert "50.00M" in drep.voting_power_ada


class TestProposal:
    """Test Proposal dataclass."""
    
    def test_proposal_vote_conversions(self):
        """Test vote amount conversions."""
        proposal = Proposal(
            proposal_id=MOCK_PROPOSAL_ID,
            proposal_type="TreasuryWithdrawals",
            epoch=400,
            yes_votes="10000000000000",  # 10M ADA
            no_votes="5000000000000",  # 5M ADA
            abstain_votes="1000000000000"  # 1M ADA
        )
        assert proposal.yes_votes_ada == "10000000"
        assert proposal.no_votes_ada == "5000000"
        assert proposal.total_votes == "16000000000000"
    
    def test_proposal_approval_percentage(self):
        """Test approval percentage calculation."""
        proposal = Proposal(
            proposal_id=MOCK_PROPOSAL_ID,
            proposal_type="ParameterChange",
            epoch=400,
            yes_votes="7500000",  # 75%
            no_votes="2500000",  # 25%
            abstain_votes="0"
        )
        assert proposal.approval_percentage == 75.0
    
    def test_proposal_approval_percentage_zero_votes(self):
        """Test approval percentage with no votes."""
        proposal = Proposal(
            proposal_id=MOCK_PROPOSAL_ID,
            proposal_type="HardForkInitiation",
            epoch=400
        )
        assert proposal.approval_percentage == 0.0


class TestVote:
    """Test Vote dataclass."""
    
    def test_vote_power_conversion(self):
        """Test voting power conversion."""
        vote = Vote(
            proposal_id=MOCK_PROPOSAL_ID,
            voter=MOCK_DREP_ID,
            vote="yes",
            voting_power="5000000",  # 5 ADA
            epoch=400
        )
        assert vote.voting_power_ada == "5"


class TestVotingPower:
    """Test VotingPower dataclass."""
    
    def test_voting_power_conversion(self):
        """Test voting power ADA conversion."""
        vp = VotingPower(
            stake_address=MOCK_STAKE_ADDRESS,
            voting_power="10000000"  # 10 ADA
        )
        assert vp.voting_power_ada == "10"


class TestGovernanceService:
    """Test GovernanceService methods."""
    
    @pytest.mark.asyncio
    async def test_get_drep_list_success(self, governance_service, mock_koios_client):
        """Test successful DRep list retrieval."""
        mock_koios_client._request.return_value = [
            {
                "drep_id": "drep1abc",
                "drep_hash": "hash123",
                "has_script": False,
                "registered": True,
                "url": "https://drep1.io",
                "metadata_hash": "meta123",
                "voting_power": "50000000000000",
                "delegators": 100,
                "votes_cast": 25,
                "last_vote_epoch": 399
            },
            {
                "drep_id": "drep2def",
                "registered": True,
                "voting_power": "30000000000000",
                "delegators": 75,
                "votes_cast": 10
            }
        ]
        
        dreps = await governance_service.get_drep_list(limit=10)
        
        assert len(dreps) == 2
        assert dreps[0].drep_id == "drep1abc"
        assert dreps[0].registered is True
        assert dreps[0].voting_power == "50000000000000"
        assert dreps[0].delegators == 100
        assert dreps[1].drep_id == "drep2def"
    
    @pytest.mark.asyncio
    async def test_get_drep_list_empty(self, governance_service, mock_koios_client):
        """Test empty DRep list (feature not implemented)."""
        mock_koios_client._request.return_value = []
        
        dreps = await governance_service.get_drep_list()
        
        assert len(dreps) == 0
    
    @pytest.mark.asyncio
    async def test_get_drep_list_error_returns_empty(self, governance_service, mock_koios_client):
        """Test DRep list returns empty on error (graceful degradation)."""
        mock_koios_client._request.side_effect = Exception("Endpoint not available")
        
        dreps = await governance_service.get_drep_list()
        
        assert len(dreps) == 0
    
    @pytest.mark.asyncio
    async def test_get_drep_info_success(self, governance_service, mock_koios_client):
        """Test successful DRep info retrieval."""
        mock_koios_client._request.return_value = [{
            "drep_id": MOCK_DREP_ID,
            "drep_hash": "hash123",
            "registered": True,
            "url": "https://mydrep.io",
            "voting_power": "25000000000000",
            "delegators": 50,
            "votes_cast": 15,
            "last_vote_epoch": 398
        }]
        
        drep = await governance_service.get_drep_info(MOCK_DREP_ID)
        
        assert drep is not None
        assert drep.drep_id == MOCK_DREP_ID
        assert drep.registered is True
        assert drep.url == "https://mydrep.io"
        assert drep.voting_power == "25000000000000"
    
    @pytest.mark.asyncio
    async def test_get_drep_info_not_found(self, governance_service, mock_koios_client):
        """Test DRep info not found."""
        mock_koios_client._request.return_value = []
        
        drep = await governance_service.get_drep_info(MOCK_DREP_ID)
        
        assert drep is None
    
    @pytest.mark.asyncio
    async def test_get_proposals_success(self, governance_service, mock_koios_client):
        """Test successful proposals retrieval."""
        mock_koios_client._request.return_value = [
            {
                "proposal_id": "prop1",
                "proposal_type": "TreasuryWithdrawals",
                "epoch": 400,
                "title": "Fund Project X",
                "abstract": "Request for funding",
                "yes_votes": "10000000000",
                "no_votes": "5000000000",
                "abstain_votes": "1000000000",
                "status": "active",
                "expiration_epoch": 410
            },
            {
                "proposal_id": "prop2",
                "proposal_type": "ParameterChange",
                "epoch": 395,
                "title": "Update min fee",
                "yes_votes": "8000000000",
                "no_votes": "2000000000",
                "abstain_votes": "500000000",
                "status": "passed"
            }
        ]
        
        proposals = await governance_service.get_proposals()
        
        assert len(proposals) == 2
        assert proposals[0].proposal_id == "prop1"
        assert proposals[0].proposal_type == "TreasuryWithdrawals"
        assert proposals[0].status == "active"
        assert proposals[1].proposal_id == "prop2"
        assert proposals[1].status == "passed"
    
    @pytest.mark.asyncio
    async def test_get_proposals_filtered_by_status(self, governance_service, mock_koios_client):
        """Test proposals filtered by status."""
        mock_koios_client._request.return_value = [{
            "proposal_id": "prop1",
            "proposal_type": "TreasuryWithdrawals",
            "epoch": 400,
            "status": "active"
        }]
        
        proposals = await governance_service.get_proposals(status="active")
        
        assert len(proposals) == 1
        assert proposals[0].status == "active"
    
    @pytest.mark.asyncio
    async def test_get_proposals_empty(self, governance_service, mock_koios_client):
        """Test empty proposals list."""
        mock_koios_client._request.return_value = []
        
        proposals = await governance_service.get_proposals()
        
        assert len(proposals) == 0
    
    @pytest.mark.asyncio
    async def test_get_proposal_votes_success(self, governance_service, mock_koios_client):
        """Test successful proposal votes retrieval."""
        mock_koios_client._request.return_value = [
            {
                "voter": "drep1abc",
                "vote": "yes",
                "voting_power": "5000000000",
                "epoch": 400,
                "tx_hash": "abc123"
            },
            {
                "voter": "drep2def",
                "vote": "no",
                "voting_power": "3000000000",
                "epoch": 400,
                "tx_hash": "def456"
            }
        ]
        
        votes = await governance_service.get_proposal_votes(MOCK_PROPOSAL_ID)
        
        assert len(votes) == 2
        assert votes[0].voter == "drep1abc"
        assert votes[0].vote == "yes"
        assert votes[0].voting_power == "5000000000"
        assert votes[1].vote == "no"
    
    @pytest.mark.asyncio
    async def test_get_proposal_votes_empty(self, governance_service, mock_koios_client):
        """Test empty proposal votes."""
        mock_koios_client._request.return_value = []
        
        votes = await governance_service.get_proposal_votes(MOCK_PROPOSAL_ID)
        
        assert len(votes) == 0
    
    @pytest.mark.asyncio
    async def test_get_voting_power_success(self, governance_service, mock_koios_client):
        """Test successful voting power retrieval."""
        mock_koios_client._request.return_value = [{
            "total_balance": "10000000",
            "delegated_drep": MOCK_DREP_ID,
            "is_drep": False
        }]
        
        vp = await governance_service.get_voting_power(MOCK_STAKE_ADDRESS)
        
        assert vp is not None
        assert vp.stake_address == MOCK_STAKE_ADDRESS
        assert vp.voting_power == "10000000"
        assert vp.delegated_drep == MOCK_DREP_ID
        assert vp.is_drep is False
    
    @pytest.mark.asyncio
    async def test_get_voting_power_not_found(self, governance_service, mock_koios_client):
        """Test voting power not found."""
        mock_koios_client._request.return_value = []
        
        vp = await governance_service.get_voting_power(MOCK_STAKE_ADDRESS)
        
        assert vp is None
    
    @pytest.mark.asyncio
    async def test_get_vote_history_success(self, governance_service, mock_koios_client):
        """Test successful vote history retrieval."""
        mock_koios_client._request.return_value = [
            {
                "proposal_id": "prop1",
                "vote": "yes",
                "voting_power": "5000000",
                "epoch": 400,
                "tx_hash": "abc123"
            },
            {
                "proposal_id": "prop2",
                "vote": "no",
                "voting_power": "5000000",
                "epoch": 399,
                "tx_hash": "def456"
            }
        ]
        
        votes = await governance_service.get_vote_history(MOCK_DREP_ID)
        
        assert len(votes) == 2
        assert votes[0].proposal_id == "prop1"
        assert votes[0].vote == "yes"
        assert votes[1].proposal_id == "prop2"
        assert votes[1].vote == "no"
    
    @pytest.mark.asyncio
    async def test_get_vote_history_empty(self, governance_service, mock_koios_client):
        """Test empty vote history."""
        mock_koios_client._request.return_value = []
        
        votes = await governance_service.get_vote_history(MOCK_DREP_ID)
        
        assert len(votes) == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_get_dreps_creates_client(self):
        """Test get_dreps creates and closes client."""
        from unittest.mock import patch
        
        with patch('decentralized_did.cardano.governance.KoiosClient') as mock_client_class:
            mock_client = Mock(spec=KoiosClient)
            mock_client.close = AsyncMock()
            mock_client._request = AsyncMock(return_value=[{
                "drep_id": "drep1",
                "registered": True,
                "voting_power": "10000000"
            }])
            mock_client_class.return_value = mock_client
            
            dreps = await get_dreps(limit=10)
            
            assert len(dreps) == 1
            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_proposals_creates_client(self):
        """Test get_active_proposals creates and closes client."""
        from unittest.mock import patch
        
        with patch('decentralized_did.cardano.governance.KoiosClient') as mock_client_class:
            mock_client = Mock(spec=KoiosClient)
            mock_client.close = AsyncMock()
            mock_client._request = AsyncMock(return_value=[{
                "proposal_id": "prop1",
                "proposal_type": "TreasuryWithdrawals",
                "epoch": 400,
                "status": "active"
            }])
            mock_client_class.return_value = mock_client
            
            proposals = await get_active_proposals()
            
            assert len(proposals) == 1
            mock_client.close.assert_called_once()
