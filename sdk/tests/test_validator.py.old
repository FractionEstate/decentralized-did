"""
Comprehensive tests for JSON Schema validation system.

Tests cover:
- Valid inputs (fingerprint, helper data, config)
- Invalid inputs (all error paths)
- Edge cases (empty, malformed, boundary values)
- Schema versioning and migration
- Error message quality and recovery guidance
"""

import json
import pytest
from pathlib import Path
from decentralized_did.validator import (
    SchemaValidator,
    ValidationError,
    validate_fingerprint_input,
    validate_helper_data,
    validate_config,
    get_schema_version,
)


# Fixtures for test data
@pytest.fixture
def valid_fingerprint():
    """Valid fingerprint input matching schema."""
    # Create 10 valid minutiae points (minimum required)
    minutiae = [
        {
            "x": 100 + i * 10,
            "y": 100 + i * 10,
            "angle": (i * 36) % 360,
            "type": "ending" if i % 2 == 0 else "bifurcation",
            "quality": 0.8 + (i * 0.01)
        }
        for i in range(10)
    ]

    return {
        "$schema": "https://decentralized-did.org/schemas/fingerprint-input-v1.0.json",
        "version": "1.0",
        "fingers": [
            {
                "finger_id": "right_thumb",
                "minutiae": minutiae,
                "quality": 85.0,
                "imageWidth": 500,
                "imageHeight": 500
            }
        ],
        "metadata": {
            "captureDate": "2025-10-11T12:00:00Z",
            "deviceId": "FP5000",
            "resolution": 500
        }
    }


@pytest.fixture
def valid_helper_data():
    """Valid helper data matching schema."""
    return {
        "version": "1.0",
        "algorithm": "fuzzy-extractor-bch127-blake2b",
        "fingers": {
            "right_thumb": {
                "fingerId": "right_thumb",
                "version": 1,
                "salt": "0" * 64,  # 32 bytes hex
                "personalization": "1" * 64,  # 32 bytes hex
                "bchSyndrome": "a" * 16,  # 8 bytes hex
                "hmac": "b" * 64  # 32 bytes hex
            }
        }
    }


@pytest.fixture
def valid_config():
    """Valid configuration matching schema."""
    return {
        "general": {
            "verbosity": "normal",
            "jsonOutput": False,
            "colorOutput": True
        },
        "biometric": {
            "qualityThreshold": 70,
            "minMinutiae": 20,
            "gridSize": 50
        },
        "storage": {
            "backend": "inline",
            "inline": {
                "embedInMetadata": True
            }
        },
        "validation": {
            "strictMode": False,
            "allowLowQuality": False
        },
        "output": {
            "format": "wallet",
            "pretty": True
        }
    }


class TestSchemaValidator:
    """Test the SchemaValidator class."""

    def test_validator_initialization(self):
        """Test validator initializes with correct schema path."""
        from decentralized_did.validator import FINGERPRINT_SCHEMA_PATH
        validator = SchemaValidator(FINGERPRINT_SCHEMA_PATH)
        assert validator.schema_path.exists()
        assert validator.schema_path.name.endswith(".schema.json")

    def test_load_and_validate(self, valid_fingerprint):
        """Test loading schema and validating data."""
        from decentralized_did.validator import FINGERPRINT_SCHEMA_PATH
        validator = SchemaValidator(FINGERPRINT_SCHEMA_PATH)
        # Should not raise
        validator.validate(valid_fingerprint)

    def test_validation_error_raised(self, valid_fingerprint):
        """Test validation raises error for invalid data."""
        from decentralized_did.validator import FINGERPRINT_SCHEMA_PATH
        validator = SchemaValidator(FINGERPRINT_SCHEMA_PATH)

        valid_fingerprint["format"] = "invalid"
        with pytest.raises(ValidationError):
            validator.validate(valid_fingerprint)


