"""
Test Data Generator for Biometric DID Testing

Generates synthetic fingerprint templates, test vectors, and benchmark datasets
with controlled noise levels, quality scores, and multi-finger scenarios.

Phase 2, Task 5 - Comprehensive Test Data Sets

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np


# ============================================================================
# CONSTANTS
# ============================================================================

# Fingerprint template size (bits)
TEMPLATE_SIZE_BITS = 512  # 64 bytes, realistic for minutiae-based templates

# Noise levels (percentage of bits to flip)
NOISE_LEVEL_CLEAN = 0.00      # Perfect match
NOISE_LEVEL_EXCELLENT = 0.02  # 2% bit flips (excellent quality)
NOISE_LEVEL_GOOD = 0.05       # 5% bit flips (good quality)
NOISE_LEVEL_FAIR = 0.10       # 10% bit flips (fair quality)
NOISE_LEVEL_POOR = 0.15       # 15% bit flips (poor quality)
NOISE_LEVEL_HIGH = 0.20       # 20% bit flips (high noise)
NOISE_LEVEL_EXTREME = 0.30    # 30% bit flips (extreme noise)

# Quality scores (NFIQ-like, 0-100)
QUALITY_EXCELLENT = 95
QUALITY_GOOD = 85
QUALITY_FAIR = 75
QUALITY_POOR = 60
QUALITY_VERY_POOR = 40

# Finger identifiers
FINGER_IDS = [
    "left_thumb", "left_index", "left_middle", "left_ring", "left_pinky",
    "right_thumb", "right_index", "right_middle", "right_ring", "right_pinky",
]


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SyntheticTemplate:
    """Synthetic fingerprint template."""
    finger_id: str
    template: np.ndarray  # 512-bit biometric template
    quality: int  # NFIQ score (0-100)
    user_id: str
    seed: int  # For reproducibility

    def to_dict(self) -> Dict:
        """Convert to dictionary (for JSON serialization)."""
        return {
            "finger_id": self.finger_id,
            "template": self.template.tolist(),
            "quality": self.quality,
            "user_id": self.user_id,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> SyntheticTemplate:
        """Load from dictionary."""
        return cls(
            finger_id=data["finger_id"],
            template=np.array(data["template"], dtype=np.uint8),
            quality=data["quality"],
            user_id=data["user_id"],
            seed=data["seed"],
        )


@dataclass
class TestVector:
    """Known-good enrollment/verification pair."""
    vector_id: str
    user_id: str
    enrollment_template: SyntheticTemplate
    verification_templates: List[SyntheticTemplate]  # Multiple noisy versions
    noise_levels: List[float]
    expected_match: bool
    description: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "vector_id": self.vector_id,
            "user_id": self.user_id,
            "enrollment_template": self.enrollment_template.to_dict(),
            "verification_templates": [t.to_dict() for t in self.verification_templates],
            "noise_levels": self.noise_levels,
            "expected_match": self.expected_match,
            "description": self.description,
        }


@dataclass
class BenchmarkDataset:
    """Performance benchmark dataset."""
    dataset_id: str
    num_users: int
    num_fingers_per_user: int
    templates: List[SyntheticTemplate]
    description: str

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "num_users": self.num_users,
            "num_fingers_per_user": self.num_fingers_per_user,
            "templates": [t.to_dict() for t in self.templates],
            "description": self.description,
        }


# ============================================================================
# SYNTHETIC TEMPLATE GENERATION
# ============================================================================

def generate_template(
    seed: int,
    finger_id: str = "left_thumb",
    user_id: str = "user001",
    quality: int = QUALITY_GOOD,
    template_size_bits: int = TEMPLATE_SIZE_BITS
) -> SyntheticTemplate:
    """
    Generate a synthetic fingerprint template.

    Uses deterministic random generation based on seed for reproducibility.

    Args:
        seed: Random seed for reproducibility
        finger_id: Finger identifier
        user_id: User identifier
        quality: Quality score (0-100)
        template_size_bits: Template size in bits

    Returns:
        SyntheticTemplate instance

    Example:
        >>> template = generate_template(seed=12345, finger_id="left_thumb")
        >>> template.template.shape
        (64,)
        >>> template.quality
        85
    """
    # Set random seed for reproducibility
    np.random.seed(seed)

    # Generate random template (uniform distribution)
    template_bytes = template_size_bits // 8
    template = np.random.randint(0, 256, size=template_bytes, dtype=np.uint8)

    return SyntheticTemplate(
        finger_id=finger_id,
        template=template,
        quality=quality,
        user_id=user_id,
        seed=seed,
    )


def add_noise(
    template: np.ndarray,
    noise_level: float,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Add controlled noise to a template by flipping bits.

    Args:
        template: Original template (numpy array of bytes)
        noise_level: Fraction of bits to flip (0.0 - 1.0)
        seed: Random seed for reproducibility

    Returns:
        Noisy template (same shape as input)

    Example:
        >>> template = np.array([0xFF, 0x00, 0xAA], dtype=np.uint8)
        >>> noisy = add_noise(template, noise_level=0.1, seed=42)
        >>> # Approximately 10% of 24 bits (~2-3 bits) will be flipped
    """
    if seed is not None:
        np.random.seed(seed)

    # Create a copy
    noisy = template.copy()

    # Calculate number of bits to flip
    total_bits = len(template) * 8
    num_flips = int(total_bits * noise_level)

    # Randomly select bits to flip
    for _ in range(num_flips):
        byte_idx = np.random.randint(0, len(template))
        bit_idx = np.random.randint(0, 8)
        noisy[byte_idx] ^= (1 << bit_idx)

    return noisy


