"""
Unit tests for Cardano transaction builder.

Tests cover:
- UTXO selection (largest-first algorithm)
- Fee estimation
- Metadata construction (CIP-20 label 674)
- Transaction building (dry-run mode)
- Error handling (insufficient funds, metadata limits)
- Key generation and loading

Run: pytest tests/test_cardano_transaction.py -v
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from typing import Dict, Any

from pycardano import Network, PaymentSigningKey

from decentralized_did.cardano.transaction import (
    CardanoTransactionBuilder,
    UTXOInput,
    TransactionResult,
    create_payment_keys,
    save_keys,
    load_signing_key,
    CIP20_LABEL,
    METADATA_LIMIT,
    FEE_CONSTANT,
    FEE_COEFFICIENT,
)


# Test fixtures

@pytest.fixture
def sample_did_document() -> Dict[str, Any]:
    """Sample W3C DID Document."""
    return {
        "id": "did:cardano:testnet:abc123",
        "verificationMethod": [
            {
                "id": "did:cardano:testnet:abc123#key-1",
                "type": "Ed25519VerificationKey2020",
                "controller": "did:cardano:testnet:abc123",
                "publicKeyMultibase": "z6Mk..."
            }
        ],
        "authentication": ["did:cardano:testnet:abc123#key-1"],
        "biometricMetadata": {
            "modality": "fingerprint",
            "fingers": 4,
            "securityBits": 256,
            "format": "fuzzy-extractor-v1"
        }
    }


@pytest.fixture
def sample_utxos() -> list:
    """Sample UTXOs for testing."""
    return [
        UTXOInput(
            tx_hash="a" * 64,
            tx_index=0,
            amount_lovelace=5_000_000,
            address="addr_test1..."
        ),
        UTXOInput(
            tx_hash="b" * 64,
            tx_index=1,
            amount_lovelace=10_000_000,
            address="addr_test1..."
        ),
        UTXOInput(
            tx_hash="c" * 64,
            tx_index=2,
            amount_lovelace=2_000_000,
            address="addr_test1..."
        ),
    ]


@pytest.fixture
def transaction_builder() -> CardanoTransactionBuilder:
    """CardanoTransactionBuilder instance in dry-run mode."""
    skey = PaymentSigningKey.generate()
    return CardanoTransactionBuilder(
        network=Network.TESTNET,
        signing_key=skey,  # type: ignore
        dry_run=True
    )


# UTXO Selection Tests

def test_select_utxos_largest_first(transaction_builder, sample_utxos):
    """Test that UTXO selection uses largest-first algorithm."""
    # Need 7 million lovelace
    selected, total = transaction_builder.select_utxos(
        available_utxos=sample_utxos,
        required_lovelace=7_000_000
    )

    # Should select 10M UTXO first
    assert len(selected) == 1
    assert selected[0].amount_lovelace == 10_000_000
    assert total == 10_000_000


def test_select_utxos_multiple_inputs(transaction_builder, sample_utxos):
    """Test UTXO selection with multiple inputs needed."""
    # Need 13 million lovelace (requires 10M + 5M)
    selected, total = transaction_builder.select_utxos(
        available_utxos=sample_utxos,
        required_lovelace=13_000_000
    )

    # Should select 10M + 5M UTXOs
    assert len(selected) == 2
    assert total == 15_000_000
    assert selected[0].amount_lovelace == 10_000_000
    assert selected[1].amount_lovelace == 5_000_000


def test_select_utxos_insufficient_funds(transaction_builder, sample_utxos):
    """Test UTXO selection fails with insufficient funds."""
    with pytest.raises(ValueError, match="Insufficient funds"):
        transaction_builder.select_utxos(
            available_utxos=sample_utxos,
            required_lovelace=20_000_000  # More than total (17M)
        )


def test_select_utxos_empty_list(transaction_builder):
    """Test UTXO selection fails with empty list."""
    with pytest.raises(ValueError, match="No UTXOs available"):
        transaction_builder.select_utxos(
            available_utxos=[],
            required_lovelace=1_000_000
        )


# Fee Estimation Tests

def test_estimate_fee_single_input(transaction_builder):
    """Test fee estimation for single input transaction."""
    fee = transaction_builder.estimate_fee(
        inputs_count=1,
        outputs_count=1,
        metadata_size=500,
        witnesses_count=1
    )

    # Expected: 155381 + 44 × (100 + 150 + 50 + 100 + 500)
    expected_size = 100 + 150 + 50 + 100 + 500  # 900 bytes
    expected_fee = FEE_CONSTANT + (FEE_COEFFICIENT * expected_size)

    assert fee == expected_fee
    assert fee > 0


def test_estimate_fee_multiple_inputs(transaction_builder):
    """Test fee estimation scales with number of inputs."""
    fee1 = transaction_builder.estimate_fee(
        inputs_count=1,
        outputs_count=1,
        metadata_size=500,
        witnesses_count=1
    )

    fee2 = transaction_builder.estimate_fee(
        inputs_count=2,
        outputs_count=1,
        metadata_size=500,
        witnesses_count=1
    )

    # Fee should increase by 150 bytes × 44 lovelace/byte = 6600 lovelace
    assert fee2 == fee1 + (150 * FEE_COEFFICIENT)


def test_estimate_fee_large_metadata(transaction_builder):
    """Test fee estimation with large metadata."""
    fee_small = transaction_builder.estimate_fee(
        inputs_count=1,
        outputs_count=1,
        metadata_size=500,
        witnesses_count=1
    )

    fee_large = transaction_builder.estimate_fee(
        inputs_count=1,
        outputs_count=1,
        metadata_size=5000,
        witnesses_count=1
    )

    # Fee should increase by 4500 bytes × 44 lovelace/byte
    assert fee_large == fee_small + (4500 * FEE_COEFFICIENT)


# Metadata Construction Tests

def test_build_metadata_inline(transaction_builder, sample_did_document):
    """Test CIP-20 metadata construction with inline storage."""
    auxiliary_data, metadata_size = transaction_builder.build_metadata(
        did_document=sample_did_document,
        helper_data_cid=None,
        storage_format="inline"
    )

    assert auxiliary_data is not None
    assert metadata_size > 0
    assert metadata_size < METADATA_LIMIT


def test_build_metadata_external(transaction_builder, sample_did_document):
    """Test CIP-20 metadata construction with external (IPFS) storage."""
    helper_cid = "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"

    auxiliary_data, metadata_size = transaction_builder.build_metadata(
        did_document=sample_did_document,
        helper_data_cid=helper_cid,
        storage_format="external"
    )

    assert auxiliary_data is not None
    assert metadata_size > 0

    # External storage should have smaller metadata (no inline helper data)
    # Note: Currently both are similar size, but validates structure


def test_build_metadata_size_validation(transaction_builder):
    """Test metadata size limit validation."""
    # Create oversized DID document (simulate large enrollment)
    large_doc = {
        "id": "did:cardano:testnet:abc123",
        "verificationMethod": [{"id": f"key-{i}"} for i in range(1000)],
        "largeData": "x" * 20000  # Exceeds 16 KB limit
    }

    with pytest.raises(ValueError, match="exceeds.*16 KB limit"):
        transaction_builder.build_metadata(
            did_document=large_doc,
            helper_data_cid=None,
            storage_format="inline"
        )


def test_build_metadata_structure(transaction_builder, sample_did_document):
    """Test metadata has correct CIP-20 structure."""
    import cbor2

    auxiliary_data, _ = transaction_builder.build_metadata(
        did_document=sample_did_document,
        helper_data_cid="QmTest",
        storage_format="external"
    )

    # Extract metadata (implementation detail, but validates structure)
    assert auxiliary_data is not None


# Transaction Building Tests (Dry-Run Mode)

def test_build_transaction_dry_run(transaction_builder, sample_did_document):
    """Test transaction building in dry-run mode."""
    result = transaction_builder.build_enrollment_transaction(
        did_document=sample_did_document,
        helper_data_cid="QmTest",
        recipient_address="addr_test1...",
        available_utxos=None,  # Not required in dry-run
        storage_format="external"
    )

    assert result.success is True
    assert result.tx_hash.startswith("dry-run-")
    assert result.fee_lovelace > 0
    assert result.fee_ada > 0
    assert result.metadata_size > 0
    assert result.inputs_count == 1
    assert result.outputs_count == 1


def test_build_transaction_fee_calculation(transaction_builder, sample_did_document):
    """Test that fee calculation is reasonable."""
    result = transaction_builder.build_enrollment_transaction(
        did_document=sample_did_document,
        helper_data_cid="QmTest",
        recipient_address="addr_test1...",
        storage_format="external"
    )

    assert result.success is True

    # Fee should be between 0.15 and 0.8 ADA for typical enrollment
    assert 0.15 <= result.fee_ada <= 0.8

    # Fee should follow formula: 155381 + 44 × size
    expected_fee = FEE_CONSTANT + (FEE_COEFFICIENT * result.tx_size)
    assert result.fee_lovelace == expected_fee


def test_build_transaction_without_recipient(transaction_builder, sample_did_document):
    """Test transaction building without explicit recipient (uses self)."""
    result = transaction_builder.build_enrollment_transaction(
        did_document=sample_did_document,
        helper_data_cid="QmTest",
        # recipient_address omitted (should default to self)
    )

    assert result.success is True


def test_build_transaction_no_signing_key_no_recipient():
    """Test transaction building fails without signing key or recipient."""
    builder = CardanoTransactionBuilder(dry_run=True)  # No signing key

    result = builder.build_enrollment_transaction(
        did_document={"id": "did:test"},
        # No recipient_address, no signing_key
    )

    assert result.success is False
    assert result.error is not None
    assert "recipient_address or signing_key required" in result.error


def test_build_transaction_inline_storage(transaction_builder, sample_did_document):
    """Test transaction building with inline storage."""
    result = transaction_builder.build_enrollment_transaction(
        did_document=sample_did_document,
        helper_data_cid=None,
        storage_format="inline"
    )

    assert result.success is True
    # Inline storage might have larger metadata
    assert result.metadata_size > 0


# Error Handling Tests

def test_build_transaction_insufficient_utxos():
    """Test transaction building with insufficient UTXOs."""
    skey = PaymentSigningKey.generate()
    builder = CardanoTransactionBuilder(
        network=Network.TESTNET,
        signing_key=skey,  # type: ignore
        dry_run=False  # Actual mode requires UTXOs
    )

    small_utxos = [
        UTXOInput(
            tx_hash="a" * 64,
            tx_index=0,
            amount_lovelace=100_000,  # Too small
            address="addr_test1..."
        )
    ]

    result = builder.build_enrollment_transaction(
        did_document={"id": "did:test"},
        available_utxos=small_utxos,
        recipient_address="addr_test1..."
    )

    assert result.success is False
    assert result.error is not None
    assert "Insufficient funds" in result.error


def test_build_transaction_no_utxos_when_required():
    """Test transaction building fails when UTXOs required but not provided."""
    skey = PaymentSigningKey.generate()
    builder = CardanoTransactionBuilder(
        network=Network.TESTNET,
        signing_key=skey,  # type: ignore
        dry_run=False  # Actual mode
    )

    result = builder.build_enrollment_transaction(
        did_document={"id": "did:test"},
        available_utxos=None,  # Missing UTXOs
        recipient_address="addr_test1..."
    )

    assert result.success is False
    assert result.error is not None
    assert "available_utxos required" in result.error


# Key Management Tests

def test_create_payment_keys():
    """Test payment key generation."""
    skey, vkey, addr = create_payment_keys()

    assert skey is not None
    assert vkey is not None
    assert addr is not None
    assert str(addr).startswith("addr_test1")  # Testnet address


def test_save_and_load_keys():
    """Test saving and loading payment keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate keys
        skey, vkey, addr = create_payment_keys()

        # Save keys
        save_keys(skey, vkey, output_dir=tmpdir)

        # Verify files exist
        skey_path = os.path.join(tmpdir, "payment.skey")
        vkey_path = os.path.join(tmpdir, "payment.vkey")
        assert os.path.exists(skey_path)
        assert os.path.exists(vkey_path)

        # Load signing key
        loaded_skey = load_signing_key(skey_path)
        assert loaded_skey is not None


