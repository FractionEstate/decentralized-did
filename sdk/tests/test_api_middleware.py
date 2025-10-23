"""
Tests for Authentication Middleware

Test Coverage:
- JWT authentication dependency
- API key authentication dependency
- Combined authentication (JWT or API key)
- Optional authentication
- Role-based access control (RBAC)
- Request context injection
- Error handling
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException

from src.decentralized_did.api.middleware import (
    AuthContext,
    AuthenticationMiddleware,
    require_roles,
    require_admin,
    inject_auth_context,
    get_auth_context,
    create_auth_middleware,
)
from src.decentralized_did.api.auth import (
    create_jwt_manager,
    create_api_key_manager,
    APIKey,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def jwt_manager():
    """Create JWT manager for testing"""
    return create_jwt_manager()


@pytest.fixture
def api_key_manager():
    """Create API key manager for testing"""
    return create_api_key_manager()


@pytest.fixture
def api_key_store(api_key_manager):
    """Create API key store with test keys"""
    store = {}

    # Generate test API key
    raw_key, stored_key = api_key_manager.generate_api_key(
        prefix="did_test_",
        metadata={"app": "Test App"}
    )

    store[stored_key.key_id] = stored_key
    store["_raw_key"] = raw_key  # Store for testing

    return store


@pytest.fixture
def auth_middleware(jwt_manager, api_key_manager, api_key_store):
    """Create authentication middleware for testing"""
    return AuthenticationMiddleware(
        jwt_manager=jwt_manager,
        api_key_manager=api_key_manager,
        api_key_store=api_key_store
    )


# ============================================================================
# AuthContext Tests
# ============================================================================

def test_auth_context_creation():
    """Test auth context creation"""
    context = AuthContext(
        user_id="user123",
        auth_method="jwt",
        roles=["user", "admin"],
        wallet_address="addr1qxyz"
    )

    assert context.user_id == "user123"
    assert context.auth_method == "jwt"
    assert context.roles == ["user", "admin"]
    assert context.wallet_address == "addr1qxyz"
    assert context.rate_limit_multiplier == 1.0


def test_auth_context_has_role():
    """Test checking if user has specific role"""
    context = AuthContext(
        user_id="user123",
        auth_method="jwt",
        roles=["user", "admin"]
    )

    assert context.has_role("user") is True
    assert context.has_role("admin") is True
    assert context.has_role("moderator") is False


def test_auth_context_has_any_role():
    """Test checking if user has any of specified roles"""
    context = AuthContext(
        user_id="user123",
        auth_method="jwt",
        roles=["user"]
    )

    assert context.has_any_role(["admin", "moderator"]) is False
    assert context.has_any_role(["user", "moderator"]) is True
    assert context.has_any_role(["user"]) is True


# ============================================================================
# JWT Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_authenticate_jwt_success(auth_middleware, jwt_manager):
    """Test successful JWT authentication"""
    # Create valid token
    token = jwt_manager.create_access_token(
        user_id="user123",
        wallet_address="addr1qxyz",
        roles=["user"]
    )

    authorization = f"Bearer {token}"

    # Authenticate
    context = await auth_middleware.authenticate_jwt(authorization)

    assert context.user_id == "user123"
    assert context.auth_method == "jwt"
    assert context.roles == ["user"]
    assert context.wallet_address == "addr1qxyz"


@pytest.mark.asyncio
async def test_authenticate_jwt_missing_header(auth_middleware):
    """Test JWT authentication with missing header"""
    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_jwt(None)

    assert exc_info.value.status_code == 401
    assert "Missing Authorization header" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authenticate_jwt_invalid_token(auth_middleware):
    """Test JWT authentication with invalid token"""
    authorization = "Bearer invalid.token.string"

    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_jwt(authorization)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_jwt_expired_token(auth_middleware, jwt_manager):
    """Test JWT authentication with expired token"""
    # Create expired token
    jwt_manager.access_token_expiry = timedelta(seconds=1)
    token = jwt_manager.create_access_token(user_id="user123")

    # Wait for expiration
    import time
    time.sleep(1.1)

    authorization = f"Bearer {token}"

    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_jwt(authorization)

    assert exc_info.value.status_code == 401


# ============================================================================
# API Key Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_authenticate_api_key_success(auth_middleware, api_key_store):
    """Test successful API key authentication"""
    raw_key = api_key_store["_raw_key"]

    # Authenticate
    context = await auth_middleware.authenticate_api_key(raw_key)

    assert context.auth_method == "api_key"
    assert context.roles == ["api_client"]
    assert context.api_key_metadata["app"] == "Test App"
    assert context.rate_limit_multiplier == 1.0


@pytest.mark.asyncio
async def test_authenticate_api_key_missing_header(auth_middleware):
    """Test API key authentication with missing header"""
    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_api_key(None)

    assert exc_info.value.status_code == 401
    assert "Missing X-API-Key header" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authenticate_api_key_invalid_key(auth_middleware):
    """Test API key authentication with invalid key"""
    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_api_key("did_test_invalid_key")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_api_key_revoked(auth_middleware, api_key_store):
    """Test API key authentication with revoked key"""
    raw_key = api_key_store["_raw_key"]
    key_id = list(k for k in api_key_store.keys() if k != "_raw_key")[0]

    # Revoke key
    api_key_store[key_id].is_active = False

    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_api_key(raw_key)

    assert exc_info.value.status_code == 401
    assert "revoked" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_authenticate_api_key_updates_last_used(auth_middleware, api_key_store):
    """Test that API key authentication updates last_used_at"""
    raw_key = api_key_store["_raw_key"]
    key_id = list(k for k in api_key_store.keys() if k != "_raw_key")[0]

    # Initial last_used_at should be None
    assert api_key_store[key_id].last_used_at is None

    # Authenticate
    await auth_middleware.authenticate_api_key(raw_key)

    # last_used_at should be updated
    assert api_key_store[key_id].last_used_at is not None
    assert isinstance(api_key_store[key_id].last_used_at, datetime)


# ============================================================================
# Combined Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_authenticate_any_jwt(auth_middleware, jwt_manager):
    """Test combined authentication with JWT"""
    token = jwt_manager.create_access_token(user_id="user123")
    authorization = f"Bearer {token}"

    context = await auth_middleware.authenticate_any(authorization, None)

    assert context.auth_method == "jwt"
    assert context.user_id == "user123"


@pytest.mark.asyncio
async def test_authenticate_any_api_key(auth_middleware, api_key_store):
    """Test combined authentication with API key"""
    raw_key = api_key_store["_raw_key"]

    context = await auth_middleware.authenticate_any(None, raw_key)

    assert context.auth_method == "api_key"


@pytest.mark.asyncio
async def test_authenticate_any_both_provided(auth_middleware, jwt_manager, api_key_store):
    """Test combined authentication with both JWT and API key (JWT takes precedence)"""
    token = jwt_manager.create_access_token(user_id="user123")
    authorization = f"Bearer {token}"
    raw_key = api_key_store["_raw_key"]

    context = await auth_middleware.authenticate_any(authorization, raw_key)

    # JWT should take precedence
    assert context.auth_method == "jwt"


@pytest.mark.asyncio
async def test_authenticate_any_none_provided(auth_middleware):
    """Test combined authentication with no credentials"""
    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware.authenticate_any(None, None)

    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


# ============================================================================
# Optional Authentication Tests
# ============================================================================

@pytest.mark.asyncio
async def test_authenticate_optional_with_jwt(auth_middleware, jwt_manager):
    """Test optional authentication with JWT"""
    token = jwt_manager.create_access_token(user_id="user123")
    authorization = f"Bearer {token}"

    context = await auth_middleware.authenticate_optional(authorization, None)

    assert context is not None
    assert context.auth_method == "jwt"


@pytest.mark.asyncio
async def test_authenticate_optional_without_credentials(auth_middleware):
    """Test optional authentication without credentials"""
    context = await auth_middleware.authenticate_optional(None, None)

    assert context is None


# ============================================================================
# RBAC Tests
# ============================================================================

@pytest.mark.asyncio
async def test_require_roles_success():
    """Test require_roles decorator with sufficient permissions"""
    @require_roles(["admin"])
    async def protected_endpoint(auth: AuthContext):
        return {"message": "success"}

    auth = AuthContext(user_id="admin1", auth_method="jwt", roles=["admin"])

    result = await protected_endpoint(auth=auth)
    assert result["message"] == "success"


@pytest.mark.asyncio
async def test_require_roles_insufficient_permissions():
    """Test require_roles decorator with insufficient permissions"""
    @require_roles(["admin"])
    async def protected_endpoint(auth: AuthContext):
        return {"message": "success"}

    auth = AuthContext(user_id="user1", auth_method="jwt", roles=["user"])

    with pytest.raises(HTTPException) as exc_info:
        await protected_endpoint(auth=auth)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_success():
    """Test require_admin decorator with admin role"""
    @require_admin
    async def admin_endpoint(auth: AuthContext):
        return {"message": "admin access"}

    auth = AuthContext(user_id="admin1", auth_method="jwt", roles=["admin"])

    result = await admin_endpoint(auth=auth)
    assert result["message"] == "admin access"


@pytest.mark.asyncio
async def test_require_admin_denied():
    """Test require_admin decorator without admin role"""
    @require_admin
    async def admin_endpoint(auth: AuthContext):
        return {"message": "admin access"}

    auth = AuthContext(user_id="user1", auth_method="jwt", roles=["user"])

    with pytest.raises(HTTPException) as exc_info:
        await admin_endpoint(auth=auth)

    assert exc_info.value.status_code == 403


# ============================================================================
# Request Context Tests
# ============================================================================

@pytest.mark.asyncio
async def test_inject_auth_context():
    """Test injecting auth context into request state"""
    request = Mock()
    request.state = Mock()

    auth = AuthContext(user_id="user123", auth_method="jwt", roles=["user"])

    await inject_auth_context(request, auth)

    assert request.state.auth == auth


def test_get_auth_context():
    """Test getting auth context from request state"""
    request = Mock()
    auth = AuthContext(user_id="user123", auth_method="jwt", roles=["user"])
    request.state = Mock(auth=auth)

    retrieved_auth = get_auth_context(request)

    assert retrieved_auth == auth


def test_get_auth_context_not_present():
    """Test getting auth context when not present"""
    request = Mock()
    request.state = Mock(spec=[])  # No auth attribute

    retrieved_auth = get_auth_context(request)

    assert retrieved_auth is None


# ============================================================================
# Helper Function Tests
# ============================================================================

def test_create_auth_middleware():
    """Test creating auth middleware with helper function"""
    jwt_secret = "a" * 32
    api_key_store = {}

    middleware = create_auth_middleware(jwt_secret, api_key_store)

    assert isinstance(middleware, AuthenticationMiddleware)
    assert middleware.jwt_manager is not None
    assert middleware.api_key_manager is not None
    assert middleware.api_key_store == api_key_store


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_jwt_authentication_flow(auth_middleware, jwt_manager):
    """Test complete JWT authentication flow"""
    # 1. Create token
    token = jwt_manager.create_access_token(
        user_id="alice",
        wallet_address="addr1qalice",
        roles=["user", "premium"]
    )

    # 2. Authenticate with token
    authorization = f"Bearer {token}"
    context = await auth_middleware.authenticate_jwt(authorization)

    # 3. Verify context
    assert context.user_id == "alice"
    assert context.wallet_address == "addr1qalice"
    assert context.has_role("user")
    assert context.has_role("premium")

    # 4. Check role-based access
    assert context.has_any_role(["admin", "premium"])


@pytest.mark.asyncio
async def test_full_api_key_authentication_flow(auth_middleware, api_key_store):
    """Test complete API key authentication flow"""
    # 1. Get API key
    raw_key = api_key_store["_raw_key"]

    # 2. Authenticate with key
    context = await auth_middleware.authenticate_api_key(raw_key)

    # 3. Verify context
    assert context.auth_method == "api_key"
    assert context.has_role("api_client")
    assert context.api_key_metadata["app"] == "Test App"

    # 4. Verify last_used_at updated
    key_id = list(k for k in api_key_store.keys() if k != "_raw_key")[0]
    assert api_key_store[key_id].last_used_at is not None


@pytest.mark.asyncio
async def test_multiple_authentication_methods(auth_middleware, jwt_manager, api_key_store):
    """Test using both authentication methods in sequence"""
    # JWT authentication
    jwt_token = jwt_manager.create_access_token(user_id="user1")
    jwt_auth = f"Bearer {jwt_token}"
    jwt_context = await auth_middleware.authenticate_any(jwt_auth, None)
    assert jwt_context.auth_method == "jwt"

    # API key authentication
    api_key = api_key_store["_raw_key"]
    api_context = await auth_middleware.authenticate_any(None, api_key)
    assert api_context.auth_method == "api_key"

    # Different contexts
    assert jwt_context.user_id != api_context.user_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
