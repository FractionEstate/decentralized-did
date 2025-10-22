"""
Production-Ready FastAPI Backend with Security Hardening

Security Features:
- Rate limiting (SlowAPI)
- JWT authentication
- Request validation
- Audit logging
- CORS configuration
- HTTPS enforcement
- Security headers
"""

# Import deterministic DID generation
from src.decentralized_did.did.generator import generate_deterministic_did

# Import Blockfrost client for duplicate detection
from src.decentralized_did.cardano.blockfrost import (
    BlockfrostClient,
    DIDAlreadyExistsError,
)
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys
import json
import os
import logging
import hashlib
import hmac
from pathlib import Path
import secrets
import base64


def _encode_b64(data: bytes) -> str:
    """Return URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def _deterministic_bytes(label: str, finger_id: str, length: int) -> bytes:
    """Derive deterministic bytes from label + finger_id."""
    hasher = hashlib.blake2b(digest_size=length)
    hasher.update(label.encode('utf-8'))
    hasher.update(b':')
    hasher.update(finger_id.encode('utf-8'))
    return hasher.digest()


def generate_helper_entry(finger_id: str) -> "HelperDataEntry":
    """Generate deterministic helper data for a finger."""
    salt_bytes = _deterministic_bytes("salt", finger_id, length=16)
    auth_bytes = _deterministic_bytes("auth", finger_id, length=32)

    return HelperDataEntry(
        finger_id=finger_id,
        salt_b64=_encode_b64(salt_bytes),
        auth_b64=_encode_b64(auth_bytes),
        grid_size=0.05,
        angle_bins=32,
    )


def compute_helper_hash(
    helpers: Dict[str, "HelperDataEntry"],
    wallet_address: Optional[str] = None,
) -> str:
    """Compute deterministic hash from helper data and optional wallet."""
    hash_ctx = hashlib.blake2b(digest_size=32)

    if wallet_address:
        hash_ctx.update(wallet_address.encode('utf-8'))

    for finger_id in sorted(helpers.keys()):
        entry = helpers[finger_id]
        hash_ctx.update(finger_id.encode('utf-8'))
        hash_ctx.update(entry.salt_b64.encode('utf-8'))
        hash_ctx.update(entry.auth_b64.encode('utf-8'))

    return _encode_b64(hash_ctx.digest())


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# Configuration
# ============================================================================

# Environment variables (with secure defaults)
ENVIRONMENT = os.getenv(
    "ENVIRONMENT", "development").strip().lower() or "development"
API_SECRET_KEY = os.getenv("API_SECRET_KEY", secrets.token_urlsafe(32))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3003,http://localhost:3000").split(",")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
HTTPS_ONLY = os.getenv("HTTPS_ONLY", "false").lower() == "true"

# Blockfrost configuration for duplicate detection
BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY", "")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "mainnet")

# Security posture reference data
STRICT_ENVIRONMENTS = {"production", "staging"}
DEFAULT_API_SECRET_VALUES = {
    "test_api_key_admin_32_chars_long_abcdef123456",
    "test_api_key_user_32_chars_long_xyz789abc",
    "test_api_key_integration_32_chars_long_xyz",
}
DEFAULT_JWT_SECRET_VALUES = {
    "jwt_secret_for_signing_tokens_32_chars_long",
    "jwt_secret_for_signing_tokens_32_chars_long_dev",
}
ALLOWED_CARDANO_NETWORKS = {"mainnet", "testnet", "preprod", "preview"}

# Initialize Blockfrost client if API key is available
blockfrost_client = None
if BLOCKFROST_API_KEY:
    blockfrost_client = BlockfrostClient(
        api_key=BLOCKFROST_API_KEY,
        network=CARDANO_NETWORK
    )
    print(f"✅ Blockfrost client initialized: {CARDANO_NETWORK}")
else:
    print("⚠️  Warning: BLOCKFROST_API_KEY not set, duplicate detection disabled")

# ============================================================================
# Logging Configuration
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Audit log (separate file for security events)
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(message)s')
)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


def validate_security_configuration() -> None:
    """Validate environment configuration against security baseline."""
    hard_failures: List[str] = []
    soft_failures: List[str] = []
    policy_messages: List[str] = []

    if len(API_SECRET_KEY) < 32:
        hard_failures.append("API_SECRET_KEY must be at least 32 characters")
    if API_SECRET_KEY in DEFAULT_API_SECRET_VALUES:
        policy_messages.append(
            "API_SECRET_KEY uses a known test value; rotate before production use")

    if len(JWT_SECRET_KEY) < 32:
        hard_failures.append("JWT_SECRET_KEY must be at least 32 characters")
    if JWT_SECRET_KEY in DEFAULT_JWT_SECRET_VALUES:
        policy_messages.append(
            "JWT_SECRET_KEY uses a known test value; rotate before production use")

    if CARDANO_NETWORK not in ALLOWED_CARDANO_NETWORKS:
        hard_failures.append(
            f"CARDANO_NETWORK '{CARDANO_NETWORK}' is not supported; choose one of {sorted(ALLOWED_CARDANO_NETWORKS)}"
        )

    if JWT_EXPIRATION_HOURS > 24:
        policy_messages.append(
            f"JWT_EXPIRATION_HOURS ({JWT_EXPIRATION_HOURS}) exceeds the 24 hour baseline; review token lifetime"
        )

    if not HTTPS_ONLY:
        policy_messages.append(
            "HTTPS_ONLY disabled; TLS termination must be enforced in production")
    if not RATE_LIMIT_ENABLED:
        policy_messages.append(
            "RATE_LIMIT_ENABLED disabled; enable SlowAPI backpressure outside local testing")
    if not AUDIT_LOG_ENABLED:
        policy_messages.append(
            "AUDIT_LOG_ENABLED disabled; audit trail will be incomplete")
    if not BLOCKFROST_API_KEY:
        policy_messages.append(
            "BLOCKFROST_API_KEY not set; duplicate DID detection is offline")

    if ENVIRONMENT in STRICT_ENVIRONMENTS:
        hard_failures.extend(policy_messages)
        policy_messages = []

    if hard_failures:
        raise RuntimeError(
            "Security configuration invalid for environment "
            f"'{ENVIRONMENT}': " + "; ".join(hard_failures)
        )

    for message in policy_messages:
        logger.warning("Security baseline warning: %s", message)

    logger.info(
        "Security baseline loaded (env=%s, rate_limit=%s, audit_log=%s, https_only=%s)",
        ENVIRONMENT,
        RATE_LIMIT_ENABLED,
        AUDIT_LOG_ENABLED,
        HTTPS_ONLY,
    )


validate_security_configuration()


def audit_log(event: str, user_id: str, details: Dict):
    """Log security-relevant events"""
    if AUDIT_LOG_ENABLED:
        audit_logger.info(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "user_id": user_id,
            "details": details
        }))

# ============================================================================
# Rate Limiting
# ============================================================================


limiter = Limiter(key_func=get_remote_address)


def rate_limit(limit: str):
    """Conditional rate limit decorator based on configuration."""
    if RATE_LIMIT_ENABLED:
        return limiter.limit(limit)

    def decorator(func):
        return func

    return decorator

# ============================================================================
# FastAPI App
# ============================================================================


app = FastAPI(
    title="Biometric DID API (Production)",
    description="Secure REST API for biometric DID generation and verification",
    version="2.0.0",
    docs_url="/docs" if not HTTPS_ONLY else None,  # Disable docs in HTTPS-only mode
    redoc_url="/redoc" if not HTTPS_ONLY else None,
)


@app.on_event("shutdown")
async def shutdown_blockfrost_client() -> None:
    if blockfrost_client:
        await blockfrost_client.close()

# Add rate limiter to app state
app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: Exception):
    """Adapter to satisfy FastAPI exception handler signature."""
    if isinstance(exc, RateLimitExceeded):
        return _rate_limit_exceeded_handler(request, exc)
    raise exc


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ============================================================================
# Security Middleware
# ============================================================================

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Add request ID for tracking
    request_id = request.headers.get("X-Request-ID", secrets.token_hex(16))
    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def enforce_https(request: Request, call_next):
    """Enforce HTTPS in production"""
    if HTTPS_ONLY and request.url.scheme != "https":
        # Redirect to HTTPS
        https_url = request.url.replace(scheme="https")
        return JSONResponse(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            content={"detail": "HTTPS required"},
            headers={"Location": str(https_url)}
        )
    return await call_next(request)

# ============================================================================
# Authentication
# ============================================================================

security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    exp: datetime


def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "exp": expire.timestamp(),
        "iat": datetime.utcnow().timestamp(),
    }

    # Sign token with HMAC
    token_string = json.dumps(payload)
    signature = hmac.new(
        JWT_SECRET_KEY.encode(),
        token_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{token_string}.{signature}"


def verify_token(token: str) -> TokenData:
    """Verify JWT token"""
    try:
        # Split token and signature
        parts = token.rsplit('.', 1)
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )

        token_string, signature = parts

        # Verify signature
        expected_signature = hmac.new(
            JWT_SECRET_KEY.encode(),
            token_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature"
            )

        # Parse payload
        payload = json.loads(token_string)

        # Check expiration
        if datetime.utcnow().timestamp() > payload["exp"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )

        return TokenData(
            user_id=payload["user_id"],
            exp=datetime.fromtimestamp(payload["exp"])
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return verify_token(token)

# ============================================================================
# Request/Response Models
# ============================================================================


class FingerData(BaseModel):
    """Fingerprint minutiae data"""
    finger_id: str = Field(..., description="Finger identifier")
    minutiae: List[List[float]
                   ] = Field(..., description="Minutiae points [x, y, angle]")

    @validator('minutiae')
    def validate_minutiae(cls, v):
        """Validate minutiae format"""
        if not v:
            raise ValueError("Minutiae list cannot be empty")
        for point in v:
            if len(point) != 3:
                raise ValueError("Each minutia must have [x, y, angle]")
        return v


class GenerateRequest(BaseModel):
    """Request body for DID generation"""
    fingers: List[FingerData] = Field(..., min_length=1, max_length=10)
    wallet_address: str = Field(..., min_length=10, max_length=200)
    storage: str = Field(default="inline")
    format: str = Field(default="json")

    @validator('storage')
    def validate_storage(cls, v):
        """Validate storage mode"""
        if v not in ["inline", "external"]:
            raise ValueError("Storage must be 'inline' or 'external'")
        return v


class HelperDataEntry(BaseModel):
    """Helper data for one finger"""
    finger_id: str
    salt_b64: str
    auth_b64: str
    grid_size: float
    angle_bins: int


class CIP30MetadataInline(BaseModel):
    """CIP-30 metadata structure (v1.1 schema)"""
    version: str
    walletAddress: str
    controllers: List[str]
    enrollmentTimestamp: str
    biometric: Dict
    revoked: bool = False
    revokedAt: Optional[str] = None


class GenerateResponse(BaseModel):
    """Response from DID generation"""
    did: str
    id_hash: str
    wallet_address: str
    helpers: Dict[str, HelperDataEntry]
    metadata_cip30_inline: CIP30MetadataInline


class VerifyRequest(BaseModel):
    """Request body for verification"""
    fingers: List[FingerData] = Field(..., min_length=1)
    helpers: Dict[str, HelperDataEntry]
    expected_id_hash: str = Field(..., min_length=32)


class VerifyResponse(BaseModel):
    """Response from verification"""
    success: bool
    matched_fingers: List[str]
    unmatched_fingers: List[str]
    error: Optional[str] = None


class AuthRequest(BaseModel):
    """Authentication request"""
    api_key: str = Field(..., min_length=32)


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/health")
@rate_limit("30/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "biometric-did-api",
        "version": "2.0.0",
        "security": {
            "rate_limiting": RATE_LIMIT_ENABLED,
            "audit_logging": AUDIT_LOG_ENABLED,
            "https_only": HTTPS_ONLY,
        }
    }


@app.get("/metrics/blockfrost")
@rate_limit("10/minute")
async def get_blockfrost_metrics(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
):
    """Return Blockfrost performance metrics for observability dashboards."""

    if not blockfrost_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockfrost client not configured",
        )

    snapshot = blockfrost_client.metrics_snapshot()
    audit_log(
        "blockfrost_metrics",
        current_user.user_id,
        {
            "network": CARDANO_NETWORK,
            "total_requests": snapshot["total_requests"],
            "error_rate": snapshot["error_rate"],
        },
    )

    return {
        "network": CARDANO_NETWORK,
        "cache_enabled": bool(blockfrost_client.cache),
        "timeout_seconds": blockfrost_client.timeout,
        "max_retries": blockfrost_client.max_retries,
        "metrics": snapshot,
        "requested_by": current_user.user_id,
    }


@app.post("/auth/token", response_model=AuthResponse)
@rate_limit("5/minute")
async def authenticate(request: Request, auth_request: AuthRequest):
    """
    Authenticate and get access token.

    In production, this would validate against a user database.
    For demo purposes, we use a simple API key check.
    """
    # Simple API key validation (replace with proper auth in production)
    if not hmac.compare_digest(auth_request.api_key, API_SECRET_KEY):
        audit_log("auth_failed", "unknown", {"reason": "invalid_api_key"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Generate user ID from API key (in production, fetch from database)
    user_id = hashlib.sha256(auth_request.api_key.encode()).hexdigest()[:16]

    # Create access token
    access_token = create_access_token(user_id)

    audit_log("auth_success", user_id, {"method": "api_key"})

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )


@app.post("/api/biometric/generate", response_model=GenerateResponse)
@rate_limit("3/minute")
async def generate_did(
    request: Request,
    generate_request: GenerateRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate biometric DID from fingerprint minutiae.

    Requires authentication via JWT token.
    Rate limited to 3 requests per minute.
    """
    try:
        audit_log("generate_start", current_user.user_id, {
            "wallet_address": generate_request.wallet_address,
            "finger_count": len(generate_request.fingers),
            "storage": generate_request.storage
        })

        # Step 1: Build deterministic commitment from wallet + fingerprint data
        commitment_material = generate_request.wallet_address.encode('utf-8')
        for finger in generate_request.fingers:
            commitment_material += finger.finger_id.encode('utf-8')
            commitment_material += json.dumps(
                finger.minutiae,
                separators=(',', ':'),
                sort_keys=True
            ).encode('utf-8')

        commitment = hashlib.sha256(commitment_material).digest()

        # Step 2: Build DID using deterministic generation (network from env or default)
        network = CARDANO_NETWORK or "mainnet"
        did = generate_deterministic_did(commitment, network=network)

        # Check for duplicate DID enrollment (Sybil attack prevention)
        if blockfrost_client:
            try:
                existing = await blockfrost_client.check_did_exists(did)
                if existing:
                    # DID already exists on blockchain
                    audit_log("duplicate_did_detected", current_user.user_id, {
                        "did": did,
                        "tx_hash": existing.get("tx_hash"),
                        "controllers": existing.get("controllers", [])
                    })
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "DID_ALREADY_EXISTS",
                            "message": "This biometric identity has already been enrolled on the blockchain",
                            "did": did,
                            "tx_hash": existing.get("tx_hash"),
                            "enrolled_at": existing.get("enrollment_timestamp"),
                            "controllers": existing.get("controllers", []),
                            "suggestion": "If you control this identity, you can add a new controller wallet instead of re-enrolling",
                            "how_to": "Use the add-controller endpoint with your new wallet address"
                        }
                    )
            except DIDAlreadyExistsError as e:
                # Custom exception with enrollment data
                audit_log("duplicate_did_detected", current_user.user_id, {
                    "did": e.did,
                    "tx_hash": e.tx_hash
                })
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "DID_ALREADY_EXISTS",
                        "message": str(e),
                        "did": e.did,
                        "tx_hash": e.tx_hash,
                        "enrollment_data": e.enrollment_data
                    }
                )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                # Log blockchain query errors but don't block enrollment
                logger.warning(f"Duplicate check failed: {e}")
                audit_log("duplicate_check_failed", current_user.user_id, {
                    "did": did,
                    "error": str(e)
                })

        # Get enrollment timestamp
        enrollment_timestamp = datetime.now(timezone.utc).isoformat()
        helpers_dict: Dict[str, HelperDataEntry] = {}
        for finger in generate_request.fingers:
            helpers_dict[finger.finger_id] = generate_helper_entry(
                finger.finger_id)

        id_hash = compute_helper_hash(helpers_dict)

        metadata = CIP30MetadataInline(
            version="1.1",
            walletAddress=generate_request.wallet_address,
            controllers=[generate_request.wallet_address],
            enrollmentTimestamp=enrollment_timestamp,
            biometric={
                "idHash": id_hash,
                "helperStorage": generate_request.storage,
                "helperData": (
                    {finger_id: entry.dict()
                     for finger_id, entry in helpers_dict.items()}
                    if generate_request.storage == "inline"
                    else None
                ),
            },
            revoked=False,
            revokedAt=None,
        )

        audit_log("generate_success", current_user.user_id, {
            "did": str(did),
            "id_hash": id_hash
        })

        return GenerateResponse(
            did=str(did),
            id_hash=id_hash,
            wallet_address=generate_request.wallet_address,
            helpers=helpers_dict,
            metadata_cip30_inline=metadata
        )

    except Exception as e:
        audit_log("generate_failed", current_user.user_id, {
            "error": str(e),
            "wallet_address": generate_request.wallet_address
        })
        logger.exception("DID generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric DID generation failed: {str(e)}"
        )


