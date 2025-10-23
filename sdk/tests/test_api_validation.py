"""
Tests for Input Validation Module

Tests all validators for:
- Cardano addresses (mainnet, testnet, stake)
- DID identifiers (deterministic, legacy)
- Hex strings (various lengths)
- API keys
- JSON structure (depth, size)
- Biometric metadata

License: Open-source (MIT)
"""

import pytest
from src.decentralized_did.api.validators import (
    # Validators
    validate_cardano_address,
    validate_did_identifier,
    validate_hex_string,
    validate_hash_256,
    validate_hash_512,
    validate_api_key,
    validate_json_depth,
    validate_json_size,
    validate_array_length,
    validate_biometric_digest,
    validate_metadata_structure,
    # Errors
    InvalidAddressError,
    InvalidDIDError,
    InvalidHexError,
    InvalidMetadataError,
    InputTooLargeError,
    ValidationError,
)


# ============================================================================
# Cardano Address Validation Tests
# ============================================================================

class TestCardanoAddressValidation:
    """Tests for Cardano address validation"""

    def test_valid_mainnet_address(self):
        """Test valid mainnet payment address"""
        valid_addresses = [
            "addr1qxyz123456789abcdefghijklmnopqrstuvwxyz123456789abcdefghijk",
            "addr1q" + "a" * 56,  # Minimum length
            "addr1q" + "a" * 96,  # Maximum length
        ]
        for addr in valid_addresses:
            assert validate_cardano_address(addr) is True

    def test_valid_testnet_address(self):
        """Test valid testnet payment address"""
        valid_addresses = [
            "addr_test1qxyz123456789abcdefghijklmnopqrstuvwxyz123456789abcde",  # 63 chars
            "addr_test1q" + "a" * 52,  # Exactly 63 chars (minimum)
        ]
        for addr in valid_addresses:
            assert validate_cardano_address(addr)

    def test_mainnet_address_with_network_filter(self):
        """Test mainnet address with network filter"""
        addr = "addr1qxyz123456789abcdefghijklmnopqrstuvwxyz123456789abcdefgh"
        assert validate_cardano_address(addr, network="mainnet") is True

        # Should fail testnet check
        with pytest.raises(InvalidAddressError, match="Invalid testnet"):
            validate_cardano_address(addr, network="testnet")

    def test_testnet_address_with_network_filter(self):
        """Test testnet address with network filter"""
        addr = "addr_test1qxyz123456789abcdefghijklmnopqrstuvwxyz123456789abcde"  # 63 chars
        assert validate_cardano_address(addr, network="testnet") is True

        # Should fail mainnet check
        with pytest.raises(InvalidAddressError, match="Invalid mainnet"):
            validate_cardano_address(addr, network="mainnet")

    def test_stake_address_rejected_by_default(self):
        """Test stake address rejected without allow_stake flag"""
        stake_addr = "stake1" + "a" * 53
        with pytest.raises(InvalidAddressError, match="Stake addresses not allowed"):
            validate_cardano_address(stake_addr)

    def test_stake_address_allowed_with_flag(self):
        """Test stake address allowed with allow_stake=True"""
        stake_addr = "stake1" + "a" * 53
        assert validate_cardano_address(stake_addr, allow_stake=True) is True

    def test_invalid_address_prefix(self):
        """Test address with invalid prefix"""
        invalid_addrs = [
            "addr2qxyz123456789abcdefghijklmnopqrstuvwxyz123456789abcdefghijk",
            "addr_mainnet1qxyz" + "a" * 56,
            "xyz1qxyz" + "a" * 56,
        ]
        for addr in invalid_addrs:
            with pytest.raises(InvalidAddressError):
                validate_cardano_address(addr)

    def test_address_too_short(self):
        """Test address shorter than minimum length"""
        short_addr = "addr1qxyz"  # Only 10 chars
        with pytest.raises(InvalidAddressError, match="length.*outside valid range"):
            validate_cardano_address(short_addr)

    def test_address_too_long(self):
        """Test address longer than maximum length"""
        long_addr = "addr1q" + "a" * 110  # Too long
        with pytest.raises(InvalidAddressError, match="length.*outside valid range"):
            validate_cardano_address(long_addr)

    def test_empty_address(self):
        """Test empty address"""
        with pytest.raises(InvalidAddressError, match="non-empty string"):
            validate_cardano_address("")

    def test_non_string_address(self):
        """Test non-string address"""
        with pytest.raises(InvalidAddressError, match="non-empty string"):
            validate_cardano_address(None)  # type: ignore


