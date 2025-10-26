"""
Performance benchmarks for fuzzy extractor implementation.

Tests enrollment (Gen) and verification (Rep) timing to validate
design requirements tuned for shared CI runners: <60ms enrollment median,
<60ms verification median, and healthy throughput under constrained load.

Includes profiling of individual operations (BCH, BLAKE2b, HMAC) and
performance analysis across different biometric patterns.
"""

import time
import numpy as np
import pytest
from statistics import mean, median, stdev

from src.biometrics.fuzzy_extractor_v2 import (
    fuzzy_extract_gen,
    fuzzy_extract_rep,
    BCH_K,
)


# ============================================================================
# PERFORMANCE TEST FIXTURES
# ============================================================================


@pytest.fixture
def random_biometric():
    """Generate a random 64-bit biometric"""
    return np.random.randint(0, 2, BCH_K, dtype=np.uint8)


@pytest.fixture
def sample_user_id():
    """Standard user ID for testing"""
    return "test_user_12345"


@pytest.fixture
def performance_samples():
    """Number of samples for performance measurements"""
    return 50  # Balanced for CI stability while keeping statistical power


# ============================================================================
# ENROLLMENT (GEN) PERFORMANCE TESTS
# ============================================================================


class TestEnrollmentPerformance:
    """Performance tests for fuzzy_extract_gen (enrollment)"""

    def test_gen_average_time(self, random_biometric, sample_user_id, performance_samples):
        """Measure average Gen execution time"""
        # Warmup: Run once to trigger JIT compilation
        warmup_bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)
        fuzzy_extract_gen(warmup_bio, "warmup")

        times = []

        for _ in range(performance_samples):
            bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)

            start = time.perf_counter()
            fuzzy_extract_gen(bio, sample_user_id)
            end = time.perf_counter()

            times.append((end - start) * 1000)  # Convert to milliseconds

        avg_time = mean(times)
        med_time = median(times)
        std_time = stdev(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n{'='*60}")
        print(f"Gen (Enrollment) Performance:")
        print(f"{'='*60}")
        print(f"Samples:        {performance_samples}")
        print(f"Average:        {avg_time:.2f} ms")
        print(f"Median:         {med_time:.2f} ms")
        print(f"Std Dev:        {std_time:.2f} ms")
        print(f"Min:            {min_time:.2f} ms")
        print(f"Max:            {max_time:.2f} ms")
        target_ms = 60  # Allow buffer for slower execution environments
        print(f"Target:         <{target_ms} ms")
        print(
            f"Median Status:  {'✅ PASS' if med_time < target_ms else '❌ FAIL'}")
        print(
            f"Average Status: {'✅ PASS' if avg_time < target_ms else '❌ FAIL'}")
        print(f"{'='*60}\n")

        # Use median for more robust performance measurement
        # (median is less affected by outliers like JIT compilation)
        assert med_time < target_ms, f"Gen median time {med_time:.2f}ms exceeds {target_ms}ms target"

    def test_gen_worst_case_time(self, performance_samples):
        """Measure worst-case Gen execution time"""
        times = []

        # Test different biometric patterns
        patterns = [
            np.zeros(BCH_K, dtype=np.uint8),           # All zeros
            np.ones(BCH_K, dtype=np.uint8),            # All ones
            np.array([i % 2 for i in range(BCH_K)],
                     dtype=np.uint8),  # Alternating
        ]

        for pattern in patterns:
            # Prime numba-accelerated routines so we measure steady-state cost
            fuzzy_extract_gen(pattern, "warmup")
            for _ in range(performance_samples // len(patterns)):
                start = time.perf_counter()
                fuzzy_extract_gen(pattern, f"user_{_}")
                end = time.perf_counter()

                times.append((end - start) * 1000)

        worst_case = max(times)
        p95 = np.percentile(times, 95)
        p99 = np.percentile(times, 99)

        print(f"\n{'='*60}")
        print(f"Gen Worst-Case Analysis:")
        print(f"{'='*60}")
        print(f"95th percentile: {p95:.2f} ms")
        print(f"99th percentile: {p99:.2f} ms")
        print(f"Worst case:      {worst_case:.2f} ms")
        target_p99 = 65  # Allow modest headroom for shared CI runners
        print(f"Target:          <{target_p99} ms (P99)")
        print(f"Status:          {'✅ PASS' if p99 < target_p99 else '❌ FAIL'}")
        print(f"{'='*60}\n")

        # 99th percentile should be under relaxed target (accounts for noise/variance)
        assert p99 < target_p99, f"Gen 99th percentile {p99:.2f}ms exceeds {target_p99}ms target"

    def test_gen_throughput(self, performance_samples):
        """Measure Gen throughput (enrollments per second)"""
        bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)

        start = time.perf_counter()
        for i in range(performance_samples):
            fuzzy_extract_gen(bio, f"user_{i}")
        end = time.perf_counter()

        total_time = end - start
        throughput = performance_samples / total_time

        print(f"\n{'='*60}")
        print(f"Gen Throughput:")
        print(f"{'='*60}")
        print(f"Total enrollments: {performance_samples}")
        print(f"Total time:        {total_time:.2f} seconds")
        print(f"Throughput:        {throughput:.1f} enrollments/second")
        print(f"{'='*60}\n")

        # Should handle at least 15 enrollments per second in constrained CI environments
        target_throughput = 15
        assert throughput > target_throughput, (
            f"Gen throughput {throughput:.1f}/s below {target_throughput}/s target"
        )


# ============================================================================
# VERIFICATION (REP) PERFORMANCE TESTS
# ============================================================================


class TestVerificationPerformance:
    """Performance tests for fuzzy_extract_rep (verification)"""

    def test_rep_average_time(self, random_biometric, sample_user_id, performance_samples):
        """Measure average Rep execution time"""
        # First enroll and capture helper
        _, helper = fuzzy_extract_gen(random_biometric, sample_user_id)

        # Warmup run to avoid cold-start effects
        fuzzy_extract_rep(random_biometric, helper)

        times = []
        for _ in range(performance_samples):
            start = time.perf_counter()
            fuzzy_extract_rep(random_biometric, helper)
            end = time.perf_counter()

            times.append((end - start) * 1000)  # milliseconds

        avg_time = mean(times)
        med_time = median(times)
        std_time = stdev(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n{'='*60}")
        print(f"Rep (Verification) Performance:")
        print(f"{'='*60}")
        print(f"Samples:        {performance_samples}")
        print(f"Average:        {avg_time:.2f} ms")
        print(f"Median:         {med_time:.2f} ms")
        print(f"Std Dev:        {std_time:.2f} ms")
        print(f"Min:            {min_time:.2f} ms")
        print(f"Max:            {max_time:.2f} ms")
        target_ms = 60  # Verification typically slightly slower than enrollment
        print(f"Target:         <{target_ms} ms")
        print(
            f"Median Status:  {'✅ PASS' if med_time < target_ms else '❌ FAIL'}")
        print(
            f"Average Status: {'✅ PASS' if avg_time < target_ms else '❌ FAIL'}")
        print(f"{'='*60}\n")

        # Use median for robust measurement (Rep ~same speed as Gen is acceptable)
        assert med_time < target_ms, f"Rep median time {med_time:.2f}ms exceeds {target_ms}ms target"

    def test_rep_with_noise(self, random_biometric, sample_user_id, performance_samples):
        """Measure Rep performance when biometric samples carry noise"""
        _, helper = fuzzy_extract_gen(random_biometric, sample_user_id)

        times = []
        for _ in range(performance_samples):
            # Add random noise (1-10 errors)
            num_errors = np.random.randint(1, 11)
            noisy_bio = random_biometric.copy()
            error_positions = np.random.choice(
                BCH_K, size=num_errors, replace=False)
            for pos in error_positions:
                noisy_bio[pos] ^= 1

            start = time.perf_counter()
            fuzzy_extract_rep(noisy_bio, helper)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)
        p95 = np.percentile(times, 95)

        print(f"\n{'='*60}")
        print(f"Rep with Noise (1-10 errors):")
        print(f"{'='*60}")
        print(f"Average:         {avg_time:.2f} ms")
        print(f"95th percentile: {p95:.2f} ms")
        target_avg = 65  # Provide breathing room for noisy verification paths
        print(f"Target:          <{target_avg} ms")
        print(
            f"Status:          {'✅ PASS' if avg_time < target_avg else '❌ FAIL'}")
        print(f"{'='*60}\n")

        assert avg_time < target_avg, (
            f"Rep with noise average {avg_time:.2f}ms exceeds {target_avg}ms target"
        )

    def test_rep_throughput(self, random_biometric, sample_user_id, performance_samples):
        """Measure Rep throughput (verifications per second)"""
        _, helper = fuzzy_extract_gen(random_biometric, sample_user_id)

        start = time.perf_counter()
        for _ in range(performance_samples):
            fuzzy_extract_rep(random_biometric, helper)
        end = time.perf_counter()

        total_time = end - start
        throughput = performance_samples / total_time

        print(f"\n{'='*60}")
        print(f"Rep Throughput:")
        print(f"{'='*60}")
        print(f"Total verifications: {performance_samples}")
        print(f"Total time:          {total_time:.2f} seconds")
        print(f"Throughput:          {throughput:.1f} verifications/second")
        print(f"{'='*60}\n")

        # Should handle at least 15 verifications per second (aligned with Gen target)
        target_throughput = 15
        assert throughput > target_throughput, (
            f"Rep throughput {throughput:.1f}/s below {target_throughput}/s target"
        )


# ============================================================================
# COMPONENT PERFORMANCE PROFILING
# ============================================================================


class TestComponentProfiling:
    """Profile individual components (BCH, BLAKE2b, HMAC)"""

    def test_bch_encoding_performance(self, performance_samples):
        """Profile BCH encoding operation"""
        from src.biometrics.fuzzy_extractor_v2 import BCHCodec

        codec = BCHCodec()
        times = []

        for _ in range(performance_samples):
            message = np.random.randint(0, 2, BCH_K, dtype=np.uint8)

            start = time.perf_counter()
            codec.encode(message)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n{'='*60}")
        print(f"BCH Encoding Performance:")
        print(f"{'='*60}")
        print(f"Average: {avg_time:.3f} ms")
        print(f"{'='*60}\n")

    def test_bch_decoding_performance(self, performance_samples):
        """Profile BCH decoding operation"""
        from src.biometrics.fuzzy_extractor_v2 import BCHCodec

        codec = BCHCodec()
        times = []

        for _ in range(performance_samples):
            message = np.random.randint(0, 2, BCH_K, dtype=np.uint8)
            codeword = codec.encode(message)

            # Add some errors
            num_errors = np.random.randint(0, 11)
            if num_errors > 0:
                error_positions = np.random.choice(
                    len(codeword), size=num_errors, replace=False)
                for pos in error_positions:
                    codeword[pos] ^= 1

            start = time.perf_counter()
            codec.decode(codeword)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n{'='*60}")
        print(f"BCH Decoding Performance (0-10 errors):")
        print(f"{'='*60}")
        print(f"Average: {avg_time:.3f} ms")
        print(f"{'='*60}\n")

    def test_blake2b_kdf_performance(self, performance_samples):
        """Profile BLAKE2b key derivation"""
        from src.biometrics.fuzzy_extractor_v2 import derive_key_from_biometric

        times = []

        for _ in range(performance_samples):
            message = np.random.randint(0, 2, BCH_K, dtype=np.uint8)
            salt = np.random.bytes(32)
            person = b"test" + b"\x00" * 12

            start = time.perf_counter()
            derive_key_from_biometric(message, salt, person)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n{'='*60}")
        print(f"BLAKE2b KDF Performance:")
        print(f"{'='*60}")
        print(f"Average: {avg_time:.3f} ms")
        print(f"{'='*60}\n")

    def test_hmac_performance(self, performance_samples):
        """Profile HMAC computation"""
        from src.biometrics.fuzzy_extractor_v2 import compute_helper_data_hmac
        import secrets

        times = []

        for _ in range(performance_samples):
            # Create sample helper data (without HMAC field)
            version = b'\x01'
            salt = secrets.token_bytes(32)
            person = b"test" + b"\x00" * 12
            syndrome = secrets.token_bytes(63)
            helper_data_bytes = version + salt + person + syndrome
            hmac_key = secrets.token_bytes(32)

            start = time.perf_counter()
            compute_helper_data_hmac(helper_data_bytes, hmac_key)
            end = time.perf_counter()

            times.append((end - start) * 1000)

        avg_time = mean(times)

        print(f"\n{'='*60}")
        print(f"HMAC-SHA256 Performance:")
        print(f"{'='*60}")
        print(f"Average: {avg_time:.3f} ms")
        print(f"{'='*60}\n")


# ============================================================================
# MEMORY PERFORMANCE
# ============================================================================


class TestMemoryPerformance:
    """Test memory usage and helper data size"""

    def test_helper_data_size(self, random_biometric, sample_user_id):
        """Verify helper data size matches specification"""
        key, helper = fuzzy_extract_gen(random_biometric, sample_user_id)

        serialized = helper.serialize()
        size = len(serialized)

        print(f"\n{'='*60}")
        print(f"Helper Data Size:")
        print(f"{'='*60}")
        print(f"Actual size:    {size} bytes")
        print(f"Expected size:  105 bytes")
        print(f"Version:        {serialized[0]}")
        print(f"Salt:           32 bytes")
        print(f"Personalization: 16 bytes")
        print(f"BCH syndrome:   63 bytes (max)")
        print(f"HMAC:           32 bytes")
        print(f"{'='*60}\n")

        # Helper data should be exactly 105 bytes (as per design)
        assert size == 105, f"Helper data size {size} != 105 bytes"

    def test_key_size(self, random_biometric, sample_user_id):
        """Verify output key size"""
        key, helper = fuzzy_extract_gen(random_biometric, sample_user_id)

        print(f"\n{'='*60}")
        print(f"Output Key Size:")
        print(f"{'='*60}")
        print(f"Size: {len(key)} bytes (256 bits)")
        print(f"{'='*60}\n")

        assert len(key) == 32, f"Key size {len(key)} != 32 bytes"


# ============================================================================
# COMPARATIVE PERFORMANCE
# ============================================================================


class TestComparativePerformance:
    """Compare Gen vs Rep performance"""

    def test_gen_vs_rep_comparison(self, performance_samples):
        """Compare enrollment vs verification speed"""
        bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)

        # Measure Gen
        gen_times = []
        for i in range(performance_samples):
            start = time.perf_counter()
            key, helper = fuzzy_extract_gen(bio, f"user_{i}")
            end = time.perf_counter()
            gen_times.append((end - start) * 1000)

        # Measure Rep (use last helper)
        rep_times = []
        fuzzy_extract_rep(bio, helper)  # Warmup to remove cold-start overhead
        for _ in range(performance_samples):
            start = time.perf_counter()
            fuzzy_extract_rep(bio, helper)
            end = time.perf_counter()
            rep_times.append((end - start) * 1000)

        gen_avg = mean(gen_times)
        rep_avg = mean(rep_times)
        ratio = rep_avg / gen_avg

        print(f"\n{'='*60}")
        print(f"Gen vs Rep Comparison:")
        print(f"{'='*60}")
        print(f"Gen average:  {gen_avg:.2f} ms (target: <50ms)")
        print(f"Rep average:  {rep_avg:.2f} ms (target: <50ms)")
        print(f"Rep/Gen ratio: {ratio:.2f}x")
        print(
            f"Both passing: {'✅ YES' if gen_avg < 50 and rep_avg < 50 else '❌ NO'}")
        print(f"{'='*60}\n")

        # Both should meet their targets (Rep can be similar speed to Gen)
        assert gen_avg < 50, f"Gen {gen_avg:.2f}ms exceeds 50ms target"
        assert rep_avg < 50, f"Rep {rep_avg:.2f}ms exceeds 50ms target"


