"""
Input Validation for API Servers

Provides custom validators for:
- Cardano wallet addresses (mainnet, testnet)
- DID identifiers (did:cardano format)
- Hex strings (signatures, hashes, keys)
- Biometric digests and metadata
- JSON depth and size limits

License: Open-source (MIT)
"""

import re
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# ============================================================================
# Constants
# ============================================================================

# Cardano address patterns
MAINNET_ADDRESS_PATTERN = re.compile(r'^addr1[a-z0-9]{53,98}$')
TESTNET_ADDRESS_PATTERN = re.compile(r'^addr_test1[a-z0-9]{53,98}$')
STAKE_ADDRESS_PATTERN = re.compile(r'^stake1[a-z0-9]{53}$')
STAKE_TEST_ADDRESS_PATTERN = re.compile(r'^stake_test1[a-z0-9]{53}$')

# DID patterns
DID_CARDANO_PATTERN = re.compile(
    r'^did:cardano:(mainnet|testnet):[a-zA-Z0-9._-]+$'
)
DID_LEGACY_PATTERN = re.compile(
    r'^did:cardano:(addr1|addr_test1)[a-z0-9]{53,98}´[a-f0-9]{64}$'
)

# Hex patterns
HEX_PATTERN = re.compile(r'^[0-9a-fA-F]+$')
HASH_256_PATTERN = re.compile(r'^[0-9a-fA-F]{64}$')  # SHA-256, Blake2b-256
HASH_512_PATTERN = re.compile(r'^[0-9a-fA-F]{128}$')  # SHA-512, Blake2b-512

# API key patterns
API_KEY_PATTERN = re.compile(r'^did_(prod|test)_[a-zA-Z0-9]{32,64}$')

# Size limits
MAX_JSON_DEPTH = 10
MAX_JSON_SIZE_BYTES = 1024 * 1024  # 1 MB
MAX_STRING_LENGTH = 10000  # 10KB
MAX_ARRAY_LENGTH = 1000
MAX_METADATA_SIZE = 100 * 1024  # 100 KB


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(Exception):
    """Base class for validation errors"""
    pass


class InvalidAddressError(ValidationError):
    """Invalid Cardano address format"""
    pass


class InvalidDIDError(ValidationError):
    """Invalid DID format"""
    pass


class InvalidHexError(ValidationError):
    """Invalid hex string format"""
    pass


class InvalidMetadataError(ValidationError):
    """Invalid metadata structure or size"""
    pass


class InputTooLargeError(ValidationError):
    """Input exceeds size limits"""
    pass


# ============================================================================
# Cardano Address Validators
# ============================================================================

def validate_cardano_address(
    address: str,
    network: Optional[str] = None,
    allow_stake: bool = False
) -> bool:
    """
    Validate Cardano wallet address format

    Args:
        address: Cardano address to validate
        network: "mainnet", "testnet", or None (allow both)
        allow_stake: Whether to allow stake addresses

    Returns:
        True if valid

    Raises:
        InvalidAddressError: If address is invalid

    Examples:
        >>> validate_cardano_address("addr1qxyz...")  # mainnet payment
        True
        >>> validate_cardano_address("addr_test1qxyz...")  # testnet payment
        True
        >>> validate_cardano_address("stake1...")  # stake address
        Raises InvalidAddressError (unless allow_stake=True)
    """
    if not address or not isinstance(address, str):
        raise InvalidAddressError("Address must be a non-empty string")

    # Check length (mainnet: 58-105, testnet: 63-108, allow range for both)
    if len(address) < 58 or len(address) > 110:
        # Special case: testnet addresses can be shorter (prefix is longer)
        if address.startswith("addr_test1"):
            if len(address) < 63 or len(address) > 110:
                raise InvalidAddressError(
                    f"Testnet address length {len(address)} outside valid range (63-110)"
                )
        else:
            raise InvalidAddressError(
                f"Address length {len(address)} outside valid range (58-110)"
            )    # Check network-specific patterns
    is_mainnet_payment = MAINNET_ADDRESS_PATTERN.match(address)
    is_testnet_payment = TESTNET_ADDRESS_PATTERN.match(address)
    is_mainnet_stake = STAKE_ADDRESS_PATTERN.match(address)
    is_testnet_stake = STAKE_TEST_ADDRESS_PATTERN.match(address)

    # Validate stake addresses
    if is_mainnet_stake or is_testnet_stake:
        if not allow_stake:
            raise InvalidAddressError(
                "Stake addresses not allowed (use payment addresses)"
            )
        return True

    # Validate payment addresses
    if network == "mainnet":
        if not is_mainnet_payment:
            raise InvalidAddressError(
                "Invalid mainnet address format (must start with 'addr1')"
            )
    elif network == "testnet":
        if not is_testnet_payment:
            raise InvalidAddressError(
                "Invalid testnet address format (must start with 'addr_test1')"
            )
    else:
        # Allow both networks
        if not (is_mainnet_payment or is_testnet_payment):
            raise InvalidAddressError(
                "Invalid address format (must start with 'addr1' or 'addr_test1')"
            )

    return True


