"""
Integration tests for Phase 4.5: Tamper-Proof Identity Security

Tests cover:
- Deterministic DID generation (Sybil-resistant)
- Metadata v1.1 format (multi-controller support)
- Backward compatibility with v1.0
- End-to-end enrollment workflow

Note: These tests verify the core Phase 4.5 features work correctly together.
Transaction builder integration is tested separately in test_cardano_transaction.py.
"""

import pytest
from datetime import datetime, timezone

from decentralized_did.did.generator import (
    generate_deterministic_did,
    build_did,
    build_metadata_payload,
)
from decentralized_did.cardano.wallet_integration import build_wallet_metadata_bundle


class TestDeterministicDIDGeneration:
    """Test deterministic DID generation for Sybil resistance."""

    def test_same_biometric_produces_same_did(self):
        """Verify that the same biometric commitment always produces the same DID."""
        digest = b"\x01" * 32

        did1 = generate_deterministic_did(digest, network="mainnet")
        did2 = generate_deterministic_did(digest, network="mainnet")

        assert did1 == did2, "Same biometric should produce identical DIDs"
        assert did1.startswith(
            "did:cardano:mainnet:"), "DID should have correct prefix"

        # Verify DID format: did:cardano:{network}:{base58_hash}
        parts = did1.split(":")
        assert len(parts) == 4
        assert parts[0] == "did"
        assert parts[1] == "cardano"
        assert parts[2] == "mainnet"
        assert len(parts[3]) > 40  # Base58 encoded 256-bit hash

    def test_different_biometrics_produce_different_dids(self):
        """Verify that different biometric commitments produce different DIDs."""
        digest1 = b"\x01" * 32
        digest2 = b"\x02" * 32

        did1 = generate_deterministic_did(digest1, network="mainnet")
        did2 = generate_deterministic_did(digest2, network="mainnet")

        assert did1 != did2, "Different biometrics should produce different DIDs"

    def test_network_parameter_affects_did(self):
        """Verify that network parameter affects DID prefix."""
        digest = b"\x01" * 32

        mainnet_did = generate_deterministic_did(digest, network="mainnet")
        testnet_did = generate_deterministic_did(digest, network="testnet")
        preprod_did = generate_deterministic_did(digest, network="preprod")

        assert mainnet_did.startswith("did:cardano:mainnet:")
        assert testnet_did.startswith("did:cardano:testnet:")
        # Preprod maps to testnet in DID
        assert preprod_did.startswith("did:cardano:testnet:")

        # Same biometric should produce same hash
        assert mainnet_did.split(":")[-1] == testnet_did.split(":")[-1]

    def test_deterministic_did_preserves_privacy(self):
        """Verify deterministic DIDs don't leak wallet addresses."""
        digest = b"\x01" * 32
        wallet = "addr1qxyz123"

        did = generate_deterministic_did(digest, network="mainnet")

        # DID should not contain wallet address
        assert wallet not in did
        assert "addr" not in did
        # Should be biometric-derived hash only
        assert did.startswith("did:cardano:mainnet:")

    def test_collision_resistance(self):
        """Verify different biometrics produce different DIDs (collision resistance)."""
        digests = [bytes([i] * 32) for i in range(10)]
        dids = [generate_deterministic_did(
            d, network="mainnet") for d in digests]

        # All DIDs should be unique
        assert len(dids) == len(set(dids))

        # All should have valid format
        for did in dids:
            assert did.startswith("did:cardano:mainnet:")


