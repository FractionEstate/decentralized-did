from tests.test_data_generator import (
    SyntheticTemplate,
    TestVector,
    BenchmarkDataset,
    load_test_vector,
    load_benchmark_dataset,
)
import sys
from pathlib import Path
from typing import Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# ============================================================================
# TEST DATA FIXTURES (Phase 2, Task 5)
# ============================================================================

# Import test data generator utilities


# Directory paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
VECTORS_DIR = FIXTURES_DIR / "vectors"
ADVERSARIAL_DIR = FIXTURES_DIR / "adversarial"
BENCHMARKS_DIR = FIXTURES_DIR / "benchmarks"


# ============================================================================
# TEST VECTOR FIXTURES
# ============================================================================

@pytest.fixture
def test_vectors_single() -> List[TestVector]:
    """Load single-finger test vectors."""
    vectors = []
    for file in sorted(VECTORS_DIR.glob("single_finger_*.json")):
        vectors.append(load_test_vector(file))
    return vectors


@pytest.fixture
def test_vectors_multi4() -> Dict[str, List[TestVector]]:
    """Load multi-finger (4 fingers) test vectors."""
    vectors_by_case = {}
    for file in sorted(VECTORS_DIR.glob("multi4_*.json")):
        parts = file.stem.split("_")
        case_id = "_".join(parts[:2])
        if case_id not in vectors_by_case:
            vectors_by_case[case_id] = []
        vectors_by_case[case_id].append(load_test_vector(file))
    return vectors_by_case


@pytest.fixture
def test_vector_clean() -> TestVector:
    """Single test vector with minimal noise (2%)."""
    return load_test_vector(VECTORS_DIR / "single_finger_000.json")


@pytest.fixture
def test_vector_good() -> TestVector:
    """Single test vector with moderate noise (5%)."""
    return load_test_vector(VECTORS_DIR / "single_finger_001.json")


@pytest.fixture
def test_vector_fair() -> TestVector:
    """Single test vector with higher noise (10%)."""
    return load_test_vector(VECTORS_DIR / "single_finger_002.json")


# ============================================================================
# ADVERSARIAL CASE FIXTURES
# ============================================================================

@pytest.fixture
def adversarial_cases() -> List[TestVector]:
    """Load all adversarial test cases."""
    cases = []
    for file in sorted(ADVERSARIAL_DIR.glob("*.json")):
        cases.append(load_test_vector(file))
    return cases


@pytest.fixture
def adversarial_high_noise() -> TestVector:
    """Adversarial case with high noise (should fail)."""
    return load_test_vector(ADVERSARIAL_DIR / "adv001_high_noise.json")


@pytest.fixture
def adversarial_boundary() -> TestVector:
    """Adversarial case at BCH error correction boundary."""
    return load_test_vector(ADVERSARIAL_DIR / "adv002_boundary.json")


@pytest.fixture
def adversarial_poor_quality() -> TestVector:
    """Adversarial case with poor quality template."""
    return load_test_vector(ADVERSARIAL_DIR / "adv003_poor_quality.json")


@pytest.fixture
def adversarial_wrong_finger() -> TestVector:
    """Adversarial case with wrong finger (should fail)."""
    return load_test_vector(ADVERSARIAL_DIR / "adv004_wrong_finger.json")


# ============================================================================
# BENCHMARK DATASET FIXTURES
# ============================================================================

@pytest.fixture
def benchmark_small() -> BenchmarkDataset:
    """Small benchmark (100 users, 4 fingers = 400 templates)."""
    return load_benchmark_dataset(BENCHMARKS_DIR / "bench_100.json")


@pytest.fixture
def benchmark_medium() -> BenchmarkDataset:
    """Medium benchmark (1000 users, 4 fingers = 4000 templates)."""
    return load_benchmark_dataset(BENCHMARKS_DIR / "bench_1000.json")


@pytest.fixture
def benchmark_large() -> BenchmarkDataset:
    """Large benchmark (10000 users, 2 fingers = 20000 templates)."""
    return load_benchmark_dataset(BENCHMARKS_DIR / "bench_10000.json")


# ============================================================================
# TEMPLATE FIXTURES
# ============================================================================

@pytest.fixture
def synthetic_template_high_quality() -> SyntheticTemplate:
    """Single high-quality synthetic template."""
    vector = load_test_vector(VECTORS_DIR / "single_finger_000.json")
    return vector.enrollment_template


@pytest.fixture
def synthetic_template_low_quality() -> SyntheticTemplate:
    """Single low-quality synthetic template."""
    case = load_test_vector(ADVERSARIAL_DIR / "adv003_poor_quality.json")
    return case.enrollment_template


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def fixtures_dir() -> Path:
    """Get fixtures directory path."""
    return FIXTURES_DIR


@pytest.fixture
def all_test_vectors() -> List[TestVector]:
    """Load ALL test vectors (single + multi + adversarial)."""
    vectors = []
    for file in sorted(VECTORS_DIR.glob("*.json")):
        vectors.append(load_test_vector(file))
    for file in sorted(ADVERSARIAL_DIR.glob("*.json")):
        vectors.append(load_test_vector(file))
    return vectors


@pytest.fixture
def all_benchmarks() -> List[BenchmarkDataset]:
    """Load ALL benchmark datasets."""
    benchmarks = []
    for file in sorted(BENCHMARKS_DIR.glob("*.json")):
        benchmarks.append(load_benchmark_dataset(file))
    return benchmarks
