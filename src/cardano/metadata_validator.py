"""Validation helpers for biometric Cardano metadata payloads."""
from __future__ import annotations

from typing import Any, Dict

from jsonschema import Draft202012Validator, ValidationError

METADATA_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "minProperties": 1,
    "patternProperties": {
        "^\\d+$": {
            "type": "object",
            "required": ["version", "walletAddress", "biometric"],
            "properties": {
                "version": {"type": "integer", "minimum": 1},
                "walletAddress": {"type": "string", "minLength": 1},
                "biometric": {
                    "type": "object",
                    "required": ["idHash", "helperStorage"],
                    "properties": {
                        "idHash": {"type": "string", "minLength": 10},
                        "helperStorage": {
                            "type": "string",
                            "enum": ["inline", "external"],
                        },
                        "helperUri": {"type": "string", "minLength": 1},
                        "helperData": {
                            "type": "object",
                            "minProperties": 1,
                            "additionalProperties": {
                                "type": "object",
                                "required": [
                                    "finger_id",
                                    "salt_b64",
                                    "auth_b64",
                                    "grid_size",
                                    "angle_bins",
                                ],
                                "properties": {
                                    "finger_id": {"type": "string", "minLength": 1},
                                    "salt_b64": {"type": "string", "minLength": 8},
                                    "auth_b64": {"type": "string", "minLength": 8},
                                    "grid_size": {"type": "number", "exclusiveMinimum": 0},
                                    "angle_bins": {"type": "integer", "minimum": 1},
                                },
                                "additionalProperties": False,
                            },
                        },
                    },
                    "additionalProperties": False,
                    "allOf": [
                        {
                            "if": {
                                "properties": {"helperStorage": {"const": "inline"}},
                                "required": ["helperStorage"],
                            },
                            "then": {"required": ["helperData"]},
                        },
                        {
                            "if": {
                                "properties": {"helperStorage": {"const": "external"}},
                                "required": ["helperStorage"],
                            },
                            "then": {
                                "not": {
                                    "required": ["helperData"],
                                }
                            },
                        },
                    ],
                },
            },
            "additionalProperties": False,
        }
    },
    "additionalProperties": False,
}

_validator = Draft202012Validator(METADATA_SCHEMA)


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """Validate metadata payload. Raises ValidationError on failure."""
    _validator.validate(metadata)


__all__ = ["ValidationError", "validate_metadata", "METADATA_SCHEMA"]
