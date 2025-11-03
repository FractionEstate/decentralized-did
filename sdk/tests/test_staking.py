"""Tests for staking service."""

import pytest
from unittest.mock import AsyncMock, Mock
from decimal import Decimal

from decentralized_did.cardano.staking import (
    StakingService,
    StakeAccount,
    StakePool,
    Reward,
    get_stake_account,
    get_active_pools,
    LOVELACE_PER_ADA,
)
from decentralized_did.cardano.koios_client import KoiosClient, KoiosError


# Mock data
MOCK_STAKE_ADDRESS = "stake1u80jysjtdzqt8qz8xq9y6dtj0rqh8kqwj5qjkqzqxqz0qg6q6q6"
MOCK_POOL_ID = "pool1pu5jlj4q9w9jlxeu370a3c9myx47md5j5m2str0naunn2q3lkdy"


@pytest.fixture
def mock_koios_client():
    """Create mock Koios client."""
    client = Mock(spec=KoiosClient)
    client._request = AsyncMock()
    return client


@pytest.fixture
def staking_service(mock_koios_client):
    """Create staking service with mock client."""
    return StakingService(mock_koios_client)


class TestStakeAccount:
    """Test StakeAccount dataclass."""
    
    def test_stake_account_balance_conversion(self):
        """Test ADA balance conversion."""
        account = StakeAccount(
            stake_address=MOCK_STAKE_ADDRESS,
            status="registered",
            total_balance="5000000",
            available_rewards="100000"
        )
        assert account.total_balance_ada == "5"
        assert account.rewards_ada == "0.1"
    
    def test_stake_account_is_delegated(self):
        """Test delegation status check."""
        account_delegated = StakeAccount(
            stake_address=MOCK_STAKE_ADDRESS,
            status="registered",
            delegated_pool=MOCK_POOL_ID
        )
        assert account_delegated.is_delegated is True
        
        account_not_delegated = StakeAccount(
            stake_address=MOCK_STAKE_ADDRESS,
            status="registered"
        )
        assert account_not_delegated.is_delegated is False


class TestStakePool:
    """Test StakePool dataclass."""
    
    def test_pool_stake_formatting(self):
        """Test stake formatting in millions."""
        pool = StakePool(
            pool_id="pool123",
            pool_id_bech32=MOCK_POOL_ID,
            active_stake="50000000000000"  # 50M ADA
        )
        assert "50.00M" in pool.active_stake_ada
    
    def test_pool_cost_conversion(self):
        """Test fixed cost conversion."""
        pool = StakePool(
            pool_id="pool123",
            pool_id_bech32=MOCK_POOL_ID,
            fixed_cost="340000000"  # 340 ADA
        )
        assert pool.fixed_cost_ada == "340"
    
    def test_pool_percentages(self):
        """Test percentage formatting."""
        pool = StakePool(
            pool_id="pool123",
            pool_id_bech32=MOCK_POOL_ID,
            margin=0.025,  # 2.5%
            live_saturation=0.75  # 75%
        )
        assert pool.margin_percentage == "2.50%"
        assert pool.saturation_percentage == "75.00%"


class TestReward:
    """Test Reward dataclass."""
    
    def test_reward_amount_conversion(self):
        """Test reward ADA conversion."""
        reward = Reward(
            epoch=400,
            amount="2500000",  # 2.5 ADA
            pool_id=MOCK_POOL_ID,
            earned_epoch=398
        )
        assert reward.amount_ada == "2.5"


