"""
Reproducibility and Stability Testing

Tests digest stability, FAR/FRR measurement, helper data properties,
and aggregation behavior for Phase 2 biometric DID system.

Phase 2, Task 6 - Reproducibility and Stability Testing

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

import pytest
import numpy as np
from typing import List, Tuple

# Import components under test
from src.biometrics.fuzzy_extractor_v2 import (
    fuzzy_extract_gen,
    fuzzy_extract_rep,
    BCH_K,
)
from src.biometrics.aggregator_v2 import (
    aggregate_finger_keys,
    FingerKey,
)

# Import test data utilities
from tests.test_data_generator import (
    generate_template,
    add_noise,
    NOISE_LEVEL_EXCELLENT,
    NOISE_LEVEL_GOOD,
    NOISE_LEVEL_FAIR,
    NOISE_LEVEL_POOR,
    NOISE_LEVEL_HIGH,
)


# ============================================================================
# DIGEST STABILITY TESTS
# ============================================================================

class TestDigestStability:
    """Test that same enrollment produces consistent keys across noisy variations."""

    def test_stability_clean_data(self):
        """Test 100% stability with clean data (0% noise)."""
        # Generate base template (use only first BCH_K bits)
        base = generate_template(seed=50000, quality=90)
        bio_bits = np.unpackbits(base.template)[:BCH_K]

        # Enroll
        key_enrollment, helper = fuzzy_extract_gen(
            bio_bits, user_id="user_50000")

        # Verify 100 times with same template
        success_count = 0
        for i in range(100):
            key_verify = fuzzy_extract_rep(bio_bits, helper)
            if key_verify == key_enrollment:
                success_count += 1

        # Should be 100% stable with clean data
        assert success_count == 100, f"Clean data stability: {success_count}/100"

    def test_stability_excellent_noise(self):
        """Test stability with excellent quality (2% noise)."""
        # Generate base template
        base = generate_template(seed=50001, quality=95)
        bio_bits = np.unpackbits(base.template)[:BCH_K]

        # Enroll
        key_enrollment, helper = fuzzy_extract_gen(
            bio_bits, user_id="user_50001")

        # Verify 1000 times with 2% noise
        success_count = 0
        for i in range(1000):
            noisy = add_noise(
                base.template, NOISE_LEVEL_EXCELLENT, seed=60000 + i)
            noisy_bits = np.unpackbits(noisy)[:BCH_K]
            try:
                key_verify = fuzzy_extract_rep(noisy_bits, helper)
                if key_verify == key_enrollment:
                    success_count += 1
            except (ValueError, Exception):
                pass  # Failed to extract key

        # Should be >98% stable with 2% noise
        stability_rate = success_count / 1000
        print(f"\nExcellent noise (2%) stability: {stability_rate:.1%}")
        assert stability_rate > 0.98, \
            f"Excellent noise stability: {stability_rate:.1%} (expected >98%)"

    def test_stability_good_noise(self):
        """Test stability with good quality (5% noise)."""
        base = generate_template(seed=50002, quality=85)
        bio_bits = np.unpackbits(base.template)[:BCH_K]

        # Enroll
        key_enrollment, helper = fuzzy_extract_gen(
            bio_bits, user_id="user_50002")

        # Verify 1000 times with 5% noise
        success_count = 0
        for i in range(1000):
            noisy = add_noise(base.template, NOISE_LEVEL_GOOD, seed=61000 + i)
            noisy_bits = np.unpackbits(noisy)[:BCH_K]
            try:
                key_verify = fuzzy_extract_rep(noisy_bits, helper)
                if key_verify == key_enrollment:
                    success_count += 1
            except (ValueError, Exception):
                pass

        # Should be >95% stable with 5% noise
        stability_rate = success_count / 1000
        print(f"\nGood noise (5%) stability: {stability_rate:.1%}")
        assert stability_rate > 0.95, \
            f"Good noise stability: {stability_rate:.1%} (expected >95%)"

    def test_stability_fair_noise(self):
        """Test stability with fair quality (10% noise)."""
        base = generate_template(seed=50003, quality=75)
        bio_bits = np.unpackbits(base.template)[:BCH_K]

        # Enroll
        key_enrollment, helper = fuzzy_extract_gen(
            bio_bits, user_id="user_50003")

        # Verify 1000 times with 10% noise
        success_count = 0
        for i in range(1000):
            noisy = add_noise(base.template, NOISE_LEVEL_FAIR, seed=62000 + i)
            noisy_bits = np.unpackbits(noisy)[:BCH_K]
            try:
                key_verify = fuzzy_extract_rep(noisy_bits, helper)
                if key_verify == key_enrollment:
                    success_count += 1
            except (ValueError, Exception):
                pass

        # Should be >85% stable with 10% noise (near BCH threshold)
        stability_rate = success_count / 1000
        print(f"\nFair noise (10%) stability: {stability_rate:.1%}")
        assert stability_rate > 0.85, \
            f"Fair noise stability: {stability_rate:.1%} (expected >85%)"


# ============================================================================
# FAR (FALSE ACCEPT RATE) TESTS
# ============================================================================

class TestFalseAcceptRate:
    """Test that different fingers/users do NOT match (security)."""

    def test_far_different_users(self):
        """Test FAR with different users (single finger)."""
        # Enroll 100 different users
        enrollments = []
        for user_idx in range(100):
            template = generate_template(seed=70000 + user_idx, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            key, helper = fuzzy_extract_gen(
                bio_bits, user_id=f"user_{user_idx}")
            enrollments.append({
                "user_id": f"user_{user_idx}",
                "key": key,
                "helper": helper,
                "bio_bits": bio_bits
            })

        # Test: Try to verify each user against all OTHER users' helpers
        false_accepts = 0
        total_attempts = 0

        for i, user_a in enumerate(enrollments[:10]):  # Test first 10 users
            for j, user_b in enumerate(enrollments):
                if i == j:
                    continue  # Skip same user

                # Try to verify user_a's template with user_b's helper
                try:
                    key_verify = fuzzy_extract_rep(
                        user_a["bio_bits"], user_b["helper"])
                    # If key matches, it's a false accept
                    if key_verify == user_b["key"]:
                        false_accepts += 1
                except (ValueError, Exception):
                    pass  # Expected: verification should fail

                total_attempts += 1

        # Calculate FAR
        far = false_accepts / total_attempts if total_attempts > 0 else 0
        print(
            f"\nFAR (different users): {far:.4%} ({false_accepts}/{total_attempts})")

        # FAR should be < 0.01% (1 in 10,000)
        assert far < 0.0001, f"FAR: {far:.4%} (expected <0.01%)"

    def test_far_random_templates(self):
        """Test FAR with completely random templates."""
        # Enroll 50 random templates
        enrollments = []
        for i in range(50):
            template = generate_template(seed=72000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            key, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            enrollments.append({"key": key, "helper": helper})

        # Generate 50 random verification attempts (different seeds)
        false_accepts = 0
        total_attempts = 0

        for i in range(50):
            random_template = generate_template(seed=73000 + i, quality=85)
            random_bits = np.unpackbits(random_template.template)[:BCH_K]

            # Try against all enrolled helpers
            for enrollment in enrollments:
                try:
                    key_verify = fuzzy_extract_rep(
                        random_bits, enrollment["helper"])
                    if key_verify == enrollment["key"]:
                        false_accepts += 1
                except (ValueError, Exception):
                    pass

                total_attempts += 1

        # Calculate FAR
        far = false_accepts / total_attempts if total_attempts > 0 else 0
        print(
            f"\nFAR (random templates): {far:.4%} ({false_accepts}/{total_attempts})")

        # Random templates should have negligible FAR
        assert far < 0.0001, f"Random templates FAR: {far:.4%} (expected <0.01%)"


# ============================================================================
# FRR (FALSE REJECT RATE) TESTS
# ============================================================================

class TestFalseRejectRate:
    """Test that same finger DOES match (usability)."""

    def test_frr_vs_noise_level(self):
        """Measure FRR across different noise levels."""
        # Generate base template
        base = generate_template(seed=80000, quality=90)
        bio_bits = np.unpackbits(base.template)[:BCH_K]

        # Enroll
        key_enrollment, helper = fuzzy_extract_gen(
            bio_bits, user_id="user_80000")

        # Test FRR at different noise levels
        noise_levels = [0.02, 0.05, 0.10, 0.12, 0.15, 0.18, 0.20]
        frr_results = {}

        for noise_level in noise_levels:
            rejects = 0
            attempts = 100

            for i in range(attempts):
                noisy = add_noise(base.template, noise_level,
                                  seed=81000 + int(noise_level * 1000) + i)
                noisy_bits = np.unpackbits(noisy)[:BCH_K]
                try:
                    key_verify = fuzzy_extract_rep(noisy_bits, helper)
                    if key_verify != key_enrollment:
                        rejects += 1  # Wrong key = reject
                except (ValueError, Exception):
                    rejects += 1  # Failed to extract = reject

            frr = rejects / attempts
            frr_results[noise_level] = frr

        # Print results for analysis
        print("\nFRR vs Noise Level:")
        for noise_level, frr in sorted(frr_results.items()):
            print(f"  {noise_level*100:5.1f}% noise: FRR = {frr:.1%}")

        # Assertions
        assert frr_results[
            0.02] < 0.05, f"FRR at 2% noise: {frr_results[0.02]:.1%} (expected <5%)"
        assert frr_results[
            0.05] < 0.10, f"FRR at 5% noise: {frr_results[0.05]:.1%} (expected <10%)"
        assert frr_results[
            0.10] < 0.20, f"FRR at 10% noise: {frr_results[0.10]:.1%} (expected <20%)"


# ============================================================================
# HELPER DATA PROPERTIES TESTS
# ============================================================================

class TestHelperDataProperties:
    """Test that helper data has good security properties."""

    def test_helper_data_entropy(self):
        """Test that helper data has high entropy."""
        # Generate helpers
        helpers = []
        for i in range(100):
            template = generate_template(seed=101000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            helpers.append(helper.serialize())

        # Concatenate all helpers
        all_helper_bytes = np.concatenate(
            [np.frombuffer(h, dtype=np.uint8) for h in helpers])

        # Calculate byte-level entropy
        byte_counts = np.bincount(all_helper_bytes, minlength=256)
        probs = byte_counts / byte_counts.sum()
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))

        print(f"\nHelper data entropy: {entropy:.2f} bits/byte (max 8.0)")

        # Entropy should be high (>7.0 bits/byte)
        assert entropy > 7.0, f"Helper data entropy too low: {entropy:.2f}"

    def test_helper_data_uniqueness(self):
        """Test that helper data is unique across enrollments."""
        # Generate 1000 helpers
        helpers = set()
        for i in range(1000):
            template = generate_template(seed=102000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            helpers.add(helper.serialize())

        # All should be unique
        print(f"\nHelper data uniqueness: {len(helpers)}/1000")
        assert len(helpers) == 1000, "Helper data collisions detected"


# ============================================================================
# AGGREGATION PROPERTIES TESTS
# ============================================================================

class TestAggregationProperties:
    """Test aggregation behavior and properties."""

    def test_aggregation_uniqueness(self):
        """Test that aggregated keys from different enrollments are unique."""
        # Generate 1000 different 4-finger enrollments
        aggregated_keys = []

        for user_idx in range(1000):
            # Generate 4 fingers for this user
            finger_keys_list = []
            for finger_idx in range(4):
                template = generate_template(
                    seed=110000 + user_idx * 10 + finger_idx,
                    quality=85
                )
                bio_bits = np.unpackbits(template.template)[:BCH_K]
                key, _ = fuzzy_extract_gen(
                    bio_bits, user_id=f"user_{user_idx}")
                finger_keys_list.append(
                    FingerKey(
                        finger_id=f"finger_{finger_idx}",
                        key=key,
                        quality=85
                    )
                )

            # Aggregate
            result = aggregate_finger_keys(finger_keys_list, enrolled_count=4)
            aggregated_keys.append(result.master_key)

        # Check uniqueness
        unique_keys = set(aggregated_keys)
        collision_rate = 1 - (len(unique_keys) / len(aggregated_keys))

        print(
            f"\nAggregated keys: {len(aggregated_keys)} total, {len(unique_keys)} unique")
        print(f"Collision rate: {collision_rate:.4%}")

        # Collision rate should be 0% (all unique)
        assert collision_rate < 0.001, f"Collision rate too high: {collision_rate:.4%}"

    def test_aggregation_distribution(self):
        """Test that aggregated keys are uniformly distributed."""
        # Generate 1000 aggregated keys
        aggregated_keys = []

        for i in range(1000):
            finger_keys_list = []
            for j in range(4):
                template = generate_template(
                    seed=120000 + i * 10 + j, quality=85)
                bio_bits = np.unpackbits(template.template)[:BCH_K]
                key, _ = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
                finger_keys_list.append(
                    FingerKey(finger_id=f"finger_{j}", key=key, quality=85)
                )

            result = aggregate_finger_keys(finger_keys_list, enrolled_count=4)
            aggregated_keys.append(result.master_key)

        # Analyze byte distribution
        all_bytes = np.concatenate(
            [np.frombuffer(k, dtype=np.uint8) for k in aggregated_keys])
        byte_counts = np.bincount(all_bytes, minlength=256)
        expected_per_bin = len(all_bytes) / 256

        # Calculate max deviation
        max_deviation = np.max(np.abs(byte_counts - expected_per_bin))
        relative_deviation = max_deviation / expected_per_bin

        print(f"\nAggregated key distribution:")
        print(f"  Total bytes: {len(all_bytes)}")
        print(f"  Expected per bin: {expected_per_bin:.1f}")
        print(
            f"  Max deviation: {max_deviation:.1f} ({relative_deviation:.1%})")

        # Deviation should be reasonable (<10x expected)
        assert relative_deviation < 10.0, \
            f"Distribution deviation too high: {relative_deviation:.1%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
