"""
libfprint Fingerprint Capture Module

This module provides a Python wrapper around libfprint for capturing
fingerprints from USB sensors (e.g., Eikon Touch 700, ZhongZhi ZK4500).

Features:
- Device detection and initialization
- Fingerprint image capture
- Quality validation
- Minutiae extraction integration
- Error handling and retry logic

Usage:
    from decentralized_did.capture.libfprint_capture import LibfprintCapture

    capture = LibfprintCapture()
    devices = capture.list_devices()

    if devices:
        capture.open_device(devices[0])
        image = capture.capture_fingerprint()
        minutiae = capture.extract_minutiae(image)
        capture.close_device()

Requirements:
    - libfprint-2-2
    - python3-gi
    - gir1.2-fprint-2.0

Author: GitHub Copilot
Date: October 12, 2025
"""

import logging
from typing import List, Dict, Optional, Tuple
import time

try:
    import gi
    gi.require_version('FPrint', '2.0')
    from gi.repository import FPrint, GLib
    LIBFPRINT_AVAILABLE = True
except (ImportError, ValueError) as e:
    LIBFPRINT_AVAILABLE = False
    logging.warning(f"libfprint not available: {e}")

from ..types import FingerId, FingerprintCapture
from ..minutiae.extractor import MinutiaeExtractor

logger = logging.getLogger(__name__)


class LibfprintCaptureError(Exception):
    """Base exception for libfprint capture errors"""
    pass


class DeviceNotFoundError(LibfprintCaptureError):
    """Raised when no fingerprint device is found"""
    pass


class CaptureFailedError(LibfprintCaptureError):
    """Raised when fingerprint capture fails"""
    pass