class TestStakingService:
    """Test StakingService methods."""
    
    @pytest.mark.asyncio
    async def test_get_account_info_success(self, staking_service, mock_koios_client):
        """Test successful account info retrieval."""
        mock_koios_client._request.return_value = [{
            "status": "registered",
            "delegated_pool": MOCK_POOL_ID,
            "total_balance": "10000000",
            "rewards_available": "500000"
        }]
        
        account = await staking_service.get_account_info(MOCK_STAKE_ADDRESS)
        
        assert account.stake_address == MOCK_STAKE_ADDRESS
        assert account.status == "registered"
        assert account.delegated_pool == MOCK_POOL_ID
        assert account.total_balance == "10000000"
        assert account.available_rewards == "500000"
        assert account.is_delegated is True
    
    @pytest.mark.asyncio
    async def test_get_account_info_not_registered(self, staking_service, mock_koios_client):
        """Test account info for unregistered account."""
        mock_koios_client._request.return_value = []
        
        account = await staking_service.get_account_info(MOCK_STAKE_ADDRESS)
        
        assert account.status == "not registered"
        assert account.is_delegated is False
    
    @pytest.mark.asyncio
    async def test_get_account_info_error(self, staking_service, mock_koios_client):
        """Test account info error handling."""
        mock_koios_client._request.side_effect = Exception("Network error")
        
        with pytest.raises(KoiosError, match="Failed to get stake account info"):
            await staking_service.get_account_info(MOCK_STAKE_ADDRESS)
    
    @pytest.mark.asyncio
    async def test_get_pool_list_success(self, staking_service, mock_koios_client):
        """Test successful pool list retrieval."""
        mock_koios_client._request.return_value = [
            {
                "pool_id_hex": "abc123",
                "pool_id_bech32": MOCK_POOL_ID,
                "ticker": "POOL1",
                "active_stake": "50000000000000",
                "live_stake": "49000000000000",
                "live_saturation": 0.60,
                "block_count": 1000,
                "live_delegators": 500
            },
            {
                "pool_id_hex": "def456",
                "pool_id_bech32": "pool2abc",
                "ticker": "POOL2",
                "active_stake": "30000000000000",
                "live_stake": "29000000000000",
                "live_saturation": 0.40,
                "block_count": 600,
                "live_delegators": 300
            }
        ]
        
        pools = await staking_service.get_pool_list(limit=10)
        
        assert len(pools) == 2
        assert pools[0].ticker == "POOL1"
        assert pools[0].live_saturation == 0.60
        assert pools[1].ticker == "POOL2"
    
    @pytest.mark.asyncio
    async def test_get_pool_list_empty(self, staking_service, mock_koios_client):
        """Test empty pool list."""
        mock_koios_client._request.return_value = []
        
        pools = await staking_service.get_pool_list()
        
        assert len(pools) == 0
    
    @pytest.mark.asyncio
    async def test_get_pool_metadata_success(self, staking_service, mock_koios_client):
        """Test successful pool metadata retrieval."""
        mock_koios_client._request.return_value = [{
            "pool_id_hex": "abc123",
            "pool_id_bech32": MOCK_POOL_ID,
            "meta_json": {
                "ticker": "POOL1",
                "name": "Test Pool",
                "description": "A test pool",
                "homepage": "https://testpool.io"
            },
            "active_stake": "50000000000000",
            "live_stake": "49000000000000",
            "live_saturation": 0.60,
            "margin": 0.02,
            "fixed_cost": "340000000",
            "block_count": 1000,
            "blocks_epoch": 5,
            "live_delegators": 500
        }]
        
        pool = await staking_service.get_pool_metadata(MOCK_POOL_ID)
        
        assert pool is not None
        assert pool.ticker == "POOL1"
        assert pool.name == "Test Pool"
        assert pool.homepage == "https://testpool.io"
        assert pool.margin == 0.02
        assert pool.fixed_cost == "340000000"
    
    @pytest.mark.asyncio
    async def test_get_pool_metadata_not_found(self, staking_service, mock_koios_client):
        """Test pool metadata not found."""
        mock_koios_client._request.return_value = []
        
        pool = await staking_service.get_pool_metadata(MOCK_POOL_ID)
        
        assert pool is None
    
    @pytest.mark.asyncio
    async def test_get_rewards_history_success(self, staking_service, mock_koios_client):
        """Test successful rewards history retrieval."""
        mock_koios_client._request.return_value = [
            {
                "epoch_no": 400,
                "amount": "2500000",
                "pool_id": MOCK_POOL_ID,
                "earned_epoch": 398
            },
            {
                "epoch_no": 399,
                "amount": "2400000",
                "pool_id": MOCK_POOL_ID,
                "earned_epoch": 397
            }
        ]
        
        rewards = await staking_service.get_rewards_history(MOCK_STAKE_ADDRESS, limit=10)
        
        assert len(rewards) == 2
        assert rewards[0].epoch == 400
        assert rewards[0].amount == "2500000"
        assert rewards[1].epoch == 399
    
    @pytest.mark.asyncio
    async def test_get_rewards_history_empty(self, staking_service, mock_koios_client):
        """Test empty rewards history."""
        mock_koios_client._request.return_value = []
        
        rewards = await staking_service.get_rewards_history(MOCK_STAKE_ADDRESS)
        
        assert len(rewards) == 0
    
    @pytest.mark.asyncio
    async def test_calculate_apy_success(self, staking_service, mock_koios_client):
        """Test APY calculation."""
        # Mock pool info response
        mock_koios_client._request.return_value = [{
            "pool_id_hex": "abc123",
            "pool_id_bech32": MOCK_POOL_ID,
            "meta_json": {"ticker": "POOL1"},
            "active_stake": "50000000000000",
            "live_stake": "49000000000000",
            "live_saturation": 0.60,
            "margin": 0.02,
            "fixed_cost": "340000000",
            "block_count": 1000,
            "live_delegators": 500
        }]
        
        apy = await staking_service.calculate_apy(MOCK_POOL_ID)
        
        assert apy is not None
        assert 0.0 < apy < 0.1  # Should be between 0% and 10%
    
    @pytest.mark.asyncio
    async def test_calculate_apy_high_saturation(self, staking_service, mock_koios_client):
        """Test APY with high saturation penalty."""
        mock_koios_client._request.return_value = [{
            "pool_id_hex": "abc123",
            "pool_id_bech32": MOCK_POOL_ID,
            "meta_json": {"ticker": "POOL1"},
            "active_stake": "50000000000000",
            "live_saturation": 0.95,  # 95% saturated
            "margin": 0.02,
            "fixed_cost": "340000000",
            "block_count": 1000,
            "live_delegators": 500
        }]
        
        apy = await staking_service.calculate_apy(MOCK_POOL_ID)
        
        assert apy is not None
        assert apy < 0.045  # Should be lower than base due to saturation
    
    @pytest.mark.asyncio
    async def test_calculate_apy_pool_not_found(self, staking_service, mock_koios_client):
        """Test APY calculation when pool not found."""
        mock_koios_client._request.return_value = []
        
        apy = await staking_service.calculate_apy(MOCK_POOL_ID)
        
        assert apy is None


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_get_stake_account_creates_client(self):
        """Test get_stake_account creates and closes client."""
        from unittest.mock import patch
        
        with patch('decentralized_did.cardano.staking.KoiosClient') as mock_client_class:
            mock_client = Mock(spec=KoiosClient)
            mock_client.close = AsyncMock()
            mock_client._request = AsyncMock(return_value=[{
                "status": "registered",
                "total_balance": "10000000",
                "rewards_available": "500000"
            }])
            mock_client_class.return_value = mock_client
            
            account = await get_stake_account(MOCK_STAKE_ADDRESS)
            
            assert account.stake_address == MOCK_STAKE_ADDRESS
            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_pools_creates_client(self):
        """Test get_active_pools creates and closes client."""
        from unittest.mock import patch
        
        with patch('decentralized_did.cardano.staking.KoiosClient') as mock_client_class:
            mock_client = Mock(spec=KoiosClient)
            mock_client.close = AsyncMock()
            mock_client._request = AsyncMock(return_value=[{
                "pool_id_hex": "abc123",
                "pool_id_bech32": MOCK_POOL_ID,
                "ticker": "POOL1"
            }])
            mock_client_class.return_value = mock_client
            
            pools = await get_active_pools(limit=10)
            
            assert len(pools) == 1
            mock_client.close.assert_called_once()