def generate_noisy_variant(
    base_template: SyntheticTemplate,
    noise_level: float,
    seed: int
) -> SyntheticTemplate:
    """
    Generate a noisy variant of a template.

    Args:
        base_template: Original template
        noise_level: Noise level (0.0 - 1.0)
        seed: Random seed

    Returns:
        Noisy variant as SyntheticTemplate
    """
    noisy_template = add_noise(base_template.template, noise_level, seed)

    # Quality degrades with noise
    quality_penalty = int(noise_level * 100)
    new_quality = max(0, base_template.quality - quality_penalty)

    return SyntheticTemplate(
        finger_id=base_template.finger_id,
        template=noisy_template,
        quality=new_quality,
        user_id=base_template.user_id,
        seed=seed,
    )


# ============================================================================
# TEST VECTOR GENERATION
# ============================================================================

def generate_test_vector(
    vector_id: str,
    user_id: str,
    finger_id: str,
    enrollment_seed: int,
    noise_levels: List[float],
    quality: int = QUALITY_GOOD,
    expected_match: bool = True,
    description: str = ""
) -> TestVector:
    """
    Generate a test vector (enrollment + verification pairs).

    Args:
        vector_id: Unique identifier
        user_id: User identifier
        finger_id: Finger identifier
        enrollment_seed: Seed for enrollment template
        noise_levels: List of noise levels for verification templates
        quality: Base quality score
        expected_match: Whether verification should succeed
        description: Human-readable description

    Returns:
        TestVector instance

    Example:
        >>> vector = generate_test_vector(
        ...     vector_id="vec001",
        ...     user_id="user001",
        ...     finger_id="left_thumb",
        ...     enrollment_seed=12345,
        ...     noise_levels=[0.02, 0.05, 0.10],
        ...     description="Good quality match"
        ... )
    """
    # Generate enrollment template
    enrollment = generate_template(
        seed=enrollment_seed,
        finger_id=finger_id,
        user_id=user_id,
        quality=quality
    )

    # Generate verification templates with different noise levels
    verification_templates = []
    for i, noise_level in enumerate(noise_levels):
        verify_seed = enrollment_seed + i + 1
        verification = generate_noisy_variant(
            enrollment, noise_level, verify_seed)
        verification_templates.append(verification)

    return TestVector(
        vector_id=vector_id,
        user_id=user_id,
        enrollment_template=enrollment,
        verification_templates=verification_templates,
        noise_levels=noise_levels,
        expected_match=expected_match,
        description=description,
    )


def generate_multi_finger_test_vector(
    vector_id: str,
    user_id: str,
    finger_ids: List[str],
    base_seed: int,
    noise_level: float = NOISE_LEVEL_GOOD,
    quality: int = QUALITY_GOOD,
    description: str = ""
) -> Dict[str, TestVector]:
    """
    Generate test vectors for multiple fingers.

    Args:
        vector_id: Base vector ID (will be suffixed with finger ID)
        user_id: User identifier
        finger_ids: List of finger identifiers
        base_seed: Base seed (will be offset for each finger)
        noise_level: Noise level for verification
        quality: Quality score
        description: Description

    Returns:
        Dictionary mapping finger_id to TestVector
    """
    vectors = {}

    for i, finger_id in enumerate(finger_ids):
        enrollment_seed = base_seed + i * 1000
        vector = generate_test_vector(
            vector_id=f"{vector_id}_{finger_id}",
            user_id=user_id,
            finger_id=finger_id,
            enrollment_seed=enrollment_seed,
            noise_levels=[noise_level],
            quality=quality,
            description=f"{description} - {finger_id}"
        )
        vectors[finger_id] = vector

    return vectors


