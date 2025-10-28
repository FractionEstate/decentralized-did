"""
FastAPI Backend Server for Biometric DID Operations (Mock Implementation)

Provides REST API endpoints for the demo-wallet to execute
biometric DID generation and verification commands.

This is a MOCK implementation that returns test data.
TODO: Integrate with real Python biometric CLI.

Endpoints:
- POST /api/biometric/generate - Generate biometric DID
- POST /api/biometric/verify - Verify fingerprints
- GET /health - Health check

Usage:
    MOCK_API_PORT=8002 python api_server_mock.py

Then configure demo-wallet to use: http://localhost:8002
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timezone
import hashlib
import base64
import os
import sys
from pathlib import Path

# Ensure SDK imports resolve
sdk_path = Path(__file__).parent.parent.parent / "sdk" / "src"
sys.path.insert(0, str(sdk_path))

# Import deterministic DID generation
from decentralized_did.did.generator import generate_deterministic_did

# Import Koios client for duplicate detection
from decentralized_did.cardano.cache import TTLCache
from decentralized_did.cardano.koios_client import KoiosClient, KoiosError

# Configuration
KOIOS_BASE_URL = os.environ.get("KOIOS_BASE_URL", "https://api.koios.rest/api/v1")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "testnet")
KOIOS_METADATA_LABEL = os.environ.get("KOIOS_METADATA_LABEL", "674")
KOIOS_METADATA_BLOCK_LIMIT = int(os.environ.get("KOIOS_METADATA_BLOCK_LIMIT", "1000"))
MOCK_API_HOST = os.environ.get("MOCK_API_HOST", "0.0.0.0")
MOCK_API_PORT = int(os.environ.get("MOCK_API_PORT", "8002"))
MOCK_API_RELOAD = os.environ.get("MOCK_API_RELOAD", "false").lower() == "true"

# Initialize Koios client for optional duplicate detection
koios_client: Optional[KoiosClient] = None
try:
    koios_client = KoiosClient(
        base_url=KOIOS_BASE_URL,
        cache=TTLCache(default_ttl=60),
        metadata_scan_limit=KOIOS_METADATA_BLOCK_LIMIT,
    )
    print(f"✅ Koios client initialized (mock server): {KOIOS_BASE_URL}")
except Exception as exc:  # pragma: no cover
    koios_client = None
    print(f"⚠️  Warning: Koios client failed to initialize: {exc}")

app = FastAPI(
    title="Biometric DID API (Mock)",
    description="Mock REST API for biometric DID generation and verification",
    version="1.0.0-mock",
)


@app.on_event("shutdown")
async def shutdown_koios_client() -> None:
    if koios_client:
        await koios_client.close()

# Configure CORS for demo-wallet access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",  # demo-wallet dev server
        "http://localhost:3000",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3000",
        "*",  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class FingerData(BaseModel):
    """Fingerprint minutiae data"""
    finger_id: str = Field(...,
                           description="Finger identifier (e.g., 'left_thumb')")
    minutiae: List[List[float]] = Field(
        ...,
        description="List of minutiae points [x, y, angle]"
    )


class GenerateRequest(BaseModel):
    """Request body for DID generation"""
    fingers: List[FingerData] = Field(...,
                                      description="List of fingerprint data")
    wallet_address: str = Field(..., description="Cardano wallet address")
    storage: str = Field(
        default="inline", description="Helper data storage method")
    format: str = Field(default="json", description="Output format")


class HelperDataEntry(BaseModel):
    """Helper data for one finger"""
    finger_id: str
    salt_b64: str
    auth_b64: str
    grid_size: float
    angle_bins: int


class CIP30MetadataInline(BaseModel):
    """CIP-30 metadata structure (v1.1 schema)"""
    version: str  # Changed from int to str for "1.1"
    walletAddress: str  # Legacy field, kept for backward compatibility
    controllers: List[str]  # NEW: Multi-controller support
    enrollmentTimestamp: str  # NEW: ISO 8601 timestamp
    biometric: Dict
    revoked: bool = False  # NEW: Revocation status
    revokedAt: Optional[str] = None  # NEW: Revocation timestamp


class GenerateResponse(BaseModel):
    """Response from DID generation"""
    did: str = Field(..., description="Generated DID")
    id_hash: str = Field(..., description="ID hash")
    wallet_address: str = Field(..., description="Wallet address")
    helpers: Dict[str, HelperDataEntry] = Field(
        ...,
        description="Helper data per finger"
    )
    metadata_cip30_inline: CIP30MetadataInline = Field(
        ...,
        description="CIP-30 formatted metadata"
    )
    tx_hash: Optional[str] = Field(
        None,
        description="Cardano transaction hash for on-chain metadata"
    )


class VerifyRequest(BaseModel):
    """Request body for verification"""
    fingers: List[FingerData] = Field(...,
                                      description="Fingerprints to verify")
    helpers: Dict[str, HelperDataEntry] = Field(
        ...,
        description="Helper data from enrollment"
    )
    expected_id_hash: str = Field(..., description="Expected ID hash to match")


class VerifyResponse(BaseModel):
    """Response from verification"""
    success: bool = Field(..., description="Whether verification succeeded")
    matched_fingers: List[str] = Field(
        ...,
        description="List of successfully matched finger IDs"
    )
    unmatched_fingers: List[str] = Field(
        ...,
        description="List of failed finger IDs"
    )
    error: Optional[str] = Field(None, description="Error message if failed")


# Helper functions
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


def generate_mock_helper(finger_id: str) -> HelperDataEntry:
    """Generate deterministic mock helper data for a finger."""
    salt_bytes = _deterministic_bytes("salt", finger_id, length=16)
    auth_bytes = _deterministic_bytes("auth", finger_id, length=32)

    return HelperDataEntry(
        finger_id=finger_id,
        salt_b64=_encode_b64(salt_bytes),
        auth_b64=_encode_b64(auth_bytes),
        grid_size=0.05,
        angle_bins=32,
    )


def compute_helper_hash(helpers: Dict[str, HelperDataEntry], wallet_address: Optional[str] = None) -> str:
    """Compute deterministic hash from helper data (and optional wallet)."""
    hash_ctx = hashlib.blake2b(digest_size=32)
    if wallet_address:
        hash_ctx.update(wallet_address.encode('utf-8'))

    for finger_id in sorted(helpers.keys()):
        entry = helpers[finger_id]
        hash_ctx.update(finger_id.encode('utf-8'))
        hash_ctx.update(entry.salt_b64.encode('utf-8'))
        hash_ctx.update(entry.auth_b64.encode('utf-8'))

    return _encode_b64(hash_ctx.digest())


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "biometric-did-api-mock",
        "version": "1.0.0-mock",
        "note": "This is a MOCK server. Integrate real Python CLI for production."
    }


@app.get("/metrics/koios")
async def koios_metrics():
    """Return Koios instrumentation counters when available."""

    if not koios_client:
        raise HTTPException(
            status_code=503,
            detail="Koios client not configured",
        )

    snapshot = koios_client.metrics_snapshot()

    return {
        "network": CARDANO_NETWORK,
        "base_url": KOIOS_BASE_URL,
        "metadata_label": KOIOS_METADATA_LABEL,
        "metadata_block_limit": KOIOS_METADATA_BLOCK_LIMIT,
        "cache_enabled": bool(koios_client.cache),
        "timeout_seconds": koios_client.timeout,
        "max_retries": koios_client.max_retries,
        "metrics": snapshot,
    }


@app.post("/api/biometric/generate", response_model=GenerateResponse)
async def generate_did(request: GenerateRequest):
    """
    Generate biometric DID from fingerprint minutiae (MOCK).

    Args:
        request: Generation request with fingerprint data

    Returns:
        Generated DID, helper data, and metadata (mock data)

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Generate mock commitment from fingerprint data
        # In production, this would be the real biometric commitment
        commitment_data = request.wallet_address.encode('utf-8')
        for finger in request.fingers:
            commitment_data += finger.finger_id.encode('utf-8')
            commitment_data += str(finger.minutiae).encode('utf-8')

        # Hash to create 32-byte commitment
        commitment = hashlib.sha256(commitment_data).digest()

        # Build DID using deterministic generation (SECURE format)
        # Note: Using "testnet" for mock server development
        did = generate_deterministic_did(commitment, network="testnet")

        # Check for duplicate DID enrollment (Sybil attack prevention)
        if koios_client:
            try:
                existing = await koios_client.check_did_exists(
                    did,
                    label=KOIOS_METADATA_LABEL,
                )
                if existing:
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
            except HTTPException:
                raise
            except KoiosError as e:
                # Log blockchain query errors but don't block enrollment
                print(f"⚠️  Warning: Koios duplicate check failed: {e}")
                print("   Continuing with enrollment (duplicate check skipped)")

        # Get current enrollment timestamp
        enrollment_timestamp = datetime.now(timezone.utc).isoformat()

        # Generate helper data for each finger
        helpers = {}
        for finger in request.fingers:
            helpers[finger.finger_id] = generate_mock_helper(finger.finger_id)

        # Generate mock ID hash from helper data (wallet optional)
        id_hash = compute_helper_hash(helpers)

        helpers_dict = {
            finger_id: entry.dict()
            for finger_id, entry in helpers.items()
        }

        # Build CIP-30 metadata with v1.1 schema
        cip30_metadata = CIP30MetadataInline(
            version="1.1",  # Updated to v1.1
            walletAddress=request.wallet_address,  # Legacy field, kept for compatibility
            # NEW: Multi-controller support
            controllers=[request.wallet_address],
            enrollmentTimestamp=enrollment_timestamp,  # NEW: Enrollment time
            biometric={
                "idHash": id_hash,
                "helperStorage": request.storage,
                "helperData": helpers_dict if request.storage == "inline" else None,
            },
            revoked=False,  # NEW: Revocation status
        )

        # Generate simulated/placeholder tx_hash for development
        # TODO: Replace with actual blockchain transaction submission in production
        tx_hash_material = f"{did}:{enrollment_timestamp}:{id_hash}".encode('utf-8')
        simulated_tx_hash = hashlib.sha256(tx_hash_material).hexdigest().lower()

        return GenerateResponse(
            did=did,
            id_hash=id_hash,
            wallet_address=request.wallet_address,
            helpers=helpers,
            metadata_cip30_inline=cip30_metadata,
            tx_hash=simulated_tx_hash  # In development/mock, this is simulated
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Biometric DID generation failed: {str(e)}"
        )


