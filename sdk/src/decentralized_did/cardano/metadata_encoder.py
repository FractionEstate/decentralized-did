"""Helpers to format biometric DID payloads for Cardano metadata."""
from __future__ import annotations

from typing import Dict, Any


DEFAULT_METADATA_LABEL = 1990


def to_wallet_metadata(payload: Dict[str, Any], label: int = DEFAULT_METADATA_LABEL) -> Dict[str, Any]:
    """Wrap payload into a Cardano transaction metadata dictionary."""
    return {str(label): payload}


def pretty_print_metadata(payload: Dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True)
