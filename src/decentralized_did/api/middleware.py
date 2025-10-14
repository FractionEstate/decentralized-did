"""
Authentication Middleware for FastAPI

Provides:
- JWT authentication dependency
- API key authentication dependency
- Role-based access control (RBAC)
- Request context injection
- Authentication error handling

License: Open-source (MIT)
"""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, Header, Request, status
from functools import wraps

from .auth import (
    JWTManager,
    APIKeyManager,
    UserRole,
    InvalidTokenError,
    InvalidAPIKeyError,
    extract_bearer_token,
    check_user_roles,
)


# ============================================================================
# Authentication Context
# ============================================================================

class AuthContext:
    """
    Authentication context for authenticated requests

    Contains:
    - User ID
    - Wallet address (optional)
    - Roles
    - Authentication method (jwt or api_key)
    - API key metadata (if using API key auth)
    """

    def __init__(
        self,
        user_id: str,
        auth_method: str,
        roles: List[str],
        wallet_address: Optional[str] = None,
        api_key_metadata: Optional[dict] = None,
        rate_limit_multiplier: float = 1.0
    ):
        self.user_id = user_id
        self.auth_method = auth_method
        self.roles = roles
        self.wallet_address = wallet_address
        self.api_key_metadata = api_key_metadata or {}
        self.rate_limit_multiplier = rate_limit_multiplier

    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return check_user_roles(roles, self.roles)


# ============================================================================
# Authentication Dependencies
# ============================================================================

