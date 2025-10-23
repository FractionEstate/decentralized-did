"""
Tests for CLI storage backend integration.

Tests the enroll and verify commands with various storage backends.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

SAMPLE = Path(__file__).resolve(
).parents[1] / "examples" / "sample_fingerprints.json"
ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run CLI command with proper Python path."""
    import os
    env = os.environ.copy()
    src_paths = [str(ROOT / "src"), str(ROOT)]
    existing = env.get("PYTHONPATH")
    if existing:
        src_paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(src_paths)
    cmd = [sys.executable, "-m", "decentralized_did.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_enroll_with_file_storage(tmp_path):
    """Test enrollment with file storage backend."""
    metadata_path = tmp_path / "metadata_file.json"
    storage_path = tmp_path / "storage"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
        "--verbose",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    assert metadata_path.exists()
    assert storage_path.exists()

    # Check metadata has external storage reference
    metadata = json.loads(metadata_path.read_text())
    biometric = next(iter(metadata.values()))["biometric"]
    assert biometric["helperStorage"] == "external"
    assert "helperUri" in biometric
    assert biometric["helperUri"].startswith(str(storage_path))
    assert "helperData" not in biometric


def test_verify_with_file_storage(tmp_path):
    """Test verification with file storage backend."""
    metadata_path = tmp_path / "metadata_file.json"
    storage_path = tmp_path / "storage"

    # First enroll
    enroll_result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
    )
    assert enroll_result.returncode == 0

    # Then verify
    verify_result = run_cli(
        "verify",
        "--metadata", str(metadata_path),
        "--input", str(SAMPLE),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
        "--verbose",
    )
    assert verify_result.returncode == 0
    assert "succeeded" in verify_result.stdout.lower()


def test_enroll_with_inline_storage(tmp_path):
    """Test enrollment with inline storage (backwards compatibility)."""
    metadata_path = tmp_path / "metadata_inline.json"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--verbose",
    )
    assert result.returncode == 0

    # Check metadata has inline helper data
    metadata = json.loads(metadata_path.read_text())
    biometric = next(iter(metadata.values()))["biometric"]
    assert biometric["helperStorage"] == "inline"
    assert "helperData" in biometric


def test_enroll_with_file_storage_and_backup(tmp_path):
    """Test enrollment with file storage and backup enabled."""
    metadata_path = tmp_path / "metadata_backup.json"
    storage_path = tmp_path / "storage"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
        "--storage-backup",
        "--verbose",
    )
    assert result.returncode == 0
    assert metadata_path.exists()


def test_enroll_dry_run_mode(tmp_path):
    """Test dry-run mode (no files written)."""
    metadata_path = tmp_path / "metadata_dryrun.json"
    storage_path = tmp_path / "storage"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
        "--dry-run",
        "--verbose",
    )
    assert result.returncode == 0
    assert "dry-run" in result.stdout.lower()
    assert not metadata_path.exists()
    assert not storage_path.exists()


def test_verify_dry_run_mode(tmp_path):
    """Test verify with dry-run mode."""
    metadata_path = tmp_path / "metadata_verify_dryrun.json"
    helpers_path = tmp_path / "helpers.json"

    # First enroll normally to get helpers
    enroll_result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--helpers-output", str(helpers_path),
    )
    assert enroll_result.returncode == 0

    # Verify with dry-run
    verify_result = run_cli(
        "verify",
        "--metadata", str(metadata_path),
        "--input", str(SAMPLE),
        "--dry-run",
        "--verbose",
    )
    assert verify_result.returncode == 0
    assert "dry-run" in verify_result.stdout.lower()


def test_enroll_json_output_mode(tmp_path):
    """Test JSON output mode."""
    metadata_path = tmp_path / "metadata_json.json"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--json-output",
    )
    assert result.returncode == 0

    # Check that output is valid JSON
    try:
        output_data = json.loads(result.stdout)
        assert "did" in output_data
        assert "helper_storage" in output_data
    except json.JSONDecodeError:
        pytest.fail("JSON output mode did not produce valid JSON")


def test_verify_json_output_mode(tmp_path):
    """Test verification with JSON output mode."""
    metadata_path = tmp_path / "metadata_verify_json.json"

    # Enroll
    enroll_result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
    )
    assert enroll_result.returncode == 0

    # Verify with JSON output
    verify_result = run_cli(
        "verify",
        "--metadata", str(metadata_path),
        "--input", str(SAMPLE),
        "--json-output",
    )
    assert verify_result.returncode == 0

    # Check JSON output
    try:
        output_data = json.loads(verify_result.stdout)
        assert output_data["result"] == "success"
        assert output_data["verified"] is True
    except json.JSONDecodeError:
        pytest.fail("JSON output mode did not produce valid JSON")


def test_enroll_with_storage_config_json(tmp_path):
    """Test enrollment with storage config as JSON string."""
    metadata_path = tmp_path / "metadata_config.json"
    storage_path = tmp_path / "custom_storage"

    storage_config = json.dumps(
        {"base_path": str(storage_path), "enable_backup": True})

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--storage-backend", "file",
        "--storage-config", storage_config,
        "--verbose",
    )
    assert result.returncode == 0
    assert storage_path.exists()


def test_verify_without_storage_fails(tmp_path):
    """Test that verification fails when helper data is missing."""
    metadata_path = tmp_path / "metadata_external.json"
    helpers_path = tmp_path / "helpers.json"

    # Enroll with external storage
    enroll_result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--exclude-helpers",
        "--helpers-output", str(helpers_path),
    )
    assert enroll_result.returncode == 0

    # Try to verify without providing helper data or storage backend
    verify_result = run_cli(
        "verify",
        "--metadata", str(metadata_path),
        "--input", str(SAMPLE),
    )
    assert verify_result.returncode != 0
    assert "helper data missing" in (
        verify_result.stderr + verify_result.stdout).lower()


def test_verbose_output_flag(tmp_path):
    """Test that verbose flag produces detailed output."""
    metadata_path = tmp_path / "metadata_verbose.json"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--verbose",
    )
    assert result.returncode == 0
    assert "Loading biometric input" in result.stdout
    assert "Computing enrollment" in result.stdout
    assert "Building metadata bundle" in result.stdout


def test_quiet_output_flag(tmp_path):
    """Test that quiet flag suppresses output."""
    metadata_path = tmp_path / "metadata_quiet.json"

    result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--quiet",
    )
    assert result.returncode == 0
    # Quiet mode should produce minimal output
    assert len(result.stdout.strip()
               ) == 0 or "did:" not in result.stdout.lower()


def test_enroll_verify_roundtrip_with_storage(tmp_path):
    """Test complete enroll/verify roundtrip with file storage."""
    metadata_path = tmp_path / "metadata_roundtrip.json"
    storage_path = tmp_path / "storage"

    # Enroll
    enroll_result = run_cli(
        "generate",
        "--input", str(SAMPLE),
        "--output", str(metadata_path),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
    )
    assert enroll_result.returncode == 0

    # Verify
    verify_result = run_cli(
        "verify",
        "--metadata", str(metadata_path),
        "--input", str(SAMPLE),
        "--storage-backend", "file",
        "--storage-path", str(storage_path),
    )
    assert verify_result.returncode == 0
    assert "succeeded" in verify_result.stdout.lower()
