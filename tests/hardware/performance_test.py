"""
Hardware Performance Test

This script measures the performance of the core biometric operations using a
connected fingerprint scanner. It provides timings for:
- Minutiae extraction from a captured image
- Enrollment (generating a DID and helper data)
- Verification (re-creating the key from a new fingerprint)

Usage:
1. Ensure a fingerprint scanner is connected and drivers are installed.
2. Set the FINGERPRINT_SENSOR_DEVICE environment variable if needed.
3. Run the script: `python tests/hardware/performance_test.py`
"""

from decentralized_did.biometrics.feature_extractor import FingerTemplate, minutiae_from_dicts
from decentralized_did.biometrics.fuzzy_extractor import FuzzyExtractor
from decentralized_did.did.generator import generate_deterministic_did
import os
import time
import statistics
from typing import List, Dict, Any, Tuple

# This is a placeholder for a real fingerprint sensor library
# You would replace this with the actual library for your hardware
# e.g., from pyfingerprint.pyfingerprint import PyFingerprint


class MockFingerprintSensor:
    """A mock sensor for demonstration purposes."""

    def __init__(self, port):
        print(f"INFO: Initializing mock sensor on port '{port}'.")
        self.port = port
        # Simulate some known minutiae data
        self.mock_minutiae = [
            (100, 150, 0.5, 0.8, 1),
            (120, 200, 0.6, 0.9, 1),
            (80, 250, 0.7, 0.7, 1),
        ] * 10  # Multiply to get a realistic number

    def read_image(self) -> bool:
        """Simulates reading an image from the sensor."""
        print("INFO: Please place your finger on the mock sensor...")
        time.sleep(1)  # Simulate capture time
        print("INFO: Mock image captured.")
        return True

    def get_minutiae(self) -> List[Dict[str, Any]]:
        """Simulates extracting minutiae from the captured image."""
        print("INFO: Extracting minutiae from mock image...")
        time.sleep(0.05)  # Simulate processing time
        minutiae_list = []
        for i, (x, y, angle, quality, m_type) in enumerate(self.mock_minutiae):
            minutiae_list.append({
                "x": x + (i % 5),  # Add slight variation
                "y": y + (i % 5),
                "angle": angle,
                "quality": quality,
                "type": m_type,
            })
        return minutiae_list


def get_sensor():
    """Initializes and returns a fingerprint sensor instance."""
    try:
        # Replace this with the actual sensor initialization
        # device_port = os.getenv("FINGERPRINT_SENSOR_DEVICE", "/dev/ttyUSB0")
        # sensor = PyFingerprint(device_port)
        # if not sensor.verify_password():
        #     raise ValueError("Fingerprint sensor password incorrect.")
        sensor = MockFingerprintSensor(
            os.getenv("FINGERPRINT_SENSOR_DEVICE", "mock"))
        return sensor
    except Exception as e:
        print(f"ERROR: Failed to initialize fingerprint sensor: {e}")
        print("Please ensure the sensor is connected and drivers are installed.")
        exit(1)


def capture_minutiae(sensor) -> Tuple[List[Dict[str, Any]], float]:
    """Captures a fingerprint and extracts minutiae."""
    start_time = time.perf_counter()
    while not sensor.read_image():
        pass
    minutiae = sensor.get_minutiae()
    end_time = time.perf_counter()
    capture_duration = end_time - start_time
    print(
        f"INFO: Minutiae extraction completed in {capture_duration:.4f} seconds.")
    return minutiae, capture_duration


def run_performance_test(iterations: int = 10):
    """
    Runs a performance benchmark test for enrollment and verification.
    """
    print("--- Starting Hardware Performance Test ---")
    sensor = get_sensor()
    extractor = FuzzyExtractor()

    capture_times = []
    enrollment_times = []
    verification_times = []

    # --- Enrollment Run ---
    print("\n--- Step 1: Enrollment Performance ---")
    print(f"Capturing first fingerprint for enrollment...")
    minutiae1_dicts, capture_time = capture_minutiae(sensor)
    capture_times.append(capture_time)

    start_enroll = time.perf_counter()
    template1 = FingerTemplate("finger1", minutiae_from_dicts(minutiae1_dicts))
    commitment1, helper_data = extractor.generate(template1)
    did = generate_deterministic_did(commitment1)
    end_enroll = time.perf_counter()
    enrollment_time = end_enroll - start_enroll
    enrollment_times.append(enrollment_time)

    print(f"\nEnrollment complete in {enrollment_time:.4f} seconds.")
    print(f"  - DID: {did}")
    print(f"  - Helper Data Size: {len(str(helper_data))}")

    # --- Verification Runs ---
    print(
        f"\n--- Step 2: Verification Performance ({iterations} iterations) ---")
    for i in range(iterations):
        print(f"\nIteration {i + 1}/{iterations}")
        print("Capturing second fingerprint for verification...")
        minutiae2_dicts, capture_time = capture_minutiae(sensor)
        capture_times.append(capture_time)

        start_verify = time.perf_counter()
        template2 = FingerTemplate(
            "finger1", minutiae_from_dicts(minutiae2_dicts))
        recreated_commitment = extractor.reproduce(template2, helper_data)
        recreated_did = generate_deterministic_did(recreated_commitment)
        end_verify = time.perf_counter()
        verification_time = end_verify - start_verify
        verification_times.append(verification_time)

        print(f"Verification complete in {verification_time:.4f} seconds.")
        if recreated_did == did:
            print("  - Result: SUCCESS (DID matched)")
        else:
            print("  - Result: FAILURE (DID did not match)")

    # --- Results Summary ---
    print("\n--- Performance Summary ---")
    print(f"Capture Time (avg):   {statistics.mean(capture_times):.4f}s")
    print(f"Enrollment Time (avg): {statistics.mean(enrollment_times):.4f}s")
    print(
        f"Verification Time (avg): {statistics.mean(verification_times):.4f}s")
    print("---------------------------\n")


def test_run_performance_test(iterations: int = 10):
    """
    Runs a performance benchmark test for enrollment and verification.
    """
    run_performance_test(iterations)


if __name__ == "__main__":
    run_performance_test()
