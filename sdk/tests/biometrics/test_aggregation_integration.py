"""
Integration tests for multi-finger aggregation with fuzzy extractor.

Tests end-to-end workflows combining biometric fuzzy extraction and key aggregation.
Uses synthetic 64-bit biometric arrays (BCH message length).
"""

import pytest
import secrets
from typing import List, Tuple

import numpy as np

from src.biometrics.fuzzy_extractor_v2 import (
    fuzzy_extract_gen,
    fuzzy_extract_rep,
)
from src.biometrics.aggregator_v2 import (
    aggregate_finger_keys,
    rotate_finger,
    revoke_finger,
    FingerKey,
    InsufficientFingersError,
    QualityThresholdError,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def four_finger_biometric_arrays() -> List[np.ndarray]:
    """
    Generate 4 synthetic biometric bit arrays (64 bits each for BCH).

    Simulates 4 different fingerprints converted to binary.
    """
    np.random.seed(42)  # Deterministic for testing
    return [
        np.random.randint(0, 2, size=64, dtype=np.uint8) for _ in range(4)
    ]


@pytest.fixture
def four_finger_noisy_arrays(four_finger_biometric_arrays) -> List[np.ndarray]:
    """
    Generate noisy versions of the 4 biometric arrays (simulating capture errors).

    Adds 5 bit flips to each array (within BCH t=10 correction capacity).
    """
    np.random.seed(43)
    noisy = []
    for template in four_finger_biometric_arrays:
        # Flip 5 bits randomly (within BCH correction capacity)
        corrupted = template.copy()
        num_flips = 5
        flip_indices = np.random.choice(
            len(template), num_flips, replace=False)
        corrupted[flip_indices] = 1 - corrupted[flip_indices]
        noisy.append(corrupted)
    return noisy


def generate_fuzzy_keys(
    biometric_arrays: List[np.ndarray],
    user_prefix: str = "user"
) -> List[Tuple[bytes, dict, int]]:
    """
    Generate fuzzy keys from biometric arrays.

    Returns:
        List of (key, helper_data, quality) tuples
    """
    keys = []
    for i, bio_array in enumerate(biometric_arrays):
        # Simulate varying quality scores
        quality = 80 + (i * 2)  # 80, 82, 84, 86

        # Generate fuzzy key and helper data
        user_id = f"{user_prefix}_{i}"
        key, helper_data = fuzzy_extract_gen(bio_array, user_id)

        keys.append((key, helper_data, quality))

    return keys


# ============================================================================
# End-to-End Enrollment and Authentication Tests
# ============================================================================

class TestEndToEndWorkflow:
    """Test complete enrollment and authentication workflows."""

    def test_four_finger_enrollment_and_authentication(
        self,
        four_finger_biometric_arrays,
        four_finger_noisy_arrays,
    ):
        """Test enrolling 4 fingers and authenticating with noisy captures."""
        # Phase 1: Enrollment
        enrolled_keys = []
        helper_data_list = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, quality) in enumerate(key_data):
            enrolled_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=quality
            ))
            helper_data_list.append(helper_data)

        # Aggregate enrolled keys
        enrollment_result = aggregate_finger_keys(
            enrolled_keys, enrolled_count=4)

        assert enrollment_result.fingers_used == 4
        assert enrollment_result.fallback_mode is False
        assert len(enrollment_result.master_key) == 32
        master_key_enrolled = enrollment_result.master_key

        # Phase 2: Authentication (noisy biometric data)
        auth_keys = []

        for i, noisy_array in enumerate(four_finger_noisy_arrays):
            helper_data = helper_data_list[i]

            # Reproduce fuzzy key
            key = fuzzy_extract_rep(noisy_array, helper_data)

            auth_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=75 + (i * 2)  # 75, 77, 79, 81
            ))

        # Aggregate authentication keys
        auth_result = aggregate_finger_keys(auth_keys, enrolled_count=4)

        assert auth_result.fingers_used == 4
        assert auth_result.fallback_mode is False

        # Master keys should match (fuzzy extractor corrected bit flips)
        assert auth_result.master_key == master_key_enrolled

    def test_three_of_four_fallback_scenario(
        self,
        four_finger_biometric_arrays,
        four_finger_noisy_arrays,
    ):
        """Test 3/4 finger fallback during authentication."""
        # Enrollment: 4 fingers
        enrolled_keys = []
        helper_data_list = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=85  # High quality
            ))
            helper_data_list.append(helper_data)

        # Authentication: Only 3 fingers available
        auth_keys = []

        for i in range(3):  # Only first 3 fingers
            noisy_array = four_finger_noisy_arrays[i]
            helper_data = helper_data_list[i]

            key = fuzzy_extract_rep(noisy_array, helper_data)

            auth_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=85  # Still high quality
            ))

        # Aggregate with fallback
        auth_result = aggregate_finger_keys(auth_keys, enrolled_count=4)

        assert auth_result.fingers_used == 3
        assert auth_result.fallback_mode is True

        # Validate with same 3 enrolled keys
        enrolled_subset = aggregate_finger_keys(
            enrolled_keys[:3], enrolled_count=3)
        assert auth_result.master_key == enrolled_subset.master_key

    def test_two_of_four_fallback_high_quality(
        self,
        four_finger_biometric_arrays,
        four_finger_noisy_arrays,
    ):
        """Test 2/4 finger fallback with very high quality."""
        # Enrollment: 4 fingers
        enrolled_keys = []
        helper_data_list = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=95  # Very high quality
            ))
            helper_data_list.append(helper_data)

        # Authentication: Only 2 fingers (very high quality required)
        auth_keys = []

        for i in range(2):
            noisy_array = four_finger_noisy_arrays[i]
            helper_data = helper_data_list[i]

            key = fuzzy_extract_rep(noisy_array, helper_data)

            auth_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=92  # Very high quality
            ))

        # Aggregate with fallback
        auth_result = aggregate_finger_keys(auth_keys, enrolled_count=4)

        assert auth_result.fingers_used == 2
        assert auth_result.fallback_mode is True
        assert auth_result.average_quality is not None
        assert auth_result.average_quality >= 85

    def test_two_of_four_fallback_low_quality_fails(
        self,
        four_finger_biometric_arrays,
        four_finger_noisy_arrays,
    ):
        """Test 2/4 finger fallback fails with low quality."""
        # Enrollment: 4 fingers
        enrolled_keys = []
        helper_data_list = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=70
            ))
            helper_data_list.append(helper_data)

        # Authentication: Only 2 fingers with low quality
        auth_keys = []

        for i in range(2):
            noisy_array = four_finger_noisy_arrays[i]
            helper_data = helper_data_list[i]

            key = fuzzy_extract_rep(noisy_array, helper_data)

            auth_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=70  # Too low for 2/4 fallback
            ))

        # Should fail quality threshold
        with pytest.raises(QualityThresholdError, match="does not meet threshold"):
            aggregate_finger_keys(auth_keys, enrolled_count=4)


