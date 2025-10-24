"""
Authentication Endpoints for API Servers

Provides REST API endpoints for:
- API key registration
- JWT token generation (wallet signature auth)
- Token refresh
- API key revocation

License: Open-source (MIT)
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, FastAPI
from pydantic import BaseModel, Field, ConfigDict

from .auth import (
    JWTManager,
    APIKeyManager,
    WalletSignatureVerifier,
    APIKey,
    InvalidTokenError,
    InvalidAPIKeyError,
    InvalidSignatureError,
)
from .middleware import AuthContext, AuthenticationMiddleware


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterAPIKeyRequest(BaseModel):
    """Request model for API key registration"""
    prefix: str = Field(default="did_prod_", pattern="^(did_prod_|did_test_)$")
    expires_days: Optional[int] = Field(default=None, ge=1, le=365)
    rate_limit_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prefix": "did_prod_",
                "expires_days": 90,
                "rate_limit_multiplier": 2.0,
                "metadata": {"app_name": "Demo Wallet", "version": "1.0"}
            }
        }
    )


class RegisterAPIKeyResponse(BaseModel):
    """Response model for API key registration"""
    api_key: str
    key_id: str
    prefix: str
    created_at: str
    expires_at: Optional[str]
    rate_limit_multiplier: float
    message: str = "API key created successfully. Store this key securely - it will not be shown again."
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_key": "did_prod_AbCdEfGhIjKlMnOpQrStUvWxYz123456",
                "key_id": "a1b2c3d4e5f6g7h8",
                "prefix": "did_prod_",
                "created_at": "2025-10-14T12:00:00Z",
                "expires_at": "2026-01-12T12:00:00Z",
                "rate_limit_multiplier": 2.0,
                "message": "API key created successfully. Store this key securely - it will not be shown again."
            }
        }
    )


class LoginRequest(BaseModel):
    """Request model for JWT login (wallet signature auth)"""
    wallet_address: str = Field(..., min_length=20, max_length=150)
    message: str = Field(..., min_length=10, max_length=500)
    signature: str = Field(..., min_length=64, max_length=256)
    public_key: Optional[str] = Field(
        default=None, min_length=64, max_length=128)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "wallet_address": "addr1qxyz123456789",
                "message": "Login to DID system at 2025-10-14T12:00:00Z",
                "signature": "abcdef1234567890" * 4,
                "public_key": "123456789abcdef0" * 4
            }
        }
    )


class LoginResponse(BaseModel):
    """Response model for JWT login"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    wallet_address: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 900,
                "wallet_address": "addr1qxyz123456789"
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 900
            }
        }
    )


class RevokeAPIKeyRequest(BaseModel):
    """Request model for API key revocation"""
    key_id: str = Field(..., min_length=16, max_length=16)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key_id": "a1b2c3d4e5f6g7h8"
            }
        }
    )


class RevokeAPIKeyResponse(BaseModel):
    """Response model for API key revocation"""
    message: str
    key_id: str
    revoked_at: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "API key revoked successfully",
                "key_id": "a1b2c3d4e5f6g7h8",
                "revoked_at": "2025-10-14T12:00:00Z"
            }
        }
    )


# ============================================================================
# Authentication Endpoints
# ============================================================================

