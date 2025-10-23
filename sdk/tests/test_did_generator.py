"""
Unit tests for deterministic DID generation (Phase 4.5).

Tests the core Sybil resistance mechanism: same biometric commitment
always produces the same DID.
"""

import pytest
from decentralized_did.did.generator import (
    generate_deterministic_did,
    verify_did_determinism,
    extract_did_hash,
    compute_commitment_fingerprint,
)


class TestDeterministicDIDGeneration:
    """Test suite for deterministic DID generation."""

    def test_deterministic_same_input_same_output(self):
        """Same commitment must always produce same DID."""
        commitment = b"test_commitment_data_12345"

        # Generate DID multiple times
        did1 = generate_deterministic_did(commitment, "mainnet")
        did2 = generate_deterministic_did(commitment, "mainnet")
        did3 = generate_deterministic_did(commitment, "mainnet")

        # All should be identical
        assert did1 == did2 == did3

    def test_different_inputs_different_outputs(self):
        """Different commitments must produce different DIDs."""
        commitment1 = b"commitment_alice"
        commitment2 = b"commitment_bob"
        commitment3 = b"commitment_charlie"

        did1 = generate_deterministic_did(commitment1, "mainnet")
        did2 = generate_deterministic_did(commitment2, "mainnet")
        did3 = generate_deterministic_did(commitment3, "mainnet")

        # All should be unique
        assert did1 != did2
        assert did1 != did3
        assert did2 != did3

    def test_did_format(self):
        """DIDs must follow correct format."""
        commitment = b"test_commitment"

        # Mainnet
        did_mainnet = generate_deterministic_did(commitment, "mainnet")
        assert did_mainnet.startswith("did:cardano:mainnet:")

        # Testnet
        did_testnet = generate_deterministic_did(commitment, "testnet")
        assert did_testnet.startswith("did:cardano:testnet:")

        # Preprod (normalized to testnet)
        did_preprod = generate_deterministic_did(commitment, "preprod")
        assert did_preprod.startswith("did:cardano:testnet:")

    def test_network_independence(self):
        """Same commitment on different networks produces different DIDs."""
        commitment = b"test_commitment"

        did_mainnet = generate_deterministic_did(commitment, "mainnet")
        did_testnet = generate_deterministic_did(commitment, "testnet")

        # Network is part of DID, so they differ
        assert did_mainnet != did_testnet

        # But the hash portion should be the same
        hash_mainnet = did_mainnet.split(":")[-1]
        hash_testnet = did_testnet.split(":")[-1]
        assert hash_mainnet == hash_testnet  # Same commitment, same hash

    def test_empty_commitment_raises_error(self):
        """Empty commitment must raise ValueError."""
        with pytest.raises(ValueError, match="Commitment cannot be empty"):
            generate_deterministic_did(b"", "mainnet")

    def test_invalid_network_raises_error(self):
        """Invalid network must raise ValueError."""
        commitment = b"test_commitment"

        with pytest.raises(ValueError, match="Invalid network"):
            generate_deterministic_did(commitment, "invalid")

        with pytest.raises(ValueError, match="Invalid network"):
            generate_deterministic_did(commitment, "bitcoin")

    def test_base58_encoding(self):
        """DID identifier must be valid Base58."""
        commitment = b"test_commitment"
        did = generate_deterministic_did(commitment, "mainnet")

        # Extract identifier
        did_id = did.split(":")[-1]

        # Base58 excludes: 0, O, I, l
        assert "0" not in did_id
        assert "O" not in did_id
        assert "I" not in did_id
        assert "l" not in did_id

        # Should only contain Base58 alphabet
        base58_alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        assert all(c in base58_alphabet for c in did_id)

    def test_collision_resistance(self):
        """Small changes in commitment should produce different DIDs."""
        commitment1 = b"test_commitment_1"
        commitment2 = b"test_commitment_2"  # One character different

        did1 = generate_deterministic_did(commitment1, "mainnet")
        did2 = generate_deterministic_did(commitment2, "mainnet")

        assert did1 != did2

    def test_large_commitment(self):
        """Should handle large commitments (e.g., 4-finger enrollment)."""
        # Simulate large commitment (~500 bytes)
        commitment = b"x" * 500

        did = generate_deterministic_did(commitment, "mainnet")

        assert did.startswith("did:cardano:mainnet:")
        assert len(did) < 100  # DID should still be compact


