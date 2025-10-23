from decentralized_did.cardano.metadata_encoder import (
    DEFAULT_METADATA_LABEL,
    to_wallet_metadata,
)
from decentralized_did.did.generator import build_metadata_payload


def test_metadata_wrapper_uses_label():
    payload = {"version": 1, "walletAddress": "addr1", "biometric": {"idHash": "abc", "helperData": {}}}
    wrapped = to_wallet_metadata(payload)
    assert str(DEFAULT_METADATA_LABEL) in wrapped
    assert wrapped[str(DEFAULT_METADATA_LABEL)] == payload


def test_metadata_payload_defaults_inline():
    digest = b"\x00" * 32
    helper_map = {"left_thumb": {"finger_id": "left_thumb"}}
    payload = build_metadata_payload("addr1", digest, helper_map)
    biometric = payload["biometric"]
    assert biometric["helperStorage"] == "inline"
    assert biometric["helperData"] == helper_map
    assert biometric["idHash"]


def test_metadata_payload_external_reference():
    digest = b"\x01" * 32
    payload = build_metadata_payload(
        "addr1",
        digest,
        None,
        helper_storage="external",
        helper_uri="ipfs://example",
    )
    biometric = payload["biometric"]
    assert biometric["helperStorage"] == "external"
    assert biometric["helperUri"] == "ipfs://example"
    assert "helperData" not in biometric
