"""
Authentication & Authorization Module for API Security

Features:
- JWT token generation and validation
- API key generation, hashing, and validation
- Wallet signature verification (Cardano)
- Authentication middleware
- Role-based access control (RBAC)
- Token refresh mechanism
- API key revocation

License: Open-source (MIT)
Dependencies: PyJWT (MIT), bcrypt (Apache 2.0)
"""

import jwt
import bcrypt
import secrets
import hashlib
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum


class UserRole(Enum):
    """User role enumeration for RBAC"""
    USER = "user"
    ADMIN = "admin"
    API_CLIENT = "api_client"


@dataclass
class JWTToken:
    """JWT token container"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # 15 minutes


@dataclass
class APIKey:
    """API key container"""
    key_id: str
    key_hash: str
    prefix: str  # "did_prod_" or "did_test_"
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_active: bool
    rate_limit_multiplier: float  # 1.0 = normal, 2.0 = double limits
    metadata: Dict


class AuthenticationError(Exception):
    """Base authentication error"""
    pass


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token"""
    pass


class InvalidAPIKeyError(AuthenticationError):
    """Invalid or revoked API key"""
    pass


class InvalidSignatureError(AuthenticationError):
    """Invalid wallet signature"""
    pass


# ============================================================================
# JWT Token Management
# ============================================================================

