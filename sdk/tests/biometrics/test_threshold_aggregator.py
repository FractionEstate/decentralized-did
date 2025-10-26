"""Tests for threshold-based aggregation."""
from __future__ import annotations

import os
import pytest

from src.biometrics.aggregator_v2 import FingerKey, AggregationError, InsufficientFingersError
from src.biometrics.threshold_aggregator import (
    ThresholdShare,
    create_threshold_enrollment,
    recover_threshold_master_key,
)


@pytest.fixture
def ten_fingers() -> list[FingerKey]:
    finger_ids = [
        "left_thumb",
        "left_index",
        "left_middle",
        "left_ring",
        "left_pinky",
        "right_thumb",
        "right_index",
        "right_middle",
        "right_ring",
        "right_pinky",
    ]
    return [
        FingerKey(finger_id=fid, key=os.urandom(32), quality=85)
        for fid in finger_ids
    ]


def test_threshold_enrollment_and_recovery(ten_fingers: list[FingerKey]) -> None:
    enrollment = create_threshold_enrollment(ten_fingers, threshold=4)
    assert enrollment.threshold == 4
    assert enrollment.total_shares == len(ten_fingers)
    assert len(enrollment.shares) == len(ten_fingers)

    share_lookup = {share.finger_id: share for share in enrollment.shares}
    chosen = [ten_fingers[i] for i in (0, 3, 6, 9)]

    result = recover_threshold_master_key(
        chosen,
        share_lookup,
        threshold=enrollment.threshold,
        total_shares=enrollment.total_shares,
    )

    assert result.master_key == enrollment.master_key
    assert result.fallback_mode is True
    assert result.fingers_used == 4


def test_threshold_requires_unique_fingers(ten_fingers: list[FingerKey]) -> None:
    enrollment = create_threshold_enrollment(ten_fingers, threshold=4)
    share_lookup = {share.finger_id: share for share in enrollment.shares}

    duplicate = [ten_fingers[0], ten_fingers[0], ten_fingers[2], ten_fingers[3]]

    with pytest.raises(AggregationError):
        recover_threshold_master_key(
            duplicate,
            share_lookup,
            threshold=enrollment.threshold,
            total_shares=enrollment.total_shares,
        )


def test_missing_share_raises(ten_fingers: list[FingerKey]) -> None:
    enrollment = create_threshold_enrollment(ten_fingers, threshold=4)
    share_lookup = {share.finger_id: share for share in enrollment.shares}
    share_lookup.pop(ten_fingers[0].finger_id)

    chosen = [ten_fingers[i] for i in (0, 1, 3, 4)]

    with pytest.raises(AggregationError):
        recover_threshold_master_key(
            chosen,
            share_lookup,
            threshold=enrollment.threshold,
            total_shares=enrollment.total_shares,
        )


def test_threshold_enrollment_validates_parameters(ten_fingers: list[FingerKey]) -> None:
    with pytest.raises(InsufficientFingersError):
        create_threshold_enrollment([], threshold=4)

    subset = ten_fingers[:3]
    with pytest.raises(ValueError):
        create_threshold_enrollment(subset, threshold=4)

    with pytest.raises(ValueError):
        create_threshold_enrollment(ten_fingers, threshold=0)


def test_recover_requires_threshold_fingers(ten_fingers: list[FingerKey]) -> None:
    enrollment = create_threshold_enrollment(ten_fingers, threshold=4)
    share_lookup = {share.finger_id: share for share in enrollment.shares}

    insufficient = [ten_fingers[i] for i in (0, 1, 2)]

    with pytest.raises(InsufficientFingersError):
        recover_threshold_master_key(
            insufficient,
            share_lookup,
            threshold=enrollment.threshold,
        )


def test_masked_share_construction(ten_fingers: list[FingerKey]) -> None:
    enrollment = create_threshold_enrollment(ten_fingers, threshold=4)
    for share in enrollment.shares:
        assert isinstance(share, ThresholdShare)
        assert share.share_index > 0
        assert len(share.masked_share) == 32
        # Ensure masked share differs from original key in most cases
        finger_key = next(fk for fk in ten_fingers if fk.finger_id == share.finger_id)
        assert share.masked_share != finger_key.key