# ============================================================================
# DID Identifier Validation Tests
# ============================================================================

class TestDIDValidation:
    """Tests for DID identifier validation"""

    def test_valid_deterministic_mainnet_did(self):
        """Test valid deterministic mainnet DID"""
        valid_dids = [
            "did:cardano:mainnet:zQmHash123456789",
            "did:cardano:mainnet:" + "a" * 50,
        ]
        for did in valid_dids:
            assert validate_did_identifier(did) is True

    def test_valid_deterministic_testnet_did(self):
        """Test valid deterministic testnet DID"""
        did = "did:cardano:testnet:zQmHash123456789"
        assert validate_did_identifier(did) is True

    def test_valid_legacy_did(self):
        """Test valid legacy wallet-based DID"""
        legacy_did = f"did:cardano:addr1{'a'*56}´{'f'*64}"
        assert validate_did_identifier(legacy_did, allow_legacy=True) is True

    def test_legacy_did_rejected_when_disabled(self):
        """Test legacy DID rejected when allow_legacy=False"""
        legacy_did = f"did:cardano:addr1{'a'*56}´{'f'*64}"
        with pytest.raises(InvalidDIDError, match="Invalid DID format"):
            validate_did_identifier(legacy_did, allow_legacy=False)

    def test_invalid_did_prefix(self):
        """Test DID with invalid prefix"""
        invalid_dids = [
            "did:ethereum:mainnet:hash",
            "did:bitcoin:mainnet:hash",
            "cardano:mainnet:hash",
        ]
        for did in invalid_dids:
            with pytest.raises(InvalidDIDError, match="must start with 'did:cardano:'"):
                validate_did_identifier(did)

    def test_did_too_short(self):
        """Test DID shorter than minimum length"""
        short_did = "did:cardano:m:z"  # Only 16 chars
        with pytest.raises(InvalidDIDError, match="length.*outside valid range"):
            validate_did_identifier(short_did)

    def test_did_too_long(self):
        """Test DID longer than maximum length"""
        long_did = "did:cardano:mainnet:" + "a" * 200
        with pytest.raises(InvalidDIDError, match="length.*outside valid range"):
            validate_did_identifier(long_did)

    def test_empty_did(self):
        """Test empty DID"""
        with pytest.raises(InvalidDIDError, match="non-empty string"):
            validate_did_identifier("")


# ============================================================================
# Hex String Validation Tests
# ============================================================================

class TestHexValidation:
    """Tests for hex string validation"""

    def test_valid_hex_string(self):
        """Test valid hex strings"""
        valid_hex = [
            "abcdef123456",
            "ABCDEF123456",
            "0123456789abcdefABCDEF",
            "f" * 64,
        ]
        for hex_str in valid_hex:
            assert validate_hex_string(hex_str) is True

    def test_hex_with_min_length(self):
        """Test hex validation with minimum length"""
        assert validate_hex_string("abcd", min_length=4) is True

        with pytest.raises(InvalidHexError, match="length.*< minimum"):
            validate_hex_string("abc", min_length=4)

    def test_hex_with_max_length(self):
        """Test hex validation with maximum length"""
        assert validate_hex_string("abcd", max_length=4) is True

        with pytest.raises(InvalidHexError, match="length.*> maximum"):
            validate_hex_string("abcde", max_length=4)

    def test_hex_with_exact_length(self):
        """Test hex validation with exact length"""
        assert validate_hex_string("abcd", exact_length=4) is True

        with pytest.raises(InvalidHexError, match="!= required"):
            validate_hex_string("abc", exact_length=4)

    def test_invalid_hex_characters(self):
        """Test hex string with invalid characters"""
        invalid_hex = [
            "abcdefg",  # 'g' not hex
            "abc def",  # space
            "abc-def",  # dash
            "xyz",      # non-hex letters
        ]
        for hex_str in invalid_hex:
            with pytest.raises(InvalidHexError, match="Invalid hex format"):
                validate_hex_string(hex_str)

    def test_hash_256_validation(self):
        """Test 256-bit hash validation"""
        valid_hash = "f" * 64
        assert validate_hash_256(valid_hash) is True

        with pytest.raises(InvalidHexError, match="256-bit hash"):
            validate_hash_256("f" * 63)  # Too short

    def test_hash_512_validation(self):
        """Test 512-bit hash validation"""
        valid_hash = "f" * 128
        assert validate_hash_512(valid_hash) is True

        with pytest.raises(InvalidHexError, match="512-bit hash"):
            validate_hash_512("f" * 127)  # Too short