# ============================================================================
# Finger Rotation Tests
# ============================================================================

class TestFingerRotation:
    """Test finger rotation with fuzzy extractor integration."""

    def test_rotate_single_finger_end_to_end(self, four_finger_biometric_arrays):
        """Test rotating a single finger in the enrollment."""
        # Initial enrollment: 4 fingers
        enrolled_keys = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(
                finger_id=f"finger_{i}",
                key=key,
                quality=80
            ))

        # Get initial master key
        initial_result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)
        initial_master = initial_result.master_key

        # Rotate finger 2 (index 1)
        # Generate new biometric data for finger 2
        np.random.seed(99)
        new_bio_array = np.random.randint(0, 2, size=64, dtype=np.uint8)

        new_key, _ = fuzzy_extract_gen(new_bio_array, "user_1_new")

        # Compute rotated master key
        old_finger_key = enrolled_keys[1].key
        rotated_master = rotate_finger(initial_master, old_finger_key, new_key)

        # Update enrollment
        enrolled_keys[1] = FingerKey("finger_1", new_key, quality=80)

        # Verify rotated master matches new aggregation
        new_result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)
        assert rotated_master == new_result.master_key

    def test_rotate_all_fingers_sequentially(self, four_finger_biometric_arrays):
        """Test rotating all 4 fingers one at a time."""
        # Initial enrollment
        enrolled_keys = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(f"finger_{i}", key, quality=80))

        master = aggregate_finger_keys(
            enrolled_keys, enrolled_count=4).master_key

        # Rotate each finger
        for i in range(4):
            # Generate new biometric data
            np.random.seed(100 + i)
            new_bio_array = np.random.randint(0, 2, size=64, dtype=np.uint8)

            new_key, _ = fuzzy_extract_gen(new_bio_array, f"user_{i}_rotated")

            # Rotate
            old_key = enrolled_keys[i].key
            master = rotate_finger(master, old_key, new_key)

            # Update enrollment
            enrolled_keys[i] = FingerKey(f"finger_{i}", new_key, quality=80)

        # Verify final master matches direct aggregation
        final_result = aggregate_finger_keys(enrolled_keys, enrolled_count=4)
        assert master == final_result.master_key


# ============================================================================
# Finger Revocation Tests
# ============================================================================

