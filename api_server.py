"""Basic FastAPI server for biometric DID operations.

This implementation mirrors the secure API's deterministic behaviour without
adding authentication or rate limiting. It supports legacy integrations and
rapid local testing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import base64
import hashlib
import json
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure local imports resolve correctly when executed as a module.
sys.path.insert(0, str(Path(__file__).parent))

from src.decentralized_did.cardano.blockfrost import (  # noqa: E402  pylint: disable=wrong-import-position
    BlockfrostClient,
    DIDAlreadyExistsError,
)
from src.decentralized_did.did.generator import (  # noqa: E402  pylint: disable=wrong-import-position
    generate_deterministic_did,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BLOCKFROST_API_KEY = os.environ.get("BLOCKFROST_API_KEY", "")
CARDANO_NETWORK = os.environ.get("CARDANO_NETWORK", "testnet")

blockfrost_client: Optional[BlockfrostClient] = None
if BLOCKFROST_API_KEY:
    blockfrost_client = BlockfrostClient(
        api_key=BLOCKFROST_API_KEY,
        network=CARDANO_NETWORK,
    )
    print(f"✅ Blockfrost client initialized: {CARDANO_NETWORK}")
else:
    print("⚠️  Warning: BLOCKFROST_API_KEY not set, duplicate detection disabled")

app = FastAPI(
    title="Biometric DID API (Basic)",
    description="Deterministic biometric DID generation and verification",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3003",
        "http://localhost:3000",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_blockfrost_client() -> None:
    if blockfrost_client:
        await blockfrost_client.close()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FingerData(BaseModel):
    finger_id: str = Field(...,
                           description="Finger identifier (e.g., 'left_thumb')")
    minutiae: List[List[float]] = Field(
        ..., description="List of minutiae points [x, y, angle]"
    )


class GenerateRequest(BaseModel):
    fingers: List[FingerData] = Field(...,
                                      description="List of fingerprint data")
    wallet_address: str = Field(..., description="Cardano wallet address")
    storage: str = Field(
        default="inline", description="Helper data storage method")
    format: str = Field(default="json", description="Output format")


class HelperDataEntry(BaseModel):
    finger_id: str
    salt_b64: str
    auth_b64: str
    grid_size: float
    angle_bins: int


class CIP30MetadataInline(BaseModel):
    version: str
    walletAddress: str
    controllers: List[str]
    enrollmentTimestamp: str
    biometric: Dict[str, Any]
    revoked: bool = False
    revokedAt: Optional[str] = None


class GenerateResponse(BaseModel):
    did: str
    id_hash: str
    wallet_address: str
    helpers: Dict[str, HelperDataEntry]
    metadata_cip30_inline: CIP30MetadataInline


class VerifyRequest(BaseModel):
    fingers: List[FingerData] = Field(...,
                                      description="Fingerprints to verify")
    helpers: Dict[str, HelperDataEntry] = Field(
        ..., description="Helper data from enrollment"
    )
    expected_id_hash: str = Field(...,
                                  description="Expected helper hash to match")


class VerifyResponse(BaseModel):
    success: bool
    matched_fingers: List[str]
    unmatched_fingers: List[str]
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _encode_b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _deterministic_bytes(label: str, finger_id: str, length: int) -> bytes:
    hasher = hashlib.blake2b(digest_size=length)
    hasher.update(label.encode("utf-8"))
    hasher.update(b":")
    hasher.update(finger_id.encode("utf-8"))
    return hasher.digest()


def generate_helper_entry(finger_id: str) -> HelperDataEntry:
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
    helpers: Dict[str, HelperDataEntry],
    wallet_address: Optional[str] = None,
) -> str:
    hash_ctx = hashlib.blake2b(digest_size=32)
    if wallet_address:
        hash_ctx.update(wallet_address.encode("utf-8"))
    for finger_id in sorted(helpers.keys()):
        entry = helpers[finger_id]
        hash_ctx.update(finger_id.encode("utf-8"))
        hash_ctx.update(entry.salt_b64.encode("utf-8"))
        hash_ctx.update(entry.auth_b64.encode("utf-8"))
    return _encode_b64(hash_ctx.digest())


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "biometric-did-api-basic",
        "version": app.version,
    }


@app.get("/metrics/blockfrost")
async def blockfrost_metrics() -> Dict[str, Any]:
    """Expose Blockfrost client performance counters for monitoring."""

    if not blockfrost_client:
        raise HTTPException(
            status_code=503,
            detail="Blockfrost client not configured",
        )

    snapshot = blockfrost_client.metrics_snapshot()

    return {
        "network": CARDANO_NETWORK,
        "cache_enabled": bool(blockfrost_client.cache),
        "timeout_seconds": blockfrost_client.timeout,
        "max_retries": blockfrost_client.max_retries,
        "metrics": snapshot,
    }


@app.post("/api/biometric/generate", response_model=GenerateResponse)
async def generate_did(request: GenerateRequest) -> GenerateResponse:
    try:
        if not request.fingers:
            raise HTTPException(
                status_code=400,
                detail="Biometric enrollment requires at least one finger template",
            )

        commitment_material = request.wallet_address.encode("utf-8")
        for finger in request.fingers:
            commitment_material += finger.finger_id.encode("utf-8")
            commitment_material += json.dumps(
                finger.minutiae,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")

        commitment = hashlib.sha256(commitment_material).digest()
        network = CARDANO_NETWORK or "testnet"
        did = generate_deterministic_did(commitment, network=network)

        if blockfrost_client:
            try:
                existing = await blockfrost_client.check_did_exists(did)
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
                            "suggestion": "If you control this identity, add a new controller wallet instead of re-enrolling",
                            "how_to": "Use the add-controller endpoint with your new wallet address",
                        },
                    )
            except DIDAlreadyExistsError as exc:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "DID_ALREADY_EXISTS",
                        "message": str(exc),
                        "did": exc.did,
                        "tx_hash": exc.tx_hash,
                        "enrollment_data": exc.enrollment_data,
                    },
                ) from exc
            except Exception as exc:  # pragma: no cover
                print(f"⚠️  Warning: Duplicate check failed: {exc}")
                print("   Continuing with enrollment (duplicate check skipped)")

        helpers: Dict[str, HelperDataEntry] = {
            finger.finger_id: generate_helper_entry(finger.finger_id)
            for finger in request.fingers
        }

        id_hash = compute_helper_hash(helpers)
        enrollment_timestamp = datetime.now(timezone.utc).isoformat()
        helpers_payload = (
            {finger_id: entry.dict() for finger_id, entry in helpers.items()}
            if request.storage == "inline"
            else None
        )

        metadata = CIP30MetadataInline(
            version="1.1",
            walletAddress=request.wallet_address,
            controllers=[request.wallet_address],
            enrollmentTimestamp=enrollment_timestamp,
            biometric={
                "idHash": id_hash,
                "helperStorage": request.storage,
                "helperData": helpers_payload,
            },
            revoked=False,
            revokedAt=None,
        )

        return GenerateResponse(
            did=str(did),
            id_hash=id_hash,
            wallet_address=request.wallet_address,
            helpers=helpers,
            metadata_cip30_inline=metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Biometric DID generation failed: {exc}",
        ) from exc


@app.post("/api/biometric/verify", response_model=VerifyResponse)
async def verify_did(request: VerifyRequest) -> VerifyResponse:
    try:
        if not request.helpers:
            raise HTTPException(
                status_code=400,
                detail="Verification requires helper data from enrollment",
            )

        matched_fingers = [
            finger.finger_id
            for finger in request.fingers
            if finger.finger_id in request.helpers
        ]
        unmatched_fingers = [
            finger.finger_id
            for finger in request.fingers
            if finger.finger_id not in request.helpers
        ]

        computed_hash = compute_helper_hash(request.helpers)
        hash_matches = computed_hash == request.expected_id_hash

        required_matches = min(2, len(request.helpers)) or 1
        success = hash_matches and len(matched_fingers) >= required_matches

        error_message: Optional[str] = None
        if not hash_matches:
            error_message = "Helper data hash mismatch"
        elif not success:
            error_message = "Insufficient matching fingerprints"

        return VerifyResponse(
            success=success,
            matched_fingers=matched_fingers,
            unmatched_fingers=unmatched_fingers,
            error=error_message,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Biometric verification failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Development server entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