# ============================================================================
# API Key Validation Tests
# ============================================================================

class TestAPIKeyValidation:
    """Tests for API key validation"""

    def test_valid_prod_api_key(self):
        """Test valid production API key"""
        valid_keys = [
            "did_prod_" + "a" * 32,
            "did_prod_" + "A" * 32,
            "did_prod_" + "0" * 64,
        ]
        for key in valid_keys:
            assert validate_api_key(key) is True

    def test_valid_test_api_key(self):
        """Test valid test API key"""
        valid_keys = [
            "did_test_" + "a" * 32,
            "did_test_" + "A" * 64,
        ]
        for key in valid_keys:
            assert validate_api_key(key) is True

    def test_invalid_api_key_prefix(self):
        """Test API key with invalid prefix"""
        invalid_keys = [
            "did_dev_" + "a" * 32,
            "api_prod_" + "a" * 32,
            "prod_" + "a" * 32,
        ]
        for key in invalid_keys:
            with pytest.raises(ValidationError, match="Invalid API key format"):
                validate_api_key(key)

    def test_api_key_too_short(self):
        """Test API key with insufficient length"""
        short_key = "did_prod_abc"  # Only 12 chars after prefix
        with pytest.raises(ValidationError, match="Invalid API key format"):
            validate_api_key(short_key)


# ============================================================================
# JSON Structure Validation Tests
# ============================================================================

class TestJSONStructureValidation:
    """Tests for JSON structure validation"""

    def test_json_depth_valid(self):
        """Test JSON depth within limits"""
        shallow = {"a": {"b": {"c": 1}}}  # Depth 3
        assert validate_json_depth(shallow, max_depth=5) is True

    def test_json_depth_exceeded(self):
        """Test JSON depth exceeds limit"""
        # Build deeply nested dict
        from typing import Any, Dict
        deep: Dict[str, Any] = {"level": 1}
        current = deep
        for i in range(15):
            current["next"] = {"level": i + 2}
            current = current["next"]

        with pytest.raises(InputTooLargeError, match="depth.*exceeds"):
            validate_json_depth(deep, max_depth=10)

    def test_json_depth_with_arrays(self):
        """Test JSON depth with nested arrays"""
        nested = {"a": [{"b": [{"c": 1}]}]}  # Depth 4
        assert validate_json_depth(nested, max_depth=5) is True

    def test_json_size_valid(self):
        """Test JSON size within limits"""
        small_obj = {"key": "value" * 100}
        assert validate_json_size(small_obj, max_size=10000) is True

    def test_json_size_exceeded(self):
        """Test JSON size exceeds limit"""
        large_obj = {"key": "x" * 1000000}  # 1MB+ string
        with pytest.raises(InputTooLargeError, match="size.*exceeds"):
            validate_json_size(large_obj, max_size=1000)  # 1KB limit

    def test_array_length_valid(self):
        """Test array length within limits"""
        arr = list(range(100))
        assert validate_array_length(arr, max_length=1000) is True

    def test_array_length_exceeded(self):
        """Test array length exceeds limit"""
        arr = list(range(2000))
        with pytest.raises(InputTooLargeError, match="length.*exceeds"):
            validate_array_length(arr, max_length=1000)