# ============================================================================
# ADVERSARIAL TEST CASE GENERATION
# ============================================================================

def generate_adversarial_cases() -> List[TestVector]:
    """
    Generate adversarial test cases.

    Returns:
        List of challenging test vectors
    """
    cases = []

    # Case 1: High noise (should fail)
    cases.append(generate_test_vector(
        vector_id="adv001_high_noise",
        user_id="user_adv001",
        finger_id="left_thumb",
        enrollment_seed=10001,
        noise_levels=[NOISE_LEVEL_HIGH, NOISE_LEVEL_EXTREME],
        quality=QUALITY_EXCELLENT,
        expected_match=False,
        description="High noise - should fail verification"
    ))

    # Case 2: Boundary condition (exactly at threshold)
    cases.append(generate_test_vector(
        vector_id="adv002_boundary",
        user_id="user_adv002",
        finger_id="right_index",
        enrollment_seed=10002,
        noise_levels=[0.12, 0.13, 0.14],  # Around BCH threshold
        quality=QUALITY_GOOD,
        expected_match=True,  # Should still match with BCH error correction
        description="Boundary condition - near BCH threshold"
    ))

    # Case 3: Poor quality
    cases.append(generate_test_vector(
        vector_id="adv003_poor_quality",
        user_id="user_adv003",
        finger_id="left_middle",
        enrollment_seed=10003,
        noise_levels=[NOISE_LEVEL_FAIR],
        quality=QUALITY_VERY_POOR,
        expected_match=True,  # Low quality but should still work
        description="Poor quality template"
    ))

    # Case 4: Different finger (should fail)
    enrollment = generate_template(
        10004, "left_thumb", "user_adv004", QUALITY_GOOD)
    wrong_finger = generate_template(
        10005, "right_thumb", "user_adv004", QUALITY_GOOD)
    cases.append(TestVector(
        vector_id="adv004_wrong_finger",
        user_id="user_adv004",
        enrollment_template=enrollment,
        verification_templates=[wrong_finger],
        noise_levels=[0.0],
        expected_match=False,
        description="Wrong finger - should fail"
    ))

    return cases


# ============================================================================
# BENCHMARK DATASET GENERATION
# ============================================================================

def generate_benchmark_dataset(
    dataset_id: str,
    num_users: int,
    num_fingers_per_user: int,
    base_seed: int = 20000,
    quality_range: Tuple[int, int] = (QUALITY_FAIR, QUALITY_EXCELLENT),
    description: str = ""
) -> BenchmarkDataset:
    """
    Generate a performance benchmark dataset.

    Args:
        dataset_id: Dataset identifier
        num_users: Number of users
        num_fingers_per_user: Fingers per user (1-10)
        base_seed: Base random seed
        quality_range: (min_quality, max_quality) range
        description: Dataset description

    Returns:
        BenchmarkDataset instance

    Example:
        >>> dataset = generate_benchmark_dataset(
        ...     dataset_id="bench_100",
        ...     num_users=100,
        ...     num_fingers_per_user=4,
        ...     description="100 users, 4 fingers each"
        ... )
    """
    templates = []

    for user_idx in range(num_users):
        user_id = f"user_{user_idx:05d}"

        for finger_idx in range(num_fingers_per_user):
            finger_id = FINGER_IDS[finger_idx % len(FINGER_IDS)]
            seed = base_seed + user_idx * 100 + finger_idx

            # Random quality within range
            np.random.seed(seed)
            quality = np.random.randint(quality_range[0], quality_range[1] + 1)

            template = generate_template(
                seed=seed,
                finger_id=finger_id,
                user_id=user_id,
                quality=quality
            )
            templates.append(template)

    return BenchmarkDataset(
        dataset_id=dataset_id,
        num_users=num_users,
        num_fingers_per_user=num_fingers_per_user,
        templates=templates,
        description=description,
    )


# ============================================================================
# DATASET PERSISTENCE
# ============================================================================

def save_test_vector(vector: TestVector, filepath: Path) -> None:
    """Save test vector to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(vector.to_dict(), f, indent=2)


def load_test_vector(filepath: Path) -> TestVector:
    """Load test vector from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    enrollment = SyntheticTemplate.from_dict(data["enrollment_template"])
    verification = [
        SyntheticTemplate.from_dict(t)
        for t in data["verification_templates"]
    ]

    return TestVector(
        vector_id=data["vector_id"],
        user_id=data["user_id"],
        enrollment_template=enrollment,
        verification_templates=verification,
        noise_levels=data["noise_levels"],
        expected_match=data["expected_match"],
        description=data["description"],
    )


