#!/usr/bin/env python3
"""
Performance Benchmark for Biometric DID API

Measures enrollment and verification latency against the API servers.
Targets: <100ms enrollment, <50ms verification.

Usage:
    python benchmark_api.py --server http://localhost:8000 --iterations 100

Requirements:
    pip install httpx aiofiles
"""

import asyncio
import time
import statistics
import argparse
from typing import List, Dict, Any
import httpx
import json


class APIPerformanceBenchmark:
    """Benchmark biometric DID API performance."""

    def __init__(self, server_url: str, iterations: int = 100):
        self.server_url = server_url.rstrip('/')
        self.iterations = iterations
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def generate_test_fingerprint(self, finger_id: str, seed: int) -> Dict[str, Any]:
        """Generate deterministic test fingerprint data."""
        # Create reproducible minutiae based on seed
        import hashlib
        hasher = hashlib.sha256(f"{finger_id}:{seed}".encode())
        digest = hasher.digest()

        # Generate 10-15 minutiae points
        minutiae = []
        for i in range(10 + (digest[0] % 6)):  # 10-15 points
            x = int.from_bytes(digest[i*3:i*3+2], 'big') % 1000 / 10.0
            y = int.from_bytes(digest[i*3+1:i*3+3], 'big') % 1000 / 10.0
            angle = (digest[i] / 255.0) * 360.0
            minutiae.append([x, y, angle])

        return {
            "finger_id": finger_id,
            "minutiae": minutiae
        }

    async def benchmark_enrollment(self) -> Dict[str, Any]:
        """Benchmark DID enrollment performance."""
        latencies = []

        for i in range(self.iterations):
            # Generate test data
            fingers = [
                self.generate_test_fingerprint("left_thumb", i),
                self.generate_test_fingerprint("left_index", i),
                self.generate_test_fingerprint("right_thumb", i),
                self.generate_test_fingerprint("right_index", i),
            ]

            request_data = {
                "fingers": fingers,
                "wallet_address": f"addr_test1{i:04d}...",
                "storage": "inline",
                "format": "json"
            }

            start_time = time.perf_counter()
            try:
                response = await self.client.post(
                    f"{self.server_url}/api/biometric/generate",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                latency = time.perf_counter() - start_time
                latencies.append(latency * 1000)  # Convert to ms
            except Exception as e:
                print(f"Enrollment {i} failed: {e}")
                continue

        if not latencies:
            return {"error": "No successful enrollments"}

        return {
            "operation": "enrollment",
            "iterations": len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "mean_latency_ms": statistics.mean(latencies),
            "median_latency_ms": statistics.median(latencies),
            # 95th percentile
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18],
            "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            "target_ms": 100,
            "within_target": statistics.mean(latencies) < 100
        }

    async def benchmark_verification(self) -> Dict[str, Any]:
        """Benchmark DID verification performance."""
        latencies = []

        # First, enroll a DID to get verification data
        fingers = [
            self.generate_test_fingerprint("left_thumb", 999),
            self.generate_test_fingerprint("right_thumb", 999),
        ]

        enroll_request = {
            "fingers": fingers,
            "wallet_address": "addr_test1_verify...",
            "storage": "inline",
            "format": "json"
        }

        enroll_response = await self.client.post(
            f"{self.server_url}/api/biometric/generate",
            json=enroll_request,
            headers={"Content-Type": "application/json"}
        )
        enroll_response.raise_for_status()
        enroll_data = enroll_response.json()

        # Extract verification data
        helpers = enroll_data["helpers"]
        expected_id_hash = enroll_data["id_hash"]

        for i in range(self.iterations):
            # Use same fingers for verification
            verify_request = {
                "fingers": fingers,
                "helpers": helpers,
                "expected_id_hash": expected_id_hash
            }

            start_time = time.perf_counter()
            try:
                response = await self.client.post(
                    f"{self.server_url}/api/biometric/verify",
                    json=verify_request,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                latency = time.perf_counter() - start_time
                latencies.append(latency * 1000)  # Convert to ms
            except Exception as e:
                print(f"Verification {i} failed: {e}")
                continue

        if not latencies:
            return {"error": "No successful verifications"}

        return {
            "operation": "verification",
            "iterations": len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "mean_latency_ms": statistics.mean(latencies),
            "median_latency_ms": statistics.median(latencies),
            "p95_latency_ms": statistics.quantiles(latencies, n=20)[18],
            "p99_latency_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            "target_ms": 50,
            "within_target": statistics.mean(latencies) < 50
        }

    async def run_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return results."""
        print(
            f"🚀 Starting API performance benchmarks against {self.server_url}")
        print(f"   Iterations: {self.iterations}")
        print()

        results = {}

        print("📝 Benchmarking enrollment...")
        enrollment_results = await self.benchmark_enrollment()
        results["enrollment"] = enrollment_results
        if "error" not in enrollment_results:
            print(
                f"   Mean: {enrollment_results.get('mean_latency_ms', 'N/A'):.1f}ms")
            print(
                f"   P95:  {enrollment_results.get('p95_latency_ms', 'N/A'):.1f}ms")
            print(
                f"   Target: <{enrollment_results.get('target_ms', 'N/A')}ms")
            print(
                f"   ✅ Within target: {enrollment_results.get('within_target', False)}")
        else:
            print(f"   Error: {enrollment_results['error']}")
        print()

        print("🔍 Benchmarking verification...")
        verification_results = await self.benchmark_verification()
        results["verification"] = verification_results
        if "error" not in verification_results:
            print(
                f"   Mean: {verification_results.get('mean_latency_ms', 'N/A'):.1f}ms")
            print(
                f"   P95:  {verification_results.get('p95_latency_ms', 'N/A'):.1f}ms")
            print(
                f"   Target: <{verification_results.get('target_ms', 'N/A')}ms")
            print(
                f"   ✅ Within target: {verification_results.get('within_target', False)}")
        else:
            print(f"   Error: {verification_results['error']}")
        print()

        # Summary
        enrollment_ok = enrollment_results.get("within_target", False)
        verification_ok = verification_results.get("within_target", False)

        results["summary"] = {
            "enrollment_target_met": enrollment_ok,
            "verification_target_met": verification_ok,
            "overall_success": enrollment_ok and verification_ok,
            "timestamp": time.time(),
            "server_url": self.server_url,
            "iterations": self.iterations
        }

        if results["summary"]["overall_success"]:
            print("🎉 All performance targets met!")
        else:
            print("⚠️  Some performance targets not met - optimization needed")

        return results


async def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Biometric DID API performance")
    parser.add_argument("--server", default="http://localhost:8000",
                        help="API server URL (default: http://localhost:8000)")
    parser.add_argument("--iterations", type=int, default=50,
                        help="Number of iterations per benchmark (default: 50)")
    parser.add_argument("--output", help="Output results to JSON file")

    args = parser.parse_args()

    async with APIPerformanceBenchmark(args.server, args.iterations) as benchmark:
        results = await benchmark.run_benchmarks()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
