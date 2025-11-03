"""Tests for token management service."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from decimal import Decimal

from decentralized_did.cardano.tokens import (
    TokenService,
    Balance,
    Asset,
    NFT,
    NFTMetadata,
    Transaction,
    get_balance,
    get_nfts_for_address,
    LOVELACE_PER_ADA,
)
from decentralized_did.cardano.koios_client import KoiosClient, KoiosError


# Mock data
MOCK_ADDRESS = "addr1qx2fxv2umyhttkxyxp8x0dlpdt3k6cwng5pxj3jhsydzer3n0d3vllmyqwsx5wktcd8cc3sq835lu7drv2xwl2wywfgse35a3x"
MOCK_STAKE_ADDRESS = "stake1u80jysjtdzqt8qz8xq9y6dtj0rqh8kqwj5qjkqzqxqz0qg6q6q6"


@pytest.fixture
def mock_koios_client():
    """Create mock Koios client."""
    client = Mock(spec=KoiosClient)
    client._request = AsyncMock()
    return client


@pytest.fixture
def token_service(mock_koios_client):
    """Create token service with mock client."""
    return TokenService(mock_koios_client)


class TestAsset:
    """Test Asset dataclass."""
    
    def test_asset_full_name(self):
        """Test full_name property."""
        asset = Asset(
            policy_id="abc123",
            asset_name="4d5954"
        )
        assert asset.full_name == "abc123.4d5954"
    
    def test_asset_display_quantity_no_decimals(self):
        """Test display_quantity with no decimals."""
        asset = Asset(
            policy_id="abc123",
            asset_name="4d5954",
            quantity="100",
            decimals=0
        )
        assert asset.display_quantity == "100"
    
    def test_asset_display_quantity_with_decimals(self):
        """Test display_quantity with decimals."""
        asset = Asset(
            policy_id="abc123",
            asset_name="4d5954",
            quantity="1000000",
            decimals=6
        )
        assert asset.display_quantity == "1"


class TestBalance:
    """Test Balance dataclass."""
    
    def test_balance_ada_amount(self):
        """Test ADA amount conversion."""
        balance = Balance(
            ada_lovelace="5000000",
            assets=[]
        )
        assert balance.ada_amount == "5"
    
    def test_balance_total_assets(self):
        """Test total_assets property."""
        assets = [
            Asset(policy_id="abc", asset_name="token1"),
            Asset(policy_id="def", asset_name="token2"),
        ]
        balance = Balance(ada_lovelace="1000000", assets=assets)
        assert balance.total_assets == 2


class TestTransaction:
    """Test Transaction dataclass."""
    
    def test_transaction_fee_ada(self):
        """Test fee_ada conversion."""
        tx = Transaction(
            tx_hash="abc123",
            fee="170000"
        )
        assert tx.fee_ada == "0.17"
    
    def test_transaction_fee_ada_none(self):
        """Test fee_ada when fee is None."""
        tx = Transaction(tx_hash="abc123")
        assert tx.fee_ada is None


class TestNFTMetadata:
    """Test NFTMetadata parsing."""
    
    def test_from_onchain_metadata(self):
        """Test parsing CIP-25 metadata."""
        metadata = {
            "name": "My NFT",
            "image": "ipfs://QmHash",
            "description": "A cool NFT",
            "mediaType": "image/png",
            "attributes": {"color": "blue"}
        }
        
        nft_metadata = NFTMetadata.from_onchain_metadata(metadata)
        assert nft_metadata.name == "My NFT"
        assert nft_metadata.image == "ipfs://QmHash"
        assert nft_metadata.description == "A cool NFT"
        assert nft_metadata.media_type == "image/png"
        assert nft_metadata.attributes == {"color": "blue"}


class TestNFT:
    """Test NFT dataclass."""
    
    def test_nft_display_name_from_metadata(self):
        """Test display_name uses metadata name."""
        metadata = NFTMetadata(name="Cool NFT")
        asset = Asset(policy_id="abc", asset_name="4d5954")
        nft = NFT(asset=asset, metadata=metadata)
        assert nft.display_name == "Cool NFT"
    
    def test_nft_display_name_from_asset_ascii(self):
        """Test display_name uses asset_name_ascii."""
        asset = Asset(policy_id="abc", asset_name="4d5954", asset_name_ascii="MYT")
        nft = NFT(asset=asset)
        assert nft.display_name == "MYT"
    
    def test_nft_display_name_truncated(self):
        """Test display_name truncates long names."""
        asset = Asset(policy_id="abc", asset_name="verylongassetnamethatshouldbetruncated")
        nft = NFT(asset=asset)
        assert "..." in nft.display_name


class TestTokenService:
    """Test TokenService methods."""
    
    @pytest.mark.asyncio
    async def test_get_address_balance_success(self, token_service, mock_koios_client):
        """Test successful balance retrieval."""
        # Mock Koios response
        mock_koios_client._request.return_value = [{
            "balance": "10000000",
            "utxo_set": [
                {
                    "asset_list": [
                        {
                            "policy_id": "policy1",
                            "asset_name": "token1",
                            "quantity": "100",
                            "decimals": 0
                        }
                    ]
                }
            ]
        }]
        
        balance = await token_service.get_address_balance(MOCK_ADDRESS)
        
        assert balance.ada_lovelace == "10000000"
        assert balance.ada_amount == "10"
        assert len(balance.assets) == 1
        assert balance.assets[0].policy_id == "policy1"
        assert balance.assets[0].asset_name == "token1"
        assert balance.assets[0].quantity == "100"
    
    @pytest.mark.asyncio
    async def test_get_address_balance_empty(self, token_service, mock_koios_client):
        """Test balance for address with no UTXOs."""
        mock_koios_client._request.return_value = []
        
        balance = await token_service.get_address_balance(MOCK_ADDRESS)
        
        assert balance.ada_lovelace == "0"
        assert len(balance.assets) == 0
    
    @pytest.mark.asyncio
    async def test_get_address_balance_aggregates_assets(self, token_service, mock_koios_client):
        """Test balance aggregates same asset from multiple UTXOs."""
        mock_koios_client._request.return_value = [{
            "balance": "5000000",
            "utxo_set": [
                {
                    "asset_list": [
                        {"policy_id": "policy1", "asset_name": "token1", "quantity": "50", "decimals": 0}
                    ]
                },
                {
                    "asset_list": [
                        {"policy_id": "policy1", "asset_name": "token1", "quantity": "30", "decimals": 0}
                    ]
                }
            ]
        }]
        
        balance = await token_service.get_address_balance(MOCK_ADDRESS)
        
        assert len(balance.assets) == 1
        assert balance.assets[0].quantity == "80"  # 50 + 30
    
    @pytest.mark.asyncio
    async def test_get_address_balance_error(self, token_service, mock_koios_client):
        """Test balance retrieval error handling."""
        mock_koios_client._request.side_effect = Exception("Network error")
        
        with pytest.raises(KoiosError, match="Failed to get address balance"):
            await token_service.get_address_balance(MOCK_ADDRESS)
    
    @pytest.mark.asyncio
    async def test_get_asset_metadata_success(self, token_service, mock_koios_client):
        """Test successful metadata retrieval."""
        mock_koios_client._request.return_value = [{
            "minting_tx_metadata": {
                "721": {
                    "policy1": {
                        "token1": {
                            "name": "My NFT",
                            "image": "ipfs://QmHash",
                            "description": "Cool NFT"
                        }
                    }
                }
            }
        }]
        
        metadata = await token_service.get_asset_metadata("policy1", "token1")
        
        assert metadata is not None
        assert metadata.name == "My NFT"
        assert metadata.image == "ipfs://QmHash"
    
    @pytest.mark.asyncio
    async def test_get_asset_metadata_not_found(self, token_service, mock_koios_client):
        """Test metadata not found."""
        mock_koios_client._request.return_value = []
        
        metadata = await token_service.get_asset_metadata("policy1", "token1")
        
        assert metadata is None
    
    @pytest.mark.asyncio
    async def test_get_nfts_success(self, token_service, mock_koios_client):
        """Test successful NFT retrieval."""
        # Mock balance call
        mock_koios_client._request.side_effect = [
            # Balance response
            [{
                "balance": "5000000",
                "utxo_set": [{
                    "asset_list": [
                        {"policy_id": "policy1", "asset_name": "nft1", "quantity": "1", "decimals": 0}
                    ]
                }]
            }],
            # Metadata response
            [{
                "minting_tx_metadata": {
                    "721": {
                        "policy1": {
                            "nft1": {"name": "NFT #1", "image": "ipfs://Hash1"}
                        }
                    }
                }
            }]
        ]
        
        nfts = await token_service.get_nfts(MOCK_ADDRESS)
        
        assert len(nfts) == 1
        assert nfts[0].asset.policy_id == "policy1"
        assert nfts[0].metadata is not None
        assert nfts[0].metadata.name == "NFT #1"
    
    @pytest.mark.asyncio
    async def test_get_nfts_filters_non_nfts(self, token_service, mock_koios_client):
        """Test NFT retrieval filters out fungible tokens."""
        mock_koios_client._request.return_value = [{
            "balance": "5000000",
            "utxo_set": [{
                "asset_list": [
                    # NFT (quantity=1, decimals=0)
                    {"policy_id": "policy1", "asset_name": "nft1", "quantity": "1", "decimals": 0},
                    # Fungible token (quantity>1)
                    {"policy_id": "policy2", "asset_name": "token2", "quantity": "100", "decimals": 0},
                    # Divisible token (decimals>0)
                    {"policy_id": "policy3", "asset_name": "token3", "quantity": "1", "decimals": 6},
                ]
            }]
        }]
        
        nfts = await token_service.get_nfts(MOCK_ADDRESS)
        
        # Only one NFT should be returned
        assert len(nfts) == 1
        assert nfts[0].asset.policy_id == "policy1"
    
    @pytest.mark.asyncio
    async def test_get_transaction_history_success(self, token_service, mock_koios_client):
        """Test successful transaction history retrieval."""
        mock_koios_client._request.return_value = [
            {
                "tx_hash": "hash1",
                "block_time": 1234567890,
                "block_height": 1000,
                "epoch_no": 100,
                "fee": "170000"
            },
            {
                "tx_hash": "hash2",
                "block_time": 1234567900,
                "block_height": 1001,
                "epoch_no": 100,
                "fee": "180000"
            }
        ]
        
        txs = await token_service.get_transaction_history(MOCK_ADDRESS, limit=10)
        
        assert len(txs) == 2
        assert txs[0].tx_hash == "hash1"
        assert txs[0].fee == "170000"
        assert txs[1].tx_hash == "hash2"


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.mark.asyncio
    async def test_get_balance_creates_client(self):
        """Test get_balance creates and closes client."""
        with patch('decentralized_did.cardano.tokens.KoiosClient') as mock_client_class:
            mock_client = Mock(spec=KoiosClient)
            mock_client.close = AsyncMock()
            mock_client._request = AsyncMock(return_value=[{"balance": "1000000", "utxo_set": []}])
            mock_client_class.return_value = mock_client
            
            balance = await get_balance(MOCK_ADDRESS)
            
            assert balance.ada_lovelace == "1000000"
            mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_nfts_for_address_creates_client(self):
        """Test get_nfts_for_address creates and closes client."""
        with patch('decentralized_did.cardano.tokens.KoiosClient') as mock_client_class:
            mock_client = Mock(spec=KoiosClient)
            mock_client.close = AsyncMock()
            mock_client._request = AsyncMock(return_value=[{"balance": "1000000", "utxo_set": []}])
            mock_client_class.return_value = mock_client
            
            nfts = await get_nfts_for_address(MOCK_ADDRESS)
            
            assert isinstance(nfts, list)
            mock_client.close.assert_called_once()
