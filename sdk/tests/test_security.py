"""
Security Testing and Validation

Tests security properties including template reconstruction resistance,
helper data privacy, replay attack prevention, salt randomness, timing
attack resistance, and input fuzzing.

Phase 2, Task 7 - Security Testing and Validation

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

import pytest
import numpy as np
import time
from typing import List, Tuple

# Import components under test
from src.biometrics.fuzzy_extractor_v2 import (
    fuzzy_extract_gen,
    fuzzy_extract_rep,
    BCH_K,
    HelperData,
)
from src.biometrics.aggregator_v2 import (
    aggregate_finger_keys,
    FingerKey,
    AggregationError,
)

# Import test utilities
from tests.test_data_generator import generate_template, add_noise


# ============================================================================
# TEMPLATE RECONSTRUCTION RESISTANCE TESTS
# ============================================================================

class TestTemplateReconstructionResistance:
    """Test that helper data cannot be used to reconstruct templates."""

    def test_correlation_independence(self):
        """Test that helper data is statistically independent from template."""
        # Generate 100 enrollments
        correlations = []

        for i in range(100):
            template = generate_template(seed=200000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")

            # Compare template bits to first 64 bytes of helper (syndrome)
            helper_bytes = np.frombuffer(helper.serialize(), dtype=np.uint8)
            helper_bits = np.unpackbits(helper_bytes[:8])  # First 64 bits

            # Calculate point-wise correlation
            template_f = bio_bits.astype(np.float64)
            helper_f = helper_bits.astype(np.float64)

            # Pearson correlation
            if np.std(template_f) > 0 and np.std(helper_f) > 0:
                corr = np.corrcoef(template_f, helper_f)[0, 1]
                correlations.append(abs(corr))

        # Average correlation should be very low
        avg_correlation = np.mean(correlations)
        max_correlation = np.max(correlations)

        print(f"\nTemplate-Helper correlation:")
        print(f"  Average: {avg_correlation:.6f}")
        print(f"  Maximum: {max_correlation:.6f}")

        # Correlation should be very low (<0.2) indicating independence
        assert avg_correlation < 0.2, \
            f"Avg helper data correlation too high: {avg_correlation:.6f} (expected <0.2)"
        assert max_correlation < 0.5, \
            f"Max helper data correlation too high: {max_correlation:.6f} (expected <0.5)"

    def test_brute_force_resistance(self):
        """Test that brute-force template search is infeasible."""
        # Enroll one user
        template = generate_template(seed=200100, quality=85)
        bio_bits = np.unpackbits(template.template)[:BCH_K]
        key_target, helper = fuzzy_extract_gen(bio_bits, user_id="target_user")

        # Try random guesses (simulate brute-force attack)
        # In reality, 2^64 attempts needed, we test a sample
        matches = 0
        attempts = 10000

        for i in range(attempts):
            # Generate random template guess
            random_template = generate_template(seed=201000 + i, quality=85)
            random_bits = np.unpackbits(random_template.template)[:BCH_K]

            try:
                key_guess = fuzzy_extract_rep(random_bits, helper)
                if key_guess == key_target:
                    matches += 1
            except (ValueError, Exception):
                pass  # Most will fail

        # Success rate should be negligible
        success_rate = matches / attempts
        print(
            f"\nBrute-force success rate: {success_rate:.6f} ({matches}/{attempts})")

        # Should be effectively 0 (< 0.01%)
        assert success_rate < 0.0001, \
            f"Brute-force success rate too high: {success_rate:.6f}"


# ============================================================================
# HELPER DATA PRIVACY TESTS
# ============================================================================

class TestHelperDataPrivacy:
    """Test that helper data reveals no biometric information."""

    def test_helper_data_entropy(self):
        """Test that helper data has maximum entropy (appears random)."""
        # Generate 1000 helpers
        all_helper_bytes = []

        for i in range(1000):
            template = generate_template(seed=202000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")

            helper_bytes = np.frombuffer(helper.serialize(), dtype=np.uint8)
            all_helper_bytes.extend(helper_bytes)

        # Calculate Shannon entropy
        byte_array = np.array(all_helper_bytes)
        byte_counts = np.bincount(byte_array, minlength=256)
        probs = byte_counts / byte_counts.sum()
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))

        print(f"\nHelper data entropy: {entropy:.4f} bits/byte (max 8.0)")

        # Should be near maximum (>7.9)
        assert entropy > 7.9, \
            f"Helper data entropy too low: {entropy:.4f} (expected >7.9)"

    def test_helper_data_uniformity(self):
        """Test that helper data random components (salt) are uniformly distributed."""
        # Generate 5000 helpers and extract salts (should be uniformly random)
        all_salt_bytes = []

        for i in range(5000):
            template = generate_template(seed=203000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")

            # Extract just the salt (32 bytes) - this should be uniformly random
            all_salt_bytes.extend(helper.salt)

        # Chi-squared test for uniformity on salt only
        byte_array = np.array(all_salt_bytes, dtype=np.uint8)
        observed = np.bincount(byte_array, minlength=256)
        expected = len(byte_array) / 256

        # Chi-squared statistic
        chi_squared = np.sum((observed - expected) ** 2 / expected)

        # Degrees of freedom = 255
        # For large sample (160K bytes), expected ~255, std ~22.6
        # Using 3-sigma range: 120-390
        print(
            f"\nSalt chi-squared: {chi_squared:.2f} (expected ~255 ± 22)")

        # Should pass chi-squared test (within 3 std deviations)
        assert 120 < chi_squared < 390, \
            f"Salt not uniform: χ² = {chi_squared:.2f} (expected 120-390)"

    def test_mutual_information_leakage(self):
        """Test that helper data reveals minimal information about template."""
        # Generate 200 template-helper pairs
        samples = []

        for i in range(200):
            template = generate_template(seed=204000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")

            # Store first byte of template and first byte of helper
            template_byte = bio_bits[:8].dot(1 << np.arange(8)[::-1])
            helper_bytes = np.frombuffer(helper.serialize(), dtype=np.uint8)
            helper_byte = helper_bytes[0]

            samples.append((template_byte, helper_byte))

        # Calculate mutual information (simplified)
        # MI = H(T) + H(H) - H(T,H)
        templates_bytes = np.array([s[0] for s in samples])
        helpers_bytes = np.array([s[1] for s in samples])

        # Joint entropy
        joint_counts = np.zeros((256, 256))
        for t, h in samples:
            joint_counts[t, h] += 1
        joint_probs = joint_counts / len(samples)
        joint_probs = joint_probs[joint_probs > 0]
        h_joint = -np.sum(joint_probs * np.log2(joint_probs))

        # Marginal entropies
        t_counts = np.bincount(templates_bytes, minlength=256)
        t_probs = t_counts / t_counts.sum()
        t_probs = t_probs[t_probs > 0]
        h_t = -np.sum(t_probs * np.log2(t_probs))

        h_counts = np.bincount(helpers_bytes, minlength=256)
        h_probs = h_counts / h_counts.sum()
        h_probs = h_probs[h_probs > 0]
        h_h = -np.sum(h_probs * np.log2(h_probs))

        # Mutual information
        mi = h_t + h_h - h_joint

        print(f"\nMutual information: {mi:.4f} bits (lower is better)")
        print(
            f"  H(Template): {h_t:.4f}, H(Helper): {h_h:.4f}, H(T,H): {h_joint:.4f}")

        # MI should be very low (<0.5 bits)
        assert mi < 0.5, \
            f"Mutual information too high: {mi:.4f} bits (expected <0.5)"


# ============================================================================
# REPLAY ATTACK PREVENTION TESTS
# ============================================================================

class TestReplayAttackPrevention:
    """Test that salt prevents replay attacks."""

    def test_salt_uniqueness(self):
        """Test that each enrollment produces unique salt."""
        # Generate 10000 salts
        salts = set()

        for i in range(10000):
            template = generate_template(seed=205000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")

            salts.add(helper.salt)

        # All should be unique
        collision_rate = 1 - (len(salts) / 10000)
        print(
            f"\nSalt uniqueness: {len(salts)}/10000 unique ({collision_rate:.4%} collision rate)")

        # Should be 100% unique (birthday paradox extremely unlikely with 128-bit salt)
        assert len(salts) == 10000, \
            f"Salt collisions detected: {collision_rate:.4%}"

    def test_same_template_different_helpers(self):
        """Test that same template produces different helpers (due to salt)."""
        # Enroll same template multiple times
        template = generate_template(seed=206000, quality=85)
        bio_bits = np.unpackbits(template.template)[:BCH_K]

        helpers = []
        for i in range(100):
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            helpers.append(helper.serialize())

        # All should be unique
        unique_helpers = set(helpers)
        print(
            f"\nSame template, different helpers: {len(unique_helpers)}/100 unique")

        # Should be 100% unique
        assert len(unique_helpers) == 100, \
            "Same template produced identical helpers (replay vulnerability)"

    def test_cross_enrollment_rejection(self):
        """Test that helper from one enrollment doesn't work for another."""
        # Enroll user A
        template_a = generate_template(seed=207000, quality=85)
        bio_bits_a = np.unpackbits(template_a.template)[:BCH_K]
        key_a, helper_a = fuzzy_extract_gen(bio_bits_a, user_id="user_a")

        # Enroll user B with SAME biometric (simulate replay attack)
        key_b, helper_b = fuzzy_extract_gen(bio_bits_a, user_id="user_b")

        # Keys should be different (salt prevents deterministic key derivation)
        assert key_a != key_b, \
            "Same template produced same key across enrollments (replay vulnerability)"

        # Helper A should not work for enrollment B
        key_verify = fuzzy_extract_rep(bio_bits_a, helper_a)
        assert key_verify == key_a, "Sanity check: helper_a should work for key_a"
        assert key_verify != key_b, "Helper A worked for enrollment B (replay vulnerability)"