class TestFingerprintValidation:
    """Test fingerprint input validation."""

    def test_valid_fingerprint(self, valid_fingerprint):
        """Test validation of valid fingerprint input."""
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_missing_required_field(self, valid_fingerprint):
        """Test validation fails on missing required field."""
        del valid_fingerprint["format"]

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert "format" in error.field_path
        assert "required" in error.message.lower()
        assert error.suggestion is not None

    def test_invalid_format_value(self, valid_fingerprint):
        """Test validation fails on invalid format value."""
        valid_fingerprint["format"] = "invalid_format"

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert "format" in error.field_path
        assert "invalid_format" in str(
            error.actual) if error.actual else "format" in error.message
        assert error.expected is not None or "enum" in error.message.lower()

    def test_invalid_image_dimensions(self, valid_fingerprint):
        """Test validation fails on invalid image dimensions."""
        valid_fingerprint["image"]["width"] = -1

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert "width" in error.field_path
        assert error.actual is not None

    def test_invalid_quality_score(self, valid_fingerprint):
        """Test validation fails on out-of-range quality score."""
        valid_fingerprint["quality"]["nfiq_score"] = 150

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert "nfiq_score" in error.field_path
        assert error.actual is not None
        assert error.expected is not None or "maximum" in error.message.lower()

    def test_missing_optional_field(self, valid_fingerprint):
        """Test validation succeeds with missing optional field."""
        del valid_fingerprint["metadata"]["capture_environment"]
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_additional_properties_allowed(self, valid_fingerprint):
        """Test validation allows additional properties."""
        valid_fingerprint["custom_field"] = "custom_value"
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_invalid_timestamp_format(self, valid_fingerprint):
        """Test validation fails on invalid timestamp."""
        valid_fingerprint["metadata"]["capture_timestamp"] = "not-a-timestamp"

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert "timestamp" in error.field.lower()

    def test_minutiae_validation(self, valid_fingerprint):
        """Test minutiae data validation."""
        valid_fingerprint["minutiae"] = [
            {
                "x": 100,
                "y": 100,
                "angle": 45,
                "type": "ending",
                "quality": 0.9
            }
        ]
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_invalid_minutiae_type(self, valid_fingerprint):
        """Test validation fails on invalid minutiae type."""
        valid_fingerprint["minutiae"] = [
            {
                "x": 100,
                "y": 100,
                "angle": 45,
                "type": "invalid_type",
                "quality": 0.9
            }
        ]

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert "type" in error.field
        assert "invalid_type" in error.actual_value


