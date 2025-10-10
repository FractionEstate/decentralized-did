import json
import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample_fingerprints.json"
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
PYTHONPATH = str(SRC_DIR)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "decentralized_did.cli", *args]
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = PYTHONPATH if not existing else f"{PYTHONPATH}:{existing}"
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_cli_generate_inline_metadata(tmp_path):
    metadata_path = tmp_path / "metadata.json"
    result = run_cli(
        "generate",
        "--input",
        str(SAMPLE),
        "--output",
        str(metadata_path),
        "--quiet",
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload = next(iter(data.values()))
    biometric = payload["biometric"]
    assert biometric["helperStorage"] == "inline"
    assert "helperData" in biometric and biometric["helperData"]


def test_cli_external_helpers_flow(tmp_path):
    metadata_path = tmp_path / "metadata_external.json"
    helpers_path = tmp_path / "helpers.json"

    result = run_cli(
        "generate",
        "--input",
        str(SAMPLE),
        "--output",
        str(metadata_path),
        "--exclude-helpers",
        "--helpers-output",
        str(helpers_path),
        "--helper-uri",
        "ipfs://cid-demo",
        "--quiet",
    )
    assert result.returncode == 0, result.stderr

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload = next(iter(data.values()))
    biometric = payload["biometric"]
    assert biometric["helperStorage"] == "external"
    assert biometric["helperUri"] == "ipfs://cid-demo"
    assert "helperData" not in biometric

    fail = run_cli(
        "verify",
        "--metadata",
        str(metadata_path),
        "--input",
        str(SAMPLE),
    )
    assert fail.returncode != 0
    assert "helper data missing" in (fail.stderr.lower() or fail.stdout.lower())

    success = run_cli(
        "verify",
        "--metadata",
        str(metadata_path),
        "--input",
        str(SAMPLE),
        "--helpers",
        str(helpers_path),
        "--quiet",
    )
    assert success.returncode == 0, success.stderr


def test_cli_generate_cip30_metadata(tmp_path):
    metadata_path = tmp_path / "metadata_cip30.json"
    result = run_cli(
        "generate",
        "--input",
        str(SAMPLE),
        "--output",
        str(metadata_path),
        "--format",
        "cip30",
        "--quiet",
    )
    assert result.returncode == 0, result.stderr

    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert "metadata" in data
    entry_label, entry_payload = data["metadata"][0]
    assert entry_label == 1990
    biometric = entry_payload["biometric"]
    assert biometric["helperStorage"] == "inline"

    verify = run_cli(
        "verify",
        "--metadata",
        str(metadata_path),
        "--input",
        str(SAMPLE),
        "--quiet",
    )
    assert verify.returncode == 0, verify.stderr


def test_cli_demo_kit(tmp_path):
    output_dir = tmp_path / "kit"
    zip_path = tmp_path / "kit.zip"
    result = run_cli(
        "demo-kit",
        "--input",
        str(SAMPLE),
        "--output-dir",
        str(output_dir),
        "--wallet",
        "addr_test1demo123",
        "--zip",
        str(zip_path),
        "--quiet",
    )
    assert result.returncode == 0, result.stderr

    expected_files = {
        "metadata_wallet_inline.json",
        "metadata_cip30_inline.json",
        "metadata_wallet_external.json",
        "metadata_cip30_external.json",
        "helpers.json",
        "demo_summary.txt",
        "cip30_payload.ts",
    }

    on_disk = {path.name for path in output_dir.iterdir() if path.is_file()}
    assert expected_files.issubset(on_disk)

    summary_text = (output_dir / "demo_summary.txt").read_text(encoding="utf-8")
    assert "DID:" in summary_text
    assert "Demo kit generated" in summary_text

    ts_text = (output_dir / "cip30_payload.ts").read_text(encoding="utf-8")
    assert "export const cip30MetadataEntries" in ts_text
    assert "export const cip30MetadataMap" in ts_text
    assert "export const helperData" in ts_text

    assert zip_path.exists()
    with ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())
        assert expected_files.issubset(names)
