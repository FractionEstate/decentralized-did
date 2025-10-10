# Decentralized Biometric DID for Cardano

Prototype for the Cardano Summit Hackathon demonstrating how anonymized ten-finger biometrics can anchor a decentralized digital identity to a Cardano wallet address.

## Why it Matters
- Bind a human to a wallet without revealing personal data or relying on centralized issuers.
- Preserve anonymity by hashing quantized minutiae into non-invertible digests.
- Provide a concrete toolkit that wallets and dApps can extend into production.

## Features
- Ten-finger aggregation with deterministic BLAKE2b-based digests.
- Helper data hardened by salted HMACs to validate scans without leaking minutiae.
- DID string + wallet metadata generator aligned with Cardano conventions.
- CLI for enrollment (`generate`), verification (`verify`), and demo kit packaging (`demo-kit`).
- Optional external helper-data storage with automatic URI tagging.
- Comprehensive documentation: architecture, privacy, governance, and roadmap.

## Quickstart
```bash
# optional: python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest

# generate DID metadata from the sample dataset
python -m decentralized_did.cli generate --input examples/sample_fingerprints.json --output metadata.json

# store helper data separately while referencing IPFS
python -m decentralized_did.cli generate \
	--input examples/sample_fingerprints.json \
	--output metadata_external.json \
	--exclude-helpers \
	--helpers-output helpers.json \
	--helper-uri ipfs://cid-demo

# verify a new scan (reuse the same sample for demonstration)
python -m decentralized_did.cli verify --metadata metadata.json --input examples/sample_fingerprints.json

# verify when helper data is stored externally
python -m decentralized_did.cli verify --metadata metadata_external.json --input examples/sample_fingerprints.json --helpers helpers.json

# build a ready-to-share demo kit with inline/external variants and helper data
python -m decentralized_did.cli demo-kit \
	--input examples/sample_fingerprints.json \
	--wallet addr_test1demo123 \
	--output-dir demo-kit
# resulting folder includes wallet/cip30 metadata JSON, helper data, summary sheet, and `cip30_payload.ts`
# (`cip30MetadataEntries`, `cip30MetadataMap`, and `helperData` exports for dApps)
# (with ready-made `cip30MetadataEntries` + `cip30MetadataMap` exports)

# or use the console script after installation
dec-did generate --input examples/sample_fingerprints.json --output metadata.json --quiet
```

## Repository Layout
- `src/decentralized_did/biometrics`: minutiae quantization, fuzzy extractor, and aggregation logic.
- `src/decentralized_did/did`: deterministic DID fragment + metadata payload builders.
- `src/decentralized_did/cardano`: helpers to wrap payloads into Cardano transaction metadata and wallet bundles.
- `src/decentralized_did/cli.py`: command-line interface tying the pipeline together.
- `demo-wallet/`: Cardano Foundation's Veridian wallet (detached from its upstream Git history) used as the reference integration target.
- `examples/`: synthetic minutiae dataset for demos.
- `docs/`: proposal, architecture, privacy, governance, roadmap, wallet integration guide, and RFC template.
- `tests/`: pytest coverage for the biometric pipeline and metadata helpers.

## Documentation Highlights
- `docs/proposal.md`: project vision, scope, success criteria.
- `docs/architecture.md`: system architecture and data flow.
- `docs/privacy-security.md`: threat model and mitigation plan.
- `docs/governance.md`: decentralized decision-making process.
- `docs/roadmap.md`: milestones and current focus areas (kept in sync with the active sprint plan).
- `docs/cardano-integration.md`: metadata schema and wallet/CIP integration guidance.
- `docs/wallet-integration.md`: step-by-step instructions for bundling metadata and wiring it into wallets (including the bundled demo wallet).
- `docs/pitch-outline.md`: storyteller's guide for demos and judging.
- `docs/hackathon-playbook.md`: role assignments and event-day checklist.

## Demo Wallet Integration

The repository embeds `demo-wallet/`, a working copy of the Cardano Foundation's Veridian wallet to serve as our reference implementation. Use the Python CLI to produce a CIP-30 metadata bundle, then follow `docs/wallet-integration.md` to load that bundle into the demo wallet flows. The short-term objective is to expose a biometric metadata hand-off inside the wallet's peer-connect flow and persist helper URIs for verification.

## Contributor Notes

Before implementing feature work, read `copilot-instructions.md` for coding conventions, required checklists (tests, docs, linting), and details on how the Python toolkit and demo wallet should evolve together. The file is updated alongside the roadmap to keep Copilot-driven contributions aligned with the active plan.

## Next Steps
1. Integrate with real capture hardware SDKs and secure enclaves.
2. Wire biometric metadata approval and storage into the demo wallet's peer connection workflow.
3. Draft a CIP for biometric metadata schema standardization.
4. Explore zero-knowledge proofs for privacy-preserving attestations.
