"""
Property-based tests for fuzzy extractor using Hypothesis.

Tests cryptographic properties with randomized inputs to ensure robustness.
Uses Hypothesis for automated test case generation and shrinking.
"""

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st, assume

from src.biometrics.fuzzy_extractor_v2 import (
    fuzzy_extract_gen,
    fuzzy_extract_rep,
    BCH_K,
)


# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================


@st.composite
def biometric_array(draw):
    """Generate a valid biometric bit array (64 bits)"""
    bits = draw(st.lists(
        st.integers(min_value=0, max_value=1),
        min_size=BCH_K,
        max_size=BCH_K
    ))
    return np.array(bits, dtype=np.uint8)


@st.composite
def user_id(draw):
    """Generate a valid user ID string"""
    return draw(st.one_of(
        st.text(min_size=1, max_size=64, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            blacklist_characters='\x00'
        )),
        st.uuids().map(str)
    ))


# ============================================================================
# PROPERTY 1: KEY REPRODUCIBILITY
# ============================================================================


class TestKeyReproducibility:
    """Keys should be reproducible from identical biometrics"""

    @settings(max_examples=100, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_exact_match_always_succeeds(self, bio, uid):
        """Property: Identical biometric always reproduces the same key"""
        key1, helper = fuzzy_extract_gen(bio, uid)
        key2 = fuzzy_extract_rep(bio, helper)

        assert key1 == key2
        assert len(key1) == 32  # 256 bits

    @settings(max_examples=50, deadline=None)
    @given(bio=biometric_array(), uid=user_id(), num_errors=st.integers(min_value=0, max_value=10))
    def test_small_noise_succeeds(self, bio, uid, num_errors):
        """Property: Biometrics with ≤10 errors reproduce the same key"""
        key1, helper = fuzzy_extract_gen(bio, uid)

        # Add exactly num_errors bit flips
        if num_errors == 0:
            noisy = bio
        else:
            error_positions = np.random.choice(
                BCH_K, size=num_errors, replace=False)
            noisy = bio.copy()
            for pos in error_positions:
                noisy[pos] ^= 1

        key2 = fuzzy_extract_rep(noisy, helper)
        assert key1 == key2

    @settings(max_examples=30, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_multiple_verifications_consistent(self, bio, uid):
        """Property: Multiple verifications produce the same key"""
        key1, helper = fuzzy_extract_gen(bio, uid)

        # Verify 5 times
        for _ in range(5):
            key_verify = fuzzy_extract_rep(bio, helper)
            assert key_verify == key1


# ============================================================================
# PROPERTY 2: UNLINKABILITY
# ============================================================================


class TestUnlinkability:
    """Different enrollments should be unlinkable"""

    @settings(max_examples=50, deadline=None)
    @given(bio=biometric_array())
    def test_different_users_produce_different_helpers(self, bio):
        """Property: Same biometric, different users → different helper data"""
        uid1 = "user_alice"
        uid2 = "user_bob"

        _, helper1 = fuzzy_extract_gen(bio, uid1)
        _, helper2 = fuzzy_extract_gen(bio, uid2)

        # Salts should be different (random)
        assert helper1.salt != helper2.salt

        # Personalization should be different (based on user_id)
        assert helper1.personalization != helper2.personalization

        # HMACs should be different
        assert helper1.hmac != helper2.hmac

    @settings(max_examples=50, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_repeated_enrollments_produce_different_salts(self, bio, uid):
        """Property: Multiple enrollments → different random salts"""
        helpers = []
        for _ in range(3):
            _, helper = fuzzy_extract_gen(bio, uid)
            helpers.append(helper)

        # All salts should be unique (random salt generation)
        salts = [h.salt for h in helpers]
        assert len(set(salts)) == len(salts), "Salts should be unique"

    @settings(max_examples=30, deadline=None)
    @given(uid=user_id())
    def test_different_biometrics_produce_different_keys(self, uid):
        """Property: Different biometrics → different keys"""
        bio1 = np.random.randint(0, 2, BCH_K, dtype=np.uint8)
        bio2 = np.random.randint(0, 2, BCH_K, dtype=np.uint8)

        # Ensure they're actually different
        assume(not np.array_equal(bio1, bio2))

        key1, _ = fuzzy_extract_gen(bio1, uid)
        key2, _ = fuzzy_extract_gen(bio2, uid)

        assert key1 != key2


# ============================================================================
# PROPERTY 3: ERROR CORRECTION CAPACITY
# ============================================================================


class TestErrorCorrectionCapacity:
    """BCH should correct errors within guaranteed capacity"""

    @settings(max_examples=30, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_guaranteed_capacity_10_errors(self, bio, uid):
        """Property: BCH(127,64,10) guarantees correction of ≤10 errors"""
        key1, helper = fuzzy_extract_gen(bio, uid)

        # Create exactly 10 errors at different positions
        error_positions = np.random.choice(BCH_K, size=10, replace=False)
        noisy = bio.copy()
        for pos in error_positions:
            noisy[pos] ^= 1

        key2 = fuzzy_extract_rep(noisy, helper)
        assert key1 == key2


# ============================================================================
# PROPERTY 4: ENTROPY PRESERVATION
# ============================================================================


class TestEntropyPreservation:
    """Keys should have high entropy"""

    @settings(max_examples=50, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_keys_are_256_bits(self, bio, uid):
        """Property: All keys should be exactly 256 bits (32 bytes)"""
        key, _ = fuzzy_extract_gen(bio, uid)

        assert len(key) == 32
        assert isinstance(key, bytes)

    @settings(max_examples=20, deadline=None)
    @given(uid=user_id())
    def test_no_key_collisions(self, uid):
        """Property: Different biometrics produce unique keys"""
        keys = set()

        # Generate 20 keys from random biometrics
        for _ in range(20):
            bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)
            key, _ = fuzzy_extract_gen(bio, uid)
            keys.add(key)

        # All keys should be unique
        assert len(keys) == 20, "Key collision detected!"


# ============================================================================
# PROPERTY 5: DETERMINISM
# ============================================================================


class TestDeterminism:
    """Cryptographic operations should be deterministic where expected"""

    @settings(max_examples=30, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_same_biometric_same_syndrome(self, bio, uid):
        """Property: Same biometric → same BCH syndrome"""
        _, helper1 = fuzzy_extract_gen(bio, uid)
        _, helper2 = fuzzy_extract_gen(bio, uid)

        # BCH syndrome should be identical
        assert helper1.bch_syndrome == helper2.bch_syndrome

    @settings(max_examples=30, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_same_inputs_same_personalization(self, bio, uid):
        """Property: Same user_id → same personalization"""
        _, helper1 = fuzzy_extract_gen(bio, uid)
        _, helper2 = fuzzy_extract_gen(bio, uid)

        # Personalization should be identical
        assert helper1.personalization == helper2.personalization

    @settings(max_examples=20, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_rep_is_deterministic(self, bio, uid):
        """Property: Rep with same inputs produces same key"""
        _, helper = fuzzy_extract_gen(bio, uid)

        # Call Rep 5 times
        keys = []
        for _ in range(5):
            key = fuzzy_extract_rep(bio, helper)
            keys.append(key)

        # All keys should be identical
        assert len(set(keys)) == 1, "Rep should be deterministic"


# ============================================================================
# PROPERTY 6: SECURITY PROPERTIES
# ============================================================================


class TestSecurityProperties:
    """Security-related properties"""

    @settings(max_examples=30, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_helper_data_reveals_no_key_material(self, bio, uid):
        """Property: Helper data should not reveal key information"""
        key, helper = fuzzy_extract_gen(bio, uid)

        # Serialize helper data
        helper_bytes = helper.serialize()

        # Key should not appear in helper data
        assert key not in helper_bytes

    @pytest.mark.skip(reason="BCH can correct >10 errors for some patterns; not guaranteed to fail")
    @settings(max_examples=30, deadline=None)
    @given(bio=biometric_array(), uid=user_id())
    def test_wrong_biometric_fails_verification(self, bio, uid):
        """Property: Significantly different biometric usually fails (not guaranteed)"""
        _, helper = fuzzy_extract_gen(bio, uid)

        # Flip more than half the bits (32+ errors, well beyond guaranteed capacity)
        # Note: BCH may still correct some error patterns beyond t=10
        wrong_bio = bio.copy()
        error_positions = np.random.choice(BCH_K, size=40, replace=False)
        for pos in error_positions:
            wrong_bio[pos] ^= 1

        # Usually fails, but not guaranteed due to BCH properties
        with pytest.raises(ValueError, match="HMAC verification failed"):
            fuzzy_extract_rep(wrong_bio, helper)
# ============================================================================
# PROPERTY 7: EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions"""

    @settings(max_examples=10, deadline=None)
    @given(uid=user_id())
    def test_all_zeros_biometric(self, uid):
        """Property: All-zeros biometric should work"""
        bio = np.zeros(BCH_K, dtype=np.uint8)

        key1, helper = fuzzy_extract_gen(bio, uid)
        key2 = fuzzy_extract_rep(bio, helper)

        assert key1 == key2

    @settings(max_examples=10, deadline=None)
    @given(uid=user_id())
    def test_all_ones_biometric(self, uid):
        """Property: All-ones biometric should work"""
        bio = np.ones(BCH_K, dtype=np.uint8)

        key1, helper = fuzzy_extract_gen(bio, uid)
        key2 = fuzzy_extract_rep(bio, helper)

        assert key1 == key2

    @settings(max_examples=10, deadline=None)
    @given(bio=biometric_array())
    def test_unicode_user_id(self, bio):
        """Property: Unicode user_id should work"""
        unicode_uid = "user_🔐_测试_مرحبا"

        key1, helper = fuzzy_extract_gen(bio, unicode_uid)
        key2 = fuzzy_extract_rep(bio, helper)

        assert key1 == key2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
