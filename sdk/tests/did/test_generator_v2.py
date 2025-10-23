"""
Unit tests for DID generation and metadata encoding (v2).

Tests:
- DID construction from master keys
- DID parsing and validation
- Metadata payload building
- Helper data entry creation
- Size estimation and limits
- URI validation
- Wallet address validation
- Schema validation

Phase 2, Task 4 - DID Generation and Metadata Encoding

Copyright 2025 Decentralized DID Project
License: Apache 2.0
"""

import json
import pytest
from src.did.generator_v2 import (
    # Constants
    DID_METHOD, DID_VERSION,
    HELPER_STORAGE_INLINE, HELPER_STORAGE_EXTERNAL,
    MAX_METADATA_SIZE_BYTES, RECOMMENDED_METADATA_SIZE_BYTES,
    # Data structures
    HelperDataEntry, BiometricMetadata, CardanoDID, WalletMetadataBundle,
    # Main API
    build_did_from_master_key, build_metadata, build_wallet_bundle,
    estimate_metadata_size,
    # Utility functions
    _encode_bytes, _decode_bytes, _validate_helper_uri, _validate_wallet_address,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_wallet_address():
    """Sample Cardano wallet address (mainnet)."""
    return "addr1qxy2l9k5z9p3v7q8hj0w5r3a4b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5f6"


@pytest.fixture
def sample_testnet_address():
    """Sample Cardano wallet address (testnet)."""
    return "addr_test1qxy2l9k5z9p3v7q8hj0w5r3a4b6c7d8e9f0g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6w7x8y9z0a1b2c3d4e5"


@pytest.fixture
def sample_master_key():
    """Sample 32-byte master key."""
    return b'\x01\x23\x45\x67\x89\xab\xcd\xef' * 4


@pytest.fixture
def sample_helper_entries():
    """Sample helper data entries for 4 fingers."""
    return [
        HelperDataEntry(
            finger_id="left_thumb",
            version=1,
            salt=_encode_bytes(b'\x00' * 16),
            personalization=_encode_bytes(b'\x01' * 16),
            bch_syndrome=_encode_bytes(b'\x02' * 64),
            hmac=_encode_bytes(b'\x03' * 32),
        ),
        HelperDataEntry(
            finger_id="left_index",
            version=1,
            salt=_encode_bytes(b'\x04' * 16),
            personalization=_encode_bytes(b'\x05' * 16),
            bch_syndrome=_encode_bytes(b'\x06' * 64),
            hmac=_encode_bytes(b'\x07' * 32),
        ),
        HelperDataEntry(
            finger_id="right_thumb",
            version=1,
            salt=_encode_bytes(b'\x08' * 16),
            personalization=_encode_bytes(b'\x09' * 16),
            bch_syndrome=_encode_bytes(b'\x0a' * 64),
            hmac=_encode_bytes(b'\x0b' * 32),
        ),
        HelperDataEntry(
            finger_id="right_index",
            version=1,
            salt=_encode_bytes(b'\x0c' * 16),
            personalization=_encode_bytes(b'\x0d' * 16),
            bch_syndrome=_encode_bytes(b'\x0e' * 64),
            hmac=_encode_bytes(b'\x0f' * 32),
        ),
    ]


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestEncoding:
    """Test base64url encoding/decoding."""

    def test_encode_decode_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        data = b'Hello, World!'
        encoded = _encode_bytes(data)
        decoded = _decode_bytes(encoded)
        assert decoded == data

    def test_encode_no_padding(self):
        """Test that encoding strips padding."""
        data = b'test'
        encoded = _encode_bytes(data)
        assert '=' not in encoded

    def test_decode_with_missing_padding(self):
        """Test decoding handles missing padding."""
        # "test" in base64url is "dGVzdA" (no padding needed)
        # "test1" in base64url is "dGVzdDE" (needs 1 padding)
        encoded = "dGVzdDE"
        decoded = _decode_bytes(encoded)
        assert decoded == b'test1'

    def test_encode_empty_bytes(self):
        """Test encoding empty bytes."""
        encoded = _encode_bytes(b'')
        assert encoded == ''

    def test_encode_url_safe(self):
        """Test that encoding uses URL-safe characters."""
        data = b'\xff' * 32
        encoded = _encode_bytes(data)
        assert '+' not in encoded  # '+' replaced with '-'
        assert '/' not in encoded  # '/' replaced with '_'


class TestWalletAddressValidation:
    """Test Cardano wallet address validation."""

    def test_valid_mainnet_address(self, sample_wallet_address):
        """Test valid mainnet address."""
        _validate_wallet_address(sample_wallet_address)  # Should not raise

    def test_valid_testnet_address(self, sample_testnet_address):
        """Test valid testnet address."""
        _validate_wallet_address(sample_testnet_address)  # Should not raise

    def test_empty_address(self):
        """Test empty address raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_wallet_address("")

    def test_invalid_prefix(self):
        """Test invalid prefix raises ValueError."""
        with pytest.raises(ValueError, match="Invalid wallet_address format"):
            _validate_wallet_address("xyz1234567890")

    def test_too_short_address(self):
        """Test address that's too short raises ValueError."""
        with pytest.raises(ValueError, match="Invalid wallet_address format"):
            _validate_wallet_address("addr1abc")


class TestHelperURIValidation:
    """Test helper URI validation."""

    def test_valid_https_uri(self):
        """Test valid HTTPS URI."""
        _validate_helper_uri(
            "https://example.com/helpers.json")  # Should not raise

    def test_valid_http_uri(self):
        """Test valid HTTP URI."""
        _validate_helper_uri("http://localhost:8080/data")  # Should not raise

    def test_valid_ipfs_uri(self):
        """Test valid IPFS URI."""
        _validate_helper_uri("ipfs://QmXyz123abc")  # Should not raise

    def test_empty_uri(self):
        """Test empty URI raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            _validate_helper_uri("")

    def test_missing_scheme(self):
        """Test URI without scheme raises ValueError."""
        with pytest.raises(ValueError, match="missing scheme"):
            _validate_helper_uri("example.com/data")

    def test_unsupported_scheme(self):
        """Test unsupported URI scheme raises ValueError."""
        with pytest.raises(ValueError, match="Invalid helper_uri scheme"):
            _validate_helper_uri("ftp://example.com/data")

    def test_http_missing_netloc(self):
        """Test HTTP URI without netloc raises ValueError."""
        with pytest.raises(ValueError, match="missing netloc"):
            _validate_helper_uri("https:///path")


# ============================================================================
# DID CONSTRUCTION TESTS
# ============================================================================

class TestCardanoDID:
    """Test CardanoDID class."""

    def test_from_master_key(self, sample_wallet_address, sample_master_key):
        """Test DID creation from master key."""
        did = CardanoDID.from_master_key(
            sample_wallet_address, sample_master_key)

        assert did.method == DID_METHOD
        assert did.wallet_address == sample_wallet_address
        assert len(did.fingerprint) > 0
        assert '=' not in did.fingerprint  # No padding

    def test_str_format(self, sample_wallet_address, sample_master_key):
        """Test DID string format."""
        did = CardanoDID.from_master_key(
            sample_wallet_address, sample_master_key)
        did_str = str(did)

        assert did_str.startswith(f"did:{DID_METHOD}:")
        assert sample_wallet_address in did_str
        assert "#" in did_str

    def test_parse_valid_did(self, sample_wallet_address):
        """Test parsing valid DID string."""
        did_str = f"did:cardano:{sample_wallet_address}#abc123xyz"
        did = CardanoDID.parse(did_str)

        assert did.method == "cardano"
        assert did.wallet_address == sample_wallet_address
        assert did.fingerprint == "abc123xyz"

    def test_parse_invalid_prefix(self):
        """Test parsing DID without 'did:' prefix."""
        with pytest.raises(ValueError, match="must start with 'did:'"):
            CardanoDID.parse("cardano:addr1xyz#abc")

    def test_parse_missing_fragment(self, sample_wallet_address):
        """Test parsing DID without fragment."""
        with pytest.raises(ValueError, match="missing fragment"):
            CardanoDID.parse(f"did:cardano:{sample_wallet_address}")

    def test_parse_wrong_method(self, sample_wallet_address):
        """Test parsing DID with wrong method."""
        with pytest.raises(ValueError, match="Invalid DID method"):
            CardanoDID.parse(f"did:btcr:{sample_wallet_address}#abc")

    def test_master_key_wrong_size(self, sample_wallet_address):
        """Test DID creation with wrong size master key."""
        with pytest.raises(ValueError, match="must be 32 bytes"):
            CardanoDID.from_master_key(sample_wallet_address, b'\x00' * 16)

    def test_roundtrip_parse_str(self, sample_wallet_address, sample_master_key):
        """Test DID creation → str → parse roundtrip."""
        did1 = CardanoDID.from_master_key(
            sample_wallet_address, sample_master_key)
        did_str = str(did1)
        did2 = CardanoDID.parse(did_str)

        assert did2.method == did1.method
        assert did2.wallet_address == did1.wallet_address
        assert did2.fingerprint == did1.fingerprint


class TestBuildDID:
    """Test build_did_from_master_key function."""

    def test_build_did_mainnet(self, sample_wallet_address, sample_master_key):
        """Test building DID for mainnet address."""
        did = build_did_from_master_key(
            sample_wallet_address, sample_master_key)

        assert str(did).startswith("did:cardano:")
        assert sample_wallet_address in str(did)

    def test_build_did_testnet(self, sample_testnet_address, sample_master_key):
        """Test building DID for testnet address."""
        did = build_did_from_master_key(
            sample_testnet_address, sample_master_key)

        assert str(did).startswith("did:cardano:")
        assert sample_testnet_address in str(did)

    def test_build_did_deterministic(self, sample_wallet_address, sample_master_key):
        """Test DID generation is deterministic."""
        did1 = build_did_from_master_key(
            sample_wallet_address, sample_master_key)
        did2 = build_did_from_master_key(
            sample_wallet_address, sample_master_key)

        assert str(did1) == str(did2)

    def test_build_did_different_keys(self, sample_wallet_address):
        """Test different master keys produce different DIDs."""
        key1 = b'\x00' * 32
        key2 = b'\xff' * 32

        did1 = build_did_from_master_key(sample_wallet_address, key1)
        did2 = build_did_from_master_key(sample_wallet_address, key2)

        assert str(did1) != str(did2)

    def test_build_did_invalid_address(self, sample_master_key):
        """Test building DID with invalid address."""
        with pytest.raises(ValueError, match="Invalid wallet_address format"):
            build_did_from_master_key("invalid_address", sample_master_key)


# ============================================================================
# HELPER DATA ENTRY TESTS
# ============================================================================

class TestHelperDataEntry:
    """Test HelperDataEntry class."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        entry = HelperDataEntry(
            finger_id="left_thumb",
            version=1,
            salt="abc",
            personalization="def",
            bch_syndrome="ghi",
            hmac="jkl",
        )

        d = entry.to_dict()

        assert d["fingerId"] == "left_thumb"
        assert d["version"] == 1
        assert d["salt"] == "abc"
        assert d["personalization"] == "def"
        assert d["bchSyndrome"] == "ghi"
        assert d["hmac"] == "jkl"

    def test_to_dict_json_serializable(self, sample_helper_entries):
        """Test that dict output is JSON-serializable."""
        entry = sample_helper_entries[0]
        d = entry.to_dict()

        # Should not raise
        json_str = json.dumps(d)
        assert len(json_str) > 0


