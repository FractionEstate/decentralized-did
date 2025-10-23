# Hardware-Dependent Tests

This directory contains tests that require specific physical hardware, such as fingerprint scanners, to run. These tests are excluded from the main `pytest` suite by default.

## Purpose

The primary goals of these tests are to:
1.  **Measure Performance**: Evaluate the real-world timing of biometric operations (capture, enrollment, verification) on target hardware.
2.  **Assess Accuracy**: Calculate the False Acceptance Rate (FAR) and False Rejection Rate (FRR) using a large dataset of real fingerprints.
3.  **Validate Compatibility**: Ensure the system works correctly with a variety of common fingerprint sensors.

## Setup

1.  **Install Hardware Drivers**: Ensure that the drivers for your fingerprint scanner are correctly installed and that the device is accessible to the operating system.
2.  **Configure the Test Environment**: You may need to set environment variables to specify the device ID or connection parameters for your sensor.
    ```bash
    export FINGERPRINT_SENSOR_DEVICE="<your_device_id>"
    ```
3.  **Install Dependencies**: The hardware tests may have additional dependencies.
    ```bash
    pip install -r tests/hardware/requirements.txt
    ```

## Running the Tests

Run each test script individually.

### Performance Test
This test measures the execution time of core biometric functions.

```bash
python tests/hardware/performance_test.py
```

### Accuracy Test
This test requires a large, structured dataset of fingerprint images to calculate FAR and FRR. The dataset should be organized by subject and finger.

```bash
python tests/hardware/accuracy_test.py --dataset /path/to/fingerprint/dataset
```

Refer to the individual test files for more detailed instructions and configuration options.
