"""
Integration tests for DID generation with aggregation pipeline.

Tests DID generation with aggregator_v2 integration:
- Multi-finger key aggregation → DID generation
- Multi-finger scenarios (2, 4, 10 fingers)
- Fallback modes (3/4, 2/4)
- Inline vs external helper storage
- Cardano metadata format validation

NOTE: These tests use mock helper data entries. Full biometric pipeline
tests (quantization → fuzzy extraction → aggregation → DID) are in
test_fingerprint_pipeline.py

Phase 2, Task 4 - DID Generation and Metadata Encoding

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

import json
import os
import pytest
from src.biometrics.aggregator_v2 import aggregate_finger_keys, FingerKey
from src.did.generator_v2 import (
    HelperDataEntry, build_did_from_master_key, build_wallet_bundle,
    HELPER_STORAGE_INLINE, HELPER_STORAGE_EXTERNAL,
    MAX_METADATA_SIZE_BYTES, _encode_bytes,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_wallet_address():
    """Sample Cardano wallet address."""
    return "addr1qxy2l9k5z9p3v7q8hj0w5r3a4b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6"


def create_mock_helper_entry(finger_id: str) -> HelperDataEntry:
    """Create mock helper data entry for testing."""
    return HelperDataEntry(
        finger_id=finger_id,
        version=1,
        salt=_encode_bytes(os.urandom(16)),
        personalization=_encode_bytes(os.urandom(16)),
        bch_syndrome=_encode_bytes(os.urandom(64)),
        hmac=_encode_bytes(os.urandom(32)),
    )


# ============================================================================
# END-TO-END ENROLLMENT & VERIFICATION
# ============================================================================

class TestEndToEndPipeline:
    """Test complete aggregation → DID generation pipeline."""

    def test_enrollment_and_aggregation_4_fingers(self, sample_wallet_address):
        """Test 4-finger aggregation and DID generation."""
        # ===== ENROLLMENT =====
        enrolled_keys = [
            FingerKey(finger_id="left_thumb", key=os.urandom(32)),
            FingerKey(finger_id="left_index", key=os.urandom(32)),
            FingerKey(finger_id="right_thumb", key=os.urandom(32)),
            FingerKey(finger_id="right_index", key=os.urandom(32)),
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        # Aggregate keys
        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)
        master_key = result.master_key

        # Build DID
        did = build_did_from_master_key(sample_wallet_address, master_key)

        # Build wallet bundle
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
            aggregation_mode="4/4",
        )

        # Validate
        assert str(did) == str(bundle.did)
        assert bundle.metadata.fingerprint_count == 4
        assert bundle.metadata.aggregation_mode == "4/4"
        assert bundle.metadata.helper_data is not None
        assert len(bundle.metadata.helper_data) == 4

    def test_enrollment_2_fingers(self, sample_wallet_address):
        """Test 2-finger enrollment."""
        enrolled_keys = [
            FingerKey(finger_id="left_thumb", key=os.urandom(32)),
            FingerKey(finger_id="left_index", key=os.urandom(32)),
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=2)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=2,
            aggregation_mode="2/2",
        )

        assert bundle.metadata.fingerprint_count == 2
        assert bundle.metadata.helper_data is not None
        assert len(bundle.metadata.helper_data) == 2

    def test_enrollment_10_fingers(self, sample_wallet_address):
        """Test 10-finger enrollment (all fingers)."""
        finger_ids = [
            "left_thumb", "left_index", "left_middle", "left_ring", "left_pinky",
            "right_thumb", "right_index", "right_middle", "right_ring", "right_pinky",
        ]

        enrolled_keys = [
            FingerKey(finger_id=fid, key=os.urandom(32))
            for fid in finger_ids
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=10)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=10,
            aggregation_mode="10/10",
        )

        assert bundle.metadata.fingerprint_count == 10
        assert bundle.metadata.helper_data is not None
        assert len(bundle.metadata.helper_data) == 10


# ============================================================================
# FALLBACK MODE TESTS
# ============================================================================

class TestFallbackModes:
    """Test fallback authentication scenarios."""

    def test_fallback_3_of_4(self, sample_wallet_address):
        """Test 3/4 fallback mode."""
        # Enroll 4 fingers
        enrolled_keys = [
            FingerKey(finger_id="left_thumb", key=os.urandom(32), quality=90),
            FingerKey(finger_id="left_index", key=os.urandom(32), quality=85),
            FingerKey(finger_id="right_thumb", key=os.urandom(32), quality=80),
            FingerKey(finger_id="right_index", key=os.urandom(32), quality=75),
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
            aggregation_mode="4/4",
        )

        # Verify with only 3 fingers (simulate missing finger)
        # Use only first 3 fingers with quality ≥70
        verify_keys = enrolled_keys[:3]

        verify_result = aggregate_finger_keys(verify_keys, enrolled_count=4)

        # Master keys will differ (fallback scenario)
        # In production, this would be handled by wallet policy
        assert verify_result.master_key != result.master_key
        assert verify_result.fingers_used == 3
        assert len(verify_result.finger_ids) == 3
        assert verify_result.fallback_mode is True

    def test_fallback_2_of_4(self, sample_wallet_address):
        """Test 2/4 fallback mode."""
        # Enroll 4 fingers with high quality scores (required for 2/4 fallback)
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32), quality=90)
            for i in range(4)
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        # Verify with only 2 fingers (require quality ≥85 for 2/4)
        verify_keys = enrolled_keys[:2]
        verify_result = aggregate_finger_keys(verify_keys, enrolled_count=4)

        assert verify_result.fingers_used == 2
        assert len(verify_result.finger_ids) == 2
        assert verify_result.fallback_mode is True


# ============================================================================
# HELPER STORAGE MODE TESTS
# ============================================================================


class TestHelperStorageModes:
    """Test inline vs external helper storage."""

    def test_inline_storage_4_fingers(self, sample_wallet_address):
        """Test inline helper storage with 4 fingers."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        # Validate inline storage
        assert bundle.metadata.helper_storage == HELPER_STORAGE_INLINE
        assert bundle.metadata.helper_data is not None
        assert len(bundle.metadata.helper_data) == 4
        assert bundle.metadata.helper_uri is None
        assert bundle.helper_data_json is None

    def test_external_storage_4_fingers(self, sample_wallet_address):
        """Test external helper storage with 4 fingers."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_EXTERNAL,
            helper_uri="ipfs://QmXyz123",
            fingerprint_count=4,
        )

        # Validate external storage
        assert bundle.metadata.helper_storage == HELPER_STORAGE_EXTERNAL
        assert bundle.metadata.helper_data is None
        assert bundle.metadata.helper_uri == "ipfs://QmXyz123"
        assert bundle.helper_data_json is not None
        assert "helperData" in bundle.helper_data_json
        assert len(bundle.helper_data_json["helperData"]) == 4

    def test_external_storage_smaller_than_inline(self, sample_wallet_address):
        """Test that external storage produces smaller metadata."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        # Build inline bundle
        inline_bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        # Build external bundle
        external_bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_EXTERNAL,
            helper_uri="ipfs://QmXyz",
            fingerprint_count=4,
        )

        # External should be smaller
        inline_size = inline_bundle.metadata.size_bytes()
        external_size = external_bundle.metadata.size_bytes()

        assert external_size < inline_size
        assert external_size < MAX_METADATA_SIZE_BYTES