class TestDIDVerification:
    """Test suite for DID verification functions."""

    def test_verify_correct_did(self):
        """Verification should pass for correctly generated DID."""
        commitment = b"test_commitment"
        did = generate_deterministic_did(commitment, "mainnet")

        assert verify_did_determinism(commitment, did, "mainnet") is True

    def test_verify_incorrect_did(self):
        """Verification should fail for incorrect DID."""
        commitment = b"test_commitment"
        wrong_did = "did:cardano:mainnet:wronghash123"

        assert verify_did_determinism(
            commitment, wrong_did, "mainnet") is False

    def test_verify_wrong_network(self):
        """Verification should fail if network doesn't match."""
        commitment = b"test_commitment"
        did = generate_deterministic_did(commitment, "mainnet")

        # Verify with wrong network
        assert verify_did_determinism(commitment, did, "testnet") is False

    def test_extract_valid_did_hash(self):
        """Should extract hash from valid DID."""
        commitment = b"test_commitment"
        did = generate_deterministic_did(commitment, "mainnet")

        hash_bytes = extract_did_hash(did)

        assert hash_bytes is not None
        assert len(hash_bytes) == 32  # BLAKE2b-256 output
        assert isinstance(hash_bytes, bytes)

    def test_extract_invalid_did_format(self):
        """Should return None for invalid DID format."""
        # Wrong format
        assert extract_did_hash("not:a:valid:did:format") is None

        # Too few parts
        assert extract_did_hash("did:cardano:mainnet") is None

        # Not a Cardano DID
        assert extract_did_hash("did:ethereum:mainnet:abc123") is None

    def test_extract_invalid_base58(self):
        """Should return None for invalid Base58 in DID."""
        # Invalid Base58 (contains 0, O, I, l)
        invalid_did = "did:cardano:mainnet:0OIl123"
        assert extract_did_hash(invalid_did) is None


class TestCommitmentFingerprint:
    """Test suite for commitment fingerprinting."""

    def test_fingerprint_format(self):
        """Fingerprint should be 16-character hex string."""
        commitment = b"test_commitment"
        fingerprint = compute_commitment_fingerprint(commitment)

        assert len(fingerprint) == 16  # 8 bytes = 16 hex chars
        assert all(c in "0123456789abcdef" for c in fingerprint)

    def test_fingerprint_deterministic(self):
        """Same commitment should produce same fingerprint."""
        commitment = b"test_commitment"

        fp1 = compute_commitment_fingerprint(commitment)
        fp2 = compute_commitment_fingerprint(commitment)

        assert fp1 == fp2

    def test_fingerprint_different_for_different_commitments(self):
        """Different commitments should produce different fingerprints."""
        fp1 = compute_commitment_fingerprint(b"commitment_1")
        fp2 = compute_commitment_fingerprint(b"commitment_2")

        assert fp1 != fp2