def validate_did_identifier(did: str, allow_legacy: bool = True) -> bool:
    """
    Validate DID identifier format

    Args:
        did: DID identifier to validate
        allow_legacy: Whether to allow legacy wallet-based format

    Returns:
        True if valid

    Raises:
        InvalidDIDError: If DID is invalid

    Examples:
        >>> validate_did_identifier("did:cardano:mainnet:zQmHash...")
        True
        >>> validate_did_identifier("did:cardano:addr1...´hash")  # legacy
        True (if allow_legacy=True)
    """
    if not did or not isinstance(did, str):
        raise InvalidDIDError("DID must be a non-empty string")

    # Check DID prefix
    if not did.startswith("did:cardano:"):
        raise InvalidDIDError("DID must start with 'did:cardano:'")

    # Check length (reasonable bounds)
    if len(did) < 30 or len(did) > 200:
        raise InvalidDIDError(
            f"DID length {len(did)} outside valid range (30-200)"
        )

    # Try deterministic format first (preferred)
    if DID_CARDANO_PATTERN.match(did):
        return True

    # Try legacy format
    if allow_legacy and DID_LEGACY_PATTERN.match(did):
        return True

    raise InvalidDIDError(
        "Invalid DID format (must be 'did:cardano:network:identifier')"
    )


# ============================================================================
# Hex String Validators
# ============================================================================

def validate_hex_string(
    hex_str: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    exact_length: Optional[int] = None
) -> bool:
    """
    Validate hex string format and length

    Args:
        hex_str: Hex string to validate
        min_length: Minimum length in characters
        max_length: Maximum length in characters
        exact_length: Exact required length

    Returns:
        True if valid

    Raises:
        InvalidHexError: If hex string is invalid

    Examples:
        >>> validate_hex_string("abcdef123456", min_length=12)
        True
        >>> validate_hex_string("abc", exact_length=64)
        Raises InvalidHexError
    """
    if not hex_str or not isinstance(hex_str, str):
        raise InvalidHexError("Hex string must be a non-empty string")

    # Check hex format
    if not HEX_PATTERN.match(hex_str):
        raise InvalidHexError(
            "Invalid hex format (must contain only 0-9, a-f, A-F)"
        )

    length = len(hex_str)

    # Check exact length
    if exact_length is not None:
        if length != exact_length:
            raise InvalidHexError(
                f"Hex string length {length} != required {exact_length}"
            )
        return True

    # Check min/max length
    if min_length is not None and length < min_length:
        raise InvalidHexError(
            f"Hex string length {length} < minimum {min_length}"
        )

    if max_length is not None and length > max_length:
        raise InvalidHexError(
            f"Hex string length {length} > maximum {max_length}"
        )

    return True


def validate_hash_256(hash_str: str) -> bool:
    """Validate 256-bit hash (SHA-256, Blake2b-256)"""
    if not HASH_256_PATTERN.match(hash_str):
        raise InvalidHexError("Invalid 256-bit hash (must be 64 hex chars)")
    return True


def validate_hash_512(hash_str: str) -> bool:
    """Validate 512-bit hash (SHA-512, Blake2b-512)"""
    if not HASH_512_PATTERN.match(hash_str):
        raise InvalidHexError("Invalid 512-bit hash (must be 128 hex chars)")
    return True


# ============================================================================
# API Key Validators
# ============================================================================

def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format

    Args:
        api_key: API key to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key or not isinstance(api_key, str):
        raise ValidationError("API key must be a non-empty string")

    if not API_KEY_PATTERN.match(api_key):
        raise ValidationError(
            "Invalid API key format (must be 'did_prod_...' or 'did_test_...')"
        )

    return True


# ============================================================================
# JSON Structure Validators
# ============================================================================

