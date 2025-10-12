"""
Tests for enhanced CLI features.

Tests CLI logging, progress indicators, and storage backend integration.
"""

import io
import json
from unittest.mock import Mock, patch

import pytest

from decentralized_did.cli_logging import CLILogger, LogLevel, create_logger
from decentralized_did.cli_progress import ProgressBar, Spinner
from decentralized_did.cli_enhanced import (
    add_common_args,
    add_storage_args,
    create_storage_backend_from_args,
    build_enhanced_parser,
)


# CLI Logging Tests

def test_cli_logger_creation():
    """Test CLI logger creation with different levels."""
    logger = CLILogger(level=LogLevel.NORMAL)
    assert logger.level == LogLevel.NORMAL
    assert logger.use_color is False  # Not a tty in tests


def test_cli_logger_levels():
    """Test CLI logger respects log levels."""
    output = io.StringIO()
    error_output = io.StringIO()

    # Quiet mode - only errors
    logger = CLILogger(
        level=LogLevel.QUIET,
        output=output,
        error_output=error_output,
        use_color=False
    )
    logger.info("Should not appear")
    logger.error("Should appear")

    output.seek(0)
    assert "Should not appear" not in output.read()

    error_output.seek(0)
    assert "Should appear" in error_output.read()


def test_cli_logger_json_mode():
    """Test CLI logger JSON output mode."""
    output = io.StringIO()
    logger = CLILogger(
        level=LogLevel.NORMAL,
        json_mode=True,
        output=output,
        use_color=False
    )

    logger.info("Test message", {"key": "value"})
    output.seek(0)
    data = json.loads(output.read())

    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["data"]["key"] == "value"


def test_cli_logger_colorize():
    """Test CLI logger colorization."""
    # Force color mode by creating logger with use_color=True
    # Color is disabled if output is not a tty, so we test the method directly
    logger = CLILogger(use_color=False)

    # Test with color disabled
    uncolored = logger._colorize("text", "red")
    assert uncolored == "text"

    # Test with color enabled
    logger.use_color = True
    colored = logger._colorize("text", "red")
    assert "\033[31m" in colored  # Red color code
    assert "\033[0m" in colored   # Reset code


def test_create_logger_from_flags():
    """Test logger creation from common CLI flags."""
    # Quiet mode
    logger = create_logger(quiet=True)
    assert logger.level == LogLevel.QUIET

    # Verbose mode
    logger = create_logger(verbose=True)
    assert logger.level == LogLevel.VERBOSE

    # Debug mode
    logger = create_logger(debug=True)
    assert logger.level == LogLevel.DEBUG

    # JSON mode
    logger = create_logger(json_output=True)
    assert logger.json_mode is True


def test_cli_logger_elapsed():
    """Test CLI logger elapsed time tracking."""
    import time

    logger = CLILogger()
    time.sleep(0.1)

    elapsed = logger.elapsed()
    assert elapsed >= 0.1


# Progress Indicator Tests

def test_progress_bar_creation():
    """Test progress bar creation."""
    output = io.StringIO()
    bar = ProgressBar(total=100, output=output)

    assert bar.total == 100
    assert bar.current == 0


def test_progress_bar_update():
    """Test progress bar update."""
    output = io.StringIO()
    bar = ProgressBar(total=100, output=output)

    bar.update(10)
    assert bar.current == 10

    bar.update(20)
    assert bar.current == 30


def test_progress_bar_finish():
    """Test progress bar finish."""
    output = io.StringIO()
    bar = ProgressBar(total=100, output=output)

    bar.update(50)
    bar.finish("Done")

    assert bar.current == 100


def test_progress_bar_elapsed():
    """Test progress bar elapsed time."""
    import time

    output = io.StringIO()
    bar = ProgressBar(total=100, output=output)

    time.sleep(0.1)
    elapsed = bar.elapsed()

    assert elapsed >= 0.1


def test_spinner_creation():
    """Test spinner creation."""
    output = io.StringIO()
    spinner = Spinner(message="Loading", output=output)

    assert spinner.message == "Loading"
    assert spinner.frame == 0


def test_spinner_start_stop():
    """Test spinner start and stop."""
    output = io.StringIO()
    spinner = Spinner(output=output)

    spinner.start()
    assert spinner._active is False  # Not a tty

    spinner.stop("Complete")
    assert spinner._active is False


def test_spinner_update():
    """Test spinner update."""
    output = io.StringIO()
    spinner = Spinner(output=output)

    spinner.update("New message")
    assert spinner.message == "New message"


def test_spinner_elapsed():
    """Test spinner elapsed time."""
    import time

    output = io.StringIO()
    spinner = Spinner(output=output)

    time.sleep(0.1)
    elapsed = spinner.elapsed()

    assert elapsed >= 0.1


# Enhanced CLI Tests

