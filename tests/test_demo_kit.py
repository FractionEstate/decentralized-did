import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample_fingerprints.json"
SRC_DIR = ROOT / "src"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(SRC_DIR) if not existing else f"{SRC_DIR}{os.pathsep}{existing}"
    )
    cmd = [sys.executable, "-m", "decentralized_did.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_demo_kit_outputs_artifacts(tmp_path: Path) -> None:
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
        "cip30_demo.ts",
    }

    on_disk = {path.name for path in output_dir.iterdir() if path.is_file()}
    assert expected_files.issubset(on_disk)

    ts_payload = (output_dir / "cip30_payload.ts").read_text(encoding="utf-8")
    assert "cip30MetadataEntries: [number, unknown][]" in ts_payload
    assert "cip30MetadataMap" in ts_payload
    assert "helperData" in ts_payload

    ts_demo = (output_dir / "cip30_demo.ts").read_text(encoding="utf-8")
    assert "attachBiometricMetadata" in ts_demo
    assert "buildBiometricMetadata" in ts_demo
    assert "experimental().tx.send" in ts_demo

    assert zip_path.exists()
    with ZipFile(zip_path, "r") as archive:
        names = set(archive.namelist())
        assert expected_files.issubset(names)