class TestSybilResistance:
    """Test suite specifically for Sybil attack resistance."""

    def test_cannot_create_multiple_dids_from_same_biometrics(self):
        """
        Sybil attack test: Attempting to create multiple DIDs from
        the same biometric commitment should always produce the same DID.
        """
        # Simulate Alice trying to create multiple identities
        alice_fingerprints = b"alice_biometric_commitment"

        # Alice tries with wallet A
        did_wallet_a = generate_deterministic_did(
            alice_fingerprints, "mainnet")

        # Alice tries with wallet B
        did_wallet_b = generate_deterministic_did(
            alice_fingerprints, "mainnet")

        # Alice tries with wallet C
        did_wallet_c = generate_deterministic_did(
            alice_fingerprints, "mainnet")

        # All attempts produce the SAME DID
        assert did_wallet_a == did_wallet_b == did_wallet_c

        # Attack prevented ✅

    def test_different_people_get_different_dids(self):
        """Different people should get different DIDs (legitimate use case)."""
        alice_commitment = b"alice_biometrics"
        bob_commitment = b"bob_biometrics"
        charlie_commitment = b"charlie_biometrics"

        alice_did = generate_deterministic_did(alice_commitment, "mainnet")
        bob_did = generate_deterministic_did(bob_commitment, "mainnet")
        charlie_did = generate_deterministic_did(charlie_commitment, "mainnet")

        # All unique
        assert len({alice_did, bob_did, charlie_did}) == 3

    def test_multi_wallet_scenario(self):
        """
        Same person can have same DID controlled by multiple wallets.
        This is a FEATURE, not a bug.
        """
        # Alice enrolls on desktop with Wallet A
        alice_commitment = b"alice_biometrics"
        did_desktop = generate_deterministic_did(alice_commitment, "mainnet")

        # Alice wants to use mobile wallet B - same DID!
        did_mobile = generate_deterministic_did(alice_commitment, "mainnet")

        # Same DID, different wallets can control it
        assert did_desktop == did_mobile

        # This enables:
        # - Multi-device support
        # - Wallet recovery
        # - Backup wallets

    def test_recovery_scenario(self):
        """Lost wallet recovery: Re-enroll fingerprints to recover DID."""
        # Alice enrolls initially
        alice_commitment = b"alice_biometrics"
        original_did = generate_deterministic_did(alice_commitment, "mainnet")

        # Alice loses wallet, re-enrolls with new wallet
        # (Same fingerprints → Same commitment)
        recovered_did = generate_deterministic_did(alice_commitment, "mainnet")

        # Same DID recovered!
        assert original_did == recovered_did

        # Alice can now:
        # 1. Prove ownership of original DID (via biometrics)
        # 2. Add new wallet as controller
        # 3. Remove lost wallet


class TestIntegrationWithExistingCode:
    """Test integration with existing wallet-based DID generation."""

    def test_both_approaches_coexist(self):
        """
        Legacy wallet-based DIDs and new deterministic DIDs
        should coexist without conflict.
        """
        from decentralized_did.did.generator import build_did

        commitment = b"test_commitment"
        wallet_address = "addr1_test_wallet_address"

        # Old approach: wallet-based (DEPRECATED - must explicitly opt-in)
        with pytest.warns(DeprecationWarning, match="Wallet-based DID format.*DEPRECATED"):
            legacy_did = build_did(
                wallet_address, commitment, deterministic=False)
        assert "#" in legacy_did  # Uses fragment

        # New approach: deterministic (DEFAULT)
        deterministic_did_via_build_did = build_did(wallet_address, commitment)
        assert "#" not in deterministic_did_via_build_did  # No fragment

        # Direct call to deterministic function
        deterministic_did = generate_deterministic_did(commitment, "mainnet")
        assert "#" not in deterministic_did  # No fragment

        # build_did with deterministic=True should match direct call
        assert deterministic_did_via_build_did == deterministic_did

        # Different formats
        assert legacy_did != deterministic_did


# Performance tests
class TestPerformance:
    """Test performance characteristics."""

    def test_generation_speed(self):
        """DID generation should be fast (<1ms per DID)."""
        import time

        commitment = b"test_commitment" * 10  # ~200 bytes

        iterations = 1000
        start = time.time()

        for _ in range(iterations):
            generate_deterministic_did(commitment, "mainnet")

        end = time.time()
        avg_time = (end - start) / iterations

        # Should be very fast (BLAKE2b + Base58 is efficient)
        assert avg_time < 0.001  # <1ms per DID

    def test_no_memory_leak(self):
        """Repeated generation should not leak memory."""
        commitment = b"test_commitment" * 100  # 1.6 KB

        # Generate many DIDs
        for _ in range(10000):
            did = generate_deterministic_did(commitment, "mainnet")
            assert did  # Ensure it works

        # If we get here without crashing, no obvious leak


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