# ============================================================================
# METADATA PAYLOAD TESTS
# ============================================================================

class TestBiometricMetadata:
    """Test BiometricMetadata class."""

    def test_inline_mode_valid(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test valid inline mode metadata."""
        metadata = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
            aggregation_mode="4/4",
        )

        metadata.validate()  # Should not raise

        assert metadata.wallet_address == sample_wallet_address
        assert metadata.helper_storage == HELPER_STORAGE_INLINE
        assert metadata.helper_data == sample_helper_entries
        assert metadata.helper_uri is None
        assert metadata.fingerprint_count == 4
        assert metadata.aggregation_mode == "4/4"

    def test_external_mode_valid(self, sample_wallet_address, sample_master_key):
        """Test valid external mode metadata."""
        metadata = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=[],
            helper_storage=HELPER_STORAGE_EXTERNAL,
            helper_uri="https://example.com/helpers.json",
        )

        metadata.validate()  # Should not raise

        assert metadata.helper_storage == HELPER_STORAGE_EXTERNAL
        assert metadata.helper_uri == "https://example.com/helpers.json"
        assert metadata.helper_data is None

    def test_inline_missing_helper_data(self, sample_wallet_address, sample_master_key):
        """Test inline mode without helper data raises ValueError."""
        with pytest.raises(ValueError, match="helper_data required"):
            build_metadata(
                wallet_address=sample_wallet_address,
                master_key=sample_master_key,
                helper_data_entries=[],
                helper_storage=HELPER_STORAGE_INLINE,
            )

    def test_external_missing_uri(self, sample_wallet_address, sample_master_key):
        """Test external mode without URI raises ValueError."""
        with pytest.raises(ValueError, match="helper_uri required"):
            build_metadata(
                wallet_address=sample_wallet_address,
                master_key=sample_master_key,
                helper_data_entries=[],
                helper_storage=HELPER_STORAGE_EXTERNAL,
            )

    def test_inline_with_uri_rejected(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test inline mode with URI raises ValueError."""
        metadata = BiometricMetadata(
            version=1,
            wallet_address=sample_wallet_address,
            id_hash="abc",
            helper_storage=HELPER_STORAGE_INLINE,
            helper_data=sample_helper_entries,
            helper_uri="https://example.com/data",  # Should be rejected
        )

        with pytest.raises(ValueError, match="helper_uri not allowed"):
            metadata.validate()

    def test_to_dict_inline(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test dictionary conversion for inline mode."""
        metadata = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
        )

        d = metadata.to_dict()

        assert d["version"] == DID_VERSION
        assert d["walletAddress"] == sample_wallet_address
        assert "biometric" in d
        assert d["biometric"]["helperStorage"] == HELPER_STORAGE_INLINE
        assert "helperData" in d["biometric"]
        assert len(d["biometric"]["helperData"]) == 4

    def test_to_dict_external(self, sample_wallet_address, sample_master_key):
        """Test dictionary conversion for external mode."""
        metadata = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=[],
            helper_storage=HELPER_STORAGE_EXTERNAL,
            helper_uri="ipfs://QmXyz",
        )

        d = metadata.to_dict()

        assert d["biometric"]["helperStorage"] == HELPER_STORAGE_EXTERNAL
        assert d["biometric"]["helperUri"] == "ipfs://QmXyz"
        assert "helperData" not in d["biometric"]

    def test_size_bytes(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test size calculation."""
        metadata = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
        )

        size = metadata.size_bytes()

        # Should be reasonable size
        assert size > 100  # At least has some content
        assert size < MAX_METADATA_SIZE_BYTES  # Within limits


class TestMetadataSizeValidation:
    """Test metadata size validation and limits."""

    def test_small_payload_accepted(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test small payload passes validation."""
        metadata = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries[:2],  # Only 2 fingers
            helper_storage=HELPER_STORAGE_INLINE,
        )

        metadata.validate()  # Should not raise

    def test_external_mode_smaller(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test external mode produces smaller payload."""
        inline = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
        )

        external = build_metadata(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=[],
            helper_storage=HELPER_STORAGE_EXTERNAL,
            helper_uri="https://example.com/data",
        )

        assert external.size_bytes() < inline.size_bytes()


# ============================================================================
# WALLET BUNDLE TESTS
# ============================================================================

class TestWalletMetadataBundle:
    """Test WalletMetadataBundle class."""

    def test_build_wallet_bundle_inline(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test building wallet bundle with inline storage."""
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
            fingerprint_count=4,
            aggregation_mode="4/4",
        )

        assert str(bundle.did).startswith("did:cardano:")
        assert bundle.metadata.helper_storage == HELPER_STORAGE_INLINE
        assert bundle.helper_data_json is None  # No external helper data

    def test_build_wallet_bundle_external(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test building wallet bundle with external storage."""
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_EXTERNAL,
            helper_uri="ipfs://QmXyz",
            fingerprint_count=4,
        )

        assert bundle.metadata.helper_storage == HELPER_STORAGE_EXTERNAL
        assert bundle.metadata.helper_uri == "ipfs://QmXyz"
        assert bundle.helper_data_json is not None  # External helper data generated
        assert "helperData" in bundle.helper_data_json

    def test_to_wallet_format(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test wallet format conversion."""
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
        )

        wallet_format = bundle.to_wallet_format()

        assert "1990" in wallet_format  # Default label
        assert "version" in wallet_format["1990"]
        assert "walletAddress" in wallet_format["1990"]
        assert "biometric" in wallet_format["1990"]

    def test_to_cip30_format(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test CIP-30 format conversion."""
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
        )

        cip30_format = bundle.to_cip30_format()

        assert "did" in cip30_format
        assert cip30_format["did"].startswith("did:cardano:")
        assert "metadata" in cip30_format
        assert isinstance(cip30_format["metadata"], list)
        assert len(cip30_format["metadata"]) == 1
        assert cip30_format["metadata"][0][0] == 1990  # Label

    def test_to_json_wallet(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test JSON export in wallet format."""
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
        )

        json_str = bundle.to_json(format="wallet")

        # Should be valid JSON
        data = json.loads(json_str)
        assert "1990" in data

    def test_to_json_cip30(self, sample_wallet_address, sample_master_key, sample_helper_entries):
        """Test JSON export in CIP-30 format."""
        bundle = build_wallet_bundle(
            wallet_address=sample_wallet_address,
            master_key=sample_master_key,
            helper_data_entries=sample_helper_entries,
            helper_storage=HELPER_STORAGE_INLINE,
        )

        json_str = bundle.to_json(format="cip30")

        # Should be valid JSON
        data = json.loads(json_str)
        assert "did" in data
        assert "metadata" in data


# ============================================================================
# SIZE ESTIMATION TESTS
# ============================================================================

class TestSizeEstimation:
    """Test metadata size estimation."""

    def test_estimate_inline_mode(self, sample_helper_entries):
        """Test size estimation for inline mode."""
        sizes = estimate_metadata_size(
            sample_helper_entries, helper_storage=HELPER_STORAGE_INLINE)

        assert "payload_bytes" in sizes
        assert "per_finger_bytes" in sizes
        assert "helper_data_bytes" in sizes
        assert "overhead_bytes" in sizes

        assert sizes["payload_bytes"] > 0
        assert sizes["helper_data_bytes"] > 0
        assert sizes["per_finger_bytes"] > 0

    def test_estimate_external_mode(self, sample_helper_entries):
        """Test size estimation for external mode."""
        sizes = estimate_metadata_size(
            sample_helper_entries, helper_storage=HELPER_STORAGE_EXTERNAL)

        # External mode should have no inline helper data
        assert sizes["helper_data_bytes"] == 0
        assert sizes["payload_bytes"] == sizes["overhead_bytes"]

    def test_estimate_scales_with_fingers(self):
        """Test that size scales linearly with number of fingers."""
        entries_2 = [
            HelperDataEntry("f1", 1, "a", "b", "c", "d"),
            HelperDataEntry("f2", 1, "e", "f", "g", "h"),
        ]
        entries_4 = entries_2 + [
            HelperDataEntry("f3", 1, "i", "j", "k", "l"),
            HelperDataEntry("f4", 1, "m", "n", "o", "p"),
        ]

        sizes_2 = estimate_metadata_size(entries_2, HELPER_STORAGE_INLINE)
        sizes_4 = estimate_metadata_size(entries_4, HELPER_STORAGE_INLINE)

        # 4 fingers should be roughly 2x the helper data size
        ratio = sizes_4["helper_data_bytes"] / sizes_2["helper_data_bytes"]
        assert 1.8 < ratio < 2.2  # Allow some JSON overhead variance


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_helper_entries_inline(self, sample_wallet_address, sample_master_key):
        """Test inline mode with empty helper entries."""
        with pytest.raises(ValueError, match="helper_data required"):
            build_metadata(
                wallet_address=sample_wallet_address,
                master_key=sample_master_key,
                helper_data_entries=[],
                helper_storage=HELPER_STORAGE_INLINE,
            )

    def test_invalid_storage_mode(self, sample_wallet_address, sample_master_key):
        """Test invalid storage mode."""
        # Create metadata with valid storage, then modify to invalid
        metadata = BiometricMetadata(
            version=1,
            wallet_address=sample_wallet_address,
            id_hash="abc",
            helper_storage=HELPER_STORAGE_INLINE,
        )
        # Bypass type checking to test runtime validation
        metadata.helper_storage = "invalid_mode"  # type: ignore

        with pytest.raises(ValueError, match="Invalid helper_storage"):
            metadata.validate()

    def test_missing_wallet_address(self, sample_master_key, sample_helper_entries):
        """Test metadata with missing wallet address."""
        metadata = BiometricMetadata(
            version=1,
            wallet_address="",  # Empty
            id_hash="abc",
            helper_storage=HELPER_STORAGE_INLINE,
            helper_data=sample_helper_entries,
        )

        with pytest.raises(ValueError, match="wallet_address is required"):
            metadata.validate()

    def test_missing_id_hash(self, sample_wallet_address, sample_helper_entries):
        """Test metadata with missing ID hash."""
        metadata = BiometricMetadata(
            version=1,
            wallet_address=sample_wallet_address,
            id_hash="",  # Empty
            helper_storage=HELPER_STORAGE_INLINE,
            helper_data=sample_helper_entries,
        )

        with pytest.raises(ValueError, match="id_hash is required"):
            metadata.validate()
