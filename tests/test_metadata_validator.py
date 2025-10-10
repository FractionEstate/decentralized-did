import json
from pathlib import Path

import pytest

from src.cardano.metadata_validator import ValidationError, validate_metadata

EXAMPLE = {
    "1990": {
        "version": 1,
        "walletAddress": "addr1example",
        "biometric": {
            "idHash": "abcd" * 8,
            "helperStorage": "inline",
            "helperData": {
                "left_thumb": {
                    "finger_id": "left_thumb",
                    "salt_b64": "aaaa",
                    "auth_b64": "bbbb",
                    "grid_size": 0.05,
                    "angle_bins": 32,
                }
            },
        },
    }
}


def test_validate_metadata_inline_passes():
    validate_metadata(EXAMPLE)


def test_validate_metadata_external_rules():
    payload = json.loads(json.dumps(EXAMPLE))
    biometric = payload["1990"]["biometric"]
    biometric.pop("helperData")
    biometric["helperStorage"] = "external"
    biometric["helperUri"] = "ipfs://cid"
    validate_metadata(payload)


def test_missing_helper_data_rejected():
    payload = json.loads(json.dumps(EXAMPLE))
    biometric = payload["1990"]["biometric"]
    biometric.pop("helperData")
    with pytest.raises(ValidationError):
        validate_metadata(payload)


def test_inline_with_extra_field_rejected():
    payload = json.loads(json.dumps(EXAMPLE))
    payload["1990"]["extra"] = 123
    with pytest.raises(ValidationError):
        validate_metadata(payload)


def test_helper_schema_checks_required_fields():
    payload = json.loads(json.dumps(EXAMPLE))
    helper = payload["1990"]["biometric"]["helperData"]["left_thumb"]
    helper.pop("salt_b64")
    with pytest.raises(ValidationError):
        validate_metadata(payload)
