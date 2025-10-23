"""Command-line interface for biometric DID enrollment and verification."""
from __future__ import annotations

import argparse
import base64
import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zipfile import ZipFile

from .biometrics.aggregator import aggregate_finger_digests, helpers_to_dict
from .biometrics.feature_extractor import FingerTemplate, minutiae_from_dicts
from .biometrics.fuzzy_extractor import FuzzyExtractor, HelperData
from .cardano.metadata_encoder import DEFAULT_METADATA_LABEL
from .cardano.wallet_integration import build_wallet_metadata_bundle
from .cli_logging import create_logger, CLILogger
from .cli_progress import spinner
from .storage import create_storage_backend, StorageBackend, StorageError


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SAMPLE_INPUT = REPO_ROOT / "examples" / "sample_fingerprints.json"


def _load_json(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _decode_digest(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode((encoded + padding).encode("ascii"))


def _build_templates(finger_payload: List[Dict[str, object]]) -> List[FingerTemplate]:
    templates: List[FingerTemplate] = []
    for entry in finger_payload:
        finger_id = str(entry["finger_id"])
        minutiae = minutiae_from_dicts(entry["minutiae"])
        grid_size = float(entry.get("grid_size", 0.05))
        angle_bins = int(entry.get("angle_bins", 32))
        templates.append(
            FingerTemplate(
                finger_id=finger_id,
                minutiae=minutiae,
                grid_size=grid_size,
                angle_bins=angle_bins,
            )
        )
    return templates


def _write_json(path: Path, data: object, pretty: bool = True) -> None:
    indent = 2 if pretty else None
    path.write_text(json.dumps(data, indent=indent), encoding="utf-8")


def _compute_enrollment(
    finger_payload: List[Dict[str, object]]
) -> Tuple[bytes, Dict[str, Dict[str, object]], List[HelperData]]:
    templates = _build_templates(finger_payload)
    extractor = FuzzyExtractor()
    digests: List[Tuple[str, bytes]] = []
    helpers: List[HelperData] = []
    for template in templates:
        digest, helper = extractor.generate(template)
        digests.append((template.finger_id, digest))
        helpers.append(helper)

    master_digest = aggregate_finger_digests(digests)
    helper_map = helpers_to_dict(helpers)
    return master_digest, helper_map, helpers


def _extract_metadata_payload(metadata: Dict[str, object]) -> Dict[str, object]:
    if not isinstance(metadata, dict):
        raise SystemExit("metadata JSON must be an object")

    cip30_entries = metadata.get(
        "metadata") if "metadata" in metadata else None
    if isinstance(cip30_entries, list):
        if not cip30_entries:
            raise SystemExit("metadata list is empty")
        first = cip30_entries[0]
        if isinstance(first, (list, tuple)) and len(first) == 2:
            payload = first[1]
        elif isinstance(first, dict) and "payload" in first:
            payload = first["payload"]
        else:
            raise SystemExit("unrecognized CIP-30 metadata structure")
        if not isinstance(payload, dict):
            raise SystemExit("metadata payload must be an object")
        return payload

    if metadata:
        payload = next(iter(metadata.values()))
        if not isinstance(payload, dict):
            raise SystemExit("metadata payload must be an object")
        return payload

    raise SystemExit("metadata JSON is empty")


def _create_storage_backend_from_args(args: argparse.Namespace, logger: Optional[CLILogger] = None, dry_run: bool = False) -> Optional[StorageBackend]:
    """Create storage backend from CLI arguments."""
    if not hasattr(args, 'storage_backend') or not args.storage_backend:
        return None

    # In dry-run mode, don't create actual storage backend
    if dry_run:
        if logger:
            logger.verbose(
                f"Dry-run: would create {args.storage_backend} storage backend")
        return None

    backend_type = args.storage_backend
    config = {}

    if backend_type == "file":
        if hasattr(args, 'storage_path') and args.storage_path:
            config["base_path"] = args.storage_path
        if hasattr(args, 'storage_backup') and args.storage_backup:
            config["enable_backup"] = True
    elif backend_type == "ipfs":
        if hasattr(args, 'ipfs_api') and args.ipfs_api:
            config["api_url"] = args.ipfs_api
        if hasattr(args, 'ipfs_gateway') and args.ipfs_gateway:
            config["gateway_url"] = args.ipfs_gateway
        if hasattr(args, 'ipfs_pin') and args.ipfs_pin:
            config["pin"] = True

    if hasattr(args, 'storage_config') and args.storage_config:
        try:
            extra_config = json.loads(args.storage_config)
            config.update(extra_config)
        except json.JSONDecodeError as e:
            if logger:
                logger.error(f"Invalid storage config JSON: {e}")
            raise SystemExit(f"Invalid storage config JSON: {e}")

    try:
        backend = create_storage_backend(backend_type, config)
        if logger:
            logger.verbose(f"Created {backend_type} storage backend", {
                           "config": config})
        return backend
    except Exception as e:
        if logger:
            logger.error(f"Failed to create storage backend: {e}")
        raise SystemExit(f"Failed to create storage backend: {e}")


def cmd_generate(args: argparse.Namespace) -> None:
    # In JSON output mode, suppress logging to avoid mixed output
    json_mode = getattr(args, 'json_output', False)
    logger = create_logger(
        quiet=args.quiet or json_mode,  # Treat JSON mode as quiet for logging
        verbose=getattr(args, 'verbose', False) and not json_mode,
        debug=getattr(args, 'debug', False) and not json_mode,
        json_output=False,  # Don't use logger's JSON mode
    )

    dry_run = getattr(args, 'dry_run', False)
    if dry_run:
        logger.info("Running in dry-run mode (no files will be written)")

    logger.step("Loading biometric input")
    input_payload = _load_json(Path(args.input))
    wallet_address = args.wallet or str(
        input_payload.get("wallet_address", "")).strip()
    if not wallet_address:
        raise SystemExit(
            "wallet address is required (via --wallet or input JSON)")

    logger.step("Computing enrollment")
    if logger.level.value > 0:
        with spinner("Extracting biometric features"):
            master_digest, helper_map, _ = _compute_enrollment(
                input_payload["fingers"])
    else:
        master_digest, helper_map, _ = _compute_enrollment(
            input_payload["fingers"])
    logger.success(f"Enrollment computed ({len(helper_map)} helper entries)")

    # Determine storage backend and helper URI
    storage_backend = _create_storage_backend_from_args(args, logger, dry_run)
    helper_uri = args.helper_uri
    helper_storage = "inline"
    metadata_helper_map = helper_map

    # Store helper data in storage backend if specified
    if storage_backend:
        logger.step("Storing helper data")
        try:
            if not dry_run:
                ref = storage_backend.store(helper_map)
                helper_uri = ref.uri
                logger.success(f"Helper data stored: {helper_uri}")
            else:
                logger.info(
                    "Dry-run: would store helper data to storage backend")
                helper_uri = f"{args.storage_backend}://dry-run-placeholder"
            helper_storage = "external"
            metadata_helper_map = None
        except StorageError as e:
            logger.error(f"Failed to store helper data: {e}")
            raise SystemExit(f"Storage error: {e}")
    elif args.helpers_output:
        # Legacy file output
        output_path = Path(args.helpers_output)
        if not dry_run:
            output_path.write_text(json.dumps(
                helper_map, indent=2), encoding="utf-8")
            logger.success(f"Helper data written to {output_path}")
        else:
            logger.info(f"Dry-run: would write helper data to {output_path}")
        if not helper_uri:
            helper_uri = str(output_path)
        if args.exclude_helpers:
            helper_storage = "external"
            metadata_helper_map = None
    elif args.exclude_helpers:
        helper_storage = "external"
        metadata_helper_map = None
        if not helper_uri:
            logger.warning("Helper storage is external but no URI specified")

    logger.step("Building metadata bundle")
    label = args.label if args.label is not None else DEFAULT_METADATA_LABEL
    bundle = build_wallet_metadata_bundle(
        wallet_address,
        master_digest,
        metadata_helper_map,
        label=label,
        helper_storage=helper_storage,
        helper_uri=helper_uri,
    )
    output_json = bundle.to_json(fmt=args.format, pretty=True)

    if args.output:
        output_path = Path(args.output)
        if not dry_run:
            output_path.write_text(output_json, encoding="utf-8")
            logger.success(f"Metadata written to {output_path}")
        else:
            logger.info(f"Dry-run: would write metadata to {output_path}")

    if not args.quiet:
        if getattr(args, 'json_output', False):
            # In JSON output mode, only print the final structured output
            print(json.dumps({
                "did": bundle.did,
                "helper_storage": helper_storage,
                "helper_uri": helper_uri,
                "metadata_label": label,
            }, indent=2))
        else:
            logger.step("Enrollment complete")
            logger.info(f"DID: {bundle.did}")
            if not args.output:
                print(output_json)


def cmd_demo_kit(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"input file not found: {input_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_payload = _load_json(input_path)
    wallet_address = args.wallet or str(
        input_payload.get("wallet_address", "")).strip()
    if not wallet_address:
        raise SystemExit(
            "wallet address is required (via --wallet or input JSON)")

    label = args.label if args.label is not None else DEFAULT_METADATA_LABEL
    master_digest, helper_map, _ = _compute_enrollment(
        input_payload["fingers"])

    inline_bundle = build_wallet_metadata_bundle(
        wallet_address,
        master_digest,
        helper_map,
        label=label,
        helper_storage="inline",
    )

    helper_uri = args.helper_uri or "ipfs://demo-helper-placeholder"
    external_bundle = build_wallet_metadata_bundle(
        wallet_address,
        master_digest,
        None,
        label=label,
        helper_storage="external",
        helper_uri=helper_uri,
    )

    files_created: List[Path] = []

    wallet_inline_path = output_dir / "metadata_wallet_inline.json"
    _write_json(wallet_inline_path,
                inline_bundle.metadata_for_format("wallet"))
    files_created.append(wallet_inline_path)

    cip30_inline_path = output_dir / "metadata_cip30_inline.json"
    _write_json(cip30_inline_path, inline_bundle.metadata_for_format("cip30"))
    files_created.append(cip30_inline_path)

    wallet_external_path = output_dir / "metadata_wallet_external.json"
    _write_json(wallet_external_path,
                external_bundle.metadata_for_format("wallet"))
    files_created.append(wallet_external_path)

    cip30_external_path = output_dir / "metadata_cip30_external.json"
    _write_json(cip30_external_path,
                external_bundle.metadata_for_format("cip30"))
    files_created.append(cip30_external_path)

    helpers_path = output_dir / "helpers.json"
    _write_json(helpers_path, helper_map)
    files_created.append(helpers_path)

    cip30_inline = inline_bundle.metadata_for_format("cip30")
    cip30_entries_literal = json.dumps(cip30_inline["metadata"], indent=2)
    helper_json_literal = json.dumps(helper_map, indent=2)

    ts_lines = [
        "// Auto-generated by decentralized_did.cli demo-kit",
        "// Provides ready-to-use CIP-30 metadata and helper payloads for demos.",
        f'export const biometricDid = "{inline_bundle.did}";',
        f'export const walletAddress = "{wallet_address}";',
        "",
        "export const cip30MetadataEntries: [number, unknown][] = "
        + cip30_entries_literal
        + ";",
        "",
        "export const cip30MetadataMap = new Map<bigint, unknown>(",
        "  cip30MetadataEntries.map(([label, payload]) => [BigInt(label), payload])",
        ");",
        "",
        "export const helperData = "
        + helper_json_literal
        + " as const;",
        "",
    ]
    ts_path = output_dir / "cip30_payload.ts"
    ts_path.write_text("\n".join(ts_lines), encoding="utf-8")
    files_created.append(ts_path)

    dapp_lines = [
        "// Auto-generated by decentralized_did.cli demo-kit",
        "// Minimal CIP-30 helper demonstrating how to attach biometric metadata.",
        'import { cip30MetadataMap } from "./cip30_payload";',
        "",
        "type ExperimentalTxSender = {",
        "  tx: {",
        "    send: (args: { metadata: Map<bigint, unknown> } & Record<string, unknown>) =>",
        "      Promise<unknown>;",
        "  };",
        "};",
        "",
        "type Cip30Wallet = {",
        "  experimental: () => ExperimentalTxSender;",
        "};",
        "",
        "export function buildBiometricMetadata(): Map<bigint, unknown> {",
        "  return cip30MetadataMap;",
        "}",
        "",
        "export async function attachBiometricMetadata(",
        "  wallet: Cip30Wallet,",
        "  extras: Record<string, unknown> = {}",
        "): Promise<unknown> {",
        "  const metadata = cip30MetadataMap;",
        "  return wallet.experimental().tx.send({",
        "    metadata,",
        "    ...extras,",
        "  });",
        "}",
        "",
    ]
    dapp_path = output_dir / "cip30_demo.ts"
    dapp_path.write_text("\n".join(dapp_lines), encoding="utf-8")
    files_created.append(dapp_path)

    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    summary_data = {
        "generatedAt": timestamp,
        "did": inline_bundle.did,
        "walletAddress": wallet_address,
        "metadataLabel": label,
        "helperEntries": len(helper_map),
        "helperUri": helper_uri,
        "artifacts": {
            "wallet": {
                "inline": wallet_inline_path.name,
                "external": wallet_external_path.name,
            },
            "cip30": {
                "inline": cip30_inline_path.name,
                "external": cip30_external_path.name,
            },
            "helpers": helpers_path.name,
            "typescript": {
                "payload": ts_path.name,
                "demo": dapp_path.name,
            },
            "notes": "demo_summary.txt",
        },
    }

    summary_json_path = output_dir / "demo_summary.json"
    _write_json(summary_json_path, summary_data)
    files_created.append(summary_json_path)

    listed_files = [path.name for path in files_created]
    summary_lines = [
        f"Demo kit generated: {timestamp}",
        f"DID: {inline_bundle.did}",
        f"Wallet address: {wallet_address}",
        f"Metadata label: {label}",
        f"Helper entries: {len(helper_map)}",
        "",
        f"External helper URI: {helper_uri}",
        "",
        "Files:",
        *[f"  - {name}" for name in listed_files],
        "",
        "See docs/wallet-integration.md for the presentation walkthrough.",
    ]

    summary_path = output_dir / "demo_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    files_created.append(summary_path)

    if args.zip:
        zip_path = Path(args.zip)
        if not zip_path.suffix:
            zip_path = zip_path.with_suffix(".zip")
        if not zip_path.is_absolute():
            zip_path = output_dir / zip_path
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path, "w") as archive:
            for file_path in files_created:
                archive.write(file_path, file_path.name)
        files_created.append(zip_path)

    if not args.quiet:
        print(f"Demo kit created at {output_dir}")
        print(f"DID: {inline_bundle.did}")
        print("Files:")
        for path in files_created:
            print(f"  - {path}")


def cmd_verify(args: argparse.Namespace) -> None:
    # In JSON output mode, suppress logging to avoid mixed output
    json_mode = getattr(args, 'json_output', False)
    logger = create_logger(
        quiet=args.quiet or json_mode,  # Treat JSON mode as quiet for logging
        verbose=getattr(args, 'verbose', False) and not json_mode,
        debug=getattr(args, 'debug', False) and not json_mode,
        json_output=False,  # Don't use logger's JSON mode
    )

    dry_run = getattr(args, 'dry_run', False)
    if dry_run:
        logger.info("Running in dry-run mode (verification simulated)")

    logger.step("Loading metadata")
    metadata = _load_json(Path(args.metadata))
    payload = _extract_metadata_payload(metadata)
    biometric = payload["biometric"]
    helper_map: Dict[str, Dict[str, object]
                     ] | None = biometric.get("helperData")

    # Try to get helper data from various sources
    if not helper_map:
        # Check if storage backend is specified
        storage_backend = _create_storage_backend_from_args(
            args, logger, dry_run)
        if storage_backend and "helperUri" in biometric:
            helper_uri = biometric["helperUri"]
            logger.step(f"Retrieving helper data from storage: {helper_uri}")
            try:
                if not dry_run:
                    # Import StorageReference
                    from .storage import StorageReference
                    # Parse URI into StorageReference if it's a string
                    if isinstance(helper_uri, str):
                        # File storage uses paths, need to create proper reference
                        if helper_uri.startswith("/") or helper_uri.startswith("file://"):
                            ref = StorageReference(
                                backend="file", uri=helper_uri)
                        elif helper_uri.startswith("data:"):
                            ref = StorageReference(
                                backend="inline", uri=helper_uri)
                        else:
                            # Try to parse as generic reference
                            backend_name = storage_backend.__class__.__name__.replace(
                                "Storage", "").lower()
                            ref = StorageReference(
                                backend=backend_name, uri=helper_uri)
                    else:
                        ref = helper_uri
                    helper_map = storage_backend.retrieve(ref)
                    logger.success("Helper data retrieved from storage")
                else:
                    logger.info(
                        "Dry-run: would retrieve helper data from storage")
                    # In dry-run, we need actual helper data to verify
                    if args.helpers:
                        helper_map = _load_json(Path(args.helpers))
                    else:
                        logger.warning(
                            "Dry-run: cannot verify without helper data")
                        return
            except StorageError as e:
                logger.error(f"Failed to retrieve helper data: {e}")
                raise SystemExit(f"Storage error: {e}")
        elif args.helpers:
            logger.verbose("Loading helper data from file")
            helper_map = _load_json(Path(args.helpers))
        else:
            raise SystemExit(
                "helper data missing in metadata; supply --helpers pointing to helper JSON or use --storage-backend"
            )
    elif args.helpers:
        logger.verbose(
            "Using helper data from --helpers (overriding inline data)")
        helper_map = _load_json(Path(args.helpers))

    expected_digest = _decode_digest(biometric["idHash"])

    logger.step("Loading verification biometric")
    new_payload = _load_json(Path(args.input))
    templates = _build_templates(new_payload["fingers"])

    logger.step("Performing verification")
    extractor = FuzzyExtractor()
    digests: List[Tuple[str, bytes]] = []

    if logger.level.value > 0:
        from .cli_progress import progress_bar
        with progress_bar(len(templates), prefix="Verifying fingerprints") as pbar:
            for template in templates:
                helper_dict = helper_map.get(template.finger_id)
                if not helper_dict:
                    logger.error(
                        f"Missing helper data for finger {template.finger_id}")
                    raise SystemExit(
                        f"missing helper data for finger {template.finger_id}")
                if not dry_run:
                    helper = HelperData(**helper_dict)
                    digest = extractor.reproduce(template, helper)
                    digests.append((template.finger_id, digest))
                pbar.update()
    else:
        for template in templates:
            helper_dict = helper_map.get(template.finger_id)
            if not helper_dict:
                raise SystemExit(
                    f"missing helper data for finger {template.finger_id}")
            if not dry_run:
                helper = HelperData(**helper_dict)
                digest = extractor.reproduce(template, helper)
                digests.append((template.finger_id, digest))

    if dry_run:
        logger.success(
            "Dry-run: verification process completed (no actual verification)")
        return

    master_digest = aggregate_finger_digests(digests)
    if master_digest != expected_digest:
        logger.error("Verification failed: biometric digest mismatch")
        raise SystemExit("verification failed: biometric digest mismatch")

    if getattr(args, 'json_output', False):
        # In JSON output mode, only print the final structured output
        print(json.dumps({
            "result": "success",
            "verified": True,
            "fingerprints_checked": len(templates),
        }, indent=2))
    else:
        logger.success("Verification succeeded ✓")


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add common CLI arguments to a parser."""
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="enable verbose output")
    parser.add_argument("--debug", action="store_true",
                        help="enable debug output (implies --verbose)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="suppress all output except errors")
    parser.add_argument("--json-output", action="store_true",
                        help="output structured JSON")
    parser.add_argument("--dry-run", action="store_true",
                        help="simulate operations without making changes")


def _add_storage_args(parser: argparse.ArgumentParser) -> None:
    """Add storage backend arguments to a parser."""
    parser.add_argument(
        "--storage-backend",
        choices=["inline", "file", "ipfs"],
        help="storage backend for helper data (default: inline/none)",
    )
    parser.add_argument(
        "--storage-config",
        help="backend-specific configuration as JSON string",
    )
    parser.add_argument(
        "--storage-path",
        help="directory path for file storage backend",
    )
    parser.add_argument(
        "--storage-backup",
        action="store_true",
        help="enable backup for file storage backend",
    )
    parser.add_argument(
        "--ipfs-api",
        help="IPFS API endpoint (e.g., /ip4/127.0.0.1/tcp/5001)",
    )
    parser.add_argument(
        "--ipfs-gateway",
        help="IPFS HTTP gateway URL for retrieval",
    )
    parser.add_argument(
        "--ipfs-pin",
        action="store_true",
        help="pin helper data in IPFS for persistence",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Biometric DID toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enroll = subparsers.add_parser(
        "generate", help="generate DID metadata from biometric input")
    enroll.add_argument("--input", required=True,
                        help="path to JSON file with finger minutiae")
    enroll.add_argument("--wallet", help="Cardano wallet address override")
    enroll.add_argument("--output", help="destination file for metadata JSON")
    enroll.add_argument("--label", type=int,
                        help="Cardano metadata label override (default 1990)")
    enroll.add_argument("--helpers-output",
                        help="path to write helper data JSON")
    enroll.add_argument(
        "--helper-uri",
        help="URI or reference where helper data is stored when excluded from metadata",
    )
    enroll.add_argument(
        "--exclude-helpers",
        action="store_true",
        help="omit helper data from metadata output",
    )
    enroll.add_argument(
        "--format",
        choices=("wallet", "cip30"),
        default="wallet",
        help="metadata output format",
    )
    _add_common_args(enroll)
    _add_storage_args(enroll)
    enroll.set_defaults(func=cmd_generate)

    demo = subparsers.add_parser(
        "demo-kit",
        help="generate a bundle of demo wallet metadata artifacts",
    )
    demo.add_argument(
        "--input",
        default=str(DEFAULT_SAMPLE_INPUT),
        help="biometric input JSON (defaults to bundled sample)",
    )
    demo.add_argument(
        "--output-dir",
        default="demo-kit",
        help="directory to write demo artifacts (default: demo-kit)",
    )
    demo.add_argument("--wallet", help="Cardano wallet address override")
    demo.add_argument("--label", type=int,
                      help="Cardano metadata label override (default 1990)")
    demo.add_argument(
        "--helper-uri",
        help="URI pointing to externally hosted helper data (default placeholder)",
    )
    demo.add_argument(
        "--zip",
        help="optional zip archive filename for the generated kit",
    )
    demo.add_argument("--quiet", action="store_true",
                      help="suppress stdout output")
    demo.set_defaults(func=cmd_demo_kit)

    verify = subparsers.add_parser(
        "verify", help="verify new biometric scan against saved metadata")
    verify.add_argument("--metadata", required=True,
                        help="metadata JSON previously generated")
    verify.add_argument("--input", required=True,
                        help="new biometric scan JSON to validate")
    verify.add_argument(
        "--helpers", help="path to helper data JSON if not in metadata")
    _add_common_args(verify)
    _add_storage_args(verify)
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
