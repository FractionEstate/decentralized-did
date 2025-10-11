"""
Unit tests for multi-finger aggregation module.

Tests XOR aggregation, quality-weighted fallback, and finger rotation.
"""

import pytest
import secrets
from typing import List

from src.biometrics.aggregator_v2 import (
    aggregate_xor,
    aggregate_finger_keys,
    rotate_finger,
    revoke_finger,
    xor_bytes,
    FingerKey,
    AggregationResult,
    AggregationError,
    InsufficientFingersError,
    QualityThresholdError,
    MIN_FINGERS_STRICT,
    QUALITY_THRESHOLD_3_OF_4,
    QUALITY_THRESHOLD_2_OF_4,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def random_key() -> bytes:
    """Generate a random 32-byte key."""
    return secrets.token_bytes(32)


@pytest.fixture
def zero_key() -> bytes:
    """32-byte all-zeros key."""
    return b'\x00' * 32


@pytest.fixture
def ones_key() -> bytes:
    """32-byte all-ones key."""
    return b'\xff' * 32


@pytest.fixture
def four_random_keys() -> List[bytes]:
    """Generate 4 random 32-byte keys."""
    return [secrets.token_bytes(32) for _ in range(4)]


@pytest.fixture
def four_finger_keys_high_quality() -> List[FingerKey]:
    """Generate 4 FingerKey objects with high quality scores."""
    return [
        FingerKey("left_thumb", secrets.token_bytes(32), quality=90),
        FingerKey("left_index", secrets.token_bytes(32), quality=85),
        FingerKey("right_thumb", secrets.token_bytes(32), quality=88),
        FingerKey("right_index", secrets.token_bytes(32), quality=82),
    ]


@pytest.fixture
def four_finger_keys_medium_quality() -> List[FingerKey]:
    """Generate 4 FingerKey objects with medium quality scores."""
    return [
        FingerKey("left_thumb", secrets.token_bytes(32), quality=75),
        FingerKey("left_index", secrets.token_bytes(32), quality=70),
        FingerKey("right_thumb", secrets.token_bytes(32), quality=68),
        FingerKey("right_index", secrets.token_bytes(32), quality=72),
    ]


@pytest.fixture
def four_finger_keys_low_quality() -> List[FingerKey]:
    """Generate 4 FingerKey objects with low quality scores."""
    return [
        FingerKey("left_thumb", secrets.token_bytes(32), quality=55),
        FingerKey("left_index", secrets.token_bytes(32), quality=60),
        FingerKey("right_thumb", secrets.token_bytes(32), quality=58),
        FingerKey("right_index", secrets.token_bytes(32), quality=52),
    ]


# ============================================================================
# XOR Aggregation Tests
# ============================================================================

class TestAggregateXOR:
    """Test core XOR aggregation function."""

    def test_aggregate_two_keys(self, four_random_keys):
        """Test XOR of two keys."""
        result = aggregate_xor(four_random_keys[:2])
        assert len(result) == 32
        assert isinstance(result, bytes)

    def test_aggregate_four_keys(self, four_random_keys):
        """Test XOR of four keys."""
        result = aggregate_xor(four_random_keys)
        assert len(result) == 32
        assert isinstance(result, bytes)

    def test_commutative_property(self, four_random_keys):
        """XOR should be commutative (order doesn't matter)."""
        k1, k2, k3, k4 = four_random_keys

        # Different orders should produce same result
        result1 = aggregate_xor([k1, k2, k3, k4])
        result2 = aggregate_xor([k4, k3, k2, k1])
        result3 = aggregate_xor([k2, k4, k1, k3])

        assert result1 == result2 == result3

    def test_associative_property(self, four_random_keys):
        """XOR should be associative."""
        k1, k2, k3, k4 = four_random_keys

        # ((K1 ⊕ K2) ⊕ K3) ⊕ K4 = K1 ⊕ (K2 ⊕ (K3 ⊕ K4))
        result1 = aggregate_xor([aggregate_xor([k1, k2]), k3, k4])
        result2 = aggregate_xor([k1, k2, k3, k4])

        assert result1 == result2

    def test_identity_with_zero(self, random_key, zero_key):
        """K ⊕ 0 = K (zero is identity element)."""
        result = aggregate_xor([random_key, zero_key])
        assert result == random_key

    def test_self_inverse(self, random_key):
        """K ⊕ K = 0 (self-inverse property)."""
        result = aggregate_xor([random_key, random_key])
        assert result == b'\x00' * 32

    def test_empty_list_raises_error(self):
        """Empty list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot aggregate empty list"):
            aggregate_xor([])

    def test_invalid_key_length_raises_error(self):
        """Keys with wrong length should raise ValueError."""
        invalid_key = b'\x00' * 16  # Only 16 bytes
        valid_key = secrets.token_bytes(32)

        with pytest.raises(ValueError, match="invalid length"):
            aggregate_xor([valid_key, invalid_key])

    def test_single_key_returns_identity(self, random_key):
        """XOR of single key should return the key itself."""
        result = aggregate_xor([random_key])
        assert result == random_key

    def test_triple_xor_cancellation(self, random_key):
        """K ⊕ K ⊕ K = K (odd count)."""
        result = aggregate_xor([random_key, random_key, random_key])
        assert result == random_key

    def test_all_zeros_keys(self, zero_key):
        """XOR of all zeros should be zero."""
        result = aggregate_xor([zero_key, zero_key, zero_key, zero_key])
        assert result == zero_key

    def test_all_ones_keys(self, ones_key):
        """XOR of even number of all-ones keys should be zero."""
        result = aggregate_xor([ones_key, ones_key, ones_key, ones_key])
        assert result == b'\x00' * 32

    def test_deterministic(self, four_random_keys):
        """Same inputs should always produce same output."""
        result1 = aggregate_xor(four_random_keys)
        result2 = aggregate_xor(four_random_keys)
        assert result1 == result2


# ============================================================================
# Finger Key Aggregation Tests
# ============================================================================

class TestAggregateFingerKeys:
    """Test high-level finger key aggregation with fallback."""

    def test_aggregate_four_fingers_ideal(self, four_finger_keys_high_quality):
        """Test aggregation with all 4 fingers (ideal case)."""
        result = aggregate_finger_keys(
            four_finger_keys_high_quality, enrolled_count=4)

        assert isinstance(result, AggregationResult)
        assert len(result.master_key) == 32
        assert result.fingers_used == 4
        assert len(result.finger_ids) == 4
        assert result.fallback_mode is False
        assert result.average_quality is not None
        assert result.average_quality >= 80  # All keys are high quality

    def test_aggregate_two_fingers(self, four_finger_keys_high_quality):
        """Test aggregation with 2 fingers."""
        result = aggregate_finger_keys(
            four_finger_keys_high_quality[:2],
            enrolled_count=2
        )

        assert result.fingers_used == 2
        assert result.fallback_mode is False

    def test_aggregate_three_of_four_high_quality(self, four_finger_keys_high_quality):
        """Test 3/4 fallback with high quality (should succeed)."""
        result = aggregate_finger_keys(
            four_finger_keys_high_quality[:3],
            enrolled_count=4
        )

        assert result.fingers_used == 3
        assert result.fallback_mode is True
        assert result.average_quality is not None
        assert result.average_quality >= QUALITY_THRESHOLD_3_OF_4

    def test_aggregate_three_of_four_medium_quality(self, four_finger_keys_medium_quality):
        """Test 3/4 fallback with medium quality (borderline)."""
        # Average quality of first 3: (75 + 70 + 68) / 3 = 71 ≥ 70 ✅
        result = aggregate_finger_keys(
            four_finger_keys_medium_quality[:3],
            enrolled_count=4
        )

        assert result.fingers_used == 3
        assert result.fallback_mode is True

    def test_aggregate_three_of_four_low_quality_fails(self, four_finger_keys_low_quality):
        """Test 3/4 fallback with low quality (should fail)."""
        # Average quality of first 3: (55 + 60 + 58) / 3 = 57.7 < 70 ❌
        with pytest.raises(QualityThresholdError, match="does not meet threshold"):
            aggregate_finger_keys(
                four_finger_keys_low_quality[:3],
                enrolled_count=4
            )

    def test_aggregate_two_of_four_very_high_quality(self):
        """Test 2/4 fallback with very high quality (should succeed)."""
        fingers = [
            FingerKey("left_thumb", secrets.token_bytes(32), quality=92),
            FingerKey("left_index", secrets.token_bytes(32), quality=90),
        ]

        # Average: (92 + 90) / 2 = 91 ≥ 85 ✅
        result = aggregate_finger_keys(fingers, enrolled_count=4)

        assert result.fingers_used == 2
        assert result.fallback_mode is True
        assert result.average_quality is not None
        assert result.average_quality >= QUALITY_THRESHOLD_2_OF_4

    def test_aggregate_two_of_four_medium_quality_fails(self, four_finger_keys_medium_quality):
        """Test 2/4 fallback with medium quality (should fail)."""
        # Average: (75 + 70) / 2 = 72.5 < 85 ❌
        with pytest.raises(QualityThresholdError, match="does not meet threshold"):
            aggregate_finger_keys(
                four_finger_keys_medium_quality[:2],
                enrolled_count=4
            )

    def test_aggregate_one_finger_fails(self, four_finger_keys_high_quality):
        """Test 1 finger (should always fail)."""
        with pytest.raises(InsufficientFingersError, match="minimum: 2"):
            aggregate_finger_keys(
                four_finger_keys_high_quality[:1],
                enrolled_count=4
            )

    def test_aggregate_zero_fingers_fails(self):
        """Test 0 fingers (should fail)."""
        with pytest.raises(InsufficientFingersError, match="No finger keys provided"):
            aggregate_finger_keys([], enrolled_count=4)

    def test_strict_mode_rejects_fallback(self, four_finger_keys_high_quality):
        """Test strict mode (require_all=True) rejects 3/4 fingers."""
        with pytest.raises(InsufficientFingersError, match="Strict mode"):
            aggregate_finger_keys(
                four_finger_keys_high_quality[:3],
                enrolled_count=4,
                require_all=True
            )

    def test_strict_mode_accepts_all_fingers(self, four_finger_keys_high_quality):
        """Test strict mode accepts 4/4 fingers."""
        result = aggregate_finger_keys(
            four_finger_keys_high_quality,
            enrolled_count=4,
            require_all=True
        )

        assert result.fingers_used == 4
        assert result.fallback_mode is False

    def test_fallback_without_quality_scores_fails(self):
        """Test fallback without quality scores (should fail)."""
        fingers = [
            FingerKey("left_thumb", secrets.token_bytes(32), quality=None),
            FingerKey("left_index", secrets.token_bytes(32), quality=None),
            FingerKey("right_thumb", secrets.token_bytes(32), quality=None),
        ]

        with pytest.raises(QualityThresholdError, match="quality scores required"):
            aggregate_finger_keys(fingers, enrolled_count=4)

    def test_finger_ids_preserved(self, four_finger_keys_high_quality):
        """Test that finger IDs are preserved in result."""
        result = aggregate_finger_keys(four_finger_keys_high_quality)

        expected_ids = ["left_thumb", "left_index",
                        "right_thumb", "right_index"]
        assert result.finger_ids == expected_ids

    def test_invalid_enrolled_count_fails(self, four_finger_keys_high_quality):
        """Test invalid enrolled_count raises ValueError."""
        with pytest.raises(ValueError, match="Invalid enrolled_count"):
            aggregate_finger_keys(
                four_finger_keys_high_quality, enrolled_count=1)

        with pytest.raises(ValueError, match="Invalid enrolled_count"):
            aggregate_finger_keys(
                four_finger_keys_high_quality, enrolled_count=11)


# ============================================================================
# Finger Rotation Tests
# ============================================================================

class TestRotateFinger:
    """Test finger rotation functionality."""

    def test_rotate_single_finger(self, four_random_keys):
        """Test rotating a single finger produces correct new master key."""
        k1, k2, k3, k4_old = four_random_keys
        k4_new = secrets.token_bytes(32)

        # Compute old master key
        master_old = aggregate_xor([k1, k2, k3, k4_old])

        # Rotate finger 4
        master_new = rotate_finger(master_old, k4_old, k4_new)

        # Verify new master key matches direct aggregation
        expected = aggregate_xor([k1, k2, k3, k4_new])
        assert master_new == expected

    def test_rotate_all_fingers_sequentially(self, four_random_keys):
        """Test rotating each finger one at a time."""
        k1, k2, k3, k4 = four_random_keys
        master = aggregate_xor([k1, k2, k3, k4])

        # Rotate finger 1
        k1_new = secrets.token_bytes(32)
        master = rotate_finger(master, k1, k1_new)
        assert master == aggregate_xor([k1_new, k2, k3, k4])

        # Rotate finger 2
        k2_new = secrets.token_bytes(32)
        master = rotate_finger(master, k2, k2_new)
        assert master == aggregate_xor([k1_new, k2_new, k3, k4])

        # Rotate finger 3
        k3_new = secrets.token_bytes(32)
        master = rotate_finger(master, k3, k3_new)
        assert master == aggregate_xor([k1_new, k2_new, k3_new, k4])

        # Rotate finger 4
        k4_new = secrets.token_bytes(32)
        master = rotate_finger(master, k4, k4_new)
        assert master == aggregate_xor([k1_new, k2_new, k3_new, k4_new])

    def test_rotate_with_invalid_key_lengths(self):
        """Test rotation with invalid key lengths raises ValueError."""
        master = secrets.token_bytes(32)
        old_key = secrets.token_bytes(32)
        new_key = secrets.token_bytes(32)

        # Invalid master key
        with pytest.raises(ValueError, match="old_master_key must be 32 bytes"):
            rotate_finger(b'\x00' * 16, old_key, new_key)

        # Invalid old key
        with pytest.raises(ValueError, match="old_finger_key must be 32 bytes"):
            rotate_finger(master, b'\x00' * 16, new_key)

        # Invalid new key
        with pytest.raises(ValueError, match="new_finger_key must be 32 bytes"):
            rotate_finger(master, old_key, b'\x00' * 16)

    def test_rotate_same_key_unchanged(self, four_random_keys):
        """Rotating a finger with same key should not change master."""
        k1, k2, k3, k4 = four_random_keys
        master_old = aggregate_xor([k1, k2, k3, k4])

        # "Rotate" with same key
        master_new = rotate_finger(master_old, k4, k4)

        assert master_new == master_old


# ============================================================================
# Finger Revocation Tests
# ============================================================================

class TestRevokeFinger:
    """Test finger revocation functionality."""

    def test_revoke_one_finger_from_four(self, four_random_keys):
        """Test revoking one finger from 4-finger enrollment."""
        k1, k2, k3, k4 = four_random_keys
        master_old = aggregate_xor([k1, k2, k3, k4])

        # Revoke finger 3
        master_new = revoke_finger(master_old, k3, [k1, k2, k4])

        # New master should be XOR of remaining fingers
        expected = aggregate_xor([k1, k2, k4])
        assert master_new == expected

    def test_revoke_last_two_fingers_fails(self, four_random_keys):
        """Test that revoking down to 1 finger fails."""
        k1, k2, k3, k4 = four_random_keys
        master = aggregate_xor([k1, k2, k3, k4])

        # Revoke down to 1 finger (should fail)
        with pytest.raises(InsufficientFingersError, match="only 1 fingers would remain"):
            revoke_finger(master, k4, [k1])

    def test_revoke_to_minimum_two_fingers(self, four_random_keys):
        """Test revoking down to minimum 2 fingers (should succeed)."""
        k1, k2, k3, k4 = four_random_keys
        master = aggregate_xor([k1, k2, k3, k4])

        # Revoke down to 2 fingers (minimum allowed)
        master_new = revoke_finger(master, k4, [k1, k2])
        expected = aggregate_xor([k1, k2])
        assert master_new == expected

    def test_revoke_with_invalid_key_length(self, four_random_keys):
        """Test revocation with invalid key length raises ValueError."""
        k1, k2, k3, k4 = four_random_keys
        master = aggregate_xor([k1, k2, k3, k4])

        with pytest.raises(ValueError, match="old_master_key must be 32 bytes"):
            revoke_finger(b'\x00' * 16, k4, [k1, k2, k3])

        with pytest.raises(ValueError, match="revoked_finger_key must be 32 bytes"):
            revoke_finger(master, b'\x00' * 16, [k1, k2, k3])


# ============================================================================
# Utility Function Tests
# ============================================================================

class TestXORBytes:
    """Test XOR bytes utility function."""

    def test_xor_same_length(self):
        """Test XOR of same-length byte arrays."""
        a = b'\x01\x02\x03\x04'
        b = b'\x05\x06\x07\x08'
        result = xor_bytes(a, b)

        expected = bytes([0x01 ^ 0x05, 0x02 ^ 0x06, 0x03 ^ 0x07, 0x04 ^ 0x08])
        assert result == expected

    def test_xor_different_length_fails(self):
        """Test XOR of different-length arrays raises ValueError."""
        a = b'\x01\x02'
        b = b'\x03\x04\x05'

        with pytest.raises(ValueError, match="must be same length"):
            xor_bytes(a, b)

    def test_xor_self_is_zero(self):
        """Test A ⊕ A = 0."""
        a = secrets.token_bytes(32)
        result = xor_bytes(a, a)
        assert result == b'\x00' * 32

    def test_xor_commutative(self):
        """Test A ⊕ B = B ⊕ A."""
        a = secrets.token_bytes(32)
        b = secrets.token_bytes(32)

        assert xor_bytes(a, b) == xor_bytes(b, a)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_maximum_fingers_ten(self):
        """Test aggregation with 10 fingers (maximum practical)."""
        fingers = [
            FingerKey(f"finger_{i}", secrets.token_bytes(32), quality=80)
            for i in range(10)
        ]

        result = aggregate_finger_keys(fingers, enrolled_count=10)
        assert result.fingers_used == 10
        assert result.fallback_mode is False

    def test_quality_score_boundary_70(self):
        """Test quality score exactly at 3/4 threshold."""
        fingers = [
            FingerKey("f1", secrets.token_bytes(32), quality=70),
            FingerKey("f2", secrets.token_bytes(32), quality=70),
            FingerKey("f3", secrets.token_bytes(32), quality=70),
        ]

        # Average = 70 (exactly at threshold)
        result = aggregate_finger_keys(fingers, enrolled_count=4)
        assert result.fingers_used == 3
        assert result.average_quality == 70

    def test_quality_score_boundary_85(self):
        """Test quality score exactly at 2/4 threshold."""
        fingers = [
            FingerKey("f1", secrets.token_bytes(32), quality=85),
            FingerKey("f2", secrets.token_bytes(32), quality=85),
        ]

        # Average = 85 (exactly at threshold)
        result = aggregate_finger_keys(fingers, enrolled_count=4)
        assert result.fingers_used == 2
        assert result.average_quality == 85

    def test_mixed_quality_scores(self):
        """Test aggregation with mixed quality scores (some None)."""
        fingers = [
            FingerKey("f1", secrets.token_bytes(32), quality=90),
            FingerKey("f2", secrets.token_bytes(
                32), quality=None),  # No quality
            FingerKey("f3", secrets.token_bytes(32), quality=85),
            FingerKey("f4", secrets.token_bytes(
                32), quality=None),  # No quality
        ]

        # All 4 fingers present, should succeed regardless of quality
        result = aggregate_finger_keys(fingers, enrolled_count=4)
        assert result.fingers_used == 4

        # Average quality should only count non-None values
        # (90 + 85) / 2 = 87.5
        assert result.average_quality == 87.5