def validate_json_depth(obj: Any, max_depth: int = MAX_JSON_DEPTH) -> bool:
    """
    Validate JSON object depth to prevent stack overflow attacks

    Args:
        obj: JSON object (dict, list, or primitive)
        max_depth: Maximum nesting depth

    Returns:
        True if valid

    Raises:
        InputTooLargeError: If depth exceeds limit
    """
    def _check_depth(obj: Any, current_depth: int) -> int:
        if current_depth > max_depth:
            raise InputTooLargeError(
                f"JSON depth {current_depth} exceeds maximum {max_depth}"
            )

        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(
                _check_depth(v, current_depth + 1)
                for v in obj.values()
            )
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(
                _check_depth(item, current_depth + 1)
                for item in obj
            )
        else:
            return current_depth

    _check_depth(obj, 0)
    return True


def validate_json_size(obj: Any, max_size: int = MAX_JSON_SIZE_BYTES) -> bool:
    """
    Validate JSON object size to prevent memory exhaustion

    Args:
        obj: JSON object
        max_size: Maximum size in bytes

    Returns:
        True if valid

    Raises:
        InputTooLargeError: If size exceeds limit
    """
    import json

    try:
        serialized = json.dumps(obj)
        size = len(serialized.encode('utf-8'))

        if size > max_size:
            raise InputTooLargeError(
                f"JSON size {size} bytes exceeds maximum {max_size} bytes"
            )

        return True
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid JSON structure: {e}")


def validate_array_length(arr: list, max_length: int = MAX_ARRAY_LENGTH) -> bool:
    """
    Validate array length to prevent DoS attacks

    Args:
        arr: Array to validate
        max_length: Maximum array length

    Returns:
        True if valid

    Raises:
        InputTooLargeError: If array is too long
    """
    if not isinstance(arr, list):
        raise ValidationError("Input must be a list")

    if len(arr) > max_length:
        raise InputTooLargeError(
            f"Array length {len(arr)} exceeds maximum {max_length}"
        )

    return True


# ============================================================================
# Biometric Metadata Validators
# ============================================================================

def validate_biometric_digest(digest: str) -> bool:
    """
    Validate biometric digest format (256-bit hex)

    Args:
        digest: Biometric digest to validate

    Returns:
        True if valid

    Raises:
        InvalidHexError: If digest is invalid
    """
    return validate_hash_256(digest)


def validate_metadata_structure(metadata: Dict[str, Any]) -> bool:
    """
    Validate DID metadata structure

    Args:
        metadata: Metadata dictionary to validate

    Returns:
        True if valid

    Raises:
        InvalidMetadataError: If metadata is invalid
    """
    if not isinstance(metadata, dict):
        raise InvalidMetadataError("Metadata must be a dictionary")

    # Check required fields
    required_fields = ["version", "digest", "controllers"]
    for field in required_fields:
        if field not in metadata:
            raise InvalidMetadataError(f"Missing required field: {field}")

    # Validate version
    version = metadata.get("version")
    if not isinstance(version, str) or version not in ["1.0", "1.1"]:
        raise InvalidMetadataError("Version must be '1.0' or '1.1'")

    # Validate digest
    digest = metadata.get("digest")
    if not isinstance(digest, str):
        raise InvalidMetadataError("Digest must be a string")
    validate_biometric_digest(digest)

    # Validate controllers (v1.1)
    controllers = metadata.get("controllers")
    if not isinstance(controllers, list) or len(controllers) == 0:
        raise InvalidMetadataError("Controllers must be a non-empty list")

    for controller in controllers:
        if not isinstance(controller, str):
            raise InvalidMetadataError("All controllers must be strings")
        validate_cardano_address(controller)

    # Validate enrollment timestamp (optional)
    if "enrollment_timestamp" in metadata:
        timestamp = metadata["enrollment_timestamp"]
        if not isinstance(timestamp, str):
            raise InvalidMetadataError("Enrollment timestamp must be a string")
        # Basic ISO 8601 format check
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', timestamp):
            raise InvalidMetadataError(
                "Enrollment timestamp must be ISO 8601 format"
            )

    # Check size
    validate_json_size(metadata, MAX_METADATA_SIZE)
    validate_json_depth(metadata)

    return True


# ============================================================================
# Pydantic Field Validators (for use with BaseModel)
# ============================================================================

class CardanoAddressStr(str):
    """Custom string type with Cardano address validation"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> str:
        validate_cardano_address(v)
        return v


class DIDIdentifierStr(str):
    """Custom string type with DID validation"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> str:
        validate_did_identifier(v)
        return v


class HexStr(str):
    """Custom string type with hex validation"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> str:
        validate_hex_string(v)
        return v


class Hash256Str(str):
    """Custom string type with 256-bit hash validation"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str) -> str:
        validate_hash_256(v)
        return v
