"""Command-line interface for biometric DID enrollment and verification."""
from __future__ import annotations

import argparse
import base64
import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from zipfile import ZipFile

from .biometrics.aggregator import aggregate_finger_digests, helpers_to_dict
from .biometrics.feature_extractor import FingerTemplate, minutiae_from_dicts
from .biometrics.fuzzy_extractor import FuzzyExtractor, HelperData
from .cardano.metadata_encoder import DEFAULT_METADATA_LABEL
from .cardano.wallet_integration import build_wallet_metadata_bundle


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


def cmd_generate(args: argparse.Namespace) -> None:
    input_payload = _load_json(Path(args.input))
    wallet_address = args.wallet or str(
        input_payload.get("wallet_address", "")).strip()
    if not wallet_address:
        raise SystemExit(
            "wallet address is required (via --wallet or input JSON)")

    master_digest, helper_map, _ = _compute_enrollment(
        input_payload["fingers"])

    helper_uri = args.helper_uri
    if args.helpers_output:
        output_path = Path(args.helpers_output)
        output_path.write_text(json.dumps(
            helper_map, indent=2), encoding="utf-8")
        if not helper_uri:
            helper_uri = str(output_path)

    helper_storage = "inline"
    metadata_helper_map = helper_map
    if args.exclude_helpers:
        helper_storage = "external"
        metadata_helper_map = None

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
        output_path.write_text(output_json, encoding="utf-8")
    if not args.quiet:
        print(bundle.did)
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
    metadata = _load_json(Path(args.metadata))
    payload = _extract_metadata_payload(metadata)
    biometric = payload["biometric"]
    helper_map: Dict[str, Dict[str, object]
                     ] | None = biometric.get("helperData")
    if not helper_map:
        if args.helpers:
            helper_map = _load_json(Path(args.helpers))
        else:
            raise SystemExit(
                "helper data missing in metadata; supply --helpers pointing to helper JSON"
            )
    elif args.helpers:
        helper_map = _load_json(Path(args.helpers))
    expected_digest = _decode_digest(biometric["idHash"])

    new_payload = _load_json(Path(args.input))
    templates = _build_templates(new_payload["fingers"])
    extractor = FuzzyExtractor()
    digests: List[Tuple[str, bytes]] = []
    for template in templates:
        helper_dict = helper_map.get(template.finger_id)
        if not helper_dict:
            raise SystemExit(
                f"missing helper data for finger {template.finger_id}")
        helper = HelperData(**helper_dict)
        digest = extractor.reproduce(template, helper)
        digests.append((template.finger_id, digest))

    master_digest = aggregate_finger_digests(digests)
    if master_digest != expected_digest:
        raise SystemExit("verification failed: biometric digest mismatch")
    if not args.quiet:
        print("verification succeeded")


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
    enroll.add_argument("--quiet", action="store_true",
                        help="suppress stdout output")
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
    verify.add_argument("--quiet", action="store_true")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
