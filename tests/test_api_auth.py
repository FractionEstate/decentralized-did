"""
Tests for Authentication & Authorization Module

Test Coverage:
- JWTManager (token creation, verification, refresh)
- APIKeyManager (key generation, verification, revocation)
- WalletSignatureVerifier (Cardano signature verification)
- Helper functions (token extraction, role checking)
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from src.decentralized_did.api.auth import (
    JWTManager,
    APIKeyManager,
    WalletSignatureVerifier,
    JWTToken,
    APIKey,
    UserRole,
    InvalidTokenError,
    InvalidAPIKeyError,
    InvalidSignatureError,
    create_jwt_manager,
    create_api_key_manager,
    extract_bearer_token,
    check_user_roles,
)


# ============================================================================
# JWTManager Tests
# ============================================================================

def test_jwt_manager_initialization():
    """Test JWT manager initialization"""
    secret = "a" * 32
    manager = JWTManager(secret)

    assert manager.secret_key == secret
    assert manager.algorithm == "HS256"


def test_jwt_manager_short_secret_raises_error():
    """Test that short secret keys are rejected"""
    with pytest.raises(ValueError, match="at least 32 bytes"):
        JWTManager("short_secret")


def test_create_access_token():
    """Test access token creation"""
    manager = create_jwt_manager()

    token = manager.create_access_token(
        user_id="user123",
        wallet_address="addr1qxyz",
        roles=["user", "admin"]
    )

    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """Test refresh token creation"""
    manager = create_jwt_manager()

    token = manager.create_refresh_token(user_id="user123")

    assert isinstance(token, str)
    assert len(token) > 0


def test_create_token_pair():
    """Test access + refresh token pair creation"""
    manager = create_jwt_manager()

    token_pair = manager.create_token_pair(
        user_id="user123",
        wallet_address="addr1qxyz",
        roles=["user"]
    )

    assert isinstance(token_pair, JWTToken)
    assert isinstance(token_pair.access_token, str)
    assert isinstance(token_pair.refresh_token, str)
    assert token_pair.token_type == "Bearer"
    assert token_pair.expires_in == 900  # 15 minutes


def test_verify_access_token():
    """Test access token verification"""
    manager = create_jwt_manager()

    token = manager.create_access_token(
        user_id="user123",
        wallet_address="addr1qxyz",
        roles=["user"]
    )

    payload = manager.verify_token(token, token_type="access")

    assert payload["sub"] == "user123"
    assert payload["wallet"] == "addr1qxyz"
    assert payload["roles"] == ["user"]
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_verify_refresh_token():
    """Test refresh token verification"""
    manager = create_jwt_manager()

    token = manager.create_refresh_token(user_id="user456")

    payload = manager.verify_token(token, token_type="refresh")

    assert payload["sub"] == "user456"
    assert payload["type"] == "refresh"
    assert "jti" in payload  # Unique token ID


def test_verify_token_wrong_type_raises_error():
    """Test that verifying token with wrong type raises error"""
    manager = create_jwt_manager()

    access_token = manager.create_access_token(user_id="user123")

    with pytest.raises(InvalidTokenError, match="Invalid token type"):
        manager.verify_token(access_token, token_type="refresh")


def test_verify_expired_token_raises_error():
    """Test that expired tokens raise error"""
    manager = create_jwt_manager()
    manager.access_token_expiry = timedelta(seconds=1)

    token = manager.create_access_token(user_id="user123")

    # Wait for token to expire
    time.sleep(1.1)

    with pytest.raises(InvalidTokenError, match="expired"):
        manager.verify_token(token)


def test_verify_invalid_token_raises_error():
    """Test that invalid tokens raise error"""
    manager = create_jwt_manager()

    with pytest.raises(InvalidTokenError, match="Invalid token"):
        manager.verify_token("invalid.token.string")


def test_refresh_access_token():
    """Test refreshing access token from refresh token"""
    manager = create_jwt_manager()

    # Create initial token pair
    token_pair = manager.create_token_pair(user_id="user123", roles=["user"])

    # Refresh access token
    new_access_token = manager.refresh_access_token(token_pair.refresh_token)

    # Verify new token
    payload = manager.verify_token(new_access_token)
    assert payload["sub"] == "user123"


def test_custom_claims_in_access_token():
    """Test adding custom claims to access token"""
    manager = create_jwt_manager()

    token = manager.create_access_token(
        user_id="user123",
        custom_claims={"app_name": "Demo Wallet", "version": "1.0"}
    )

    payload = manager.verify_token(token)

    assert payload["app_name"] == "Demo Wallet"
    assert payload["version"] == "1.0"


# ============================================================================
# APIKeyManager Tests
# ============================================================================

def test_api_key_manager_initialization():
    """Test API key manager initialization"""
    manager = APIKeyManager(bcrypt_rounds=10)

    assert manager.bcrypt_rounds == 10


def test_generate_api_key():
    """Test API key generation"""
    manager = create_api_key_manager()

    raw_key, api_key = manager.generate_api_key(
        prefix="did_prod_",
        expires_days=30,
        rate_limit_multiplier=2.0,
        metadata={"app_name": "Test App"}
    )

    # Check raw key format
    assert raw_key.startswith("did_prod_")
    assert len(raw_key) > 40  # Prefix + 32 bytes base64

    # Check APIKey object
    assert isinstance(api_key, APIKey)
    assert api_key.prefix == "did_prod_"
    assert api_key.is_active is True
    assert api_key.rate_limit_multiplier == 2.0
    assert api_key.metadata["app_name"] == "Test App"
    assert api_key.expires_at is not None


def test_generate_api_key_no_expiration():
    """Test generating API key without expiration"""
    manager = create_api_key_manager()

    raw_key, api_key = manager.generate_api_key(expires_days=None)

    assert api_key.expires_at is None


def test_verify_api_key_success():
    """Test successful API key verification"""
    manager = create_api_key_manager()

    raw_key, stored_key = manager.generate_api_key()

    # Verification should succeed
    is_valid = manager.verify_api_key(raw_key, stored_key)
    assert is_valid is True


def test_verify_api_key_wrong_key_raises_error():
    """Test that wrong API key raises error"""
    manager = create_api_key_manager()

    raw_key, stored_key = manager.generate_api_key()
    wrong_key = "did_prod_wrongkeywrongkeywrongkey"

    with pytest.raises(InvalidAPIKeyError, match="Invalid API key"):
        manager.verify_api_key(wrong_key, stored_key)


def test_verify_revoked_api_key_raises_error():
    """Test that revoked API keys raise error"""
    manager = create_api_key_manager()

    raw_key, stored_key = manager.generate_api_key()

    # Revoke key
    manager.revoke_api_key(stored_key)

    # Verification should fail
    with pytest.raises(InvalidAPIKeyError, match="revoked"):
        manager.verify_api_key(raw_key, stored_key)


def test_verify_expired_api_key_raises_error():
    """Test that expired API keys raise error"""
    manager = create_api_key_manager()

    # Generate key that expires immediately
    raw_key, stored_key = manager.generate_api_key(expires_days=0)

    # Set expiration to past
    stored_key.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    # Verification should fail
    with pytest.raises(InvalidAPIKeyError, match="expired"):
        manager.verify_api_key(raw_key, stored_key)


def test_extract_key_id():
    """Test extracting key ID from raw key"""
    manager = create_api_key_manager()

    raw_key, stored_key = manager.generate_api_key()

    extracted_id = manager.extract_key_id(raw_key)

    assert extracted_id == stored_key.key_id
    assert len(extracted_id) == 16  # 16-char hex string


def test_api_key_uniqueness():
    """Test that generated API keys are unique"""
    manager = create_api_key_manager()

    key1, _ = manager.generate_api_key()
    key2, _ = manager.generate_api_key()
    key3, _ = manager.generate_api_key()

    # All keys should be different
    assert key1 != key2
    assert key2 != key3
    assert key1 != key3


# ============================================================================
# WalletSignatureVerifier Tests
# ============================================================================

def test_verify_signature_valid_format():
    """Test wallet signature verification with valid format"""
    verifier = WalletSignatureVerifier()

    # Note: This is a placeholder test since actual verification is TODO
    is_valid = verifier.verify_signature(
        wallet_address="addr1qxyz123456789",
        message="Login to DID system",
        signature="abcdef1234567890" * 4,  # 64-char hex
        public_key="123456789abcdef0" * 4
    )

    assert is_valid is True


def test_verify_signature_invalid_address_format():
    """Test that invalid wallet address format raises error"""
    verifier = WalletSignatureVerifier()

    with pytest.raises(InvalidSignatureError, match="Invalid wallet address"):
        verifier.verify_signature(
            wallet_address="invalid_address",
            message="Login",
            signature="abcdef1234567890" * 4
        )


def test_verify_signature_invalid_signature_format():
    """Test that invalid signature format raises error"""
    verifier = WalletSignatureVerifier()

    with pytest.raises(InvalidSignatureError, match="Invalid signature format"):
        verifier.verify_signature(
            wallet_address="addr1qxyz123456789",
            message="Login",
            signature="not_hex_string"
        )


def test_verify_signature_testnet_address():
    """Test verification with testnet address"""
    verifier = WalletSignatureVerifier()

    is_valid = verifier.verify_signature(
        wallet_address="addr_test1qxyz123456789",
        message="Login to DID system",
        signature="abcdef1234567890" * 4
    )

    assert is_valid is True


# ============================================================================
# Helper Function Tests
# ============================================================================

def test_extract_bearer_token_success():
    """Test extracting token from Bearer header"""
    header = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"

    token = extract_bearer_token(header)

    assert token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"


def test_extract_bearer_token_missing_header():
    """Test that missing header raises error"""
    with pytest.raises(InvalidTokenError, match="Missing Authorization header"):
        extract_bearer_token("")


def test_extract_bearer_token_invalid_format():
    """Test that invalid header format raises error"""
    with pytest.raises(InvalidTokenError, match="Invalid Authorization header format"):
        extract_bearer_token("InvalidFormat token123")


def test_extract_bearer_token_case_insensitive():
    """Test that Bearer is case-insensitive"""
    header = "bearer mytoken123"

    token = extract_bearer_token(header)

    assert token == "mytoken123"


def test_check_user_roles_match():
    """Test checking user roles with match"""
    required_roles = ["admin", "moderator"]
    user_roles = ["user", "admin"]

    has_role = check_user_roles(required_roles, user_roles)

    assert has_role is True


def test_check_user_roles_no_match():
    """Test checking user roles without match"""
    required_roles = ["admin", "moderator"]
    user_roles = ["user", "guest"]

    has_role = check_user_roles(required_roles, user_roles)

    assert has_role is False


def test_check_user_roles_multiple_matches():
    """Test checking user roles with multiple matches"""
    required_roles = ["admin", "moderator"]
    user_roles = ["user", "admin", "moderator"]

    has_role = check_user_roles(required_roles, user_roles)

    assert has_role is True


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_jwt_authentication_flow():
    """Test complete JWT authentication flow"""
    manager = create_jwt_manager()

    # 1. User logs in, gets token pair
    token_pair = manager.create_token_pair(
        user_id="alice",
        wallet_address="addr1qalice",
        roles=["user"]
    )

    # 2. Access protected resource with access token
    payload = manager.verify_token(token_pair.access_token)
    assert payload["sub"] == "alice"

    # 3. Access token expires, refresh it
    new_access_token = manager.refresh_access_token(token_pair.refresh_token)

    # 4. Use new access token
    new_payload = manager.verify_token(new_access_token)
    assert new_payload["sub"] == "alice"


def test_full_api_key_lifecycle():
    """Test complete API key lifecycle"""
    manager = create_api_key_manager()

    # 1. Generate API key
    raw_key, stored_key = manager.generate_api_key(
        prefix="did_prod_",
        expires_days=30,
        metadata={"app": "Test"}
    )

    # 2. Verify key (success)
    assert manager.verify_api_key(raw_key, stored_key) is True

    # 3. Use key multiple times
    for _ in range(5):
        assert manager.verify_api_key(raw_key, stored_key) is True

    # 4. Revoke key
    manager.revoke_api_key(stored_key)

    # 5. Verification fails after revocation
    with pytest.raises(InvalidAPIKeyError):
        manager.verify_api_key(raw_key, stored_key)


def test_mixed_authentication_methods():
    """Test using both JWT and API keys"""
    jwt_manager = create_jwt_manager()
    api_manager = create_api_key_manager()

    # JWT authentication
    jwt_token = jwt_manager.create_access_token(
        user_id="user1", roles=["user"])
    jwt_payload = jwt_manager.verify_token(jwt_token)

    # API key authentication
    raw_key, stored_key = api_manager.generate_api_key()
    api_valid = api_manager.verify_api_key(raw_key, stored_key)

    assert jwt_payload["sub"] == "user1"
    assert api_valid is True


# ============================================================================
# Security Tests
# ============================================================================

def test_jwt_token_cannot_be_modified():
    """Test that modifying JWT token invalidates it"""
    manager = create_jwt_manager()

    token = manager.create_access_token(user_id="user123", roles=["user"])

    # Try to modify token
    modified_token = token[:-5] + "AAAAA"

    with pytest.raises(InvalidTokenError):
        manager.verify_token(modified_token)


def test_api_key_hash_is_different_each_time():
    """Test that same key generates different hashes (bcrypt salt)"""
    manager = create_api_key_manager()

    # Generate same key twice (for testing)
    # In practice, keys are always unique due to random generation
    test_key = "did_prod_test_key_12345678901234567890"

    import bcrypt
    hash1 = bcrypt.hashpw(test_key.encode(), bcrypt.gensalt(12))
    hash2 = bcrypt.hashpw(test_key.encode(), bcrypt.gensalt(12))

    # Hashes should be different (different salts)
    assert hash1 != hash2

    # But both should verify correctly
    assert bcrypt.checkpw(test_key.encode(), hash1)
    assert bcrypt.checkpw(test_key.encode(), hash2)


def test_jwt_different_secrets_incompatible():
    """Test that tokens from different secrets are incompatible"""
    manager1 = create_jwt_manager()
    manager2 = create_jwt_manager()  # Different secret

    token = manager1.create_access_token(user_id="user123")

    with pytest.raises(InvalidTokenError):
        manager2.verify_token(token)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