class TestHelperDataValidation:
    """Test helper data validation."""

    def test_valid_helper_data(self, valid_helper_data):
        """Test validation of valid helper data."""
        result = validate_helper_data(valid_helper_data)
        assert result is True

    def test_missing_required_field(self, valid_helper_data):
        """Test validation fails on missing required field."""
        del valid_helper_data["salt"]

        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(valid_helper_data)

        error = exc_info.value
        assert error.field == "salt"
        assert "required" in error.message.lower()

    def test_invalid_salt_length(self, valid_helper_data):
        """Test validation fails on invalid salt length."""
        valid_helper_data["salt"] = "tooshort"

        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(valid_helper_data)

        error = exc_info.value
        assert "salt" in error.field
        assert "64" in error.expected_value

    def test_invalid_hex_format(self, valid_helper_data):
        """Test validation fails on non-hex characters."""
        valid_helper_data["salt"] = "z" * 64  # 'z' is not hex

        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(valid_helper_data)

        error = exc_info.value
        assert "salt" in error.field
        assert "hex" in error.message.lower()

    def test_invalid_format_value(self, valid_helper_data):
        """Test validation fails on invalid format."""
        valid_helper_data["format"] = "invalid_format"

        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(valid_helper_data)

        error = exc_info.value
        assert error.field == "format"
        assert "wallet" in error.expected_value or "cip30" in error.expected_value

    def test_invalid_quantization_bits(self, valid_helper_data):
        """Test validation fails on invalid quantization bits."""
        valid_helper_data["parameters"]["quantization_bits"] = 3

        with pytest.raises(ValidationError) as exc_info:
            validate_helper_data(valid_helper_data)

        error = exc_info.value
        assert "quantization_bits" in error.field
        assert "3" in error.actual_value

    def test_missing_optional_metadata(self, valid_helper_data):
        """Test validation succeeds with missing optional metadata."""
        del valid_helper_data["metadata"]["version"]
        result = validate_helper_data(valid_helper_data)
        assert result is True


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_config(self, valid_config):
        """Test validation of valid configuration."""
        result = validate_config(valid_config)
        assert result is True

    def test_missing_required_section(self, valid_config):
        """Test validation fails on missing required section."""
        del valid_config["general"]

        with pytest.raises(ValidationError) as exc_info:
            validate_config(valid_config)

        error = exc_info.value
        assert error.field == "general"

    def test_invalid_log_level(self, valid_config):
        """Test validation fails on invalid log level."""
        valid_config["general"]["log_level"] = "invalid_level"

        with pytest.raises(ValidationError) as exc_info:
            validate_config(valid_config)

        error = exc_info.value
        assert "log_level" in error.field
        assert "invalid_level" in error.actual_value

    def test_invalid_quality_threshold(self, valid_config):
        """Test validation fails on out-of-range quality threshold."""
        valid_config["biometric"]["quality_threshold"] = 150

        with pytest.raises(ValidationError) as exc_info:
            validate_config(valid_config)

        error = exc_info.value
        assert "quality_threshold" in error.field
        assert "150" in error.actual_value

    def test_invalid_storage_backend(self, valid_config):
        """Test validation fails on invalid storage backend."""
        valid_config["storage"]["backend"] = "invalid_backend"

        with pytest.raises(ValidationError) as exc_info:
            validate_config(valid_config)

        error = exc_info.value
        assert "backend" in error.field

    def test_ipfs_backend_config(self, valid_config):
        """Test validation of IPFS backend configuration."""
        valid_config["storage"]["backend"] = "ipfs"
        valid_config["storage"]["ipfs"] = {
            "api_url": "http://localhost:5001",
            "gateway_url": "http://localhost:8080",
            "pin": True,
            "timeout": 30
        }
        result = validate_config(valid_config)
        assert result is True

    def test_arweave_backend_config(self, valid_config):
        """Test validation of Arweave backend configuration."""
        valid_config["storage"]["backend"] = "arweave"
        valid_config["storage"]["arweave"] = {
            "gateway_url": "https://arweave.net",
            "wallet_path": "~/.arweave/wallet.json",
            "timeout": 60
        }
        result = validate_config(valid_config)
        assert result is True

    def test_file_backend_config(self, valid_config):
        """Test validation of file backend configuration."""
        valid_config["storage"]["backend"] = "file"
        valid_config["storage"]["file"] = {
            "base_path": "~/.dec-did/storage",
            "create_dirs": True,
            "backup": False
        }
        result = validate_config(valid_config)
        assert result is True

    def test_plugin_configuration(self, valid_config):
        """Test validation of plugin configuration."""
        valid_config["plugins"] = {
            "directory": "~/.dec-did/plugins",
            "auto_discover": True,
            "enabled": ["ipfs-storage", "custom-formatter"]
        }
        result = validate_config(valid_config)
        assert result is True

    def test_security_configuration(self, valid_config):
        """Test validation of security configuration."""
        valid_config["security"] = {
            "require_confirmation": True,
            "audit_log": True,
            "audit_log_path": "~/.dec-did/audit.log",
            "strict_validation": True
        }
        result = validate_config(valid_config)
        assert result is True


class TestSchemaVersioning:
    """Test schema versioning and migration."""

    def test_get_schema_version(self, valid_fingerprint):
        """Test extracting schema version from data."""
        version = get_schema_version(valid_fingerprint)
        assert version == "1.0"

    def test_missing_version_field(self):
        """Test handling of missing version field."""
        data = {"format": "wsq"}
        version = get_schema_version(data)
        assert version is None

    def test_version_mismatch_warning(self, valid_fingerprint):
        """Test warning on version mismatch."""
        valid_fingerprint["version"] = "2.0"  # Future version

        # Should still validate against v1.0 schema but may log warning
        # In production, this would trigger migration or compatibility check
        with pytest.raises(ValidationError):
            validate_fingerprint_input(valid_fingerprint)