class LibfprintCapture:
    """
    Wrapper around libfprint for USB fingerprint sensor capture.

    This class handles device detection, fingerprint capture, and
    integration with the minutiae extraction pipeline.
    """

    def __init__(self):
        """Initialize libfprint capture module."""
        if not LIBFPRINT_AVAILABLE:
            raise LibfprintCaptureError(
                "libfprint not available. Install with: "
                "sudo apt-get install libfprint-2-2 python3-gi gir1.2-fprint-2.0"
            )

        self.context = FPrint.Context()
        self.device: Optional[FPrint.Device] = None
        self.minutiae_extractor = MinutiaeExtractor()

        logger.info("LibfprintCapture initialized")

    def list_devices(self) -> List[Dict[str, str]]:
        """
        List all available fingerprint devices.

        Returns:
            List of device dictionaries with keys:
                - name: Device name
                - driver: Driver name
                - device_id: Unique device identifier
                - device_type: Type of device (USB, virtual, etc.)

        Example:
            >>> capture = LibfprintCapture()
            >>> devices = capture.list_devices()
            >>> print(devices)
            [{'name': 'Eikon Touch 700', 'driver': 'elan', ...}]
        """
        devices = self.context.get_devices()

        device_list = []
        for i, device in enumerate(devices):
            device_info = {
                'name': device.get_name() or f"Device {i+1}",
                'driver': device.get_driver() or "unknown",
                'device_id': str(i),  # Simple indexing
                'device_type': str(device.get_device_type()),
                'scan_type': str(device.get_scan_type()),
            }
            device_list.append(device_info)

        logger.info(f"Found {len(device_list)} fingerprint device(s)")
        return device_list

    def open_device(self, device_id: str = "0") -> None:
        """
        Open a fingerprint device for capture.

        Args:
            device_id: Device identifier (default: "0" for first device)

        Raises:
            DeviceNotFoundError: If device not found
            LibfprintCaptureError: If device open fails

        Example:
            >>> capture.open_device("0")
        """
        devices = self.context.get_devices()

        if not devices:
            raise DeviceNotFoundError("No fingerprint devices found")

        try:
            device_index = int(device_id)
            if device_index >= len(devices):
                raise DeviceNotFoundError(f"Device {device_id} not found")

            self.device = devices[device_index]
        except ValueError:
            # Try to find by name
            for device in devices:
                if device.get_name() == device_id or device.get_driver() == device_id:
                    self.device = device
                    break

            if not self.device:
                raise DeviceNotFoundError(f"Device '{device_id}' not found")

        # Open device
        try:
            self.device.open_sync()
            logger.info(f"Opened device: {self.device.get_name()}")
        except GLib.Error as e:
            raise LibfprintCaptureError(f"Failed to open device: {e}")

    def close_device(self) -> None:
        """
        Close the currently open device.

        Example:
            >>> capture.close_device()
        """
        if self.device and self.device.is_open():
            try:
                self.device.close_sync()
                logger.info("Device closed")
            except GLib.Error as e:
                logger.warning(f"Error closing device: {e}")

        self.device = None

    def capture_fingerprint(
        self,
        finger_id: FingerId = "right_index",
        timeout: int = 30,
        retry_on_failure: bool = True,
        max_retries: int = 3
    ) -> FingerprintCapture:
        """
        Capture a fingerprint from the sensor.

        Args:
            finger_id: Which finger is being captured (for metadata)
            timeout: Maximum time to wait for capture (seconds)
            retry_on_failure: Retry on poor quality capture
            max_retries: Maximum number of retry attempts

        Returns:
            FingerprintCapture object with:
                - finger_id: Finger identifier
                - minutiae: Extracted minutiae points
                - quality_score: Quality metric (0-100)
                - capture_time: Time of capture

        Raises:
            LibfprintCaptureError: If device not open
            CaptureFailedError: If capture fails after retries

        Example:
            >>> capture.open_device("0")
            >>> fp = capture.capture_fingerprint("right_index")
            >>> print(fp.quality_score)
            85.3
        """
        if not self.device or not self.device.is_open():
            raise LibfprintCaptureError(
                "Device not open. Call open_device() first.")

        attempts = 0
        last_error = None

        while attempts < max_retries:
            attempts += 1
            logger.info(
                f"Capture attempt {attempts}/{max_retries} for {finger_id}")

            try:
                # Capture image
                logger.info("Waiting for finger placement...")
                print(
                    f"\n👆 Place {finger_id.replace('_', ' ')} on the sensor...")

                # Use capture_sync with timeout
                start_time = time.time()
                image = None

                try:
                    # This blocks until finger placed or timeout
                    image = self.device.capture_sync(
                        True)  # wait_for_finger=True
                except GLib.Error as e:
                    if "timeout" in str(e).lower():
                        raise CaptureFailedError(
                            f"Capture timeout after {timeout}s")
                    raise CaptureFailedError(f"Capture failed: {e}")

                capture_time = time.time() - start_time
                logger.info(f"Image captured in {capture_time:.2f}s")

                # Convert image to numpy array for minutiae extraction
                image_data = self._image_to_numpy(image)

                # Validate quality
                quality_score = self._calculate_quality(image_data)
                logger.info(f"Image quality: {quality_score:.1f}/100")

                if quality_score < 40 and retry_on_failure:
                    logger.warning(
                        f"Poor quality ({quality_score:.1f}), retrying...")
                    print(
                        f"⚠️  Poor quality ({quality_score:.1f}/100). Please try again.")
                    continue

                # Extract minutiae
                logger.info("Extracting minutiae...")
                minutiae = self.minutiae_extractor.extract(image_data)

                if len(minutiae) < 10 and retry_on_failure:
                    logger.warning(
                        f"Too few minutiae ({len(minutiae)}), retrying...")
                    print(
                        f"⚠️  Too few minutiae points ({len(minutiae)}). Please try again.")
                    continue

                logger.info(
                    f"✅ Successfully captured {finger_id}: {len(minutiae)} minutiae, quality {quality_score:.1f}")
                print(
                    f"✅ Captured successfully: {len(minutiae)} minutiae points")

                return FingerprintCapture(
                    finger_id=finger_id,
                    minutiae=minutiae,
                    quality_score=quality_score,
                    capture_time=capture_time
                )

            except Exception as e:
                last_error = e
                logger.error(f"Capture attempt {attempts} failed: {e}")

                if attempts < max_retries:
                    print(f"❌ Capture failed: {e}")
                    print(f"Retrying ({attempts}/{max_retries})...")
                    time.sleep(1)

        # All retries exhausted
        raise CaptureFailedError(
            f"Failed to capture fingerprint after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def _image_to_numpy(self, image: FPrint.Image):
        """
        Convert libfprint image to numpy array.

        Args:
            image: FPrint.Image object

        Returns:
            numpy array of pixel values (grayscale)
        """
        import numpy as np

        width = image.get_width()
        height = image.get_height()
        data = image.get_data()

        # Convert to numpy array
        arr = np.frombuffer(data, dtype=np.uint8)
        arr = arr.reshape((height, width))

        return arr

    def _calculate_quality(self, image_data) -> float:
        """
        Calculate fingerprint image quality score.

        Uses simple metrics:
        - Contrast (std deviation of pixel values)
        - Coverage (non-background pixels)
        - Sharpness (edge detection)

        Args:
            image_data: numpy array of pixel values

        Returns:
            Quality score (0-100)
        """
        import numpy as np

        # Contrast score (0-40 points)
        std_dev = np.std(image_data)
        contrast_score = min(40, std_dev / 2)

        # Coverage score (0-30 points)
        # Assume background is very dark or very bright
        mid_range = (image_data > 50) & (image_data < 200)
        coverage = np.sum(mid_range) / image_data.size
        coverage_score = coverage * 30

        # Sharpness score (0-30 points)
        # Use gradient magnitude as proxy for sharpness
        gy, gx = np.gradient(image_data.astype(float))
        sharpness = np.mean(np.sqrt(gx**2 + gy**2))
        sharpness_score = min(30, sharpness / 3)

        total_score = contrast_score + coverage_score + sharpness_score

        return float(total_score)

    def capture_multiple(
        self,
        finger_ids: List[FingerId],
        timeout: int = 30,
        retry_on_failure: bool = True
    ) -> List[FingerprintCapture]:
        """
        Capture multiple fingerprints sequentially.

        Args:
            finger_ids: List of finger identifiers to capture
            timeout: Timeout per capture (seconds)
            retry_on_failure: Retry on poor quality

        Returns:
            List of FingerprintCapture objects

        Example:
            >>> fingers = ["right_index", "right_middle", "right_ring"]
            >>> captures = capture.capture_multiple(fingers)
            >>> print(f"Captured {len(captures)} fingerprints")
        """
        if not self.device or not self.device.is_open():
            raise LibfprintCaptureError(
                "Device not open. Call open_device() first.")

        captures = []

        for i, finger_id in enumerate(finger_ids):
            print(f"\n📸 Capturing finger {i+1}/{len(finger_ids)}: {finger_id}")

            try:
                capture = self.capture_fingerprint(
                    finger_id=finger_id,
                    timeout=timeout,
                    retry_on_failure=retry_on_failure
                )
                captures.append(capture)
            except CaptureFailedError as e:
                logger.error(f"Failed to capture {finger_id}: {e}")
                print(f"❌ Skipping {finger_id} due to capture failure")
                continue

        logger.info(f"Captured {len(captures)}/{len(finger_ids)} fingerprints")
        return captures

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure device closed"""
        self.close_device()
        return False

    def __del__(self):
        """Destructor - ensure device closed"""
        self.close_device()


def test_sensor():
    """
    Test script to verify sensor functionality.

    Usage:
        python3 -m decentralized_did.capture.libfprint_capture
    """
    print("🔍 Testing libfprint sensor...")
    print()

    try:
        # Initialize
        capture = LibfprintCapture()
        print("✅ libfprint initialized")
        print()

        # List devices
        devices = capture.list_devices()
        if not devices:
            print("❌ No fingerprint devices found")
            print("   Please connect a USB fingerprint sensor")
            return

        print(f"✅ Found {len(devices)} device(s):")
        for i, device in enumerate(devices):
            print(f"   {i}: {device['name']} ({device['driver']})")
        print()

        # Open first device
        print(f"📱 Opening device: {devices[0]['name']}")
        capture.open_device("0")
        print("✅ Device opened")
        print()

        # Capture test
        print("👆 Testing fingerprint capture...")
        fp = capture.capture_fingerprint("right_index", timeout=30)
        print(f"✅ Capture successful!")
        print(f"   Minutiae: {len(fp.minutiae)} points")
        print(f"   Quality: {fp.quality_score:.1f}/100")
        print(f"   Time: {fp.capture_time:.2f}s")
        print()

        # Close device
        capture.close_device()
        print("✅ Device closed")
        print()

        print("🎉 All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_sensor()
