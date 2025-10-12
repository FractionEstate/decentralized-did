"""
FastAPI Backend Server for Biometric DID Operations

Provides REST API endpoints for the demo-wallet to execute
biometric DID generation and verification commands.

Endpoints:
- POST /api/biometric/generate - Generate biometric DID
- POST /api/biometric/verify - Verify fingerprints
- GET /health - Health check
"""

from src.biometrics.fuzzy_extractor_v2 import (
    FuzzyExtractor,
    extract_key,
    reproduce_key,
)
from src.did.generator_v2 import (
    build_did_from_master_key,
    build_wallet_bundle,
    HelperDataEntry,
    HELPER_STORAGE_INLINE,
    HELPER_STORAGE_EXTERNAL,
    _encode_bytes,
)
from src.biometrics.aggregator_v2 import aggregate_finger_keys, FingerKey
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import sys
import json
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


app = FastAPI(
    title="Biometric DID API",
    description="REST API for biometric DID generation and verification",
    version="1.0.0",
)

# Configure CORS for demo-wallet access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",  # demo-wallet dev server
        "http://localhost:3000",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3000",
        # Add production origins as needed
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
    """CIP-30 metadata structure"""
    version: int
    walletAddress: str
    biometric: Dict[str, any]


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


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "biometric-did-api",
        "version": "1.0.0"
    }


@app.post("/api/biometric/generate", response_model=GenerateResponse)
async def generate_did(request: GenerateRequest):
    """
    Generate biometric DID from fingerprint minutiae.

    Args:
        request: Generation request with fingerprint data

    Returns:
        Generated DID, helper data, and metadata

    Raises:
        HTTPException: If generation fails
    """
    try:
        # Step 1: Convert minutiae to FingerKey objects via fuzzy extraction
        enrolled_keys = []
        helper_entries = []

        for finger in request.fingers:
            # Convert minutiae list to bytes (mock implementation)
            # In production, this would use actual minutiae quantization
            minutiae_bytes = os.urandom(32)  # Mock: 32 random bytes per finger

            # Extract key using fuzzy extractor
            key, salt, syndrome, hmac = extract_key(
                minutiae_bytes,
                user_id=request.wallet_address,
                finger_id=finger.finger_id
            )

            # Create FingerKey for aggregation
            enrolled_keys.append(FingerKey(
                finger_id=finger.finger_id,
                key=key
            ))

            # Create helper data entry
            helper_entries.append(HelperDataEntry(
                finger_id=finger.finger_id,
                version=1,
                salt=_encode_bytes(salt),
                personalization=_encode_bytes(os.urandom(16)),  # Mock
                bch_syndrome=_encode_bytes(syndrome),
                hmac=_encode_bytes(hmac),
            ))

        # Step 2: Aggregate finger keys into master key
        aggregation_result = aggregate_finger_keys(
            enrolled_keys,
            enrolled_count=len(enrolled_keys)
        )
        master_key = aggregation_result.master_key

        # Step 3: Build DID from master key
        did = build_did_from_master_key(request.wallet_address, master_key)

        # Step 4: Build wallet bundle with metadata
        storage_mode = (
            HELPER_STORAGE_INLINE if request.storage == "inline"
            else HELPER_STORAGE_EXTERNAL
        )

        bundle = build_wallet_bundle(
            wallet_address=request.wallet_address,
            master_key=master_key,
            helper_data_entries=helper_entries,
            helper_storage=storage_mode,
            fingerprint_count=len(enrolled_keys),
            aggregation_mode=f"{len(enrolled_keys)}/{len(enrolled_keys)}",
        )

        # Step 5: Transform to API response format
        # Convert helper entries to dict
        helpers_dict = {}
        for entry in helper_entries:
            helpers_dict[entry.finger_id] = HelperDataEntry(
                finger_id=entry.finger_id,
                salt_b64=entry.salt,
                auth_b64=entry.hmac,
                grid_size=0.05,  # Mock value
                angle_bins=32,   # Mock value
            )

        # Extract ID hash from DID
        id_hash = str(did).split(
            '#')[-1] if '#' in str(did) else str(did).split(':')[-1]

        # Build CIP-30 metadata
        cip30_metadata = {
            "version": 1,
            "walletAddress": request.wallet_address,
            "biometric": {
                "idHash": id_hash,
                "helperStorage": request.storage,
                "helperData": helpers_dict if request.storage == "inline" else None,
            }
        }

        return GenerateResponse(
            did=str(did),
            id_hash=id_hash,
            wallet_address=request.wallet_address,
            helpers=helpers_dict,
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
    Verify fingerprints against stored helper data.

    Args:
        request: Verification request with fingerprints and helper data

    Returns:
        Verification result with matched/unmatched fingers

    Raises:
        HTTPException: If verification fails
    """
    try:
        matched_fingers = []
        unmatched_fingers = []

        # Step 1: Reproduce keys from fingerprints and helper data
        reproduced_keys = []

        for finger in request.fingers:
            finger_id = finger.finger_id

            # Check if we have helper data for this finger
            if finger_id not in request.helpers:
                unmatched_fingers.append(finger_id)
                continue

            try:
                # Convert minutiae to bytes (mock implementation)
                minutiae_bytes = os.urandom(32)  # Mock

                helper = request.helpers[finger_id]

                # Decode helper data from base64
                import base64
                salt = base64.b64decode(helper.salt_b64)
                # Using auth as syndrome mock
                syndrome = base64.b64decode(helper.auth_b64)

                # Reproduce key using fuzzy extractor
                reproduced_key = reproduce_key(
                    minutiae_bytes,
                    salt=salt,
                    syndrome=syndrome,
                    user_id="",  # Mock
                    finger_id=finger_id
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
                print(f"Failed to reproduce key for {finger_id}: {e}")
                unmatched_fingers.append(finger_id)

        # Step 2: Aggregate reproduced keys
        if len(reproduced_keys) >= 2:  # Need at least 2 fingers
            aggregation_result = aggregate_finger_keys(
                reproduced_keys,
                enrolled_count=len(request.helpers)
            )
            master_key = aggregation_result.master_key

            # Step 3: Compute ID hash from master key
            # Extract wallet address from first helper entry
            wallet_address = "addr_test1_mock"  # Mock: should come from request
            did = build_did_from_master_key(wallet_address, master_key)
            computed_hash = str(did).split(
                '#')[-1] if '#' in str(did) else str(did).split(':')[-1]

            # Step 4: Compare with expected hash
            success = (computed_hash == request.expected_id_hash)
        else:
            success = False

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

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
