"""
Focused tests for JSON Schema validation system.

Tests core validation functionality with correct schema structures.
"""

import pytest
from decentralized_did.validator import (
    SchemaValidator,
    ValidationError,
    validate_fingerprint_input,
    validate_helper_data,
    validate_config,
)


class TestFingerprintValidation:
    """Test fingerprint input validation."""

    def test_valid_fingerprint_single_finger(self):
        """Test validation of valid single-finger fingerprint input."""
        data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": 100, "y": 100, "angle": 45, "type": "ending"},
                        {"x": 200, "y": 200, "angle": 90, "type": "bifurcation"},
                        {"x": 300, "y": 300, "angle": 135, "type": "ending"},
                        {"x": 400, "y": 400, "angle": 180, "type": "bifurcation"},
                        {"x": 500, "y": 500, "angle": 225, "type": "ending"},
                        {"x": 600, "y": 600, "angle": 270, "type": "bifurcation"},
                        {"x": 700, "y": 700, "angle": 315, "type": "ending"},
                        {"x": 800, "y": 800, "angle": 0, "type": "bifurcation"},
                        {"x": 900, "y": 900, "angle": 60, "type": "ending"},
                        {"x": 1000, "y": 1000, "angle": 120, "type": "bifurcation"},
                    ],
                    "quality": 85.0,
                    "imageWidth": 500,
                    "imageHeight": 500
                }
            ]
        }
        # Should not raise
        validate_fingerprint_input(data)

    def test_valid_fingerprint_with_metadata(self):
        """Test validation with optional metadata."""
        data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": "left_index",
                    "minutiae": [
                        {"x": i * 100, "y": i * 100, "angle": i * 36,
                            "type": "ending" if i % 2 == 0 else "bifurcation"}
                        for i in range(10)
                    ]
                }
            ],
            "metadata": {
                "captureDate": "2025-10-11T12:00:00Z",
                "deviceId": "FP5000",
                "resolution": 500
            }
        }
        # Should not raise
        validate_fingerprint_input(data)

    def test_missing_required_version(self):
        """Test validation fails when version is missing."""
        data = {
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": 100, "y": 100, "angle": 45, "type": "ending"}
                        for _ in range(10)
                    ]
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        assert "version" in exc_info.value.message.lower()

    def test_missing_required_fingers(self):
        """Test validation fails when fingers array is missing."""
        data = {
            "version": "1.0"
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        assert "fingers" in exc_info.value.message.lower()

    def test_invalid_finger_id(self):
        """Test validation fails with invalid finger ID."""
        data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": "invalid_finger",
                    "minutiae": [
                        {"x": 100, "y": 100, "angle": 45, "type": "ending"}
                        for _ in range(10)
                    ]
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        assert "finger_id" in exc_info.value.field_path or "finger_id" in exc_info.value.message.lower()

    def test_too_few_minutiae(self):
        """Test validation fails with < 10 minutiae points."""
        data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": 100, "y": 100, "angle": 45, "type": "ending"},
                        {"x": 200, "y": 200, "angle": 90, "type": "bifurcation"}
                    ]
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        # Should mention "too short" in the message
        assert "too short" in exc_info.value.message.lower()

    def test_invalid_minutia_type(self):
        """Test validation fails with invalid minutia type."""
        data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": 100, "y": 100, "angle": 45, "type": "invalid_type"}
                        for _ in range(10)
                    ]
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        # Should mention enum or "not one of"
        assert "not one of" in exc_info.value.message.lower(
        ) or "enum" in exc_info.value.message.lower()

    def test_invalid_quality_range(self):
        """Test validation fails with quality out of range."""
        data = {
            "version": "1.0",
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": i * 100, "y": i * 100,
                            "angle": i * 36, "type": "ending"}
                        for i in range(10)
                    ],
                    "quality": 150.0  # Invalid: > 100
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        # Should mention maximum or greater than
        assert "maximum" in exc_info.value.message.lower(
        ) or "greater" in exc_info.value.message.lower()