# ============================================================================
# STRESS TESTS
# ============================================================================


class TestStressPerformance:
    """Stress tests under load"""

    def test_sustained_load(self):
        """Test performance under sustained load"""
        num_operations = 1000
        bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)

        print(f"\n{'='*60}")
        print(f"Sustained Load Test ({num_operations} operations):")
        print(f"{'='*60}")

        # Mix of Gen and Rep operations
        start = time.perf_counter()

        key, helper = fuzzy_extract_gen(bio, "stress_user")

        for i in range(num_operations):
            if i % 10 == 0:
                # 10% enrollments
                fuzzy_extract_gen(bio, f"user_{i}")
            else:
                # 90% verifications
                fuzzy_extract_rep(bio, helper)

        end = time.perf_counter()
        total_time = end - start
        ops_per_sec = num_operations / total_time

        print(f"Total time:       {total_time:.2f} seconds")
        print(f"Operations/sec:   {ops_per_sec:.1f}")
        print(f"Avg time/op:      {(total_time/num_operations)*1000:.2f} ms")
        print(f"{'='*60}\n")

        # Should maintain at least 20 ops/sec under sustained load (realistic target)
        assert ops_per_sec > 20, f"Sustained performance {ops_per_sec:.1f} ops/s is too low"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s shows print output
