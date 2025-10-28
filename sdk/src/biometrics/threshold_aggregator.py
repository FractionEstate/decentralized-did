"""Threshold-based multi-finger aggregation utilities.

Implements k-of-n reconstruction over 32-byte master keys derived from
per-finger fuzzy extractor outputs. The construction combines deterministic
XOR aggregation (for entropy preservation) with Shamir secret sharing over
GF(2^8) to enable recovery with any subset of enrolled fingers that meets the
configured threshold.

This module keeps helper shares masked with the originating finger key so
that individual shares remain protected at rest. During verification, masked
shares are unmasked with the reproduced finger keys and interpolated to
recover the original master key.

Phase 4.5 – Tamper-Proof Identity Security
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import galois
import secrets

from .aggregator_v2 import (
    AggregationError,
    AggregationResult,
    FingerKey,
    InsufficientFingersError,
    QualityThresholdError,
    aggregate_xor,
)

GF256 = galois.GF(2 ** 8)


@dataclass
class ThresholdShare:
    """Masked share bound to an enrolled finger."""

    finger_id: str
    share_index: int
    masked_share: bytes  # XOR(master share, finger key)

    def __post_init__(self) -> None:
        if self.share_index <= 0:
            raise ValueError("share_index must be positive")
        if len(self.masked_share) != 32:
            raise ValueError(
                f"masked_share must be 32 bytes, got {len(self.masked_share)}"
            )


@dataclass
class ThresholdEnrollmentResult:
    """Result bundle for threshold enrollment."""

    master_key: bytes
    shares: List[ThresholdShare]
    threshold: int
    total_shares: int
    average_quality: Optional[float]


def _mask_share(share: bytes, finger_key: bytes) -> bytes:
    if len(share) != 32:
        raise ValueError(f"share must be 32 bytes, got {len(share)}")
    if len(finger_key) != 32:
        raise ValueError(
            f"finger_key must be 32 bytes, got {len(finger_key)}"
        )
    return bytes(a ^ b for a, b in zip(share, finger_key))


def _unmask_share(masked_share: bytes, finger_key: bytes) -> bytes:
    return _mask_share(masked_share, finger_key)


def _build_coefficient_matrix(secret: bytes, threshold: int) -> galois.FieldArray:
    """Construct coefficient matrix for Shamir polynomials per byte."""
    secret_vec = GF256(list(secret))
    coeffs = GF256.Zeros((threshold, len(secret)))
    coeffs[0, :] = secret_vec
    if threshold > 1:
        random_bytes = secrets.token_bytes((threshold - 1) * len(secret))
        coeffs[1:, :] = GF256(list(random_bytes)).reshape(threshold - 1, len(secret))
    return coeffs


def _evaluate_polynomial(coeffs: galois.FieldArray, x_value: int) -> bytes:
    x = GF256(x_value)
    result = coeffs[-1, :].copy()
    for row in reversed(range(len(coeffs) - 1)):
        result = result * x + coeffs[row, :]
    return bytes(int(part) for part in result)


def _lagrange_interpolate_at_zero(
    xs: Iterable[int],
    ys: Iterable[bytes],
) -> bytes:
    xs_list = list(xs)
    ys_list = list(ys)
    if not xs_list or not ys_list:
        raise ValueError("Shares required for interpolation")

    field_xs = GF256(xs_list)
    field_ys = [GF256(list(share)) for share in ys_list]

    secret = GF256.Zeros(len(field_ys[0]))
    for idx, xi in enumerate(field_xs):
        numerator = GF256(1)
        denominator = GF256(1)
        for jdx, xj in enumerate(field_xs):
            if idx == jdx:
                continue
            numerator *= xj  # In GF(2^m), -xj == xj
            denominator *= xi + xj  # subtraction == addition in characteristic 2
        if denominator == 0:
            raise AggregationError("Duplicate share indices detected")
        lambda_i = numerator / denominator
        secret += field_ys[idx] * lambda_i

    return bytes(int(part) for part in secret)


def create_threshold_enrollment(
    finger_keys: List[FingerKey],
    *,
    threshold: int = 4,
) -> ThresholdEnrollmentResult:
    """Create masked shares for threshold reconstruction.

    Args:
        finger_keys: Enrolled finger keys (each 32 bytes)
        threshold: Minimum fingers required to reconstruct master key

    Returns:
        ThresholdEnrollmentResult bundle with masked shares

    Raises:
        ValueError: If parameters invalid
    """
    total = len(finger_keys)
    if total == 0:
        raise InsufficientFingersError("No finger keys provided")
    if threshold < 2:
        raise ValueError("threshold must be at least 2")
    if total > 255:
        raise ValueError("total_shares cannot exceed 255")
    if threshold > total:
        raise ValueError(
            f"threshold {threshold} cannot exceed enrolled finger count {total}"
        )

    finger_ids = [fk.finger_id for fk in finger_keys]
    if len(set(finger_ids)) != len(finger_ids):
        raise AggregationError("Duplicate finger_id detected during enrollment")

    master_key = aggregate_xor([fk.key for fk in finger_keys])

    qualities = [fk.quality for fk in finger_keys if fk.quality is not None]
    average_quality = sum(qualities) / len(qualities) if qualities else None

    coeffs = _build_coefficient_matrix(master_key, threshold)

    shares: List[ThresholdShare] = []
    for idx, finger in enumerate(finger_keys, start=1):
        share_bytes = _evaluate_polynomial(coeffs, idx)
        masked = _mask_share(share_bytes, finger.key)
        shares.append(
            ThresholdShare(
                finger_id=finger.finger_id,
                share_index=idx,
                masked_share=masked,
            )
        )

    return ThresholdEnrollmentResult(
        master_key=master_key,
        shares=shares,
        threshold=threshold,
        total_shares=total,
        average_quality=average_quality,
    )


def recover_threshold_master_key(
    finger_keys: List[FingerKey],
    share_lookup: Dict[str, ThresholdShare],
    *,
    threshold: int,
    total_shares: Optional[int] = None,
    require_quality: Optional[float] = None,
) -> AggregationResult:
    """Reconstruct master key from subset of threshold shares.

    Args:
        finger_keys: Verified finger keys (subset of enrollment)
        share_lookup: Mapping of finger_id → ThresholdShare from enrollment
        threshold: Minimum number of fingers required for reconstruction
        total_shares: Total shares generated during enrollment (for metadata)
        require_quality: Optional minimum average quality gate

    Returns:
        AggregationResult containing reconstructed master key

    Raises:
        InsufficientFingersError: If fewer than threshold fingers supplied
        AggregationError: If share metadata missing or inconsistent
        QualityThresholdError: If average quality below requirement
    """
    if len(finger_keys) < threshold:
        raise InsufficientFingersError(
            f"Threshold reconstruction requires at least {threshold} fingers, "
            f"got {len(finger_keys)}"
        )

    finger_ids = [fk.finger_id for fk in finger_keys]
    if len(set(finger_ids)) != len(finger_ids):
        raise AggregationError("Duplicate finger_id detected during recovery")

    xs: List[int] = []
    ys: List[bytes] = []
    for finger in finger_keys:
        share = share_lookup.get(finger.finger_id)
        if share is None:
            raise AggregationError(
                f"Missing threshold share for finger '{finger.finger_id}'"
            )
        xs.append(share.share_index)
        ys.append(_unmask_share(share.masked_share, finger.key))

    qualities = [fk.quality for fk in finger_keys if fk.quality is not None]
    average_quality = sum(qualities) / len(qualities) if qualities else None

    if require_quality is not None and average_quality is not None:
        if average_quality < require_quality:
            raise QualityThresholdError(
                f"Average quality {average_quality:.1f} below {require_quality:.1f}"
            )

    master_key = _lagrange_interpolate_at_zero(xs, ys)

    fallback_mode = False
    if total_shares is not None and len(finger_keys) < total_shares:
        fallback_mode = True

    return AggregationResult(
        master_key=master_key,
        fingers_used=len(finger_keys),
        finger_ids=finger_ids,
        average_quality=average_quality,
        fallback_mode=fallback_mode,
    )


__all__ = [
    "ThresholdShare",
    "ThresholdEnrollmentResult",
    "create_threshold_enrollment",
    "recover_threshold_master_key",
]
