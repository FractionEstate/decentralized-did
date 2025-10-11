"""
Test Data Validation Tests

Validates statistical properties and correctness of generated test data.

Phase 2, Task 5 - Test Data Validation

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

import pytest
import numpy as np
from pathlib import Path

from tests.test_data_generator import (
    generate_template,
    add_noise,
    generate_noisy_variant,
    NOISE_LEVEL_EXCELLENT,
    NOISE_LEVEL_GOOD,
    NOISE_LEVEL_FAIR,
    TEMPLATE_SIZE_BITS,
)


# ============================================================================
# TEMPLATE GENERATION TESTS
# ============================================================================

def test_template_size():
    """Test that templates have correct size."""
    template = generate_template(seed=12345)

    # Should be 64 bytes (512 bits)
    assert template.template.shape == (64,)
    assert template.template.dtype == np.uint8


def test_template_reproducibility():
    """Test that same seed produces same template."""
    t1 = generate_template(seed=12345)
    t2 = generate_template(seed=12345)

    assert np.array_equal(
        t1.template, t2.template), "Same seed should produce identical templates"


def test_template_uniqueness():
    """Test that different seeds produce different templates."""
    t1 = generate_template(seed=12345)
    t2 = generate_template(seed=12346)

    assert not np.array_equal(
        t1.template, t2.template), "Different seeds should produce different templates"


def test_template_distribution():
    """Test that templates are uniformly distributed."""
    # Generate many templates
    templates = [generate_template(seed=1000 + i) for i in range(1000)]
    flattened = np.concatenate([t.template for t in templates])

    # Simple uniformity check: each byte value should appear roughly equally
    observed, _ = np.histogram(flattened, bins=256, range=(0, 256))
    expected_per_bin = len(flattened) / 256

    # Check that no bin is too far from expected (>5x deviation)
    max_deviation = np.max(np.abs(observed - expected_per_bin))
    assert max_deviation < 5 * np.sqrt(expected_per_bin), \
        f"Templates not uniformly distributed (max deviation: {max_deviation:.1f})"


# ============================================================================
# NOISE GENERATION TESTS
# ============================================================================

def test_noise_reproducibility():
    """Test that noise generation is reproducible."""
    template = generate_template(seed=1000).template

    noisy1 = add_noise(template, 0.1, seed=2000)
    noisy2 = add_noise(template, 0.1, seed=2000)

    assert np.array_equal(
        noisy1, noisy2), "Same seed should produce identical noise"


def test_noise_level_accuracy():
    """Test that noise level matches expected bit flip count approximately."""
    template = generate_template(seed=1000).template
    noise_levels = [0.02, 0.05, 0.10, 0.15, 0.20]

    for noise_level in noise_levels:
        noisy = add_noise(template, noise_level, seed=2000)

        # Count bit differences
        diff = np.bitwise_xor(template, noisy)
        bit_diff_count = int(np.unpackbits(diff).sum()
                             )  # Convert to Python int

        expected_flips = int(TEMPLATE_SIZE_BITS * noise_level)

        # Should be approximately correct (within 30% tolerance)
        # Note: Some bits may be flipped twice (back to original), causing under-counting
        tolerance = int(expected_flips * 0.3)
        assert abs(bit_diff_count - expected_flips) <= tolerance, \
            f"Noise level {noise_level}: expected ~{expected_flips} flips, got {bit_diff_count}"


def test_noise_independence():
    """Test that different noise seeds produce independent patterns."""
    template = generate_template(seed=1000).template

    noisy1 = add_noise(template, 0.1, seed=2000)
    noisy2 = add_noise(template, 0.1, seed=2001)

    # Noise patterns should be different
    assert not np.array_equal(
        noisy1, noisy2), "Different seeds should produce different noise"

    # Check: Less than 20% overlap in noise patterns
    diff1 = np.bitwise_xor(template, noisy1)
    diff2 = np.bitwise_xor(template, noisy2)
    overlap = np.bitwise_and(diff1, diff2)
    overlap_count = np.unpackbits(overlap).sum()
    total_flips = int(TEMPLATE_SIZE_BITS * 0.1)

    overlap_ratio = overlap_count / total_flips
    assert overlap_ratio < 0.2, f"Noise patterns too similar (overlap={overlap_ratio:.2%})"


def test_noise_preserves_other_bits():
    """Test that noise roughly matches expected number of flips."""
    template = generate_template(seed=1000).template
    noise_level = 0.1

    noisy = add_noise(template, noise_level, seed=2000)

    # Count total differences
    diff = np.bitwise_xor(template, noisy)
    bit_diff_count = int(np.unpackbits(diff).sum())  # Convert to Python int

    # Should be approximately noise_level * TEMPLATE_SIZE_BITS (within 30%)
    expected = int(TEMPLATE_SIZE_BITS * noise_level)
    tolerance = int(expected * 0.3)
    assert abs(bit_diff_count - expected) <= tolerance
# ============================================================================
# QUALITY DEGRADATION TESTS
# ============================================================================


def test_quality_degradation():
    """Test that quality degrades with noise."""
    base = generate_template(seed=1000, quality=85)

    noisy_02 = generate_noisy_variant(base, 0.02, seed=2000)
    noisy_10 = generate_noisy_variant(base, 0.10, seed=2001)
    noisy_20 = generate_noisy_variant(base, 0.20, seed=2002)

    # Quality should decrease with noise
    assert noisy_02.quality > noisy_10.quality
    assert noisy_10.quality > noisy_20.quality


def test_quality_calculation():
    """Test quality calculation formula."""
    base = generate_template(seed=1000, quality=90)

    noise_levels = [0.0, 0.05, 0.10, 0.15, 0.20]
    expected_qualities = [90, 85, 80, 75, 70]

    for noise_level, expected in zip(noise_levels, expected_qualities):
        noisy = generate_noisy_variant(base, noise_level, seed=2000)
        assert noisy.quality == expected, \
            f"Quality at {noise_level*100:.0f}% noise: expected {expected}, got {noisy.quality}"


def test_quality_bounds():
    """Test that quality stays in [0, 100] range."""
    base = generate_template(seed=1000, quality=20)

    # Very high noise should not make quality negative
    noisy = generate_noisy_variant(base, 0.50, seed=2000)
    assert 0 <= noisy.quality <= 100


# ============================================================================
# TEST VECTOR VALIDATION
# ============================================================================

def test_test_vectors_single(test_vectors_single):
    """Validate single-finger test vectors."""
    assert len(test_vectors_single) == 3, "Should have 3 single-finger vectors"

    for vector in test_vectors_single:
        # Check structure
        assert vector.vector_id
        assert vector.user_id
        assert vector.enrollment_template
        assert len(vector.verification_templates) > 0
        assert len(vector.noise_levels) == len(vector.verification_templates)

        # Check template sizes
        assert vector.enrollment_template.template.shape == (64,)
        for vt in vector.verification_templates:
            assert vt.template.shape == (64,)


def test_test_vectors_multi4(test_vectors_multi4):
    """Validate multi-finger test vectors."""
    assert len(test_vectors_multi4) == 3, "Should have 3 multi-finger cases"

    for case_id, vectors in test_vectors_multi4.items():
        assert len(vectors) == 4, f"Case {case_id} should have 4 fingers"

        # Check that all vectors have same user_id
        user_ids = {v.user_id for v in vectors}
        assert len(user_ids) == 1, f"Case {case_id} has mixed user IDs"

        # Check that finger IDs are unique
        finger_ids = [v.enrollment_template.finger_id for v in vectors]
        assert len(set(finger_ids)
                   ) == 4, f"Case {case_id} has duplicate finger IDs"


def test_adversarial_cases(adversarial_cases):
    """Validate adversarial test cases."""
    assert len(adversarial_cases) == 4, "Should have 4 adversarial cases"

    # Check that we have the expected cases
    vector_ids = {case.vector_id for case in adversarial_cases}
    expected = {
        "adv001_high_noise",
        "adv002_boundary",
        "adv003_poor_quality",
        "adv004_wrong_finger",
    }
    assert vector_ids == expected


def test_adversarial_high_noise(adversarial_high_noise):
    """Validate high noise adversarial case."""
    assert not adversarial_high_noise.expected_match, "High noise should expect failure"

    # Check noise levels are high
    for noise_level in adversarial_high_noise.noise_levels:
        assert noise_level >= 0.20, f"High noise case has low noise: {noise_level}"


def test_adversarial_boundary(adversarial_boundary):
    """Validate BCH boundary adversarial case."""
    assert adversarial_boundary.expected_match, "Boundary case should expect success"

    # Check noise levels are near threshold
    for noise_level in adversarial_boundary.noise_levels:
        assert 0.12 <= noise_level <= 0.14, \
            f"Boundary case has wrong noise level: {noise_level}"


def test_adversarial_poor_quality(adversarial_poor_quality):
    """Validate poor quality adversarial case."""
    quality = adversarial_poor_quality.enrollment_template.quality
    assert quality < 50, f"Poor quality case has high quality: {quality}"


def test_adversarial_wrong_finger(adversarial_wrong_finger):
    """Validate wrong finger adversarial case."""
    assert not adversarial_wrong_finger.expected_match, "Wrong finger should expect failure"

    # Check that enrollment and verification have different finger IDs
    enroll_finger = adversarial_wrong_finger.enrollment_template.finger_id
    verify_finger = adversarial_wrong_finger.verification_templates[0].finger_id

    assert enroll_finger != verify_finger, "Wrong finger case has same finger IDs"


# ============================================================================
# BENCHMARK DATASET VALIDATION
# ============================================================================

def test_benchmark_small(benchmark_small):
    """Validate small benchmark dataset."""
    assert benchmark_small.num_users == 100
    assert benchmark_small.num_fingers_per_user == 4
    assert len(benchmark_small.templates) == 400


def test_benchmark_medium(benchmark_medium):
    """Validate medium benchmark dataset."""
    assert benchmark_medium.num_users == 1000
    assert benchmark_medium.num_fingers_per_user == 4
    assert len(benchmark_medium.templates) == 4000


def test_benchmark_large(benchmark_large):
    """Validate large benchmark dataset."""
    assert benchmark_large.num_users == 10000
    assert benchmark_large.num_fingers_per_user == 2
    assert len(benchmark_large.templates) == 20000


def test_benchmark_user_distribution(benchmark_small):
    """Test that benchmark has correct user distribution."""
    # Count templates per user
    user_counts = {}
    for template in benchmark_small.templates:
        user_id = template.user_id
        user_counts[user_id] = user_counts.get(user_id, 0) + 1

    # Should have 100 users
    assert len(user_counts) == 100

    # Each user should have 4 templates
    for user_id, count in user_counts.items():
        assert count == 4, f"User {user_id} has {count} templates (expected 4)"


def test_benchmark_quality_range(benchmark_small):
    """Test that benchmark templates have quality in expected range."""
    qualities = [t.quality for t in benchmark_small.templates]

    assert min(qualities) >= 75, f"Quality too low: {min(qualities)}"
    assert max(qualities) <= 95, f"Quality too high: {max(qualities)}"


# ============================================================================
# REPRODUCIBILITY TESTS
# ============================================================================

def test_seed_reproducibility():
    """Test that seed assignment is consistent."""
    # Generate same vector multiple times
    from tests.test_data_generator import generate_test_vector

    v1 = generate_test_vector(
        vector_id="test",
        user_id="user",
        finger_id="left_thumb",
        enrollment_seed=12345,
        noise_levels=[0.05],
    )

    v2 = generate_test_vector(
        vector_id="test",
        user_id="user",
        finger_id="left_thumb",
        enrollment_seed=12345,
        noise_levels=[0.05],
    )

    # Should be identical
    assert np.array_equal(
        v1.enrollment_template.template,
        v2.enrollment_template.template
    )
    assert np.array_equal(
        v1.verification_templates[0].template,
        v2.verification_templates[0].template
    )


def test_fixtures_loaded_correctly(test_vector_clean, test_vector_good, test_vector_fair):
    """Test that fixtures load correctly and have expected properties."""
    # Clean: 2% noise
    assert 0.01 <= test_vector_clean.noise_levels[0] <= 0.03

    # Good: 5% noise
    assert 0.04 <= test_vector_good.noise_levels[0] <= 0.06

    # Fair: 10% noise
    assert 0.09 <= test_vector_fair.noise_levels[0] <= 0.11


# ============================================================================
# STATISTICAL PROPERTIES TESTS
# ============================================================================

def test_template_entropy():
    """Test that templates have high entropy."""
    # Generate many templates and check aggregate entropy
    templates = [generate_template(seed=1000 + i) for i in range(100)]
    flattened = np.concatenate([t.template for t in templates])

    # Byte-level histogram across all templates
    byte_counts = np.bincount(flattened, minlength=256)

    # Shannon entropy
    probs = byte_counts / byte_counts.sum()
    probs = probs[probs > 0]  # Remove zeros
    entropy = -np.sum(probs * np.log2(probs))

    # Should be close to 8 bits (uniform distribution)
    # Aggregate entropy across many templates should be high
    assert entropy > 7.8, f"Low entropy: {entropy:.2f} bits"


def test_noise_uniformity():
    """Test that noise is uniformly distributed across template."""
    template = generate_template(seed=1000).template
    noisy = add_noise(template, 0.1, seed=2000)

    # Count flips per byte
    diff = np.bitwise_xor(template, noisy)
    flips_per_byte = [bin(byte).count('1') for byte in diff]

    # Should not have all flips in one region
    # (This is a weak test, but sufficient for detecting obvious bugs)
    assert max(flips_per_byte) <= 3, "Noise concentrated in few bytes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