# ============================================================================
# Biometric Metadata Validation Tests
# ============================================================================

class TestBiometricValidation:
    """Tests for biometric metadata validation"""

    def test_valid_biometric_digest(self):
        """Test valid biometric digest (256-bit hex)"""
        valid_digest = "f" * 64
        assert validate_biometric_digest(valid_digest) is True

    def test_invalid_biometric_digest(self):
        """Test invalid biometric digest"""
        with pytest.raises(InvalidHexError):
            validate_biometric_digest("f" * 63)  # Too short

    def test_valid_metadata_v1_1(self):
        """Test valid metadata v1.1 structure"""
        metadata = {
            "version": "1.1",
            "digest": "f" * 64,
            "controllers": ["addr1" + "a" * 56],
            "enrollment_timestamp": "2025-10-15T12:00:00Z",
            "revoked": False,
        }
        assert validate_metadata_structure(metadata) is True

    def test_valid_metadata_v1_0(self):
        """Test valid metadata v1.0 structure"""
        metadata = {
            "version": "1.0",
            "digest": "f" * 64,
            "controllers": ["addr1" + "a" * 56],
        }
        assert validate_metadata_structure(metadata) is True

    def test_metadata_missing_version(self):
        """Test metadata missing version field"""
        metadata = {
            "digest": "f" * 64,
            "controllers": ["addr1" + "a" * 56],
        }
        with pytest.raises(InvalidMetadataError, match="Missing required field: version"):
            validate_metadata_structure(metadata)

    def test_metadata_invalid_version(self):
        """Test metadata with invalid version"""
        metadata = {
            "version": "2.0",  # Invalid version
            "digest": "f" * 64,
            "controllers": ["addr1" + "a" * 56],
        }
        with pytest.raises(InvalidMetadataError, match="Version must be"):
            validate_metadata_structure(metadata)

    def test_metadata_missing_digest(self):
        """Test metadata missing digest field"""
        metadata = {
            "version": "1.1",
            "controllers": ["addr1" + "a" * 56],
        }
        with pytest.raises(InvalidMetadataError, match="Missing required field: digest"):
            validate_metadata_structure(metadata)

    def test_metadata_invalid_digest(self):
        """Test metadata with invalid digest"""
        metadata = {
            "version": "1.1",
            "digest": "invalid",  # Not a hash
            "controllers": ["addr1" + "a" * 56],
        }
        with pytest.raises(InvalidHexError):
            validate_metadata_structure(metadata)

    def test_metadata_missing_controllers(self):
        """Test metadata missing controllers field"""
        metadata = {
            "version": "1.1",
            "digest": "f" * 64,
        }
        with pytest.raises(InvalidMetadataError, match="Missing required field: controllers"):
            validate_metadata_structure(metadata)

    def test_metadata_empty_controllers(self):
        """Test metadata with empty controllers list"""
        metadata = {
            "version": "1.1",
            "digest": "f" * 64,
            "controllers": [],  # Empty
        }
        with pytest.raises(InvalidMetadataError, match="non-empty list"):
            validate_metadata_structure(metadata)

    def test_metadata_invalid_controller_address(self):
        """Test metadata with invalid controller address"""
        metadata = {
            "version": "1.1",
            "digest": "f" * 64,
            "controllers": ["invalid_address"],
        }
        with pytest.raises(InvalidAddressError):
            validate_metadata_structure(metadata)

    def test_metadata_invalid_timestamp_format(self):
        """Test metadata with invalid timestamp format"""
        metadata = {
            "version": "1.1",
            "digest": "f" * 64,
            "controllers": ["addr1" + "a" * 56],
            "enrollment_timestamp": "invalid",
        }
        with pytest.raises(InvalidMetadataError, match="ISO 8601 format"):
            validate_metadata_structure(metadata)

    def test_metadata_not_dict(self):
        """Test metadata that is not a dictionary"""
        with pytest.raises(InvalidMetadataError, match="must be a dictionary"):
            validate_metadata_structure("not a dict")  # type: ignore


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