class TestHelperDataValidation:
    """Test helper data validation."""

    def test_valid_helper_data_single_finger(self):
        """Test validation of valid single-finger helper data."""
        data = {
            "version": "1.0",
            "algorithm": "fuzzy-extractor-bch127-blake2b",
            "fingers": {
                "right_thumb": {
                    "fingerId": "right_thumb",
                    "version": 1,
                    "salt": "0123456789abcdef" * 4,  # 64 hex chars (32 bytes)
                    "personalization": "fedcba9876543210" * 4,  # 64 hex chars
                    # 16 hex chars (8 bytes)
                    "bchSyndrome": "abcdef0123456789",
                    "hmac": "0" * 64  # 64 hex chars (32 bytes)
                }
            }
        }
        # Should not raise
        validate_helper_data(data)

    def test_valid_helper_data_multiple_fingers(self):
        """Test validation with multiple fingers."""
        data = {
            "version": "1.0",
            "algorithm": "fuzzy-extractor-bch127-blake2b",
            "fingers": {
                "right_thumb": {
                    "fingerId": "right_thumb",
                    "version": 1,
                    "salt": "a" * 64,
                    "personalization": "b" * 64,
                    "bchSyndrome": "c" * 16,
                    "hmac": "d" * 64
                },
                "left_index": {
                    "fingerId": "left_index",
                    "version": 1,
                    "salt": "e" * 64,
                    "personalization": "f" * 64,
                    "bchSyndrome": "0" * 16,
                    "hmac": "1" * 64
                }
            }
        }
        # Should not raise
        validate_helper_data(data)

    def test_missing_required_algorithm(self):
        """Test validation fails when algorithm is missing."""
        data = {
            "version": "1.0",
            "fingers": {
                "right_thumb": {
                    "fingerId": "right_thumb",
                    "version": 1,
                    "salt": "0" * 64,
                    "personalization": "1" * 64,
                    "bchSyndrome": "a" * 16,
                    "hmac": "b" * 64
                }
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(data)
        assert "algorithm" in exc_info.value.message.lower()

    def test_invalid_salt_length(self):
        """Test validation fails with incorrect salt length."""
        data = {
            "version": "1.0",
            "algorithm": "fuzzy-extractor-bch127-blake2b",
            "fingers": {
                "right_thumb": {
                    "fingerId": "right_thumb",
                    "version": 1,
                    "salt": "short",  # Invalid: not 64 hex chars
                    "personalization": "1" * 64,
                    "bchSyndrome": "a" * 16,
                    "hmac": "b" * 64
                }
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(data)
        # Should mention pattern match failure
        assert "does not match" in exc_info.value.message or "pattern" in exc_info.value.message.lower()

    def test_invalid_hex_format(self):
        """Test validation fails with non-hex characters."""
        data = {
            "version": "1.0",
            "algorithm": "fuzzy-extractor-bch127-blake2b",
            "fingers": {
                "right_thumb": {
                    "fingerId": "right_thumb",
                    "version": 1,
                    "salt": "GGGGGGGG" + ("0" * 56),  # Invalid: G is not hex
                    "personalization": "1" * 64,
                    "bchSyndrome": "a" * 16,
                    "hmac": "b" * 64
                }
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(data)
        # Should mention pattern match failure
        assert "does not match" in exc_info.value.message or "pattern" in exc_info.value.message.lower()


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_minimal_config(self):
        """Test validation of minimal valid config."""
        data = {
            "general": {
                "verbosity": "normal"
            }
        }
        # Should not raise
        validate_config(data)

    def test_valid_full_config(self):
        """Test validation of complete config."""
        data = {
            "general": {
                "verbosity": "verbose",
                "jsonOutput": True,
                "colorOutput": False
            },
            "biometric": {
                "qualityThreshold": 75,
                "minMinutiae": 25,
                "gridSize": 60
            },
            "storage": {
                "backend": "ipfs",
                "ipfs": {
                    "apiUrl": "http://localhost:5001",
                    "gateway": "http://localhost:8080",
                    "pinning": True
                }
            }
        }
        # Should not raise
        validate_config(data)

    def test_invalid_verbosity_value(self):
        """Test validation fails with invalid verbosity."""
        data = {
            "general": {
                "verbosity": "invalid_level"
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_config(data)
        assert "verbosity" in exc_info.value.message.lower(
        ) or "enum" in exc_info.value.message.lower()

    def test_invalid_quality_threshold(self):
        """Test validation fails with out-of-range quality threshold."""
        data = {
            "biometric": {
                "qualityThreshold": 150  # Invalid: > 100
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_config(data)
        assert "qualityThreshold" in exc_info.value.message or "maximum" in exc_info.value.message.lower()

    def test_invalid_storage_backend(self):
        """Test validation fails with invalid storage backend."""
        data = {
            "storage": {
                "backend": "invalid_backend"
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_config(data)
        assert "backend" in exc_info.value.message.lower(
        ) or "enum" in exc_info.value.message.lower()


class TestErrorMessages:
    """Test error message quality."""

    def test_error_has_field_path(self):
        """Test that validation errors include field path."""
        data = {
            "version": "1.0",
            "fingers": []  # Invalid: minItems is 1
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)

        error = exc_info.value
        assert error.field_path is not None
        assert error.message is not None

    def test_error_has_suggestion(self):
        """Test that validation errors include suggestions."""
        data = {
            "version": "1.0"
            # Missing required 'fingers'
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)

        error = exc_info.value
        assert error.suggestion is not None
        assert len(error.suggestion) > 0

    def test_error_string_representation(self):
        """Test error string representation is informative."""
        data = {
            "version": "2.0",  # Invalid: must be "1.0"
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": i * 100, "y": i * 100,
                            "angle": i * 36, "type": "ending"}
                        for i in range(10)
                    ]
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)

        error_str = str(exc_info.value)
        assert "Validation Error" in error_str
        assert "Field:" in error_str or "version" in error_str.lower()


class TestSchemaVersioning:
    """Test schema versioning support."""

    def test_fingerprint_version_enforcement(self):
        """Test that fingerprint schema enforces version 1.0."""
        data = {
            "version": "2.0",  # Invalid version
            "fingers": [
                {
                    "finger_id": "right_thumb",
                    "minutiae": [
                        {"x": i * 100, "y": i * 100,
                            "angle": i * 36, "type": "ending"}
                        for i in range(10)
                    ]
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(data)
        assert "version" in exc_info.value.message.lower(
        ) or "const" in exc_info.value.message.lower()

    def test_helper_data_version_enforcement(self):
        """Test that helper data schema enforces version 1.0."""
        data = {
            "version": "2.0",  # Invalid version
            "algorithm": "fuzzy-extractor-bch127-blake2b",
            "fingers": {
                "right_thumb": {
                    "fingerId": "right_thumb",
                    "version": 1,
                    "salt": "0" * 64,
                    "personalization": "1" * 64,
                    "bchSyndrome": "a" * 16,
                    "hmac": "b" * 64
                }
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(data)
        assert "version" in exc_info.value.message.lower(
        ) or "const" in exc_info.value.message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