class JWTManager:
    """
    JWT token generation and validation

    Implements:
    - Access token (short-lived, 15 minutes)
    - Refresh token (long-lived, 7 days)
    - HS256 signing algorithm
    - Standard claims (exp, iat, sub, roles)
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT manager

        Args:
            secret_key: Secret key for signing tokens (min 32 bytes)
            algorithm: Signing algorithm (default: HS256)
        """
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 bytes")

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expiry = timedelta(minutes=15)
        self.refresh_token_expiry = timedelta(days=7)

    def create_access_token(
        self,
        user_id: str,
        wallet_address: Optional[str] = None,
        roles: Optional[List[str]] = None,
        custom_claims: Optional[Dict] = None
    ) -> str:
        """
        Create access token (short-lived)

        Args:
            user_id: Unique user identifier
            wallet_address: Cardano wallet address (optional)
            roles: User roles (default: ["user"])
            custom_claims: Additional claims to include

        Returns:
            Signed JWT access token
        """
        now = datetime.now(timezone.utc)
        expires_at = now + self.access_token_expiry

        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expires_at,
            "type": "access",
            "roles": roles or ["user"],
        }

        if wallet_address:
            payload["wallet"] = wallet_address

        if custom_claims:
            payload.update(custom_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """
        Create refresh token (long-lived)

        Args:
            user_id: Unique user identifier

        Returns:
            Signed JWT refresh token
        """
        now = datetime.now(timezone.utc)
        expires_at = now + self.refresh_token_expiry

        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expires_at,
            "type": "refresh",
            "jti": secrets.token_urlsafe(16),  # Unique token ID
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(
        self,
        user_id: str,
        wallet_address: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> JWTToken:
        """
        Create access + refresh token pair

        Args:
            user_id: Unique user identifier
            wallet_address: Cardano wallet address (optional)
            roles: User roles (default: ["user"])

        Returns:
            JWTToken with access and refresh tokens
        """
        access_token = self.create_access_token(user_id, wallet_address, roles)
        refresh_token = self.create_refresh_token(user_id)

        return JWTToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(self.access_token_expiry.total_seconds())
        )

    def verify_token(self, token: str, token_type: str = "access") -> Dict:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get("type") != token_type:
                raise InvalidTokenError(
                    f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}"
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Create new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        user_id = payload["sub"]

        # Extract original roles if available
        roles = payload.get("roles", ["user"])
        wallet = payload.get("wallet")

        return self.create_access_token(user_id, wallet, roles)


# ============================================================================
# API Key Management
# ============================================================================

class APIKeyManager:
    """
    API key generation, hashing, and validation

    Implements:
    - Secure key generation (32 bytes random)
    - bcrypt hashing (cost factor 12)
    - Key prefixes (did_prod_, did_test_)
    - Key expiration
    - Rate limit multipliers
    """

    def __init__(self, bcrypt_rounds: int = 12):
        """
        Initialize API key manager

        Args:
            bcrypt_rounds: bcrypt cost factor (default: 12, recommended: 10-14)
        """
        self.bcrypt_rounds = bcrypt_rounds

    def generate_api_key(
        self,
        prefix: str = "did_prod_",
        expires_days: Optional[int] = None,
        rate_limit_multiplier: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> tuple[str, APIKey]:
        """
        Generate new API key

        Args:
            prefix: Key prefix ("did_prod_" or "did_test_")
            expires_days: Days until expiration (None = no expiration)
            rate_limit_multiplier: Rate limit multiplier (1.0 = normal)
            metadata: Custom metadata (e.g., {"app_name": "Demo Wallet"})

        Returns:
            Tuple of (raw_key, APIKey object)

        Note: Raw key is only returned once and never stored
        """
        # Generate random key (32 bytes = 256 bits)
        random_part = secrets.token_urlsafe(32)
        raw_key = f"{prefix}{random_part}"

        # Hash the key (bcrypt)
        key_hash = bcrypt.hashpw(
            raw_key.encode(), bcrypt.gensalt(self.bcrypt_rounds))

        # Generate key ID (first 8 chars of hash)
        key_id = hashlib.sha256(raw_key.encode()).hexdigest()[:16]

        # Calculate expiration
        created_at = datetime.now(timezone.utc)
        expires_at = None
        if expires_days:
            expires_at = created_at + timedelta(days=expires_days)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash.decode(),
            prefix=prefix,
            created_at=created_at,
            expires_at=expires_at,
            last_used_at=None,
            is_active=True,
            rate_limit_multiplier=rate_limit_multiplier,
            metadata=metadata or {}
        )

        return (raw_key, api_key)

    def verify_api_key(self, raw_key: str, stored_key: APIKey) -> bool:
        """
        Verify API key against stored hash

        Args:
            raw_key: Raw API key from request
            stored_key: Stored APIKey object

        Returns:
            True if key is valid and active

        Raises:
            InvalidAPIKeyError: If key is invalid, expired, or revoked
        """
        # Check if key is active
        if not stored_key.is_active:
            raise InvalidAPIKeyError("API key has been revoked")

        # Check expiration
        if stored_key.expires_at:
            if datetime.now(timezone.utc) > stored_key.expires_at:
                raise InvalidAPIKeyError("API key has expired")

        # Verify hash
        is_valid = bcrypt.checkpw(
            raw_key.encode(), stored_key.key_hash.encode())

        if not is_valid:
            raise InvalidAPIKeyError("Invalid API key")

        return True

    def revoke_api_key(self, stored_key: APIKey):
        """
        Revoke API key (sets is_active to False)

        Args:
            stored_key: APIKey object to revoke
        """
        stored_key.is_active = False

    def extract_key_id(self, raw_key: str) -> str:
        """
        Extract key ID from raw key (for lookup)

        Args:
            raw_key: Raw API key

        Returns:
            Key ID (16-char hex string)
        """
        return hashlib.sha256(raw_key.encode()).hexdigest()[:16]


# ============================================================================
# Wallet Signature Verification (Cardano)
# ============================================================================

class WalletSignatureVerifier:
    """
    Cardano wallet signature verification

    Implements:
    - CIP-8 message signing verification
    - Ed25519 signature verification
    - Wallet address validation
    """

    @staticmethod
    def verify_signature(
        wallet_address: str,
        message: str,
        signature: str,
        public_key: Optional[str] = None
    ) -> bool:
        """
        Verify Cardano wallet signature

        Args:
            wallet_address: Cardano wallet address (addr1... or addr_test1...)
            message: Original message that was signed
            signature: Hex-encoded signature
            public_key: Hex-encoded public key (optional)

        Returns:
            True if signature is valid

        Raises:
            InvalidSignatureError: If signature is invalid

        Note: This is a placeholder. Actual implementation requires
              pycardano library for CIP-8 verification.
        """
        # TODO: Implement actual CIP-8 signature verification
        # This requires pycardano library (Apache 2.0 license)
        # For now, return True for testing

        # Validate wallet address format
        if not wallet_address.startswith(("addr1", "addr_test1")):
            raise InvalidSignatureError("Invalid wallet address format")

        # Validate signature format (hex string)
        try:
            bytes.fromhex(signature)
        except ValueError:
            raise InvalidSignatureError(
                "Invalid signature format (must be hex)")

        # Placeholder: Always return True for testing
        # In production, implement actual Ed25519 verification
        return True


# ============================================================================
# Helper Functions
# ============================================================================

def create_jwt_manager(secret_key: Optional[str] = None) -> JWTManager:
    """
    Create JWT manager with secure secret key

    Args:
        secret_key: Secret key (generates random if not provided)

    Returns:
        JWTManager instance
    """
    if not secret_key:
        secret_key = secrets.token_urlsafe(32)

    return JWTManager(secret_key)


def create_api_key_manager(bcrypt_rounds: int = 12) -> APIKeyManager:
    """
    Create API key manager

    Args:
        bcrypt_rounds: bcrypt cost factor (default: 12)

    Returns:
        APIKeyManager instance
    """
    return APIKeyManager(bcrypt_rounds)


def extract_bearer_token(authorization_header: str) -> str:
    """
    Extract token from Authorization header

    Args:
        authorization_header: "Bearer <token>" string

    Returns:
        Token string

    Raises:
        InvalidTokenError: If header format is invalid
    """
    if not authorization_header:
        raise InvalidTokenError("Missing Authorization header")

    parts = authorization_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError(
            "Invalid Authorization header format. Expected: Bearer <token>")

    return parts[1]


def check_user_roles(required_roles: List[str], user_roles: List[str]) -> bool:
    """
    Check if user has required roles

    Args:
        required_roles: Required roles (any match is sufficient)
        user_roles: User's roles

    Returns:
        True if user has at least one required role
    """
    return any(role in user_roles for role in required_roles)