def test_add_common_args():
    """Test adding common CLI arguments."""
    import argparse

    parser = argparse.ArgumentParser()
    add_common_args(parser)

    # Test parsing
    args = parser.parse_args(["--verbose", "--dry-run"])
    assert args.verbose is True
    assert args.dry_run is True

    args = parser.parse_args(["--quiet", "--json-output"])
    assert args.quiet is True
    assert args.json_output is True


def test_add_storage_args():
    """Test adding storage backend arguments."""
    import argparse

    parser = argparse.ArgumentParser()
    add_storage_args(parser)

    # Test parsing
    args = parser.parse_args(["--storage-backend", "file"])
    assert args.storage_backend == "file"

    args = parser.parse_args([
        "--storage-backend", "ipfs",
        "--ipfs-pin",
        "--ipfs-api", "/ip4/127.0.0.1/tcp/5001"
    ])
    assert args.storage_backend == "ipfs"
    assert args.ipfs_pin is True
    assert args.ipfs_api == "/ip4/127.0.0.1/tcp/5001"


def test_create_storage_backend_from_args_inline():
    """Test creating inline storage backend from args."""
    import argparse

    args = argparse.Namespace(
        storage_backend="inline",
        storage_config=None,
        storage_path=None,
        storage_backup=False,
        ipfs_api="/ip4/127.0.0.1/tcp/5001",
        ipfs_gateway="https://ipfs.io/ipfs/",
        ipfs_pin=False,
        verbose=False,
        debug=False,
    )

    logger = create_logger()
    backend = create_storage_backend_from_args(args, logger)

    assert backend.get_backend_type() == "inline"


def test_create_storage_backend_from_args_file():
    """Test creating file storage backend from args."""
    import argparse
    from pathlib import Path

    args = argparse.Namespace(
        storage_backend="file",
        storage_config=None,
        storage_path=Path("/tmp/test-storage"),
        storage_backup=True,
        ipfs_api="/ip4/127.0.0.1/tcp/5001",
        ipfs_gateway="https://ipfs.io/ipfs/",
        ipfs_pin=False,
        verbose=False,
        debug=False,
    )

    logger = create_logger()
    backend = create_storage_backend_from_args(args, logger)

    assert backend.get_backend_type() == "file"


def test_build_enhanced_parser():
    """Test building enhanced argument parser."""
    parser = build_enhanced_parser()

    # Test storage-info command
    args = parser.parse_args(["storage-info"])
    assert args.command == "storage-info"
    assert hasattr(args, "func")

    # Test storage-test command
    args = parser.parse_args([
        "storage-test",
        "--storage-backend", "file",
        "--verbose"
    ])
    assert args.command == "storage-test"
    assert args.storage_backend == "file"
    assert args.verbose is True


def test_enhanced_cli_dry_run_flag():
    """Test dry-run flag in enhanced CLI."""
    parser = build_enhanced_parser()

    args = parser.parse_args(["storage-test", "--dry-run"])
    assert args.dry_run is True


def test_enhanced_cli_json_output():
    """Test JSON output mode in enhanced CLI."""
    parser = build_enhanced_parser()

    args = parser.parse_args(["storage-info", "--json-output"])
    assert args.json_output is True


def test_enhanced_cli_storage_config_json():
    """Test storage config as JSON string."""
    parser = build_enhanced_parser()

    config_json = '{"max_size": 10000, "compress": true}'
    args = parser.parse_args([
        "storage-test",
        "--storage-config", config_json
    ])

    assert args.storage_config == {"max_size": 10000, "compress": True}


# Integration Tests

def test_storage_info_command():
    """Test storage-info command execution."""
    from decentralized_did.cli_enhanced import cmd_storage_info
    import argparse

    args = argparse.Namespace(
        quiet=False,
        verbose=False,
        debug=False,
        json_output=False,
        no_color=True,
    )

    # Should not raise
    cmd_storage_info(args)


def test_storage_test_command_inline():
    """Test storage-test command with inline backend."""
    from decentralized_did.cli_enhanced import cmd_storage_test
    import argparse

    args = argparse.Namespace(
        storage_backend="inline",
        storage_config=None,
        storage_path=None,
        storage_backup=False,
        ipfs_api="/ip4/127.0.0.1/tcp/5001",
        ipfs_gateway="https://ipfs.io/ipfs/",
        ipfs_pin=False,
        quiet=False,
        verbose=False,
        debug=False,
        json_output=False,
        no_color=True,
    )

    # Should not raise
    cmd_storage_test(args)


def test_storage_test_command_file(tmp_path):
    """Test storage-test command with file backend."""
    from decentralized_did.cli_enhanced import cmd_storage_test
    import argparse

    args = argparse.Namespace(
        storage_backend="file",
        storage_config=None,
        storage_path=tmp_path,
        storage_backup=False,
        ipfs_api="/ip4/127.0.0.1/tcp/5001",
        ipfs_gateway="https://ipfs.io/ipfs/",
        ipfs_pin=False,
        quiet=False,
        verbose=False,
        debug=False,
        json_output=False,
        no_color=True,
    )

    # Should not raise
    cmd_storage_test(args)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