def create_auth_router(
    jwt_manager: JWTManager,
    api_key_manager: APIKeyManager,
    api_key_store: Dict[str, APIKey],
    auth_middleware: AuthenticationMiddleware,
    require_auth: bool = False
) -> APIRouter:
    """
    Create authentication router with all auth endpoints

    Args:
        jwt_manager: JWT token manager
        api_key_manager: API key manager
        api_key_store: API key storage (key_id -> APIKey)
        auth_middleware: Authentication middleware
        require_auth: Whether to require authentication for registration

    Returns:
        FastAPI router with auth endpoints
    """
    router = APIRouter(prefix="/auth", tags=["authentication"])

    # ========================================================================
    # POST /auth/register - Create API Key
    # ========================================================================

    if require_auth:
        @router.post(
            "/register",
            response_model=RegisterAPIKeyResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register new API key",
            description="Create a new API key for programmatic access. Store the returned key securely."
        )
        async def register_api_key(
            request: RegisterAPIKeyRequest,
            auth: AuthContext = Depends(auth_middleware.authenticate_optional)
        ) -> RegisterAPIKeyResponse:
            """
            Register new API key

            - **prefix**: Key prefix (did_prod_ or did_test_)
            - **expires_days**: Days until expiration (optional)
            - **rate_limit_multiplier**: Rate limit multiplier (1.0 = normal)
            - **metadata**: Custom metadata (e.g., app name, version)

            Returns the API key (shown only once) and key metadata.
            """
            # Generate API key
            raw_key, stored_key = api_key_manager.generate_api_key(
                prefix=request.prefix,
                expires_days=request.expires_days,
                rate_limit_multiplier=request.rate_limit_multiplier,
                metadata=request.metadata
            )

            # Store the key
            api_key_store[stored_key.key_id] = stored_key

            # Return response
            return RegisterAPIKeyResponse(
                api_key=raw_key,
                key_id=stored_key.key_id,
                prefix=stored_key.prefix,
                created_at=stored_key.created_at.isoformat(),
                expires_at=stored_key.expires_at.isoformat() if stored_key.expires_at else None,
                rate_limit_multiplier=stored_key.rate_limit_multiplier
            )
    else:
        @router.post(
            "/register",
            response_model=RegisterAPIKeyResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register new API key",
            description="Create a new API key for programmatic access. Store the returned key securely."
        )
        async def register_api_key(
            request: RegisterAPIKeyRequest
        ) -> RegisterAPIKeyResponse:
            """
            Register new API key

            - **prefix**: Key prefix (did_prod_ or did_test_)
            - **expires_days**: Days until expiration (optional)
            - **rate_limit_multiplier**: Rate limit multiplier (1.0 = normal)
            - **metadata**: Custom metadata (e.g., app name, version)

            Returns the API key (shown only once) and key metadata.
            """
            # Generate API key
            raw_key, stored_key = api_key_manager.generate_api_key(
                prefix=request.prefix,
                expires_days=request.expires_days,
                rate_limit_multiplier=request.rate_limit_multiplier,
                metadata=request.metadata
            )

            # Store the key
            api_key_store[stored_key.key_id] = stored_key

            # Return response
            return RegisterAPIKeyResponse(
                api_key=raw_key,
                key_id=stored_key.key_id,
                prefix=stored_key.prefix,
                created_at=stored_key.created_at.isoformat(),
                expires_at=stored_key.expires_at.isoformat() if stored_key.expires_at else None,
                rate_limit_multiplier=stored_key.rate_limit_multiplier
            )

    # ========================================================================
    # POST /auth/login - Get JWT Token (Wallet Signature Auth)
    # ========================================================================

    @router.post(
        "/login",
        response_model=LoginResponse,
        status_code=status.HTTP_200_OK,
        summary="Login with wallet signature",
        description="Authenticate using Cardano wallet signature (CIP-8) and receive JWT tokens."
    )
    async def login(request: LoginRequest) -> LoginResponse:
        """
        Login with wallet signature

        - **wallet_address**: Cardano wallet address (addr1... or addr_test1...)
        - **message**: Message that was signed (include timestamp)
        - **signature**: Hex-encoded signature
        - **public_key**: Hex-encoded public key (optional)

        Returns JWT access token (15 min) and refresh token (7 days).
        """
        # Verify wallet signature
        verifier = WalletSignatureVerifier()

        try:
            is_valid = verifier.verify_signature(
                wallet_address=request.wallet_address,
                message=request.message,
                signature=request.signature,
                public_key=request.public_key
            )

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid wallet signature"
                )

        except InvalidSignatureError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

        # Create JWT token pair
        token_pair = jwt_manager.create_token_pair(
            user_id=request.wallet_address,
            wallet_address=request.wallet_address,
            roles=["user"]
        )

        return LoginResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            wallet_address=request.wallet_address
        )

    # ========================================================================
    # POST /auth/refresh - Refresh Access Token
    # ========================================================================

    @router.post(
        "/refresh",
        response_model=RefreshTokenResponse,
        status_code=status.HTTP_200_OK,
        summary="Refresh access token",
        description="Refresh an expired access token using a valid refresh token."
    )
    async def refresh_token(request: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Refresh access token

        - **refresh_token**: Valid refresh token

        Returns new access token (15 min).
        """
        try:
            # Refresh access token
            new_access_token = jwt_manager.refresh_access_token(
                request.refresh_token)

            return RefreshTokenResponse(
                access_token=new_access_token,
                expires_in=int(jwt_manager.access_token_expiry.total_seconds())
            )

        except InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    # ========================================================================
    # DELETE /auth/revoke/{key_id} - Revoke API Key
    # ========================================================================

    @router.delete(
        "/revoke/{key_id}",
        response_model=RevokeAPIKeyResponse,
        status_code=status.HTTP_200_OK,
        summary="Revoke API key",
        description="Revoke an API key. Requires authentication with the key being revoked or admin access."
    )
    async def revoke_api_key(
        key_id: str,
        auth: AuthContext = Depends(auth_middleware.authenticate_any)
    ) -> RevokeAPIKeyResponse:
        """
        Revoke API key

        - **key_id**: Key ID to revoke (path parameter)

        Requires authentication. Users can revoke their own keys.
        Admins can revoke any key.
        """
        # Get stored key
        stored_key = api_key_store.get(key_id)

        if not stored_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key not found: {key_id}"
            )

        # Check permissions (users can revoke their own keys, admins can revoke any)
        if auth.auth_method == "api_key":
            if auth.user_id != key_id and not auth.has_role("admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only revoke your own API key"
                )

        # Revoke key
        api_key_manager.revoke_api_key(stored_key)
        revoked_at = datetime.now(timezone.utc)

        return RevokeAPIKeyResponse(
            message="API key revoked successfully",
            key_id=key_id,
            revoked_at=revoked_at.isoformat()
        )

    return router


# ============================================================================
# Helper Function
# ============================================================================

def setup_auth_endpoints(
    app: FastAPI,
    jwt_secret: str,
    api_key_store: Optional[Dict[str, APIKey]] = None,
    require_auth_for_registration: bool = False
) -> Tuple[AuthenticationMiddleware, Dict[str, APIKey]]:
    """
    Setup authentication endpoints on FastAPI app

    Args:
        app: FastAPI application
        jwt_secret: JWT secret key (min 32 bytes)
        api_key_store: API key storage (creates new dict if None)
        require_auth_for_registration: Require auth for API key registration

    Returns:
        Tuple of (auth_middleware, api_key_store) for use in other endpoints
    """
    from .auth import create_jwt_manager, create_api_key_manager
    from .middleware import AuthenticationMiddleware

    # Create managers
    jwt_manager = create_jwt_manager(jwt_secret)
    api_key_manager = create_api_key_manager()

    # Create or use provided store
    if api_key_store is None:
        store: Dict[str, APIKey] = {}
    else:
        store = api_key_store

    # Create middleware
    auth_middleware = AuthenticationMiddleware(
        jwt_manager=jwt_manager,
        api_key_manager=api_key_manager,
        api_key_store=store
    )

    # Create and include router
    auth_router = create_auth_router(
        jwt_manager=jwt_manager,
        api_key_manager=api_key_manager,
        api_key_store=store,
        auth_middleware=auth_middleware,
        require_auth=require_auth_for_registration
    )

    app.include_router(auth_router)

    return auth_middleware, store
