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
    python api_server_mock.py

Then configure demo-wallet to use: http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timezone
import hashlib
import base64
import os

# Import deterministic DID generation
from src.decentralized_did.did.generator import generate_deterministic_did

# Import Blockfrost client for duplicate detection
from src.decentralized_did.cardano.blockfrost import (
    BlockfrostClient,
    DIDAlreadyExistsError,
)

# Configuration
BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY", "")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "testnet")

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

app = FastAPI(
    title="Biometric DID API (Mock)",
    description="Mock REST API for biometric DID generation and verification",
    version="1.0.0-mock",
)

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
def generate_mock_id_hash(wallet_address: str, fingers: List[FingerData]) -> str:
    """Generate a deterministic mock ID hash from inputs"""
    # Create a deterministic hash from wallet address and finger IDs
    data = wallet_address + "".join(sorted([f.finger_id for f in fingers]))
    hash_bytes = hashlib.sha256(data.encode()).digest()
    return base64.b64encode(hash_bytes)[:16].decode('utf-8').replace('/', '_').replace('+', '-')


def generate_mock_helper(finger_id: str) -> HelperDataEntry:
    """Generate mock helper data for a finger"""
    # Use finger_id as seed for deterministic mock data
    seed = hashlib.md5(finger_id.encode()).digest()

    return HelperDataEntry(
        finger_id=finger_id,
        salt_b64=base64.b64encode(seed[:16]).decode('utf-8'),
        auth_b64=base64.b64encode(seed[16:] + os.urandom(16)).decode('utf-8'),
        grid_size=0.05,
        angle_bins=32,
    )


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

        # Generate mock ID hash for helper data compatibility
        id_hash = generate_mock_id_hash(
            request.wallet_address, request.fingers)

        # Build DID using deterministic generation (SECURE format)
        # Note: Using "testnet" for mock server development
        did = generate_deterministic_did(commitment, network="testnet")

        # Check for duplicate DID enrollment (Sybil attack prevention)
        if blockfrost_client:
            try:
                existing = blockfrost_client.check_did_exists(did)
                if existing:
                    # DID already exists on blockchain
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
            except Exception as e:
                # Log blockchain query errors but don't block enrollment
                print(f"⚠️  Warning: Duplicate check failed: {e}")
                print("   Continuing with enrollment (duplicate check skipped)")

        # Get current enrollment timestamp
        enrollment_timestamp = datetime.now(timezone.utc).isoformat()

        # Generate helper data for each finger
        helpers = {}
        for finger in request.fingers:
            helpers[finger.finger_id] = generate_mock_helper(finger.finger_id)

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
                "helperData": helpers if request.storage == "inline" else None,
            },
            revoked=False,  # NEW: Revocation status
        )

        return GenerateResponse(
            did=did,
            id_hash=id_hash,
            wallet_address=request.wallet_address,
            helpers=helpers,
            metadata_cip30_inline=cip30_metadata
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

        # Mock: Success if we matched at least 2 fingers
        success = len(matched_fingers) >= 2

        return VerifyResponse(
            success=success,
            matched_fingers=matched_fingers,
            unmatched_fingers=unmatched_fingers,
            error=None if success else "Insufficient matching fingerprints"
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
    print("Starting server at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print()
    print("⚠️  This is a MOCK server for development.")
    print("   Real biometric operations will be added in production.")
    print("=" * 60)
    print()

    uvicorn.run(
        "api_server_mock:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
