"""Command-line interface for biometric DID enrollment and verification."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Dict, List, Tuple

from .biometrics.aggregator import aggregate_finger_digests, helpers_to_dict
from .biometrics.feature_extractor import FingerTemplate, minutiae_from_dicts
from .biometrics.fuzzy_extractor import FuzzyExtractor, HelperData
from .cardano.metadata_encoder import (
    DEFAULT_METADATA_LABEL,
    pretty_print_metadata,
    to_wallet_metadata,
)
from .did.generator import build_did, build_metadata_payload


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


def cmd_generate(args: argparse.Namespace) -> None:
    input_payload = _load_json(Path(args.input))
    wallet_address = args.wallet or str(input_payload.get("wallet_address", "")).strip()
    if not wallet_address:
        raise SystemExit("wallet address is required (via --wallet or input JSON)")

    templates = _build_templates(input_payload["fingers"])
    extractor = FuzzyExtractor()
    digests: List[Tuple[str, bytes]] = []
    helpers: List[HelperData] = []
    for template in templates:
        digest, helper = extractor.generate(template)
        digests.append((template.finger_id, digest))
        helpers.append(helper)

    master_digest = aggregate_finger_digests(digests)
    helper_map = helpers_to_dict(helpers)

    helper_uri = args.helper_uri
    if args.helpers_output:
        output_path = Path(args.helpers_output)
        output_path.write_text(json.dumps(helper_map, indent=2), encoding="utf-8")
        if not helper_uri:
            helper_uri = str(output_path)

    helper_storage = "inline"
    metadata_helper_map = helper_map
    if args.exclude_helpers:
        helper_storage = "external"
        metadata_helper_map = None

    did = build_did(wallet_address, master_digest)
    payload = build_metadata_payload(
        wallet_address,
        master_digest,
        metadata_helper_map,
        helper_storage=helper_storage,
        helper_uri=helper_uri,
    )
    label = args.label if args.label is not None else DEFAULT_METADATA_LABEL
    metadata = to_wallet_metadata(payload, label)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    if not args.quiet:
        print(did)
        print(pretty_print_metadata(metadata))


def cmd_verify(args: argparse.Namespace) -> None:
    metadata = _load_json(Path(args.metadata))
    payload = next(iter(metadata.values())) if isinstance(metadata, dict) else metadata
    biometric = payload["biometric"]
    helper_map: Dict[str, Dict[str, object]] | None = biometric.get("helperData")
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
            raise SystemExit(f"missing helper data for finger {template.finger_id}")
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

    enroll = subparsers.add_parser("generate", help="generate DID metadata from biometric input")
    enroll.add_argument("--input", required=True, help="path to JSON file with finger minutiae")
    enroll.add_argument("--wallet", help="Cardano wallet address override")
    enroll.add_argument("--output", help="destination file for metadata JSON")
    enroll.add_argument("--label", type=int, help="Cardano metadata label override (default 1990)")
    enroll.add_argument("--helpers-output", help="path to write helper data JSON")
    enroll.add_argument(
        "--helper-uri",
        help="URI or reference where helper data is stored when excluded from metadata",
    )
    enroll.add_argument(
        "--exclude-helpers",
        action="store_true",
        help="omit helper data from metadata output",
    )
    enroll.add_argument("--quiet", action="store_true", help="suppress stdout output")
    enroll.set_defaults(func=cmd_generate)

    verify = subparsers.add_parser("verify", help="verify new biometric scan against saved metadata")
    verify.add_argument("--metadata", required=True, help="metadata JSON previously generated")
    verify.add_argument("--input", required=True, help="new biometric scan JSON to validate")
    verify.add_argument("--helpers", help="path to helper data JSON if not in metadata")
    verify.add_argument("--quiet", action="store_true")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