class TestMetadataV11Format:
    """Test metadata v1.1 format with multi-controller support."""

    def test_v11_uses_controllers_array(self):
        """Verify v1.1 metadata uses controllers array instead of walletAddress."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32

        metadata = build_metadata_payload(
            wallet_address=wallet,
            digest=digest,
            version="1.1",
        )

        assert metadata["version"] == "1.1"
        assert "controllers" in metadata
        controllers = metadata["controllers"]
        assert isinstance(controllers, list)
        assert wallet in controllers
        assert "walletAddress" not in metadata

    def test_v11_supports_enrollment_timestamp(self):
        """Verify v1.1 metadata includes enrollment timestamp."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32
        timestamp = "2025-10-14T12:00:00Z"

        metadata = build_metadata_payload(
            wallet_address=wallet,
            digest=digest,
            version="1.1",
            enrollment_timestamp=timestamp,
        )

        assert "enrollmentTimestamp" in metadata
        assert metadata["enrollmentTimestamp"] == timestamp

    def test_v11_supports_revocation(self):
        """Verify v1.1 metadata supports revocation mechanism."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32
        revoked_at = "2025-10-15T10:00:00Z"

        metadata = build_metadata_payload(
            wallet_address=wallet,
            digest=digest,
            version="1.1",
            revoked=True,
            revoked_at=revoked_at,
        )

        assert metadata["revoked"] is True
        assert metadata["revokedAt"] == revoked_at

    def test_v11_multi_controller_support(self):
        """Verify v1.1 supports multiple controllers for one DID."""
        wallet1 = "addr_test1qpl4w3u"
        wallet2 = "addr_test1xyz789"
        digest = b"\x01" * 32

        metadata = build_metadata_payload(
            wallet_address=wallet1,
            digest=digest,
            version="1.1",
            controllers=[wallet1, wallet2],
        )

        controllers = metadata["controllers"]
        assert isinstance(controllers, list)
        assert len(controllers) == 2
        assert wallet1 in controllers
        assert wallet2 in controllers


class TestBackwardCompatibility:
    """Test backward compatibility with metadata v1.0."""

    def test_v10_format_still_works(self):
        """Verify v1.0 format still works for backward compatibility."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32

        with pytest.warns(DeprecationWarning):
            metadata = build_metadata_payload(
                wallet_address=wallet,
                digest=digest,
                version="1.0",
            )

        assert metadata["version"] == 1
        assert "walletAddress" in metadata
        assert metadata["walletAddress"] == wallet
        assert "controllers" not in metadata

    def test_wallet_integration_defaults_to_v11(self):
        """Verify wallet integration defaults to v1.1 format."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32
        helper_map = {"left_thumb": {"finger_id": "left_thumb", "salt": "abc"}}

        bundle = build_wallet_metadata_bundle(
            wallet,
            digest,
            helper_map,
            label=2024,
        )

        metadata = bundle.as_wallet_metadata()["2024"]
        assert metadata["version"] == "1.1"
        assert "controllers" in metadata

    def test_wallet_integration_supports_v10(self):
        """Verify wallet integration can create v1.0 format when requested."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32
        helper_map = {"left_thumb": {"finger_id": "left_thumb", "salt": "abc"}}

        with pytest.warns(DeprecationWarning):
            bundle = build_wallet_metadata_bundle(
                wallet,
                digest,
                helper_map,
                label=2024,
                version="1.0",
            )

        metadata = bundle.as_wallet_metadata()["2024"]
        assert metadata["version"] == 1
        assert "walletAddress" in metadata

    def test_legacy_build_did_shows_deprecation(self):
        """Verify legacy wallet-based DID format shows deprecation warning."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32

        with pytest.warns(DeprecationWarning, match="Wallet-based DID format"):
            did = build_did(wallet, digest, deterministic=False)

        # Legacy format includes wallet address
        assert wallet in did


class TestSybilResistance:
    """Test Sybil resistance properties of deterministic DIDs."""

    def test_one_person_one_did_enforcement(self):
        """Verify that one biometric produces one DID across multiple wallets."""
        digest = b"\x01" * 32
        wallet1 = "addr_test1qpl4w3u"
        wallet2 = "addr_test1xyz789"

        # Same person tries to enroll with different wallets
        did1 = generate_deterministic_did(digest, network="mainnet")
        did2 = generate_deterministic_did(digest, network="mainnet")

        # Should produce identical DIDs (prevents Sybil attacks)
        assert did1 == did2

        # Metadata can have different controllers, but DID is the same
        metadata1 = build_metadata_payload(wallet1, digest, version="1.1")
        metadata2 = build_metadata_payload(wallet2, digest, version="1.1")

        # Controllers are different
        assert metadata1["controllers"] != metadata2["controllers"]


class TestEndToEndWorkflow:
    """Test complete enrollment workflow with v1.1 format."""

    def test_single_controller_enrollment(self):
        """Test enrolling a single controller with deterministic DID."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32
        helper_map = {"left_thumb": {"finger_id": "left_thumb", "salt": "abc"}}

        # Generate deterministic DID
        did = generate_deterministic_did(digest, network="mainnet")

        # Build metadata bundle
        bundle = build_wallet_metadata_bundle(
            wallet,
            digest,
            helper_map,
            label=674,
            version="1.1",
        )

        # Verify bundle structure
        metadata = bundle.as_wallet_metadata()["674"]
        controllers = metadata["controllers"]
        assert isinstance(controllers, list)
        assert controllers[0] == wallet
        assert metadata["version"] == "1.1"
        # enrollmentTimestamp is optional - not included by default
        # (transaction builder adds it when building full metadata)

    def test_multi_controller_metadata(self):
        """Test creating metadata with multiple controllers."""
        wallet1 = "addr_test1qpl4w3u"
        wallet2 = "addr_test1xyz789"
        digest = b"\x01" * 32

        # Generate deterministic DID
        did = generate_deterministic_did(digest, network="mainnet")

        # Build metadata with multiple controllers
        metadata = build_metadata_payload(
            wallet_address=wallet1,
            digest=digest,
            version="1.1",
            controllers=[wallet1, wallet2],
        )

        controllers = metadata["controllers"]
        assert isinstance(controllers, list)
        assert len(controllers) == 2
        assert wallet1 in controllers
        assert wallet2 in controllers

    def test_revocation_workflow(self):
        """Test enrollment with revocation capability."""
        wallet = "addr_test1qpl4w3u"
        digest = b"\x01" * 32

        # Initial enrollment (not revoked) - revoked field not included when False
        metadata_active = build_metadata_payload(
            wallet_address=wallet,
            digest=digest,
            version="1.1",
            revoked=False,
        )

        # revoked and revokedAt are optional - only included when revoked=True
        assert "revoked" not in metadata_active
        assert "revokedAt" not in metadata_active

        # Later revocation - now fields are included
        revoked_time = datetime.now(timezone.utc).isoformat()
        metadata_revoked = build_metadata_payload(
            wallet_address=wallet,
            digest=digest,
            version="1.1",
            revoked=True,
            revoked_at=revoked_time,
        )

        assert metadata_revoked["revoked"] is True
        assert metadata_revoked["revokedAt"] == revoked_time
