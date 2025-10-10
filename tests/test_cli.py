import json
import os
import subprocess
import sys
from pathlib import Path

SAMPLE = Path(__file__).resolve(
).parents[1] / "examples" / "sample_fingerprints.json"
ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    cmd = [sys.executable, "-m", "src.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_cli_generate_and_validate_inline(tmp_path):
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

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    biometric = next(iter(payload.values()))["biometric"]
    assert biometric["helperStorage"] == "inline"
    assert "helperData" in biometric

    validate = run_cli("validate", "--metadata", str(metadata_path), "--quiet")
    assert validate.returncode == 0, validate.stderr


def test_cli_external_helpers_requires_helpers_for_verify(tmp_path):
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

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    biometric = next(iter(payload.values()))["biometric"]
    assert biometric["helperStorage"] == "external"
    assert biometric["helperUri"] == "ipfs://cid-demo"
    assert "helperData" not in biometric

    # Verification without helpers should fail.
    fail = run_cli(
        "verify",
        "--metadata",
        str(metadata_path),
        "--input",
        str(SAMPLE),
    )
    assert fail.returncode != 0
    assert "helper data missing" in (
        fail.stderr.lower() or fail.stdout.lower())

    # Provide helpers to succeed.
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

    validate = run_cli("validate", "--metadata", str(metadata_path), "--quiet")
    assert validate.returncode == 0, validate.stderr