class TestFingerRevocation:
    """Test finger revocation with fuzzy extractor integration."""

    def test_revoke_compromised_finger(self, four_finger_biometric_arrays):
        """Test revoking a compromised finger."""
        # Initial enrollment: 4 fingers
        enrolled_keys = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(f"finger_{i}", key, quality=80))

        initial_master = aggregate_finger_keys(
            enrolled_keys, enrolled_count=4
        ).master_key

        # Revoke finger 2 (index 1)
        compromised_key = enrolled_keys[1].key
        remaining_keys = [k.key for i, k in enumerate(enrolled_keys) if i != 1]

        new_master = revoke_finger(
            initial_master, compromised_key, remaining_keys)

        # Verify new master matches aggregation of remaining 3 fingers
        remaining_finger_keys = [
            k for i, k in enumerate(enrolled_keys) if i != 1]
        expected_result = aggregate_finger_keys(
            remaining_finger_keys, enrolled_count=3
        )

        assert new_master == expected_result.master_key

    def test_revoke_down_to_minimum_two_fingers(self, four_finger_biometric_arrays):
        """Test revoking down to minimum 2 fingers."""
        # Initial enrollment: 4 fingers
        enrolled_keys = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(f"finger_{i}", key, quality=80))

        master = aggregate_finger_keys(
            enrolled_keys, enrolled_count=4).master_key

        # Revoke fingers 2 and 3
        for revoke_idx in [3, 2]:  # Revoke in reverse order
            compromised_key = enrolled_keys[revoke_idx].key
            remaining_keys = [
                k.key for i, k in enumerate(enrolled_keys)
                if i != revoke_idx and k in enrolled_keys
            ]

            master = revoke_finger(master, compromised_key, remaining_keys)
            enrolled_keys.pop(revoke_idx)

        # Should now have 2 fingers left
        assert len(enrolled_keys) == 2

        # Verify master matches aggregation
        final_result = aggregate_finger_keys(enrolled_keys, enrolled_count=2)
        assert master == final_result.master_key


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error conditions in integration scenarios."""

    def test_fuzzy_extractor_failure_with_heavy_corruption(
        self, four_finger_biometric_arrays
    ):
        """Test that heavily corrupted biometric data produces different key."""
        # Enrollment
        bio_array = four_finger_biometric_arrays[0]
        key_enrolled, helper_data = fuzzy_extract_gen(bio_array, "user_0")

        # Create heavily corrupted template (20 bit flips, beyond BCH t=10)
        np.random.seed(999)
        corrupted = bio_array.copy()
        num_flips = 20  # Exceeds BCH t=10 correction capacity
        flip_indices = np.random.choice(
            len(corrupted), num_flips, replace=False)
        corrupted[flip_indices] = 1 - corrupted[flip_indices]

        # Reproduction now fails deterministically when errors exceed BCH capacity
        with pytest.raises(ValueError, match="BCH decoding failed"):
            fuzzy_extract_rep(corrupted, helper_data)

    def test_insufficient_fingers_during_authentication(
        self, four_finger_biometric_arrays
    ):
        """Test authentication with only 1 finger (should fail)."""
        # Enrollment: 4 fingers
        enrolled_keys = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(f"finger_{i}", key, quality=80))

        # Try to authenticate with only 1 finger
        auth_keys = [enrolled_keys[0]]

        with pytest.raises(InsufficientFingersError, match="minimum: 2"):
            aggregate_finger_keys(auth_keys, enrolled_count=4)


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics of integration workflows."""

    def test_ten_finger_aggregation(self):
        """Test aggregation with maximum 10 fingers."""
        np.random.seed(42)

        # Generate 10 synthetic biometric arrays
        bio_arrays = [
            np.random.randint(0, 2, size=64, dtype=np.uint8) for _ in range(10)
        ]

        # Enrollment
        enrolled_keys = []

        key_data = generate_fuzzy_keys(bio_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(f"finger_{i}", key, quality=80))

        # Aggregate all 10 fingers
        result = aggregate_finger_keys(enrolled_keys, enrolled_count=10)

        assert result.fingers_used == 10
        assert result.fallback_mode is False
        assert len(result.master_key) == 32

    def test_aggregation_timing_benchmark(self, four_finger_biometric_arrays):
        """Test that aggregation is fast (<2µs target)."""
        import time

        # Enrollment
        enrolled_keys = []

        key_data = generate_fuzzy_keys(four_finger_biometric_arrays)

        for i, (key, helper_data, _) in enumerate(key_data):
            enrolled_keys.append(FingerKey(f"finger_{i}", key, quality=80))

        # Benchmark aggregation (1000 iterations)
        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            _ = aggregate_finger_keys(enrolled_keys, enrolled_count=4)

        end = time.perf_counter()
        avg_time_ms = ((end - start) / iterations) * 1000
        avg_time_us = avg_time_ms * 1000

        # Should be well under 2µs per aggregation
        # (Note: This includes Python overhead, actual XOR is much faster)
        print(f"\nAverage aggregation time: {avg_time_us:.2f}µs")

        # Very lenient threshold (Python overhead is significant)
        assert avg_time_us < 100  # 100µs including all Python overhead
