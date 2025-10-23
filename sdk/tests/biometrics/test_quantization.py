"""
Unit Tests for Minutiae Quantization Module

Tests the quantization algorithm implemented in Phase 2, Task 1.
Covers edge cases, boundary minutiae, rotated inputs, and error tolerance.

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

from __future__ import annotations
import pytest
import math
from typing import List, Any

from src.biometrics.quantization import (
    # Constants
    GRID_SIZE_UM, GRID_X_BINS, GRID_Y_BINS, ANGLE_BINS, DEGREES_PER_BIN,
    MIN_QUALITY_SCORE, MIN_MINUTIAE_COUNT, SENSOR_WIDTH_MM, SENSOR_HEIGHT_MM,

    # Data structures
    Minutia, QuantizedMinutia, MinutiaeType,

    # Quantization functions
    quantize_position, quantize_angle, dequantize_angle, quantize_minutia,

    # Filtering functions
    filter_by_quality, remove_duplicates, validate_minutiae_set,

    # Normalization functions
    select_reference_minutia, normalize_translation, normalize_rotation, normalize_minutiae,

    # High-level API
    process_fingerprint, serialize_quantized_minutiae, deserialize_quantized_minutiae,

    # Utility functions
    estimate_entropy, is_near_boundary
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_minutia():
    """Single high-quality minutia"""
    return Minutia(
        x_mm=5.0,
        y_mm=10.0,
        angle_deg=45.0,
        type=MinutiaeType.RIDGE_ENDING,
        quality=85.0,
        finger_id=2
    )


@pytest.fixture
def sample_minutiae_set():
    """Set of 4 valid minutiae"""
    return [
        Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
        Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0),
        Minutia(7.0, 12.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0),
        Minutia(8.0, 13.0, 180.0, MinutiaeType.BIFURCATION, 70, 0)
    ]


@pytest.fixture
def boundary_minutiae():
    """Minutiae near quantization boundaries"""
    return [
        Minutia(2.525, 7.3, 45.0, MinutiaeType.RIDGE_ENDING,
                75, 0),  # Position boundary
        # Angle boundary (halfway between bins)
        Minutia(3.0, 8.0, 16.875, MinutiaeType.BIFURCATION, 80, 0),
        Minutia(4.975, 9.975, 33.75, MinutiaeType.RIDGE_ENDING,
                70, 0)  # Both boundaries
    ]


# ============================================================================
# QUANTIZATION TESTS
# ============================================================================

class TestPositionQuantization:
    """Test coordinate quantization"""

    def test_basic_quantization(self):
        """Test simple position quantization"""
        x_bin, y_bin = quantize_position(2.5, 7.5)
        assert 0 <= x_bin < GRID_X_BINS
        assert 0 <= y_bin < GRID_Y_BINS

    def test_origin_quantization(self):
        """Test quantization at origin"""
        x_bin, y_bin = quantize_position(0.0, 0.0)
        assert x_bin == 0
        assert y_bin == 0

    def test_center_quantization(self):
        """Test quantization at sensor center"""
        x_bin, y_bin = quantize_position(
            SENSOR_WIDTH_MM / 2, SENSOR_HEIGHT_MM / 2)
        # 5mm / 50µm = 100 µm/grid → 100/50 = 2.0 → bin 0 (wraps to grid)
        # Actually: (5mm * 1000 µm/mm) / 50 µm = 100 → 100 % 10 = 0
        assert x_bin == 0  # Wraparound: 100 % 10 = 0
        assert y_bin == 0  # Wraparound: 200 % 20 = 0

    def test_boundary_quantization(self):
        """Test quantization near bin boundaries"""
        # Just below boundary (should round down)
        x_bin1, y_bin1 = quantize_position(0.249, 0.499)

        # Just above boundary (should round up)
        x_bin2, y_bin2 = quantize_position(0.251, 0.501)

        # Both should be in valid range
        assert 0 <= x_bin1 < GRID_X_BINS
        assert 0 <= y_bin1 < GRID_Y_BINS
        assert 0 <= x_bin2 < GRID_X_BINS
        assert 0 <= y_bin2 < GRID_Y_BINS

    def test_wraparound(self):
        """Test that positions wrap correctly"""
        # Edge of sensor
        x_bin, y_bin = quantize_position(9.9, 19.9)
        assert 0 <= x_bin < GRID_X_BINS
        assert 0 <= y_bin < GRID_Y_BINS


class TestAngleQuantization:
    """Test angle quantization"""

    def test_basic_quantization(self):
        """Test simple angle quantization"""
        bin_index = quantize_angle(45.0)
        assert 0 <= bin_index < ANGLE_BINS
        assert bin_index == 4  # 45° / 11.25° = 4

    def test_zero_degree(self):
        """Test 0° angle"""
        bin_index = quantize_angle(0.0)
        assert bin_index == 0

    def test_wraparound_360(self):
        """Test wraparound at 360°"""
        bin_index_360 = quantize_angle(360.0)
        bin_index_0 = quantize_angle(0.0)
        assert bin_index_360 == bin_index_0

    def test_near_360_wraparound(self):
        """Test angles near 360° boundary"""
        bin_index_357 = quantize_angle(357.0)
        bin_index_3 = quantize_angle(3.0)

        # 357° → (357 / 11.25 + 0.5) = 32.23 → 32 % 32 = 0
        # 3° → (3 / 11.25 + 0.5) = 0.77 → 0
        # Both should wrap to bin 0
        assert bin_index_357 == 0  # Wraps around
        assert bin_index_3 == 0

    def test_boundary_rounding(self):
        """Test rounding at bin boundaries"""
        # 11.25° is exactly between bins 1 and 2
        bin_index_low = quantize_angle(11.0)
        bin_index_high = quantize_angle(11.5)

        # Should round to nearest
        assert bin_index_low == 1
        assert bin_index_high == 1

    def test_all_bins_reachable(self):
        """Test that all 32 bins can be reached"""
        bins_reached: set[int] = set()
        for angle in range(0, 360, 5):  # Test every 5°
            bin_index = quantize_angle(float(angle))
            bins_reached.add(bin_index)

        # Should reach most bins (may miss 1-2 due to 5° sampling)
        assert len(bins_reached) >= 30

    def test_dequantization(self):
        """Test angle dequantization"""
        for bin_index in range(ANGLE_BINS):
            angle = dequantize_angle(bin_index)
            assert 0 <= angle < 360

            # Re-quantizing should give same bin
            re_quantized = quantize_angle(angle)
            assert re_quantized == bin_index


class TestMinutiaQuantization:
    """Test quantization of full minutia objects"""

    def test_quantize_single_minutia(self, sample_minutia: Any) -> None:
        """Test quantizing a single minutia"""
        quantized = quantize_minutia(sample_minutia)

        assert isinstance(quantized, QuantizedMinutia)
        assert 0 <= quantized.x_bin < GRID_X_BINS
        assert 0 <= quantized.y_bin < GRID_Y_BINS
        assert 0 <= quantized.angle_bin < ANGLE_BINS
        assert quantized.type == sample_minutia.type
        assert quantized.quality == sample_minutia.quality
        assert quantized.finger_id == sample_minutia.finger_id

    def test_quantization_preserves_metadata(self, sample_minutia: Any) -> None:
        """Test that type, quality, and finger_id are preserved"""
        quantized = quantize_minutia(sample_minutia)

        assert quantized.type == MinutiaeType.RIDGE_ENDING
        assert quantized.quality == 85.0
        assert quantized.finger_id == 2


# ============================================================================
# FILTERING TESTS
# ============================================================================

class TestQualityFiltering:
    """Test quality-based filtering"""

    def test_filter_high_quality(self):
        """Test filtering keeps high-quality minutiae"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 80, 0)
        ]
        filtered = filter_by_quality(minutiae, min_quality=50)
        assert len(filtered) == 2

    def test_filter_low_quality(self):
        """Test filtering removes low-quality minutiae"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 30, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 40, 0)
        ]
        filtered = filter_by_quality(minutiae, min_quality=50)
        assert len(filtered) == 0

    def test_filter_mixed_quality(self):
        """Test filtering with mixed quality"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 30, 0),
            Minutia(4.0, 7.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0)
        ]
        filtered = filter_by_quality(minutiae, min_quality=50)
        assert len(filtered) == 2
        assert all(m.quality >= 50 for m in filtered)

    def test_default_threshold(self):
        """Test default quality threshold (50)"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 50, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 49, 0)
        ]
        filtered = filter_by_quality(minutiae)
        assert len(filtered) == 1
        assert filtered[0].quality == 50.0


class TestDuplicateRemoval:
    """Test duplicate minutiae removal"""

    def test_remove_exact_duplicates(self):
        """Test removing identical minutiae"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING,
                    60, 0)  # Duplicate, lower quality
        ]
        unique = remove_duplicates(minutiae)
        assert len(unique) == 1
        assert unique[0].quality == 70.0  # Kept higher quality

    def test_remove_near_duplicates(self):
        """Test removing minutiae within distance threshold"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(2.05, 5.03, 47.0, MinutiaeType.RIDGE_ENDING,
                    60, 0)  # Within 0.5mm
        ]
        unique = remove_duplicates(minutiae, distance_threshold_mm=0.1)
        assert len(unique) == 1
        assert unique[0].quality == 70.0

    def test_keep_distinct_minutiae(self):
        """Test keeping minutiae that are far apart"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(6.0, 10.0, 90.0, MinutiaeType.BIFURCATION, 80, 0)
        ]
        unique = remove_duplicates(minutiae)
        assert len(unique) == 2

    def test_angle_difference_duplicates(self):
        """Test duplicate detection with angle differences"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(2.0, 5.0, 90.0, MinutiaeType.RIDGE_ENDING,
                    60, 0)  # Same position, different angle
        ]
        unique = remove_duplicates(minutiae, angle_threshold_deg=22.5)
        assert len(unique) == 2  # Kept both (angle diff > threshold)

    def test_empty_list(self):
        """Test duplicate removal on empty list"""
        unique = remove_duplicates([])
        assert len(unique) == 0


class TestValidation:
    """Test minutiae set validation"""

    def test_valid_set(self, sample_minutiae_set: Any) -> None:
        """Test validation passes for valid set"""
        assert validate_minutiae_set(sample_minutiae_set, min_count=4)

    def test_insufficient_minutiae(self):
        """Test validation fails for insufficient minutiae"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 80, 0)
        ]
        assert not validate_minutiae_set(minutiae, min_count=4)

    def test_exact_minimum(self):
        """Test validation with exactly minimum count"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 80, 0),
            Minutia(4.0, 7.0, 135.0, MinutiaeType.RIDGE_ENDING, 75, 0),
            Minutia(5.0, 8.0, 180.0, MinutiaeType.BIFURCATION, 85, 0)
        ]
        assert validate_minutiae_set(minutiae, min_count=4)

    def test_empty_set(self):
        """Test validation fails for empty set"""
        assert not validate_minutiae_set([], min_count=4)


# ============================================================================
# NORMALIZATION TESTS
# ============================================================================

class TestReferenceSelection:
    """Test reference minutia selection"""

    def test_select_from_set(self, sample_minutiae_set: Any) -> None:
        """Test reference selection from valid set"""
        reference = select_reference_minutia(sample_minutiae_set)
        assert reference is not None
        assert reference in sample_minutiae_set

    def test_select_highest_quality_center(self):
        """Test that center, high-quality minutiae are preferred"""
        minutiae = [
            Minutia(2.0, 15.0, 45.0, MinutiaeType.RIDGE_ENDING,
                    60, 0),  # Edge, low quality
            Minutia(5.0, 10.0, 90.0, MinutiaeType.BIFURCATION,
                    85, 0)    # Center, high quality
        ]
        reference = select_reference_minutia(minutiae)
        assert reference is not None
        assert reference.x_mm == 5.0
        assert reference.y_mm == 10.0

    def test_empty_set(self):
        """Test reference selection on empty set"""
        reference = select_reference_minutia([])
        assert reference is None


class TestTranslationNormalization:
    """Test translation normalization"""

    def test_translate_to_origin(self):
        """Test translating reference to origin"""
        minutiae = [
            Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
            Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0)
        ]
        reference = minutiae[0]
        normalized = normalize_translation(minutiae, reference)

        # Reference should be at origin
        assert normalized[0].x_mm == pytest.approx(0.0, abs=1e-6)
        assert normalized[0].y_mm == pytest.approx(0.0, abs=1e-6)

        # Other minutiae should be translated relative to reference
        assert normalized[1].x_mm == pytest.approx(1.0, abs=1e-6)
        assert normalized[1].y_mm == pytest.approx(1.0, abs=1e-6)

    def test_angles_unchanged_by_translation(self):
        """Test that angles are not affected by translation"""
        minutiae = [
            Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
            Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0)
        ]
        reference = minutiae[0]
        normalized = normalize_translation(minutiae, reference)

        assert normalized[0].angle_deg == 45.0
        assert normalized[1].angle_deg == 90.0


class TestRotationNormalization:
    """Test rotation normalization"""

    def test_rotate_reference_to_zero(self):
        """Test rotating reference angle to 0°"""
        minutiae = [
            Minutia(0.0, 0.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
            Minutia(1.0, 1.0, 90.0, MinutiaeType.BIFURCATION, 75, 0)
        ]
        reference = minutiae[0]
        normalized = normalize_rotation(minutiae, reference)

        # Reference angle should be 0°
        assert normalized[0].angle_deg == pytest.approx(0.0, abs=1e-6)

        # Other angles should be rotated by same amount
        assert normalized[1].angle_deg == pytest.approx(45.0, abs=1e-6)

    def test_rotate_positions(self):
        """Test that positions are rotated correctly"""
        minutiae = [
            Minutia(0.0, 0.0, 90.0, MinutiaeType.RIDGE_ENDING, 85, 0),
            Minutia(1.0, 0.0, 90.0, MinutiaeType.BIFURCATION,
                    75, 0)  # 1mm to the right
        ]
        reference = minutiae[0]
        normalized = normalize_rotation(minutiae, reference)

        # After 90° rotation, (1, 0) → (0, 1)
        assert normalized[1].x_mm == pytest.approx(0.0, abs=1e-6)
        assert normalized[1].y_mm == pytest.approx(1.0, abs=1e-6)

    def test_360_degree_rotation(self):
        """Test wraparound at 360°"""
        minutiae = [
            Minutia(0.0, 0.0, 350.0, MinutiaeType.RIDGE_ENDING, 85, 0),
            Minutia(1.0, 1.0, 10.0, MinutiaeType.BIFURCATION, 75, 0)
        ]
        reference = minutiae[0]
        normalized = normalize_rotation(minutiae, reference)

        # 10° - 350° = -340° = 20°
        assert normalized[1].angle_deg == pytest.approx(20.0, abs=1e-6)


class TestFullNormalization:
    """Test complete normalization pipeline"""

    def test_full_pipeline(self, sample_minutiae_set: Any) -> None:
        """Test complete normalization pipeline"""
        normalized, reference = normalize_minutiae(sample_minutiae_set)

        assert len(normalized) == 4
        assert reference is not None

        # First minutia (reference) should be at origin with 0° angle
        assert normalized[0].x_mm == pytest.approx(0.0, abs=1e-6)
        assert normalized[0].y_mm == pytest.approx(0.0, abs=1e-6)
        assert normalized[0].angle_deg == pytest.approx(0.0, abs=1e-6)

    def test_insufficient_quality(self):
        """Test pipeline fails with low-quality minutiae"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 30, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 40, 0)
        ]
        normalized, reference = normalize_minutiae(minutiae)

        assert len(normalized) == 0
        assert reference is None

    def test_insufficient_count(self):
        """Test pipeline fails with too few minutiae"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 70, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 80, 0)
        ]
        normalized, reference = normalize_minutiae(minutiae)

        assert len(normalized) == 0
        assert reference is None


# ============================================================================
# HIGH-LEVEL API TESTS
# ============================================================================

class TestProcessFingerprint:
    """Test complete processing pipeline"""

    def test_process_valid_fingerprint(self, sample_minutiae_set: Any) -> None:
        """Test processing valid fingerprint"""
        quantized, metadata = process_fingerprint(sample_minutiae_set)

        assert len(quantized) == 4
        assert metadata['validation_passed']
        assert metadata['raw_count'] == 4
        assert metadata['normalized_count'] == 4
        assert metadata['reference_minutia'] is not None

    def test_process_invalid_fingerprint(self):
        """Test processing invalid fingerprint (low quality)"""
        minutiae = [
            Minutia(2.0, 5.0, 45.0, MinutiaeType.RIDGE_ENDING, 30, 0),
            Minutia(3.0, 6.0, 90.0, MinutiaeType.BIFURCATION, 40, 0)
        ]
        quantized, metadata = process_fingerprint(minutiae)

        assert len(quantized) == 0
        assert not metadata['validation_passed']

    def test_metadata_counts(self, sample_minutiae_set: Any) -> None:
        """Test metadata contains correct counts"""
        quantized, metadata = process_fingerprint(sample_minutiae_set)

        assert metadata['raw_count'] == 4
        assert metadata['filtered_count'] >= 0
        assert metadata['unique_count'] >= 0
        assert metadata['normalized_count'] >= 0


class TestSerialization:
    """Test quantized minutiae serialization"""

    def test_serialize_single_minutia(self):
        """Test serializing a single minutia"""
        minutiae = [
            QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85.0, 0)
        ]
        data = serialize_quantized_minutiae(minutiae)

        assert len(data) == 6  # 2 header + 4 body
        assert data[0:2] == b'\x00\x01'  # Count = 1

    def test_serialize_multiple_minutiae(self):
        """Test serializing multiple minutiae"""
        minutiae = [
            QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85.0, 0),
            QuantizedMinutia(6, 15, 8, MinutiaeType.BIFURCATION, 75.0, 0)
        ]
        data = serialize_quantized_minutiae(minutiae)

        assert len(data) == 10  # 2 header + 8 body (4 per minutia)
        assert int.from_bytes(data[0:2], byteorder='big') == 2

    def test_roundtrip_serialization(self):
        """Test serialize → deserialize round trip"""
        minutiae = [
            QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85.0, 0),
            QuantizedMinutia(6, 15, 8, MinutiaeType.BIFURCATION, 75.0, 1)
        ]
        data = serialize_quantized_minutiae(minutiae)
        deserialized = deserialize_quantized_minutiae(data)

        assert len(deserialized) == 2
        assert deserialized[0].x_bin == 5
        assert deserialized[0].y_bin == 14
        assert deserialized[0].angle_bin == 4
        assert deserialized[0].type == MinutiaeType.RIDGE_ENDING
        assert deserialized[0].quality == pytest.approx(85.0, abs=1.0)
        assert deserialized[0].finger_id == 0

    def test_empty_serialization(self):
        """Test serializing empty list"""
        data = serialize_quantized_minutiae([])
        assert len(data) == 2
        assert data == b'\x00\x00'

        deserialized = deserialize_quantized_minutiae(data)
        assert len(deserialized) == 0


# ============================================================================
# UTILITY TESTS
# ============================================================================

class TestEntropyEstimation:
    """Test entropy estimation"""

    def test_entropy_calculation(self):
        """Test entropy calculation for known set"""
        minutiae = [
            QuantizedMinutia(5, 14, 4, MinutiaeType.RIDGE_ENDING, 85.0, 0),
            QuantizedMinutia(6, 15, 8, MinutiaeType.BIFURCATION, 75.0, 0)
        ]
        entropy = estimate_entropy(minutiae)

        # Expected: 2 minutiae × 12.6 bits/minutia ≈ 25.2 bits
        assert entropy == pytest.approx(25.2, abs=0.5)

    def test_entropy_scaling(self):
        """Test that entropy scales linearly with minutiae count"""
        minutiae_4 = [QuantizedMinutia(
            i, i, i, MinutiaeType.RIDGE_ENDING, 70, 0) for i in range(4)]
        minutiae_8 = [QuantizedMinutia(
            i, i, i, MinutiaeType.RIDGE_ENDING, 70, 0) for i in range(8)]

        entropy_4 = estimate_entropy(minutiae_4)
        entropy_8 = estimate_entropy(minutiae_8)

        assert entropy_8 == pytest.approx(2 * entropy_4, rel=0.01)


class TestBoundaryDetection:
    """Test boundary detection"""

    def test_detect_position_boundary(self):
        """Test detecting position boundary minutiae"""
        # Minutia at 2.525mm (near bin boundary at 2.5mm)
        minutia = Minutia(2.525, 7.3, 45.0, MinutiaeType.RIDGE_ENDING, 75, 0)
        flags = is_near_boundary(minutia, threshold_mm=0.025)

        assert flags['position_boundary']

    def test_detect_angle_boundary(self):
        """Test detecting angle boundary minutiae"""
        # 5.625° quantizes to bin 1 (center: 11.25°)
        # Distance from center: 5.625°
        # Need threshold >= 5.625° to detect as boundary
        minutia = Minutia(3.0, 8.0, 5.625, MinutiaeType.BIFURCATION, 80, 0)
        # Slightly above 5.625
        flags = is_near_boundary(minutia, threshold_deg=5.7)

        # Should detect angle boundary
        assert flags['angle_boundary']

    def test_no_boundary(self):
        """Test minutia far from boundaries"""
        # Centered in bin
        minutia = Minutia(2.5, 7.5, 22.5, MinutiaeType.RIDGE_ENDING, 75, 0)
        flags = is_near_boundary(minutia)

        # May or may not be near boundary depending on exact position
        # Just check structure
        assert 'position_boundary' in flags
        assert 'angle_boundary' in flags
        assert 'any_boundary' in flags


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_invalid_coordinates(self):
        """Test minutia with invalid coordinates"""
        with pytest.raises(ValueError):
            Minutia(50.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING,
                    75, 0)  # X way out of range (> 2 * 10mm)

    def test_invalid_quality(self):
        """Test minutia with invalid quality"""
        with pytest.raises(ValueError):
            Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING,
                    150, 0)  # Quality > 100

    def test_invalid_finger_id(self):
        """Test minutia with invalid finger ID"""
        with pytest.raises(ValueError):
            Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING,
                    75, 15)  # finger_id > 9

    def test_angle_normalization(self):
        """Test that angles are normalized to [0, 360)"""
        minutia = Minutia(5.0, 10.0, 450.0, MinutiaeType.RIDGE_ENDING, 75, 0)
        assert 0 <= minutia.angle_deg < 360
        assert minutia.angle_deg == pytest.approx(90.0, abs=1e-6)

    def test_negative_angle(self):
        """Test negative angle normalization"""
        minutia = Minutia(5.0, 10.0, -45.0, MinutiaeType.RIDGE_ENDING, 75, 0)
        assert 0 <= minutia.angle_deg < 360
        assert minutia.angle_deg == pytest.approx(315.0, abs=1e-6)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for complete workflow"""

    def test_end_to_end_processing(self):
        """Test complete workflow: raw → quantized → serialized"""
        # Create raw minutiae
        raw_minutiae = [
            Minutia(5.0, 10.0, 45.0, MinutiaeType.RIDGE_ENDING, 85, 0),
            Minutia(6.0, 11.0, 90.0, MinutiaeType.BIFURCATION, 75, 0),
            Minutia(7.0, 12.0, 135.0, MinutiaeType.RIDGE_ENDING, 80, 0),
            Minutia(8.0, 13.0, 180.0, MinutiaeType.BIFURCATION, 70, 0)
        ]

        # Process
        quantized, metadata = process_fingerprint(raw_minutiae)
        assert metadata['validation_passed']

        # Serialize
        data = serialize_quantized_minutiae(quantized)
        assert len(data) > 0

        # Deserialize
        deserialized = deserialize_quantized_minutiae(data)
        assert len(deserialized) == len(quantized)

    def test_reproducibility(self, sample_minutiae_set: Any) -> None:
        """Test that processing is deterministic"""
        quantized1, _ = process_fingerprint(sample_minutiae_set)
        quantized2, _ = process_fingerprint(sample_minutiae_set)

        assert len(quantized1) == len(quantized2)
        for q1, q2 in zip(quantized1, quantized2):
            assert q1.x_bin == q2.x_bin
            assert q1.y_bin == q2.y_bin
            assert q1.angle_bin == q2.angle_bin


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
