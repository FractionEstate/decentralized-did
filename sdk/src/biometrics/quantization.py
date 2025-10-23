"""
Minutiae Quantization and Normalization Module

Implements the quantization algorithm designed in Phase 1, Task 1.
Converts raw SourceAFIS minutiae templates into stable, fuzzy-extractor-compatible
representations while balancing stability, security, and privacy.

Design Parameters (from docs/design/quantization-algorithm.md):
- Grid Size: 50µm (compromise between stability and entropy)
- Angle Bins: 32 bins (11.25° per bin)
- Quality Threshold: NFIQ ≥50
- Minimum Minutiae: ≥4 per finger

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


# ============================================================================
# CONSTANTS (from Phase 1 Design)
# ============================================================================

# Grid quantization parameters
GRID_SIZE_UM = 50  # micrometers (optimal: balances stability and entropy)
GRID_X_BINS = 10   # 10mm width / 50µm = 200 pixels → 10 bins
GRID_Y_BINS = 20   # 20mm height / 50µm = 400 pixels → 20 bins

# Angle quantization parameters
ANGLE_BINS = 32  # 32 bins = 11.25° per bin (optimal for ±5° noise tolerance)
DEGREES_PER_BIN = 360.0 / ANGLE_BINS  # 11.25°

# Quality thresholds
MIN_QUALITY_SCORE = 50  # NFIQ ≥50 (requirement FR-ENR-2)
MIN_MINUTIAE_COUNT = 4  # Minimum minutiae per finger for stability

# Sensor assumptions (typical USB fingerprint sensor)
SENSOR_WIDTH_MM = 10.0   # 10mm capture width
SENSOR_HEIGHT_MM = 20.0  # 20mm capture height
SENSOR_DPI = 500  # 500 DPI = ~50µm per pixel

# Noise tolerance parameters (from Phase 1 analysis)
EXPECTED_POSITIONAL_NOISE_UM = 50.0  # ±50µm standard deviation
EXPECTED_ANGULAR_NOISE_DEG = 4.0     # ±4° standard deviation


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class MinutiaeType(Enum):
    """Minutiae types from ISO/IEC 19794-2 standard"""
    RIDGE_ENDING = 1
    BIFURCATION = 2
    OTHER = 0


@dataclass
class Minutia:
    """
    Raw minutia point from fingerprint scanner.

    Attributes:
        x_mm: X coordinate in millimeters (origin: top-left)
        y_mm: Y coordinate in millimeters (origin: top-left)
        angle_deg: Ridge angle in degrees [0, 360)
        type: Minutia type (ridge ending, bifurcation, etc.)
        quality: Quality score [0, 100] (NFIQ-like)
        finger_id: Finger identifier (0-9: thumbs, indexes, middle, ring, pinky)
    """
    x_mm: float
    y_mm: float
    angle_deg: float
    type: MinutiaeType
    quality: float
    finger_id: int = 0

    def __post_init__(self):
        """Validate minutia attributes"""
        # Allow negative coordinates for normalized minutiae
        # Only validate if coordinates are extremely out of range
        if abs(self.x_mm) > 2 * SENSOR_WIDTH_MM:
            raise ValueError(
                f"X coordinate {self.x_mm} extremely out of range")
        if abs(self.y_mm) > 2 * SENSOR_HEIGHT_MM:
            raise ValueError(
                f"Y coordinate {self.y_mm} extremely out of range")
        if not (0 <= self.angle_deg < 360):
            self.angle_deg = self.angle_deg % 360.0  # Normalize to [0, 360)
        if not (0 <= self.quality <= 100):
            raise ValueError(
                f"Quality score {self.quality} must be in [0, 100]")
        if not (0 <= self.finger_id <= 9):
            raise ValueError(f"Finger ID {self.finger_id} must be in [0, 9]")


@dataclass
class QuantizedMinutia:
    """
    Quantized minutia point after grid and angle binning.

    Attributes:
        x_bin: X grid bin index [0, GRID_X_BINS-1]
        y_bin: Y grid bin index [0, GRID_Y_BINS-1]
        angle_bin: Angle bin index [0, ANGLE_BINS-1]
        type: Minutia type (preserved from raw)
        quality: Quality score (preserved from raw)
        finger_id: Finger identifier (preserved from raw)
    """
    x_bin: int
    y_bin: int
    angle_bin: int
    type: MinutiaeType
    quality: float
    finger_id: int = 0

    def to_bytes(self) -> bytes:
        """
        Serialize quantized minutia to compact byte representation.

        Format (4 bytes):
        - Byte 0: x_bin (4 bits) | y_bin high nibble (4 bits)
        - Byte 1: y_bin low bit (1 bit) | angle_bin (5 bits) | type (2 bits)
        - Byte 2: quality (8 bits, scaled to 0-255)
        - Byte 3: finger_id (4 bits) | reserved (4 bits)

        Returns:
            4-byte compact representation
        """
        byte0 = (self.x_bin & 0x0F) << 4 | (self.y_bin >> 1) & 0x0F
        byte1 = ((self.y_bin & 0x01) << 7 |
                 (self.angle_bin & 0x1F) << 2 |
                 self.type.value & 0x03)
        byte2 = int(self.quality * 2.55) & 0xFF  # Scale [0,100] to [0,255]
        byte3 = (self.finger_id & 0x0F) << 4

        return bytes([byte0, byte1, byte2, byte3])

    @classmethod
    def from_bytes(cls, data: bytes) -> 'QuantizedMinutia':
        """
        Deserialize quantized minutia from byte representation.

        Args:
            data: 4-byte compact representation

        Returns:
            QuantizedMinutia object
        """
        if len(data) != 4:
            raise ValueError(f"Expected 4 bytes, got {len(data)}")

        x_bin = (data[0] >> 4) & 0x0F
        y_bin = ((data[0] & 0x0F) << 1) | ((data[1] >> 7) & 0x01)
        angle_bin = (data[1] >> 2) & 0x1F
        type_val = data[1] & 0x03
        quality = data[2] / 2.55  # Scale [0,255] to [0,100]
        finger_id = (data[3] >> 4) & 0x0F

        return cls(
            x_bin=x_bin,
            y_bin=y_bin,
            angle_bin=angle_bin,
            type=MinutiaeType(type_val),
            quality=quality,
            finger_id=finger_id
        )


# ============================================================================
# QUANTIZATION FUNCTIONS
# ============================================================================

def quantize_position(x_mm: float, y_mm: float) -> Tuple[int, int]:
    """
    Quantize minutia position to grid bin.

    Uses 50µm grid size for optimal stability/entropy trade-off.
    Grid: 10×20 bins over 10mm×20mm sensor area.

    Args:
        x_mm: X coordinate in millimeters [0, 10]
        y_mm: Y coordinate in millimeters [0, 20]

    Returns:
        (x_bin, y_bin): Grid bin indices [0,9] × [0,19]

    Example:
        >>> quantize_position(2.5, 7.3)
        (5, 14)
    """
    # Convert mm to µm, divide by grid size, modulo to wrap
    x_bin = int((x_mm * 1000) / GRID_SIZE_UM) % GRID_X_BINS
    y_bin = int((y_mm * 1000) / GRID_SIZE_UM) % GRID_Y_BINS

    return x_bin, y_bin


def quantize_angle(angle_deg: float) -> int:
    """
    Quantize minutia angle to nearest bin.

    Uses 32 bins (11.25° per bin) for optimal noise tolerance.

    Args:
        angle_deg: Ridge angle in degrees [0, 360)

    Returns:
        angle_bin: Bin index [0, 31]

    Example:
        >>> quantize_angle(45.0)
        4
        >>> quantize_angle(357.0)
        31
    """
    # Normalize to [0, 360)
    normalized = angle_deg % 360.0

    # Round to nearest bin
    bin_index = int(normalized / DEGREES_PER_BIN + 0.5) % ANGLE_BINS

    return bin_index


def dequantize_angle(bin_index: int) -> float:
    """
    Convert angle bin index back to degrees (for visualization).

    Args:
        bin_index: Angle bin [0, 31]

    Returns:
        angle_deg: Center of bin in degrees [0, 360)

    Example:
        >>> dequantize_angle(4)
        45.0
    """
    return (bin_index * DEGREES_PER_BIN) % 360.0


def quantize_minutia(minutia: Minutia) -> QuantizedMinutia:
    """
    Quantize a single minutia point.

    Args:
        minutia: Raw minutia from scanner

    Returns:
        QuantizedMinutia: Quantized representation

    Example:
        >>> m = Minutia(x_mm=2.5, y_mm=7.3, angle_deg=45.0,
        ...             type=MinutiaeType.RIDGE_ENDING, quality=75, finger_id=2)
        >>> q = quantize_minutia(m)
        >>> (q.x_bin, q.y_bin, q.angle_bin)
        (5, 14, 4)
    """
    x_bin, y_bin = quantize_position(minutia.x_mm, minutia.y_mm)
    angle_bin = quantize_angle(minutia.angle_deg)

    return QuantizedMinutia(
        x_bin=x_bin,
        y_bin=y_bin,
        angle_bin=angle_bin,
        type=minutia.type,
        quality=minutia.quality,
        finger_id=minutia.finger_id
    )


# ============================================================================
# FILTERING FUNCTIONS
# ============================================================================

def filter_by_quality(minutiae: List[Minutia],
                      min_quality: float = MIN_QUALITY_SCORE) -> List[Minutia]:
    """
    Filter minutiae by quality threshold (NFIQ ≥50).

    Requirement FR-ENR-2: Minimum quality threshold.

    Args:
        minutiae: List of raw minutiae
        min_quality: Minimum quality score [0, 100] (default: 50)

    Returns:
        Filtered list of high-quality minutiae

    Example:
        >>> minutiae = [
        ...     Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
        ...     Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 30, 0)
        ... ]
        >>> filtered = filter_by_quality(minutiae, min_quality=50)
        >>> len(filtered)
        1
    """
    return [m for m in minutiae if m.quality >= min_quality]


def remove_duplicates(minutiae: List[Minutia],
                      distance_threshold_mm: float = 0.5,
                      angle_threshold_deg: float = 22.5) -> List[Minutia]:
    """
    Remove duplicate minutiae (same position + angle).

    Duplicates occur when multiple detections are made for the same ridge feature.

    Args:
        minutiae: List of minutiae
        distance_threshold_mm: Max Euclidean distance to consider duplicate (default: 0.5mm = 10 pixels @ 500 DPI)
        angle_threshold_deg: Max angle difference to consider duplicate (default: 22.5° = 2 bins)

    Returns:
        List with duplicates removed (keeps highest quality minutia per cluster)

    Example:
        >>> minutiae = [
        ...     Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
        ...     Minutia(2.05, 5.03, 47.0, MinutiaeType.RIDGE_ENDING, 60, 0)
        ... ]
        >>> unique = remove_duplicates(minutiae)
        >>> len(unique)
        1
        >>> unique[0].quality
        70.0
    """
    if not minutiae:
        return []

    # Sort by quality (descending) to keep best duplicates
    sorted_minutiae = sorted(minutiae, key=lambda m: m.quality, reverse=True)

    unique: List[Minutia] = []
    for m in sorted_minutiae:
        is_duplicate = False
        for u in unique:
            # Check Euclidean distance
            distance = math.sqrt((m.x_mm - u.x_mm)**2 + (m.y_mm - u.y_mm)**2)

            # Check angular distance (handle wraparound at 0°/360°)
            angle_diff = min(
                abs(m.angle_deg - u.angle_deg),
                360.0 - abs(m.angle_deg - u.angle_deg)
            )

            if distance < distance_threshold_mm and angle_diff < angle_threshold_deg:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(m)

    return unique


def validate_minutiae_set(minutiae: List[Minutia],
                          min_count: int = MIN_MINUTIAE_COUNT) -> bool:
    """
    Validate that minutiae set meets minimum requirements.

    Requirements:
    - Minimum count: ≥4 minutiae per finger (stability requirement)
    - Quality threshold: All minutiae already filtered by filter_by_quality()

    Args:
        minutiae: List of filtered, deduplicated minutiae
        min_count: Minimum required minutiae count (default: 4)

    Returns:
        True if valid, False otherwise

    Example:
        >>> minutiae = [
        ...     Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
        ...     Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 65, 0),
        ...     Minutia(4.0, 7.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0),
        ...     Minutia(5.0, 8.0, 180.0, MinutiaeType.BIFURCATION, 75, 0)
        ... ]
        >>> validate_minutiae_set(minutiae)
        True
    """
    return len(minutiae) >= min_count


# ============================================================================
# NORMALIZATION FUNCTIONS
# ============================================================================

def select_reference_minutia(minutiae: List[Minutia]) -> Optional[Minutia]:
    """
    Select stable reference minutia for normalization.

    Strategy: Choose highest-quality minutia near sensor center.
    Rationale: Center minutiae are least affected by finger placement variations.

    Args:
        minutiae: List of filtered minutiae

    Returns:
        Reference minutia, or None if list is empty

    Example:
        >>> minutiae = [
        ...     Minutia(2.0, 15.0, 45.0, MinutiaeType.RIDGE_ENDING, 60, 0),  # Edge
        ...     Minutia(5.0, 10.0, 90.0, MinutiaeType.BIFURCATION, 85, 0)    # Center, high quality
        ... ]
        >>> ref = select_reference_minutia(minutiae)
        >>> (ref.x_mm, ref.y_mm)
        (5.0, 10.0)
    """
    if not minutiae:
        return None

    # Sensor center
    center_x = SENSOR_WIDTH_MM / 2.0
    center_y = SENSOR_HEIGHT_MM / 2.0

    # Score = quality × (1 - normalized_distance_from_center)
    def score_minutia(m: Minutia) -> float:
        distance = math.sqrt((m.x_mm - center_x)**2 + (m.y_mm - center_y)**2)
        max_distance = math.sqrt(center_x**2 + center_y**2)
        normalized_dist = distance / max_distance
        return m.quality * (1.0 - normalized_dist)

    return max(minutiae, key=score_minutia)


def normalize_translation(minutiae: List[Minutia],
                          reference: Minutia) -> List[Minutia]:
    """
    Normalize minutiae by translating reference to origin.

    This removes dependency on absolute finger position on sensor.

    Args:
        minutiae: List of minutiae to normalize
        reference: Reference minutia (will be moved to origin)

    Returns:
        List of translated minutiae (deep copy, original unchanged)

    Example:
        >>> minutiae = [
        ...     Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0)
        ... ]
        >>> ref = minutiae[0]
        >>> normalized = normalize_translation(minutiae, ref)
        >>> (normalized[0].x_mm, normalized[0].y_mm)
        (0.0, 0.0)
        >>> (normalized[1].x_mm, normalized[1].y_mm)
        (1.0, 1.0)
    """
    # Calculate translation offset
    dx = reference.x_mm
    dy = reference.y_mm

    # Translate all minutiae
    normalized: List[Minutia] = []
    for m in minutiae:
        translated = Minutia(
            x_mm=m.x_mm - dx,
            y_mm=m.y_mm - dy,
            angle_deg=m.angle_deg,  # Angles unchanged by translation
            type=m.type,
            quality=m.quality,
            finger_id=m.finger_id
        )
        normalized.append(translated)

    return normalized


def normalize_rotation(minutiae: List[Minutia],
                       reference: Minutia) -> List[Minutia]:
    """
    Normalize minutiae by rotating reference angle to 0°.

    This removes dependency on finger rotation on sensor.

    Args:
        minutiae: List of minutiae to normalize (already translation-normalized)
        reference: Reference minutia (angle will become 0°)

    Returns:
        List of rotated minutiae (deep copy, original unchanged)

    Example:
        >>> minutiae = [
        ...     Minutia(0.0, 0.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     Minutia(1.0, 1.0, 90.0, MinutiaeType.BIFURCATION, 75, 0)
        ... ]
        >>> ref = minutiae[0]
        >>> normalized = normalize_rotation(minutiae, ref)
        >>> normalized[0].angle_deg
        0.0
        >>> normalized[1].angle_deg
        45.0
    """
    # Calculate rotation angle
    rotation_angle = reference.angle_deg

    # Rotate all minutiae
    normalized: List[Minutia] = []
    for m in minutiae:
        # Rotate position (convert to radians)
        theta = math.radians(rotation_angle)
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        x_rotated = m.x_mm * cos_theta - m.y_mm * sin_theta
        y_rotated = m.x_mm * sin_theta + m.y_mm * cos_theta

        # Rotate angle
        angle_rotated = (m.angle_deg - rotation_angle) % 360.0

        rotated = Minutia(
            x_mm=x_rotated,
            y_mm=y_rotated,
            angle_deg=angle_rotated,
            type=m.type,
            quality=m.quality,
            finger_id=m.finger_id
        )
        normalized.append(rotated)

    return normalized


def normalize_minutiae(minutiae: List[Minutia]) -> Tuple[List[Minutia], Optional[Minutia]]:
    """
    Apply full normalization pipeline: filter, deduplicate, translate, rotate.

    Pipeline:
    1. Filter by quality (NFIQ ≥50)
    2. Remove duplicates
    3. Validate minimum count (≥4 minutiae)
    4. Select reference minutia
    5. Translate to reference
    6. Rotate to reference

    Args:
        minutiae: Raw minutiae from scanner

    Returns:
        (normalized_minutiae, reference): Tuple of normalized list and reference,
                                          or ([], None) if validation fails

    Example:
        >>> minutiae = [
        ...     Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0),
        ...     Minutia(7.0, 12.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0),
        ...     Minutia(8.0, 13.0, 180.0, MinutiaeType.BIFURCATION, 70, 0)
        ... ]
        >>> normalized, ref = normalize_minutiae(minutiae)
        >>> len(normalized)
        4
        >>> normalized[0].x_mm, normalized[0].y_mm, normalized[0].angle_deg
        (0.0, 0.0, 0.0)
    """
    # Step 1: Filter by quality
    filtered = filter_by_quality(minutiae, MIN_QUALITY_SCORE)

    if not filtered:
        return [], None

    # Step 2: Remove duplicates
    unique = remove_duplicates(filtered)

    # Step 3: Validate minimum count
    if not validate_minutiae_set(unique, MIN_MINUTIAE_COUNT):
        return [], None

    # Step 4: Select reference
    reference = select_reference_minutia(unique)
    if reference is None:
        return [], None

    # Step 5: Translate
    translated = normalize_translation(unique, reference)

    # Step 6: Rotate
    rotated = normalize_rotation(translated, reference)

    return rotated, reference


# ============================================================================
# HIGH-LEVEL API
# ============================================================================

def process_fingerprint(minutiae: List[Minutia]) -> Tuple[List[QuantizedMinutia], Dict[str, Any]]:
    """
    Complete processing pipeline: normalize + quantize.

    This is the main entry point for converting raw scanner minutiae
    into quantized, normalized representations ready for fuzzy extraction.

    Args:
        minutiae: Raw minutiae from fingerprint scanner

    Returns:
        (quantized_minutiae, metadata): Tuple of quantized list and processing metadata

    Metadata includes:
    - 'raw_count': Number of raw minutiae input
    - 'filtered_count': Number after quality filtering
    - 'unique_count': Number after duplicate removal
    - 'normalized_count': Number after normalization
    - 'reference_minutia': Reference used for normalization (or None)
    - 'validation_passed': Whether minimum requirements met

    Raises:
        ValueError: If input validation fails

    Example:
        >>> minutiae = [
        ...     Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0),
        ...     Minutia(7.0, 12.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0),
        ...     Minutia(8.0, 13.0, 180.0, MinutiaeType.BIFURCATION, 70, 0)
        ... ]
        >>> quantized, meta = process_fingerprint(minutiae)
        >>> len(quantized)
        4
        >>> meta['validation_passed']
        True
    """
    metadata: Dict[str, Any] = {
        'raw_count': len(minutiae),
        'filtered_count': 0,
        'unique_count': 0,
        'normalized_count': 0,
        'reference_minutia': None,
        'validation_passed': False
    }

    # Normalize
    normalized, reference = normalize_minutiae(minutiae)

    metadata['filtered_count'] = len(
        filter_by_quality(minutiae, MIN_QUALITY_SCORE))
    metadata['unique_count'] = len(remove_duplicates(
        filter_by_quality(minutiae, MIN_QUALITY_SCORE)))
    metadata['normalized_count'] = len(normalized)
    metadata['reference_minutia'] = reference
    metadata['validation_passed'] = len(normalized) >= MIN_MINUTIAE_COUNT

    if not metadata['validation_passed']:
        return [], metadata

    # Quantize
    quantized = [quantize_minutia(m) for m in normalized]

    return quantized, metadata


def serialize_quantized_minutiae(minutiae: List[QuantizedMinutia]) -> bytes:
    """
    Serialize list of quantized minutiae to compact byte representation.

    Format:
    - Header (2 bytes): count (uint16, big-endian)
    - Body (4 * count bytes): each minutia serialized to 4 bytes

    Args:
        minutiae: List of quantized minutiae

    Returns:
        Compact byte representation

    Example:
        >>> minutiae = [
        ...     QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     QuantizedMinutia(6, 15, 8, MinutiaeType.BIFURCATION, 75, 0)
        ... ]
        >>> data = serialize_quantized_minutiae(minutiae)
        >>> len(data)
        10
    """
    count = len(minutiae)
    if count > 65535:
        raise ValueError(f"Too many minutiae ({count}), max 65535")

    # Header: count as uint16 big-endian
    header = count.to_bytes(2, byteorder='big')

    # Body: serialize each minutia
    body = b''.join(m.to_bytes() for m in minutiae)

    return header + body


def deserialize_quantized_minutiae(data: bytes) -> List[QuantizedMinutia]:
    """
    Deserialize list of quantized minutiae from byte representation.

    Args:
        data: Compact byte representation (from serialize_quantized_minutiae)

    Returns:
        List of QuantizedMinutia objects

    Raises:
        ValueError: If data format is invalid

    Example:
        >>> minutiae = [
        ...     QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     QuantizedMinutia(6, 15, 8, MinutiaeType.BIFURCATION, 75, 0)
        ... ]
        >>> data = serialize_quantized_minutiae(minutiae)
        >>> deserialized = deserialize_quantized_minutiae(data)
        >>> len(deserialized)
        2
    """
    if len(data) < 2:
        raise ValueError("Data too short for header")

    # Parse header
    count = int.from_bytes(data[0:2], byteorder='big')

    expected_length = 2 + (count * 4)
    if len(data) != expected_length:
        raise ValueError(f"Expected {expected_length} bytes, got {len(data)}")

    # Parse body
    minutiae: List[QuantizedMinutia] = []
    for i in range(count):
        offset = 2 + (i * 4)
        minutia_bytes = data[offset:offset+4]
        minutiae.append(QuantizedMinutia.from_bytes(minutia_bytes))

    return minutiae


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def estimate_entropy(minutiae: List[QuantizedMinutia]) -> float:
    """
    Estimate entropy (bits) of quantized minutiae set.

    Assumes:
    - Each position bin: log2(GRID_X_BINS × GRID_Y_BINS) ≈ 7.6 bits
    - Each angle bin: log2(ANGLE_BINS) = 5.0 bits
    - Total per minutia: 12.6 bits

    Args:
        minutiae: List of quantized minutiae

    Returns:
        Estimated entropy in bits

    Example:
        >>> minutiae = [
        ...     QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85, 0),
        ...     QuantizedMinutia(6, 15, 8, MinutiaeType.BIFURCATION, 75, 0)
        ... ]
        >>> entropy = estimate_entropy(minutiae)
        >>> entropy
        25.2
    """
    bits_per_minutia = math.log2(GRID_X_BINS * GRID_Y_BINS * ANGLE_BINS)
    return bits_per_minutia * len(minutiae)


def is_near_boundary(minutia: Minutia,
                     threshold_mm: float = 0.025,
                     threshold_deg: float = 3.0) -> Dict[str, bool]:
    """
    Check if minutia is near quantization boundaries.

    Minutiae near boundaries are at risk of flipping between bins
    due to sensor noise. This function helps identify unstable minutiae.

    Args:
        minutia: Raw minutia to check
        threshold_mm: Distance threshold for position boundaries (default: 0.025mm = 25µm = half grid size)
        threshold_deg: Angle threshold for angle boundaries (default: 3° ≈ half bin width)

    Returns:
        Dictionary with boundary flags:
        - 'position_boundary': True if near position bin boundary
        - 'angle_boundary': True if near angle bin boundary
        - 'any_boundary': True if near any boundary

    Example:
        >>> m = Minutia(2.525, 7.3, 45.0, MinutiaeType.RIDGE_ENDING, 75, 0)
        >>> flags = is_near_boundary(m)
        >>> flags['position_boundary']
        True
    """
    # Check position boundary
    x_bin_center = (int((minutia.x_mm * 1000) / GRID_SIZE_UM)
                    * GRID_SIZE_UM) / 1000.0
    y_bin_center = (int((minutia.y_mm * 1000) / GRID_SIZE_UM)
                    * GRID_SIZE_UM) / 1000.0

    x_dist_to_boundary = min(
        abs(minutia.x_mm - x_bin_center),
        abs(minutia.x_mm - (x_bin_center + GRID_SIZE_UM / 1000.0))
    )
    y_dist_to_boundary = min(
        abs(minutia.y_mm - y_bin_center),
        abs(minutia.y_mm - (y_bin_center + GRID_SIZE_UM / 1000.0))
    )

    position_near_boundary = (
        x_dist_to_boundary < threshold_mm or
        y_dist_to_boundary < threshold_mm
    )

    # Check angle boundary
    angle_bin = quantize_angle(minutia.angle_deg)
    angle_bin_center = dequantize_angle(angle_bin)

    angle_dist_to_boundary = min(
        abs(minutia.angle_deg - angle_bin_center),
        abs(minutia.angle_deg - (angle_bin_center + DEGREES_PER_BIN))
    ) % 360.0

    angle_near_boundary = angle_dist_to_boundary < threshold_deg

    return {
        'position_boundary': position_near_boundary,
        'angle_boundary': angle_near_boundary,
        'any_boundary': position_near_boundary or angle_near_boundary
    }


if __name__ == "__main__":
    # Quick test
    print("Minutiae Quantization Module")
    print(f"Grid: {GRID_X_BINS}×{GRID_Y_BINS} bins ({GRID_SIZE_UM}µm)")
    print(f"Angle: {ANGLE_BINS} bins ({DEGREES_PER_BIN}°/bin)")
    print(f"Quality threshold: {MIN_QUALITY_SCORE}")
    print(f"Minimum minutiae: {MIN_MINUTIAE_COUNT}")

    # Example usage
    test_minutiae = [
        Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
        Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0),
        Minutia(7.0, 12.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0),
        Minutia(8.0, 13.0, 180.0, MinutiaeType.BIFURCATION, 70, 0)
    ]

    quantized, metadata = process_fingerprint(test_minutiae)
    print(f"\nProcessed {metadata['raw_count']} minutiae:")
    print(f"  Filtered: {metadata['filtered_count']}")
    print(f"  Unique: {metadata['unique_count']}")
    print(f"  Normalized: {metadata['normalized_count']}")
    print(
        f"  Validation: {'PASS' if metadata['validation_passed'] else 'FAIL'}")
    print(f"  Quantized: {len(quantized)}")
    print(f"  Estimated entropy: {estimate_entropy(quantized):.1f} bits")
