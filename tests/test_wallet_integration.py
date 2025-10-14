from pathlib import Path

from decentralized_did.cardano.wallet_integration import build_wallet_metadata_bundle


def test_bundle_produces_both_formats(tmp_path):
    digest = b"\x01" * 32
    helper_map = {"left_thumb": {"finger_id": "left_thumb", "salt": "abc"}}
    bundle = build_wallet_metadata_bundle(
        "addr_test1qpl4w3u",
        digest,
        helper_map,
        label=2024,
    )

    wallet_metadata = bundle.as_wallet_metadata()
    assert "2024" in wallet_metadata
    payload = wallet_metadata["2024"]
    # v1.1 format uses controllers array
    assert payload["version"] == "1.1"
    assert payload["controllers"][0] == "addr_test1qpl4w3u"
    assert payload["biometric"]["helperData"] == helper_map

    cip30 = bundle.as_cip30_request()
    assert cip30["metadata"][0][0] == 2024
    # v1.1 format uses controllers array
    assert cip30["metadata"][0][1]["version"] == "1.1"
    assert cip30["metadata"][0][1]["controllers"][0] == "addr_test1qpl4w3u"

    pretty = bundle.to_json(fmt="wallet", pretty=True)
    assert "\n" in pretty
    bundle.write_json(tmp_path / "wallet.json", fmt="wallet")
    bundle.write_json(tmp_path / "cip30.json", fmt="cip30")

    cip30_loaded = (tmp_path / "cip30.json").read_text(encoding="utf-8")
    assert "metadata" in cip30_loaded


def test_bundle_external_helpers_sets_storage():
    digest = b"\x02" * 32
    bundle = build_wallet_metadata_bundle(
        "addr1qxyz",
        digest,
        None,
        helper_storage="external",
        helper_uri="ipfs://cid",
    )

    payload = bundle.as_wallet_metadata()["1990"]
    biometric = payload["biometric"]
    assert biometric["helperStorage"] == "external"
    assert biometric["helperUri"] == "ipfs://cid"
    assert "helperData" not in biometric