class TestErrorMessages:
    """Test error message quality and recovery hints."""

    def test_error_message_structure(self, valid_fingerprint):
        """Test error message contains all required fields."""
        valid_fingerprint["format"] = "invalid"

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert error.field is not None
        assert error.message is not None
        assert error.actual_value is not None
        assert error.expected_value is not None
        assert error.recovery_hint is not None

    def test_recovery_hint_quality(self, valid_fingerprint):
        """Test recovery hints are actionable."""
        valid_fingerprint["quality"]["nfiq_score"] = 150

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        # Recovery hint should suggest valid range
        assert "0" in error.recovery_hint or "100" in error.recovery_hint

    def test_nested_field_error_path(self, valid_fingerprint):
        """Test error path for nested fields."""
        valid_fingerprint["image"]["width"] = -1

        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        # Field path should show nesting
        assert "image" in error.field
        assert "width" in error.field

    def test_multiple_errors_reported(self, valid_fingerprint):
        """Test multiple validation errors are reported."""
        valid_fingerprint["format"] = "invalid"
        valid_fingerprint["quality"]["nfiq_score"] = 150

        # jsonschema validates one error at a time by default
        # But our error message should be clear
        with pytest.raises(ValidationError) as exc_info:
            validate_fingerprint_input(valid_fingerprint)

        error = exc_info.value
        assert len(error.message) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_fingerprint(self):
        """Test validation of empty fingerprint."""
        with pytest.raises(ValidationError):
            validate_fingerprint_input({})

    def test_null_values(self, valid_fingerprint):
        """Test validation of null values."""
        valid_fingerprint["format"] = None

        with pytest.raises(ValidationError):
            validate_fingerprint_input(valid_fingerprint)

    def test_empty_strings(self, valid_fingerprint):
        """Test validation of empty strings."""
        valid_fingerprint["image"]["data"] = ""

        with pytest.raises(ValidationError):
            validate_fingerprint_input(valid_fingerprint)

    def test_boundary_quality_scores(self, valid_fingerprint):
        """Test boundary values for quality scores."""
        # Minimum valid score
        valid_fingerprint["quality"]["nfiq_score"] = 0
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

        # Maximum valid score
        valid_fingerprint["quality"]["nfiq_score"] = 100
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_large_image_dimensions(self, valid_fingerprint):
        """Test validation of large but valid image dimensions."""
        valid_fingerprint["image"]["width"] = 10000
        valid_fingerprint["image"]["height"] = 10000
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_unicode_metadata(self, valid_fingerprint):
        """Test validation with Unicode characters in metadata."""
        valid_fingerprint["metadata"]["notes"] = "Test with émojis 🔐"
        result = validate_fingerprint_input(valid_fingerprint)
        assert result is True

    def test_very_long_strings(self, valid_helper_data):
        """Test validation with very long string values."""
        # Helper data hex strings have maximum lengths
        valid_helper_data["salt"] = "0" * 64
        result = validate_helper_data(valid_helper_data)
        assert result is True

    def test_negative_numbers(self, valid_config):
        """Test validation rejects negative numbers where inappropriate."""
        valid_config["biometric"]["quality_threshold"] = -10

        with pytest.raises(ValidationError):
            validate_config(valid_config)


class TestIntegration:
    """Integration tests with real-world scenarios."""

    def test_full_enrollment_validation(self, valid_fingerprint, valid_helper_data):
        """Test validation of full enrollment workflow."""
        # Validate fingerprint input
        result1 = validate_fingerprint_input(valid_fingerprint)
        assert result1 is True

        # Validate generated helper data
        result2 = validate_helper_data(valid_helper_data)
        assert result2 is True

    def test_multi_finger_validation(self, valid_fingerprint):
        """Test validation of multi-finger enrollment."""
        fingers = []
        for position in ["right_thumb", "right_index", "left_thumb"]:
            finger = valid_fingerprint.copy()
            finger["metadata"]["finger_position"] = position
            result = validate_fingerprint_input(finger)
            assert result is True
            fingers.append(finger)

        assert len(fingers) == 3

    def test_config_with_all_backends(self, valid_config):
        """Test validation of config with all storage backends."""
        # Add all backend configs
        valid_config["storage"]["ipfs"] = {
            "api_url": "http://localhost:5001",
            "gateway_url": "http://localhost:8080",
            "pin": True,
            "timeout": 30
        }
        valid_config["storage"]["arweave"] = {
            "gateway_url": "https://arweave.net",
            "wallet_path": "~/.arweave/wallet.json",
            "timeout": 60
        }
        valid_config["storage"]["file"] = {
            "base_path": "~/.dec-did/storage",
            "create_dirs": True,
            "backup": False
        }

        result = validate_config(valid_config)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