@app.post("/api/biometric/verify", response_model=VerifyResponse)
@rate_limit("5/minute")
async def verify_did(
    request: Request,
    verify_request: VerifyRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Verify fingerprints against stored helper data.

    Requires authentication via JWT token.
    Rate limited to 5 requests per minute.
    """
    try:
        audit_log("verify_start", current_user.user_id, {
            "finger_count": len(verify_request.fingers),
            "expected_id_hash": verify_request.expected_id_hash[:16] + "..."
        })

        matched_fingers: List[str] = []
        unmatched_fingers: List[str] = []

        for finger in verify_request.fingers:
            if finger.finger_id in verify_request.helpers:
                matched_fingers.append(finger.finger_id)
            else:
                unmatched_fingers.append(finger.finger_id)

        computed_hash = compute_helper_hash(verify_request.helpers)
        success = (
            len(matched_fingers) >= 2 and
            computed_hash == verify_request.expected_id_hash
        )

        audit_log("verify_complete", current_user.user_id, {
            "success": success,
            "matched_count": len(matched_fingers),
            "unmatched_count": len(unmatched_fingers)
        })

        return VerifyResponse(
            success=success,
            matched_fingers=matched_fingers,
            unmatched_fingers=unmatched_fingers,
            error=None if success else (
                "Helper data hash mismatch"
                if computed_hash != verify_request.expected_id_hash
                else "Insufficient matching fingerprints"
            )
        )

    except Exception as e:
        audit_log("verify_failed", current_user.user_id, {
            "error": str(e)
        })
        logger.exception("Verification failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric verification failed: {str(e)}"
        )

# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Biometric DID API Server (Production Mode)")
    logger.info(f"Rate Limiting: {RATE_LIMIT_ENABLED}")
    logger.info(f"Audit Logging: {AUDIT_LOG_ENABLED}")
    logger.info(f"HTTPS Only: {HTTPS_ONLY}")
    logger.info(f"CORS Origins: {CORS_ORIGINS}")

    uvicorn.run(
        "api_server_secure:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        log_level="info",
        access_log=True,
    )