def save_benchmark_dataset(dataset: BenchmarkDataset, filepath: Path) -> None:
    """Save benchmark dataset to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)


def load_benchmark_dataset(filepath: Path) -> BenchmarkDataset:
    """Load benchmark dataset from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    templates = [SyntheticTemplate.from_dict(t) for t in data["templates"]]

    return BenchmarkDataset(
        dataset_id=data["dataset_id"],
        num_users=data["num_users"],
        num_fingers_per_user=data["num_fingers_per_user"],
        templates=templates,
        description=data["description"],
    )


# ============================================================================
# MAIN GENERATION SCRIPT
# ============================================================================

def generate_all_test_data(output_dir: Path = Path("tests/fixtures")) -> None:
    """
    Generate all test data sets.

    Args:
        output_dir: Output directory for test data
    """
    print("Generating test data sets...")

    # Create directory structure
    synthetic_dir = output_dir / "synthetic"
    vectors_dir = output_dir / "vectors"
    adversarial_dir = output_dir / "adversarial"
    benchmarks_dir = output_dir / "benchmarks"

    for d in [synthetic_dir, vectors_dir, adversarial_dir, benchmarks_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Generate known-good test vectors
    print("  Generating known-good test vectors...")

    # Single finger, various noise levels
    for i, noise_level in enumerate([NOISE_LEVEL_EXCELLENT, NOISE_LEVEL_GOOD, NOISE_LEVEL_FAIR]):
        vector = generate_test_vector(
            vector_id=f"vec_single_{i:03d}",
            user_id=f"user_{i:03d}",
            finger_id="left_thumb",
            enrollment_seed=1000 + i,
            noise_levels=[noise_level],
            quality=QUALITY_GOOD,
            expected_match=True,
            description=f"Single finger, {noise_level*100:.0f}% noise"
        )
        save_test_vector(vector, vectors_dir / f"single_finger_{i:03d}.json")

    # Multi-finger (4 fingers)
    for i in range(3):
        vectors = generate_multi_finger_test_vector(
            vector_id=f"vec_multi4_{i:03d}",
            user_id=f"user_multi_{i:03d}",
            finger_ids=["left_thumb", "left_index",
                        "right_thumb", "right_index"],
            base_seed=2000 + i * 1000,
            noise_level=NOISE_LEVEL_GOOD,
            quality=QUALITY_GOOD,
            description=f"Multi-finger (4) test case {i}"
        )
        for finger_id, vector in vectors.items():
            save_test_vector(
                vector,
                vectors_dir / f"multi4_{i:03d}_{finger_id}.json"
            )

    # 2. Generate adversarial cases
    print("  Generating adversarial test cases...")
    adversarial_cases = generate_adversarial_cases()
    for case in adversarial_cases:
        save_test_vector(case, adversarial_dir / f"{case.vector_id}.json")

    # 3. Generate benchmark datasets
    print("  Generating benchmark datasets...")

    # Small: 100 users, 4 fingers
    bench_small = generate_benchmark_dataset(
        dataset_id="bench_100",
        num_users=100,
        num_fingers_per_user=4,
        description="Small benchmark: 100 users, 4 fingers each (400 templates)"
    )
    save_benchmark_dataset(bench_small, benchmarks_dir / "bench_100.json")

    # Medium: 1000 users, 4 fingers
    bench_medium = generate_benchmark_dataset(
        dataset_id="bench_1000",
        num_users=1000,
        num_fingers_per_user=4,
        base_seed=30000,
        description="Medium benchmark: 1000 users, 4 fingers each (4000 templates)"
    )
    save_benchmark_dataset(bench_medium, benchmarks_dir / "bench_1000.json")

    # Large: 10000 users, 2 fingers (for memory testing)
    bench_large = generate_benchmark_dataset(
        dataset_id="bench_10000",
        num_users=10000,
        num_fingers_per_user=2,
        base_seed=40000,
        description="Large benchmark: 10000 users, 2 fingers each (20000 templates)"
    )
    save_benchmark_dataset(bench_large, benchmarks_dir / "bench_10000.json")

    print(f"✅ Test data generated in {output_dir}")
    print(f"  - Test vectors: {len(list(vectors_dir.glob('*.json')))} files")
    print(
        f"  - Adversarial cases: {len(list(adversarial_dir.glob('*.json')))} files")
    print(
        f"  - Benchmark datasets: {len(list(benchmarks_dir.glob('*.json')))} files")


if __name__ == "__main__":
    # Generate all test data
    generate_all_test_data()