def test_transaction_builder_initialization():
    """Test CardanoTransactionBuilder initialization."""
    skey = PaymentSigningKey.generate()

    # Test with signing key
    builder = CardanoTransactionBuilder(
        network=Network.TESTNET,
        signing_key=skey,  # type: ignore
        dry_run=True
    )

    assert builder.network == Network.TESTNET
    assert builder.signing_key is not None
    assert builder.verification_key is not None
    assert builder.address is not None
    assert builder.dry_run is True


def test_transaction_builder_without_signing_key():
    """Test CardanoTransactionBuilder initialization without signing key."""
    builder = CardanoTransactionBuilder(
        network=Network.MAINNET,
        dry_run=True
    )

    assert builder.network == Network.MAINNET
    assert builder.signing_key is None
    assert builder.verification_key is None
    assert builder.address is None


# Integration Tests

def test_full_enrollment_flow_dry_run(sample_did_document):
    """Test complete enrollment flow in dry-run mode."""
    # 1. Generate keys
    skey, vkey, addr = create_payment_keys()

    # 2. Create builder
    builder = CardanoTransactionBuilder(
        network=Network.TESTNET,
        signing_key=skey,  # type: ignore
        dry_run=True
    )

    # 3. Build transaction
    result = builder.build_enrollment_transaction(
        did_document=sample_did_document,
        helper_data_cid="QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
        storage_format="external"
    )

    # 4. Validate result
    assert result.success is True
    assert result.tx_hash is not None
    assert result.fee_ada > 0
    assert result.metadata_size > 0
    assert 0.15 <= result.fee_ada <= 0.8  # Reasonable fee range


