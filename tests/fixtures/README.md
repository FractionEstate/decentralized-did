# Test Fixtures Directory

This directory contains synthetic test data for the Decentralized DID project.

**Phase 2, Task 5 - Comprehensive Test Data Sets**

## Structure

```
fixtures/
├── vectors/          # Known-good enrollment/verification pairs
├── adversarial/      # Challenging test cases
├── benchmarks/       # Performance benchmark datasets
└── README.md         # This file
```

## Dataset Categories

### 1. Test Vectors (`vectors/`)

Known-good test cases for enrollment and verification testing.

**Single Finger Vectors** (`single_finger_*.json`):
- `single_finger_000.json` - Excellent quality (2% noise)
- `single_finger_001.json` - Good quality (5% noise)
- `single_finger_002.json` - Fair quality (10% noise)

**Multi-Finger Vectors** (`multi4_*.json`):
- 3 test cases, each with 4 fingers
- Files named: `multi4_XXX_<finger_id>.json`
- Grouped by case ID (e.g., `multi4_000_*`)

### 2. Adversarial Cases (`adversarial/`)

Challenging test cases designed to test error handling and boundary conditions.

- `adv001_high_noise.json` - High noise (20-30%), should fail verification
- `adv002_boundary.json` - At BCH error correction boundary (~12-14% noise)
- `adv003_poor_quality.json` - Poor quality template (quality < 50)
- `adv004_wrong_finger.json` - Different finger for verification, should fail

### 3. Benchmark Datasets (`benchmarks/`)

Performance and scalability testing datasets.

- `bench_100.json` - 100 users, 4 fingers = 400 templates (~1.5 MB)
- `bench_1000.json` - 1,000 users, 4 fingers = 4,000 templates (~15 MB)
- `bench_10000.json` - 10,000 users, 2 fingers = 20,000 templates (~75 MB)

## Data Format

### TestVector Format

```json
{
  "vector_id": "vec_single_000",
  "user_id": "user_000",
  "enrollment_template": {
    "finger_id": "left_thumb",
    "template": [/* 512-bit array */],
    "quality": 85,
    "user_id": "user_000",
    "seed": 1000
  },
  "verification_templates": [
    {
      "finger_id": "left_thumb",
      "template": [/* noisy 512-bit array */],
      "quality": 83,
      "user_id": "user_000",
      "seed": 1001
    }
  ],
  "noise_levels": [0.02],
  "expected_match": true,
  "description": "Single finger, 2% noise"
}
```

### BenchmarkDataset Format

```json
{
  "dataset_id": "bench_100",
  "num_users": 100,
  "num_fingers_per_user": 4,
  "templates": [/* array of SyntheticTemplate objects */],
  "description": "Small benchmark: 100 users, 4 fingers each"
}
```

## Reproducibility

All test data is generated with **fixed random seeds** for reproducibility:

- Single finger vectors: seeds 1000-1002
- Multi-finger vectors: seeds 2000-4999 (case_id * 1000 + finger_index)
- Adversarial cases: seeds 10001-10999
- Small benchmark: seeds 20000-29999
- Medium benchmark: seeds 30000-39999
- Large benchmark: seeds 40000-49999

To regenerate all data:

```bash
python tests/test_data_generator.py
```

## Usage in Tests

Load fixtures using pytest fixtures from `tests/conftest.py`:

```python
def test_enrollment(test_vector_clean):
    """Test enrollment with clean data."""
    template = test_vector_clean.enrollment_template
    # Use template for testing...

def test_multi_finger(test_vectors_multi4):
    """Test multi-finger scenarios."""
    for case_id, vectors in test_vectors_multi4.items():
        # Use vectors for testing...
        assert len(vectors) == 4  # 4 fingers per case
```

Available fixtures:
- `test_vectors_single` - All single-finger vectors
- `test_vectors_multi4` - All multi-finger (4) vectors
- `test_vector_clean` - Single clean vector (2% noise)
- `test_vector_good` - Single good vector (5% noise)
- `test_vector_fair` - Single fair vector (10% noise)
- `adversarial_cases` - All adversarial cases
- `adversarial_high_noise` - High noise case
- `adversarial_boundary` - BCH boundary case
- `adversarial_poor_quality` - Poor quality case
- `adversarial_wrong_finger` - Wrong finger case
- `benchmark_small` - Small benchmark (400 templates)
- `benchmark_medium` - Medium benchmark (4K templates)
- `benchmark_large` - Large benchmark (20K templates)
- `synthetic_template_high_quality` - Single high-quality template
- `synthetic_template_low_quality` - Single low-quality template
- `fixtures_dir` - Path to fixtures directory
- `all_test_vectors` - ALL test vectors (use with caution)
- `all_benchmarks` - ALL benchmarks (use with caution)

## Data Properties

### Template Characteristics

- **Size**: 512 bits (64 bytes) per template
- **Distribution**: Uniform random (0-255 per byte)
- **Noise Model**: Random bit flips
- **Quality Range**: 0-100 (NFIQ-like)

### Noise Levels

| Level | Noise % | Description | Expected Result |
|-------|---------|-------------|-----------------|
| Clean | 0% | Perfect match | ✅ Always succeeds |
| Excellent | 2% | ~10 bits flipped | ✅ Always succeeds |
| Good | 5% | ~26 bits flipped | ✅ Always succeeds |
| Fair | 10% | ~51 bits flipped | ✅ Usually succeeds |
| Poor | 15% | ~77 bits flipped | ⚠️ May fail |
| High | 20% | ~102 bits flipped | ❌ Usually fails |
| Extreme | 30% | ~154 bits flipped | ❌ Always fails |

### BCH Error Correction Capacity

The fuzzy extractor uses BCH(255, 131, 18) codes:
- **Error correction capacity**: Up to 18 bit errors per 255-bit block
- **Threshold**: ~7% error rate per block
- **Multi-block**: 512 bits = 2 BCH blocks (independent correction)

## Statistics

Generated datasets:
- **Test vectors**: 15 files (~60 KB)
  - Single finger: 3 files
  - Multi-finger (4): 12 files (3 cases × 4 fingers)
- **Adversarial cases**: 4 files (~16 KB)
- **Benchmarks**: 3 files (~91 MB total)
  - Small: ~1.5 MB (400 templates)
  - Medium: ~15 MB (4,000 templates)
  - Large: ~75 MB (20,000 templates)

## Maintenance

To update test data:

1. Edit `tests/test_data_generator.py`
2. Run: `python tests/test_data_generator.py`
3. Verify: `pytest tests/` (ensure all tests pass)
4. Commit: Changes to `tests/fixtures/`

## License

Copyright 2025 Decentralized DID Project
Licensed under Apache License 2.0
