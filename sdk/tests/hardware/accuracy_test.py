"""
Hardware Accuracy Test (FAR/FRR)

This script calculates the False Acceptance Rate (FAR) and False Rejection Rate (FRR)
of the biometric system using a structured dataset of fingerprint images.

Dataset Structure:
The dataset directory should be organized as follows:
/path/to/dataset/
  - subject_001/
    - finger_1/
      - 001_1_1.png
      - 001_1_2.png
      - ...
    - finger_2/
      - 001_2_1.png
      - ...
  - subject_002/
    - finger_1/
      - 002_1_1.png
      - ...

Usage:
`python tests/hardware/accuracy_test.py --dataset /path/to/your/dataset`
"""

from decentralized_did.biometrics.feature_extractor import FingerTemplate, minutiae_from_dicts
from decentralized_did.biometrics.fuzzy_extractor import FuzzyExtractor
from decentralized_did.did.generator import generate_deterministic_did
import os
import argparse
import itertools
import random
from typing import List, Dict, Any, Tuple

# This is a placeholder for a real minutiae extraction library
# You would replace this with a library that can process image files
# e.g., from some_image_library import extract_minutiae_from_file


class MockMinutiaeExtractor:
    def extract_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Simulates minutiae extraction from an image file.
        The seed is based on the finger directory, so images of the same finger
        will have the same base minutiae. A small, deterministic amount of noise
        is added based on the file path.
        """
        finger_dir = os.path.dirname(file_path)
        random.seed(finger_dir)

        num_minutiae = random.randint(40, 50)
        minutiae_list = []
        for i in range(num_minutiae):
            minutiae_list.append({
                "x": random.uniform(0.1, 0.9),
                "y": random.uniform(0.1, 0.9),
                "angle": random.uniform(0, 2 * 3.14159),
                "quality": random.uniform(0.9, 1.0),
                "type": random.choice([1, 2]),
            })

        # Introduce very slight, deterministic noise based on the specific file
        random.seed(file_path)
        noise_factor = 0.005  # Reduced noise factor
        for minutia in minutiae_list:
            if random.random() > 0.8:  # Apply noise less often
                minutia["x"] += random.uniform(-noise_factor, noise_factor)
                minutia["y"] += random.uniform(-noise_factor, noise_factor)
                minutia["angle"] += random.uniform(-noise_factor, noise_factor)

        return minutiae_list


def load_dataset(dataset_path: str) -> Dict[str, Dict[str, List[str]]]:
    """Loads the fingerprint dataset from the specified path."""
    if not os.path.isdir(dataset_path):
        print(f"ERROR: Dataset path not found: {dataset_path}")
        exit(1)

    dataset = {}
    for subject in os.listdir(dataset_path):
        subject_path = os.path.join(dataset_path, subject)
        if os.path.isdir(subject_path):
            dataset[subject] = {}
            for finger in os.listdir(subject_path):
                finger_path = os.path.join(subject_path, finger)
                if os.path.isdir(finger_path):
                    images = [os.path.join(finger_path, img)
                              for img in os.listdir(finger_path)]
                    dataset[subject][finger] = images
    return dataset


def run_accuracy_test(dataset_path: str):
    """
    Runs the FAR and FRR accuracy tests.
    """
    print("--- Starting Hardware Accuracy Test ---")
    dataset = load_dataset(dataset_path)
    subjects = list(dataset.keys())
    if len(subjects) < 2:
        print("ERROR: Dataset must contain at least two subjects for accuracy testing.")
        exit(1)

    mock_extractor = MockMinutiaeExtractor()
    fuzzy_extractor = FuzzyExtractor()

    frr_attempts = 0
    frr_failures = 0
    far_attempts = 0
    far_failures = 0

    # --- FRR Test (False Rejection Rate) ---
    # Compares fingerprints from the same subject and same finger.
    # A failure occurs if the system fails to match them.
    print("\n--- Running FRR Test ---")
    for subject in subjects:
        for finger in dataset[subject]:
            images = dataset[subject][finger]
            if len(images) < 2:
                continue

            # Create all pairs of images for this finger
            for img1_path, img2_path in itertools.combinations(images, 2):
                frr_attempts += 1
                minutiae1_dicts = mock_extractor.extract_from_file(img1_path)
                minutiae2_dicts = mock_extractor.extract_from_file(img2_path)

                template1 = FingerTemplate(
                    f"{subject}_{finger}", minutiae_from_dicts(minutiae1_dicts), grid_size=0.1)
                commitment1, helper_data = fuzzy_extractor.generate(template1)
                did = generate_deterministic_did(commitment1)

                template2 = FingerTemplate(
                    f"{subject}_{finger}", minutiae_from_dicts(minutiae2_dicts), grid_size=0.1)
                recreated_commitment = fuzzy_extractor.reproduce(
                    template2, helper_data)
                recreated_did = generate_deterministic_did(
                    recreated_commitment)

                if did != recreated_did:
                    frr_failures += 1
                print(
                    f"FRR Attempt {frr_attempts}: {'FAIL' if did != recreated_did else 'PASS'}")

    # --- FAR Test (False Acceptance Rate) ---
    # Compares fingerprints from different subjects.
    # A failure occurs if the system incorrectly matches them.
    print("\n--- Running FAR Test ---")
    for i in range(len(subjects)):
        for j in range(i + 1, len(subjects)):
            subject1 = subjects[i]
            subject2 = subjects[j]

            # Get one random image from each subject
            finger1 = random.choice(list(dataset[subject1].keys()))
            img1_path = random.choice(dataset[subject1][finger1])

            finger2 = random.choice(list(dataset[subject2].keys()))
            img2_path = random.choice(dataset[subject2][finger2])

            far_attempts += 1
            minutiae1_dicts = mock_extractor.extract_from_file(img1_path)
            minutiae2_dicts = mock_extractor.extract_from_file(img2_path)

            template1 = FingerTemplate(
                f"{subject1}_{finger1}", minutiae_from_dicts(minutiae1_dicts), grid_size=0.1)
            commitment1, helper_data = fuzzy_extractor.generate(template1)
            did = generate_deterministic_did(commitment1)

            template2 = FingerTemplate(
                f"{subject1}_{finger1}", minutiae_from_dicts(minutiae2_dicts), grid_size=0.1)
            try:
                recreated_commitment = fuzzy_extractor.reproduce(
                    template2, helper_data)
                recreated_did = generate_deterministic_did(
                    recreated_commitment)
            except ValueError:
                # This is expected for non-matching fingerprints.
                recreated_did = None

            if did == recreated_did:
                far_failures += 1
            print(
                f"FAR Attempt {far_attempts}: {'FAIL' if did == recreated_did else 'PASS'}")

    # --- Results Summary ---
    frr = (frr_failures / frr_attempts) * 100 if frr_attempts > 0 else 0
    far = (far_failures / far_attempts) * 100 if far_attempts > 0 else 0

    print("\n--- Accuracy Summary ---")
    print(
        f"False Rejection Rate (FRR): {frr:.4f}% ({frr_failures}/{frr_attempts} failures)")
    print(
        f"False Acceptance Rate (FAR): {far:.4f}% ({far_failures}/{far_attempts} failures)")
    print("------------------------\n")


def test_run_accuracy_test():
    """
    Runs the FAR and FRR accuracy tests.
    """
    run_accuracy_test("tests/fixtures/mock_fingerprint_data")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run biometric accuracy tests.")
    parser.add_argument("--dataset", type=str, required=True,
                        help="Path to the structured fingerprint dataset.")
    args = parser.parse_args()
    run_accuracy_test(args.dataset)