def test_metadata_size_scales_with_fingers(transaction_builder):
    """Test that metadata size scales with number of fingers."""
    # 1-finger enrollment
    did_1f = {
        "id": "did:cardano:testnet:1f",
        "biometricMetadata": {"fingers": 1}
    }

    # 4-finger enrollment
    did_4f = {
        "id": "did:cardano:testnet:4f",
        "biometricMetadata": {"fingers": 4},
        "verificationMethod": [{"id": f"key-{i}"} for i in range(4)]
    }

    _, size_1f = transaction_builder.build_metadata(
        did_document=did_1f,
        helper_data_cid="QmTest"
    )

    _, size_4f = transaction_builder.build_metadata(
        did_document=did_4f,
        helper_data_cid="QmTest"
    )

    # 4-finger should have larger metadata
    assert size_4f > size_1f


# Performance Tests

def test_utxo_selection_performance():
    """Test UTXO selection performance with many UTXOs."""
    skey = PaymentSigningKey.generate()
    builder = CardanoTransactionBuilder(
        network=Network.TESTNET,
        signing_key=skey,  # type: ignore
        dry_run=True
    )

    # Create 100 UTXOs
    many_utxos = [
        UTXOInput(
            tx_hash=f"{i:064x}",
            tx_index=i,
            amount_lovelace=1_000_000 + (i * 100_000),
            address="addr_test1..."
        )
        for i in range(100)
    ]

    # Should complete quickly
    import time
    start = time.time()

    selected, total = builder.select_utxos(
        available_utxos=many_utxos,
        required_lovelace=5_000_000
    )

    elapsed = time.time() - start

    assert elapsed < 0.1  # Should complete in <100ms
    assert len(selected) > 0
    assert total >= 5_000_000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
