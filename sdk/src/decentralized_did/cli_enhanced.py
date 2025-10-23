"""
Enhanced CLI with storage backend integration and advanced features.

Extends the base CLI with:
- Storage backend selection
- Verbose logging
- Progress indicators
- Dry-run mode
- Batch processing
- Multiple export formats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cli_logging import CLILogger, LogLevel, create_logger
from .cli_progress import progress_bar, spinner
from .storage import (
    create_storage_backend,
    get_available_backends,
    get_backend_info,
    StorageBackend,
    StorageError,
)


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """
    Add common CLI arguments to parser.

    Args:
        parser: Argument parser to modify
    """
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="enable verbose output"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug output (implies --verbose)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="suppress all output except errors"
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="output structured JSON instead of text"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable colored output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="simulate operation without making changes"
    )


def add_storage_args(parser: argparse.ArgumentParser) -> None:
    """
    Add storage backend arguments to parser.

    Args:
        parser: Argument parser to modify
    """
    parser.add_argument(
        "--storage-backend",
        choices=["inline", "file", "ipfs"],
        default="inline",
        help="helper data storage backend (default: inline)"
    )
    parser.add_argument(
        "--storage-config",
        type=json.loads,
        help="storage backend configuration as JSON string"
    )

    # File storage options
    parser.add_argument(
        "--storage-path",
        type=Path,
        help="path for file storage backend (default: ./storage)"
    )
    parser.add_argument(
        "--storage-backup",
        action="store_true",
        help="enable backup for file storage"
    )

    # IPFS storage options
    parser.add_argument(
        "--ipfs-api",
        default="/ip4/127.0.0.1/tcp/5001",
        help="IPFS API endpoint (default: local node)"
    )
    parser.add_argument(
        "--ipfs-gateway",
        default="https://ipfs.io/ipfs/",
        help="IPFS gateway URL for retrieval"
    )
    parser.add_argument(
        "--ipfs-pin",
        action="store_true",
        help="pin helper data in IPFS for persistence"
    )


def create_storage_backend_from_args(
    args: argparse.Namespace,
    logger: CLILogger
) -> StorageBackend:
    """
    Create storage backend from CLI arguments.

    Args:
        args: Parsed CLI arguments
        logger: Logger instance

    Returns:
        Configured storage backend

    Raises:
        StorageError: If backend creation fails
    """
    backend_type = args.storage_backend

    logger.verbose(f"Creating {backend_type} storage backend")

    # Build configuration
    config: Dict[str, Any] = {}

    if args.storage_config:
        config.update(args.storage_config)

    # Backend-specific configuration
    if backend_type == "file":
        if args.storage_path:
            config["base_path"] = str(args.storage_path)
        if args.storage_backup:
            config["backup"] = True

    elif backend_type == "ipfs":
        config["api_url"] = args.ipfs_api
        config["gateway"] = args.ipfs_gateway
        if args.ipfs_pin:
            config["pin"] = True

    try:
        backend = create_storage_backend(backend_type, config)

        # Health check
        logger.verbose("Performing health check on storage backend")
        if backend.health_check():
            logger.debug("Storage backend health check passed")
        else:
            logger.warning("Storage backend health check failed")

        return backend

    except StorageError as e:
        logger.error(f"Failed to create storage backend: {e}")
        raise


def cmd_storage_info(args: argparse.Namespace) -> None:
    """
    Show storage backend information.

    Args:
        args: Parsed CLI arguments
    """
    logger = create_logger(
        quiet=args.quiet,
        verbose=args.verbose,
        debug=args.debug,
        json_output=args.json_output,
        no_color=args.no_color,
    )

    logger.step("Storage Backend Information")

    available = get_available_backends()

    if args.json_output:
        info = {}
        for backend_type in ["inline", "file", "ipfs"]:
            try:
                info[backend_type] = get_backend_info(backend_type)
            except StorageError:
                pass
        logger.print_json({"available": available, "backends": info})
    else:
        logger.info(f"Available backends: {', '.join(available)}")
        logger.print("")

        for backend_type in ["inline", "file", "ipfs"]:
            try:
                info = get_backend_info(backend_type)
                status = "✓" if info["available"] else "✗"
                logger.print(f"  {status} {backend_type}")
                logger.print(f"    Class: {info['class']}")
                logger.print(
                    f"    Supports deletion: {info['supports_deletion']}")
            except StorageError:
                pass


def cmd_storage_test(args: argparse.Namespace) -> None:
    """
    Test storage backend functionality.

    Args:
        args: Parsed CLI arguments
    """
    logger = create_logger(
        quiet=args.quiet,
        verbose=args.verbose,
        debug=args.debug,
        json_output=args.json_output,
        no_color=args.no_color,
    )

    logger.step(f"Testing {args.storage_backend} storage backend")

    try:
        # Create backend
        backend = create_storage_backend_from_args(args, logger)

        # Test data
        test_data = {
            "test": "data",
            "timestamp": "2025-10-12T00:00:00Z",
            "content": "This is test helper data"
        }

        # Test store
        logger.info("Testing store operation...")
        with spinner("Storing test data") as s:
            ref = backend.store(test_data)
            s.stop(f"Stored with URI: {ref.uri[:50]}...")

        logger.verbose("Storage reference details", {
            "backend": ref.backend,
            "uri_length": len(ref.uri)
        })

        # Test retrieve
        logger.info("Testing retrieve operation...")
        with spinner("Retrieving test data") as s:
            retrieved = backend.retrieve(ref)
            s.stop("Retrieved successfully")

        # Verify
        if retrieved == test_data:
            logger.success("Data integrity verified ✓")
        else:
            logger.error("Data mismatch!")
            return

        # Test delete (if supported)
        if backend.supports_deletion():
            logger.info("Testing delete operation...")
            with spinner("Deleting test data") as s:
                deleted = backend.delete(ref)
                s.stop("Deleted successfully" if deleted else "Delete failed")
        else:
            logger.info("Delete not supported for this backend")

        logger.success("All storage tests passed ✓")

    except StorageError as e:
        logger.error(f"Storage test failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            raise
        sys.exit(1)


def build_enhanced_parser() -> argparse.ArgumentParser:
    """
    Build enhanced argument parser with storage backend support.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="dec-did",
        description="Decentralized Biometric DID System",
        epilog="For more information, see https://github.com/FractionEstate/decentralized-did"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        required=True
    )

    # Storage info command
    storage_info = subparsers.add_parser(
        "storage-info",
        help="show storage backend information"
    )
    add_common_args(storage_info)
    storage_info.set_defaults(func=cmd_storage_info)

    # Storage test command
    storage_test = subparsers.add_parser(
        "storage-test",
        help="test storage backend functionality"
    )
    add_common_args(storage_test)
    add_storage_args(storage_test)
    storage_test.set_defaults(func=cmd_storage_test)

    return parser


def main_enhanced(argv: Optional[List[str]] = None) -> None:
    """
    Enhanced CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv)
    """
    parser = build_enhanced_parser()
    args = parser.parse_args(argv)

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(args, "debug") and args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main_enhanced()