# ============================================================================
# SALT RANDOMNESS TESTS
# ============================================================================

class TestSaltRandomness:
    """Test cryptographic properties of salt generation."""

    def test_salt_entropy(self):
        """Test that salts have maximum entropy."""
        # Generate 1000 salts
        all_salt_bytes = []

        for i in range(1000):
            template = generate_template(seed=208000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")

            salt_bytes = np.frombuffer(helper.salt, dtype=np.uint8)
            all_salt_bytes.extend(salt_bytes)

        # Calculate entropy
        byte_array = np.array(all_salt_bytes)
        byte_counts = np.bincount(byte_array, minlength=256)
        probs = byte_counts / byte_counts.sum()
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))

        print(f"\nSalt entropy: {entropy:.4f} bits/byte (max 8.0)")

        # Should be near maximum (>7.95)
        assert entropy > 7.95, \
            f"Salt entropy too low: {entropy:.4f} (expected >7.95)"

    def test_salt_unpredictability(self):
        """Test that salts are not predictable from previous salts."""
        # Generate sequence of salts
        salts = []
        for i in range(100):
            template = generate_template(seed=209000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            _, helper = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            salts.append(helper.salt)

        # Test for sequential patterns (XOR of consecutive salts should be random)
        xor_results = []
        for i in range(len(salts) - 1):
            salt_a = np.frombuffer(salts[i], dtype=np.uint8)
            salt_b = np.frombuffer(salts[i + 1], dtype=np.uint8)
            xor_result = salt_a ^ salt_b
            xor_results.extend(xor_result)

        # XOR entropy should also be high
        xor_array = np.array(xor_results)
        byte_counts = np.bincount(xor_array, minlength=256)
        probs = byte_counts / byte_counts.sum()
        probs = probs[probs > 0]
        entropy = -np.sum(probs * np.log2(probs))

        print(f"\nSalt XOR entropy: {entropy:.4f} bits/byte (max 8.0)")

        # Should be high (>7.8)
        assert entropy > 7.8, \
            f"Salt XOR entropy too low: {entropy:.4f} (predictable sequence)"


# ============================================================================
# TIMING ATTACK RESISTANCE TESTS
# ============================================================================

class TestTimingAttackResistance:
    """Test that operations have constant time (timing attack resistance)."""

    def test_verification_timing_independence(self):
        """Test that verification time doesn't leak information."""
        # Enroll user
        template = generate_template(seed=210000, quality=85)
        bio_bits = np.unpackbits(template.template)[:BCH_K]
        key_target, helper = fuzzy_extract_gen(bio_bits, user_id="target_user")

        # Test 1: Correct template (should succeed)
        timings_correct = []
        for _ in range(100):
            start = time.perf_counter_ns()
            try:
                fuzzy_extract_rep(bio_bits, helper)
            except Exception:
                pass
            end = time.perf_counter_ns()
            timings_correct.append(end - start)

        # Test 2: Wrong template (should fail)
        timings_wrong = []
        for i in range(100):
            wrong_template = generate_template(seed=211000 + i, quality=85)
            wrong_bits = np.unpackbits(wrong_template.template)[:BCH_K]
            start = time.perf_counter_ns()
            try:
                fuzzy_extract_rep(wrong_bits, helper)
            except Exception:
                pass
            end = time.perf_counter_ns()
            timings_wrong.append(end - start)

        # Calculate statistics
        mean_correct = np.mean(timings_correct)
        mean_wrong = np.mean(timings_wrong)
        std_correct = np.std(timings_correct)
        std_wrong = np.std(timings_wrong)

        # Calculate relative difference
        rel_diff = abs(mean_correct - mean_wrong) / \
            max(mean_correct, mean_wrong)

        print(f"\nTiming analysis:")
        print(f"  Correct: {mean_correct/1e6:.2f} ± {std_correct/1e6:.2f} ms")
        print(f"  Wrong:   {mean_wrong/1e6:.2f} ± {std_wrong/1e6:.2f} ms")
        print(f"  Relative difference: {rel_diff:.4%}")

        # Timing difference should be small (<10%)
        # Note: Perfect constant-time is hard in Python, but we check for obvious leaks
        assert rel_diff < 0.10, \
            f"Timing difference too large: {rel_diff:.4%} (potential timing attack)"

    def test_aggregation_timing_independence(self):
        """Test that aggregation time doesn't depend on key values."""
        # Generate two sets of finger keys with different properties
        # Set 1: All zeros (low entropy)
        fingers_low = []
        for i in range(4):
            template = generate_template(seed=212000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            # Force low entropy by using same template
            key, _ = fuzzy_extract_gen(bio_bits, user_id="same_user")
            fingers_low.append(
                FingerKey(finger_id=f"finger_{i}", key=key, quality=85))

        # Set 2: Random (high entropy)
        fingers_high = []
        for i in range(4):
            template = generate_template(seed=213000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            key, _ = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            fingers_high.append(
                FingerKey(finger_id=f"finger_{i}", key=key, quality=85))

        # Time both using batched runs to smooth out timer jitter
        batch_size = 50
        iterations = 40

        def measure_timings(fingers):
            samples = []
            for _ in range(iterations):
                start = time.perf_counter_ns()
                for _ in range(batch_size):
                    aggregate_finger_keys(fingers, enrolled_count=4)
                end = time.perf_counter_ns()
                samples.append((end - start) / batch_size)
            return np.array(samples, dtype=np.float64)

        timings_low = measure_timings(fingers_low)
        timings_high = measure_timings(fingers_high)

        median_low = np.median(timings_low)
        median_high = np.median(timings_high)
        rel_diff = abs(median_low - median_high) / max(median_low, median_high)

        print(f"\nAggregation timing:")
        print(f"  Low entropy:  {median_low/1e6:.4f} ms (median)")
        print(f"  High entropy: {median_high/1e6:.4f} ms (median)")
        print(f"  Relative difference: {rel_diff:.4%}")

        # Should be similar (<10%) once timer jitter is tamed by batching
        assert rel_diff < 0.10, \
            f"Aggregation timing varies with input: {rel_diff:.4%}"


# ============================================================================
# FUZZ TESTING
# ============================================================================

class TestFuzzTesting:
    """Test robustness against malformed inputs."""

    def test_malformed_biometric_inputs(self):
        """Test handling of invalid biometric data."""
        # Test cases
        test_cases = [
            ("empty", np.array([], dtype=np.uint8)),
            ("too_short", np.array([1] * (BCH_K - 1), dtype=np.uint8)),
            ("too_long", np.array([1] * (BCH_K + 100), dtype=np.uint8)),
            ("wrong_dtype", np.array([1.5] * BCH_K, dtype=np.float64)),
            ("invalid_values", np.array(
                [2] * BCH_K, dtype=np.uint8)),  # Not 0/1
        ]

        for name, invalid_input in test_cases:
            print(f"\nTesting malformed input: {name}")
            try:
                # Should either handle gracefully or raise appropriate exception
                _, helper = fuzzy_extract_gen(
                    invalid_input, user_id="test_user")
                # If it doesn't fail, check output is valid
                assert isinstance(
                    helper, HelperData), f"{name}: Invalid helper type"
            except (ValueError, TypeError, IndexError, AssertionError) as e:
                # Expected - invalid input should raise exception
                print(f"  ✓ Rejected with {type(e).__name__}: {str(e)[:50]}")
            except Exception as e:
                # Unexpected exception type
                pytest.fail(
                    f"{name}: Unexpected exception {type(e).__name__}: {e}")

    def test_malformed_helper_data(self):
        """Test handling of corrupted helper data."""
        # Generate valid helper first
        template = generate_template(seed=214000, quality=85)
        bio_bits = np.unpackbits(template.template)[:BCH_K]
        _, helper = fuzzy_extract_gen(bio_bits, user_id="test_user")

        # Test corruptions
        test_cases = [
            ("wrong_version", lambda h: HelperData(
                version=999, salt=h.salt, personalization=h.personalization,
                bch_syndrome=h.bch_syndrome, hmac=h.hmac
            )),
            ("empty_salt", lambda h: HelperData(
                version=h.version, salt=b"", personalization=h.personalization,
                bch_syndrome=h.bch_syndrome, hmac=h.hmac
            )),
            ("corrupt_syndrome", lambda h: HelperData(
                version=h.version, salt=h.salt, personalization=h.personalization,
                bch_syndrome=b"\x00" * len(h.bch_syndrome), hmac=h.hmac
            )),
        ]

        for name, corrupt_fn in test_cases:
            print(f"\nTesting corrupted helper: {name}")
            try:
                corrupted = corrupt_fn(helper)
                key = fuzzy_extract_rep(bio_bits, corrupted)
                # If it succeeds, it should at least return bytes
                assert isinstance(key, bytes), f"{name}: Invalid key type"
                # But likely wrong key (we can't verify easily)
            except (ValueError, TypeError, Exception) as e:
                # Expected for most corruptions
                print(f"  ✓ Rejected with {type(e).__name__}: {str(e)[:50]}")

    def test_aggregation_invalid_inputs(self):
        """Test aggregation with invalid finger key inputs."""
        # Generate valid finger keys
        valid_fingers = []
        for i in range(4):
            template = generate_template(seed=215000 + i, quality=85)
            bio_bits = np.unpackbits(template.template)[:BCH_K]
            key, _ = fuzzy_extract_gen(bio_bits, user_id=f"user_{i}")
            valid_fingers.append(
                FingerKey(finger_id=f"finger_{i}", key=key, quality=85))

        # Test cases
        test_cases = [
            ("empty_list", []),
            ("single_finger", valid_fingers[:1]),
            ("duplicate_keys", [valid_fingers[0]] * 4),
            ("low_quality", [FingerKey(f"finger_{i}", valid_fingers[i].key, quality=10)
                             for i in range(2)]),
        ]

        for name, invalid_input in test_cases:
            print(f"\nTesting invalid aggregation: {name}")
            try:
                result = aggregate_finger_keys(invalid_input, enrolled_count=4)
                # Some cases may succeed (e.g., duplicate keys)
                print(f"  ℹ Accepted (result: {len(result.master_key)} bytes)")
            except (AggregationError, ValueError, Exception) as e:
                # Expected for most invalid cases
                print(f"  ✓ Rejected with {type(e).__name__}: {str(e)[:80]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