# ============================================================================
# CARDANO METADATA FORMAT TESTS
# ============================================================================

class TestCardanoMetadataFormat:
    """Test Cardano transaction metadata format compatibility."""

    def test_wallet_format_structure(self, sample_wallet_address):
        """Test wallet format has correct structure."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        wallet_format = bundle.to_wallet_format()

        # Validate structure
        assert "1990" in wallet_format
        payload = wallet_format["1990"]

        assert "version" in payload
        assert "walletAddress" in payload
        assert "biometric" in payload

        biometric = payload["biometric"]
        assert "idHash" in biometric
        assert "helperStorage" in biometric
        assert "helperData" in biometric

    def test_cip30_format_structure(self, sample_wallet_address):
        """Test CIP-30 format has correct structure."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        cip30_format = bundle.to_cip30_format()

        # Validate structure
        assert "did" in cip30_format
        assert cip30_format["did"].startswith("did:cardano:")

        assert "metadata" in cip30_format
        assert isinstance(cip30_format["metadata"], list)
        assert len(cip30_format["metadata"]) == 1

        label, payload = cip30_format["metadata"][0]
        assert label == 1990
        assert "version" in payload

    def test_json_serialization(self, sample_wallet_address):
        """Test JSON serialization for both formats."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        # Test wallet format JSON
        wallet_json = bundle.to_json(format="wallet")
        wallet_data = json.loads(wallet_json)
        assert "1990" in wallet_data

        # Test CIP-30 format JSON
        cip30_json = bundle.to_json(format="cip30")
        cip30_data = json.loads(cip30_json)
        assert "did" in cip30_data
        assert "metadata" in cip30_data

    def test_metadata_within_cardano_limit(self, sample_wallet_address):
        """Test metadata stays within Cardano's 16KB limit."""
        enrolled_keys = [
            FingerKey(finger_id=f"finger_{i}", key=os.urandom(32))
            for i in range(4)
        ]

        helper_entries = [
            create_mock_helper_entry(fk.finger_id)
            for fk in enrolled_keys
        ]

        result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=result.master_key,
            helper_data_entries=helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        size = bundle.metadata.size_bytes()
        assert size < MAX_METADATA_SIZE_BYTES