class AuthenticationMiddleware:
    """
    FastAPI authentication middleware

    Provides dependency injection for:
    - JWT authentication
    - API key authentication
    - Optional authentication (no error if missing)
    - Role-based access control
    """

    def __init__(
        self,
        jwt_manager: JWTManager,
        api_key_manager: APIKeyManager,
        api_key_store: dict  # In production, use database
    ):
        """
        Initialize authentication middleware

        Args:
            jwt_manager: JWT token manager
            api_key_manager: API key manager
            api_key_store: API key storage (key_id -> APIKey)
        """
        self.jwt_manager = jwt_manager
        self.api_key_manager = api_key_manager
        self.api_key_store = api_key_store

    async def authenticate_jwt(
        self,
        authorization: Optional[str] = Header(None, alias="Authorization")
    ) -> AuthContext:
        """
        Authenticate request using JWT token

        Args:
            authorization: Authorization header (Bearer <token>)

        Returns:
            AuthContext with user information

        Raises:
            HTTPException: 401 if authentication fails
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"}
            )

        try:
            # Extract and verify token
            token = extract_bearer_token(authorization)
            payload = self.jwt_manager.verify_token(token, token_type="access")

            # Create auth context
            return AuthContext(
                user_id=payload["sub"],
                auth_method="jwt",
                roles=payload.get("roles", ["user"]),
                wallet_address=payload.get("wallet")
            )

        except InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"}
            )

    async def authenticate_api_key(
        self,
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ) -> AuthContext:
        """
        Authenticate request using API key

        Args:
            x_api_key: API key from X-API-Key header

        Returns:
            AuthContext with API client information

        Raises:
            HTTPException: 401 if authentication fails
        """
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-Key header"
            )

        try:
            # Extract key ID and lookup stored key
            key_id = self.api_key_manager.extract_key_id(x_api_key)
            stored_key = self.api_key_store.get(key_id)

            if not stored_key:
                raise InvalidAPIKeyError("API key not found")

            # Verify API key
            self.api_key_manager.verify_api_key(x_api_key, stored_key)

            # Update last used timestamp
            from datetime import datetime, timezone
            stored_key.last_used_at = datetime.now(timezone.utc)

            # Create auth context
            return AuthContext(
                user_id=key_id,
                auth_method="api_key",
                roles=["api_client"],
                api_key_metadata=stored_key.metadata,
                rate_limit_multiplier=stored_key.rate_limit_multiplier
            )

        except InvalidAPIKeyError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    async def authenticate_any(
        self,
        authorization: Optional[str] = Header(None, alias="Authorization"),
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ) -> AuthContext:
        """
        Authenticate using either JWT or API key

        Tries JWT first, then API key

        Args:
            authorization: Authorization header (Bearer <token>)
            x_api_key: API key from X-API-Key header

        Returns:
            AuthContext with user information

        Raises:
            HTTPException: 401 if both authentication methods fail
        """
        # Try JWT first
        if authorization:
            try:
                return await self.authenticate_jwt(authorization)
            except HTTPException:
                pass  # Try API key

        # Try API key
        if x_api_key:
            try:
                return await self.authenticate_api_key(x_api_key)
            except HTTPException:
                pass

        # Both failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Authorization (JWT) or X-API-Key header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    async def authenticate_optional(
        self,
        authorization: Optional[str] = Header(None, alias="Authorization"),
        x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ) -> Optional[AuthContext]:
        """
        Optional authentication (returns None if not authenticated)

        Args:
            authorization: Authorization header (Bearer <token>)
            x_api_key: API key from X-API-Key header

        Returns:
            AuthContext if authenticated, None otherwise
        """
        try:
            return await self.authenticate_any(authorization, x_api_key)
        except HTTPException:
            return None


# ============================================================================
# Role-Based Access Control (RBAC)
# ============================================================================

def require_roles(required_roles: List[str]):
    """
    Decorator to require specific roles

    Usage:
        @app.get("/admin")
        @require_roles(["admin"])
        async def admin_endpoint(auth: AuthContext = Depends(middleware.authenticate_jwt)):
            ...

    Args:
        required_roles: List of required roles (any match is sufficient)

    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract auth context from kwargs
            auth_context = kwargs.get('auth')

            if not auth_context:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication context not found"
                )

            if not auth_context.has_any_role(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {required_roles}"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(func: Callable):
    """
    Decorator to require admin role

    Usage:
        @app.get("/admin")
        @require_admin
        async def admin_endpoint(auth: AuthContext = Depends(middleware.authenticate_jwt)):
            ...
    """
    return require_roles(["admin"])(func)


# ============================================================================
# Request Context Injection
# ============================================================================

async def inject_auth_context(
    request: Request,
    auth: AuthContext
):
    """
    Inject authentication context into request state

    Usage:
        @app.middleware("http")
        async def add_auth_context(request: Request, call_next):
            if hasattr(request.state, "auth"):
                # Auth already injected by dependency
                pass
            response = await call_next(request)
            return response

    Args:
        request: FastAPI request object
        auth: Authentication context
    """
    request.state.auth = auth


def get_auth_context(request: Request) -> Optional[AuthContext]:
    """
    Get authentication context from request state

    Args:
        request: FastAPI request object

    Returns:
        AuthContext if authenticated, None otherwise
    """
    return getattr(request.state, "auth", None)


# ============================================================================
# Helper Functions
# ============================================================================

def create_auth_middleware(
    jwt_secret: str,
    api_key_store: dict
) -> AuthenticationMiddleware:
    """
    Create authentication middleware with default configuration

    Args:
        jwt_secret: JWT secret key (min 32 bytes)
        api_key_store: API key storage (key_id -> APIKey)

    Returns:
        AuthenticationMiddleware instance
    """
    from .auth import create_jwt_manager, create_api_key_manager

    jwt_manager = create_jwt_manager(jwt_secret)
    api_key_manager = create_api_key_manager()

    return AuthenticationMiddleware(
        jwt_manager=jwt_manager,
        api_key_manager=api_key_manager,
        api_key_store=api_key_store
    )


# ============================================================================
# Error Handlers
# ============================================================================

def authentication_error_handler(request: Request, exc: HTTPException):
    """
    Custom error handler for authentication errors

    Returns consistent error format:
    {
        "error": "authentication_failed",
        "message": "Invalid token",
        "status": 401
    }
    """
    return {
        "error": "authentication_failed",
        "message": exc.detail,
        "status": exc.status_code
    }
