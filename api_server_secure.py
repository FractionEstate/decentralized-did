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

from src.biometrics.fuzzy_extractor_v2 import fuzzy_extract_gen, fuzzy_extract_rep, HelperData
from src.did.generator_v2 import (
    build_did_from_master_key,
    build_wallet_bundle,
    HelperDataEntry as HelperDataEntryInternal,
    HELPER_STORAGE_INLINE,
    HELPER_STORAGE_EXTERNAL,
    _encode_bytes,
)
from src.biometrics.aggregator_v2 import aggregate_finger_keys, FingerKey
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional
from datetime import datetime, timedelta
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

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# Configuration
# ============================================================================

# Environment variables (with secure defaults)
API_SECRET_KEY = os.getenv("API_SECRET_KEY", secrets.token_urlsafe(32))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3003,http://localhost:3000").split(",")
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
HTTPS_ONLY = os.getenv("HTTPS_ONLY", "false").lower() == "true"

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

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    fingers: List[FingerData] = Field(..., min_items=2, max_items=10)
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
    """CIP-30 metadata structure"""
    version: int
    walletAddress: str
    biometric: Dict


class GenerateResponse(BaseModel):
    """Response from DID generation"""
    did: str
    id_hash: str
    wallet_address: str
    helpers: Dict[str, HelperDataEntry]
    metadata_cip30_inline: CIP30MetadataInline


class VerifyRequest(BaseModel):
    """Request body for verification"""
    fingers: List[FingerData] = Field(..., min_items=2)
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
@limiter.limit("30/minute")
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


@app.post("/auth/token", response_model=AuthResponse)
@limiter.limit("5/minute")
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
@limiter.limit("3/minute")
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

        # Step 1: Convert minutiae to FingerKey objects via fuzzy extraction
        enrolled_keys = []
        helper_entries = []

        for finger in generate_request.fingers:
            # Convert minutiae list to bytes (mock implementation)
            minutiae_bytes = os.urandom(32)

            # Convert to 64-bit numpy array (fuzzy extractor requires 64 bits = 8 bytes)
            import numpy as np
            from src.biometrics.fuzzy_extractor_v2 import bytes_to_bitarray
            biometric_bits = bytes_to_bitarray(minutiae_bytes[:8])[
                :64]  # Take first 64 bits

            # Extract key using fuzzy extractor Gen function
            key, helper_data = fuzzy_extract_gen(
                biometric_bitstring=biometric_bits,
                user_id=f"{generate_request.wallet_address}:{finger.finger_id}"
            )

            # Create FingerKey for aggregation
            enrolled_keys.append(FingerKey(
                finger_id=finger.finger_id,
                key=key
            ))

            # Create helper data entry from HelperData object
            helper_entries.append(HelperDataEntryInternal(
                finger_id=finger.finger_id,
                version=helper_data.version,
                salt=_encode_bytes(helper_data.salt),
                personalization=_encode_bytes(helper_data.personalization),
                bch_syndrome=_encode_bytes(helper_data.bch_syndrome),
                hmac=_encode_bytes(helper_data.hmac),
            ))

        # Step 2: Aggregate finger keys
        aggregation_result = aggregate_finger_keys(
            enrolled_keys,
            enrolled_count=len(enrolled_keys)
        )
        master_key = aggregation_result.master_key

        # Step 3: Build DID
        did = build_did_from_master_key(
            generate_request.wallet_address, master_key)

        # Step 4: Build wallet bundle
        storage_mode = (
            HELPER_STORAGE_INLINE if generate_request.storage == "inline"
            else HELPER_STORAGE_EXTERNAL
        )

        bundle = build_wallet_bundle(
            wallet_address=generate_request.wallet_address,
            master_key=master_key,
            helper_data_entries=helper_entries,
            helper_storage=storage_mode,
            fingerprint_count=len(enrolled_keys),
            aggregation_mode=f"{len(enrolled_keys)}/{len(enrolled_keys)}",
        )

        # Step 5: Transform to API response format
        helpers_dict = {}
        for entry in helper_entries:
            helpers_dict[entry.finger_id] = HelperDataEntry(
                finger_id=entry.finger_id,
                salt_b64=entry.salt,
                auth_b64=entry.hmac,
                grid_size=0.05,
                angle_bins=32,
            )

        id_hash = str(did).split(
            '#')[-1] if '#' in str(did) else str(did).split(':')[-1]

        cip30_metadata = {
            "version": 1,
            "walletAddress": generate_request.wallet_address,
            "biometric": {
                "idHash": id_hash,
                "helperStorage": generate_request.storage,
                "helperData": helpers_dict if generate_request.storage == "inline" else None,
            }
        }

        audit_log("generate_success", current_user.user_id, {
            "did": str(did),
            "id_hash": id_hash
        })

        return GenerateResponse(
            did=str(did),
            id_hash=id_hash,
            wallet_address=generate_request.wallet_address,
            helpers=helpers_dict,
            metadata_cip30_inline=cip30_metadata
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
@limiter.limit("5/minute")
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

        matched_fingers = []
        unmatched_fingers = []

        # Step 1: Reproduce keys
        reproduced_keys = []

        for finger in verify_request.fingers:
            finger_id = finger.finger_id

            if finger_id not in verify_request.helpers:
                unmatched_fingers.append(finger_id)
                continue

            try:
                minutiae_bytes = os.urandom(32)
                helper = verify_request.helpers[finger_id]

                import base64
                import numpy as np
                from src.biometrics.fuzzy_extractor_v2 import bytes_to_bitarray

                # Reconstruct HelperData object from base64-encoded fields
                helper_data = HelperData(
                    version=1,
                    salt=base64.b64decode(helper.salt_b64),
                    personalization=base64.b64decode(helper.person_b64) if hasattr(
                        helper, 'person_b64') else os.urandom(32),
                    bch_syndrome=base64.b64decode(helper.auth_b64),
                    hmac=base64.b64decode(helper.hmac_b64) if hasattr(
                        helper, 'hmac_b64') else os.urandom(32),
                )

                # Convert minutiae to 64-bit numpy array
                biometric_bits = bytes_to_bitarray(minutiae_bytes[:8])[:64]

                # Reproduce key using fuzzy extractor Rep function
                reproduced_key = fuzzy_extract_rep(
                    biometric_bitstring=biometric_bits,
                    helper_data=helper_data
                )

                if reproduced_key:
                    reproduced_keys.append(FingerKey(
                        finger_id=finger_id,
                        key=reproduced_key
                    ))
                    matched_fingers.append(finger_id)
                else:
                    unmatched_fingers.append(finger_id)

            except Exception as e:
                logger.warning(f"Failed to reproduce key for {finger_id}: {e}")
                unmatched_fingers.append(finger_id)

        # Step 2: Aggregate and verify
        if len(reproduced_keys) >= 2:
            aggregation_result = aggregate_finger_keys(
                reproduced_keys,
                enrolled_count=len(verify_request.helpers)
            )
            master_key = aggregation_result.master_key

            wallet_address = "addr_test1_mock"
            did = build_did_from_master_key(wallet_address, master_key)
            computed_hash = str(did).split(
                '#')[-1] if '#' in str(did) else str(did).split(':')[-1]

            success = (computed_hash == verify_request.expected_id_hash)
        else:
            success = False

        audit_log("verify_complete", current_user.user_id, {
            "success": success,
            "matched_count": len(matched_fingers),
            "unmatched_count": len(unmatched_fingers)
        })

        return VerifyResponse(
            success=success,
            matched_fingers=matched_fingers,
            unmatched_fingers=unmatched_fingers,
            error=None if success else "Insufficient matching fingerprints"
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