@app.post("/api/biometric/verify", response_model=VerifyResponse)
async def verify_did(request: VerifyRequest):
    """
    Verify fingerprints against stored helper data (MOCK).

    Args:
        request: Verification request with fingerprints and helper data

    Returns:
        Verification result with matched/unmatched fingers (mock: always succeeds)

    Raises:
        HTTPException: If verification fails
    """
    try:
        # Mock: Match all fingers that have helper data
        matched_fingers = []
        unmatched_fingers = []

        for finger in request.fingers:
            if finger.finger_id in request.helpers:
                matched_fingers.append(finger.finger_id)
            else:
                unmatched_fingers.append(finger.finger_id)

        computed_hash = compute_helper_hash(request.helpers)
        hash_matches = computed_hash == request.expected_id_hash

        success = len(matched_fingers) >= 2 and hash_matches

        error_message = None
        if not hash_matches:
            error_message = "Helper data hash mismatch"
        elif not success:
            error_message = "Insufficient matching fingerprints"

        return VerifyResponse(
            success=success,
            matched_fingers=matched_fingers,
            unmatched_fingers=unmatched_fingers,
            error=error_message
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Biometric verification failed: {str(e)}"
        )


# Development server
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🔐 Biometric DID API Server (MOCK)")
    print("=" * 60)
    print(f"Starting server at: http://{MOCK_API_HOST}:{MOCK_API_PORT}")
    print(f"API docs at: http://{MOCK_API_HOST}:{MOCK_API_PORT}/docs")
    print(f"Health check: http://{MOCK_API_HOST}:{MOCK_API_PORT}/health")
    print()
    print("⚠️  This is a MOCK server for development.")
    print("   Real biometric operations will be added in production.")
    print("=" * 60)
    print()

    uvicorn.run(
        "api_server_mock:app",
        host=MOCK_API_HOST,
        port=MOCK_API_PORT,
        reload=MOCK_API_RELOAD,
        log_level="info"
    )
