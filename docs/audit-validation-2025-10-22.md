# Audit Validation – 22 Oct 2025

Validation of the "Decentralized Biometric DID for Cardano" audit summary against the code presently in this repository.

## Scope

- Python package under `src/decentralized_did`
- Command-line workflow (`dec-did`)
- Supporting Cardano helpers and storage modules
- High-level documentation (README, roadmap excerpts)

## Summary

The referenced audit still overstates several advanced biometric capabilities. The most significant gaps remain the lack of BCH-backed fuzzy extraction, the absence of XOR-style aggregation with fallback policies, and the missing mobile enrollment / liveness features. Recent work has aligned other areas—deterministic DID integration in the demo wallet, performance instrumentation, and production deployment assets—with the audit narrative. The sections below document the claims that continue to diverge from the live codebase.

## Claim-by-Claim Verification

| Topic | Audit Claim | Reality in Repository | Evidence / Notes |
| --- | --- | --- | --- |
| Fuzzy extractor | BCH(127,64,10) with helper syndrome, 105-byte helper payload | Default extractor salts the quantised minutiae and hashes with BLAKE2b; helper contains base64 salt + truncated HMAC | `src/decentralized_did/biometrics/fuzzy_extractor.py`
| Helper data size | 105 bytes with BCH parity | JSON object containing strings (`salt_b64`, `auth_b64`, grid metadata) | Same file as above
| Multi-finger aggregation | XOR aggregation with quality thresholds (4→3→2 finger fallbacks) | Aggregates by hashing sorted `(finger_id, digest)` pairs with BLAKE2b; no fallback logic or quality scoring | `src/decentralized_did/biometrics/aggregator.py`
| Quantisation parameters | Grid size 10.0, 8 angle bins | `FingerTemplate` defaults to grid size `0.05` and `32` angle bins | `src/decentralized_did/biometrics/feature_extractor.py`
| Helper data secrecy | BCH syndromes publicly stored on-chain | Helper data is optional; metadata embeds helper map when inline, otherwise relies on external storage with URI | `src/decentralized_did/did/generator.py` (`build_metadata_payload`)
| Metadata label | CIP-20 label 674 only | CLI defaults to label `1990`; transaction builder uses 674 when invoked directly | `src/decentralized_did/cardano/metadata_encoder.py`, `cardano/transaction.py`
| Mobile enrollment | Implemented QR bridge and device capture | No mobile capture or QR workflow; CLI expects pre-generated minutiae JSON | Entire CLI (`src/decentralized_did/cli.py`)
| Liveness detection | Required before production | No liveness or anti-spoofing checks in code | Not implemented
| Koios dependency | Needs failover | Client now async with TTL cache and metrics, but still single-provider (no fallback) | `src/decentralized_did/cardano/koios_client.py`
| Demo wallet | Fully wired to deterministic DID | Phase 4.6 Task 1 delivered deterministic DID flow with updated fixtures, tests, and documentation | `demo-wallet/src/core/biometric/biometricDidService.ts`, `demo-wallet/DETERMINISTIC-DID-IMPLEMENTATION.md`
| Performance metrics | 41 ms enrollment / 43 ms verification | Benchmark harness records mean ~2.5 ms enrollment / ~1.1 ms verification (P95 < 10 ms) | `benchmark_api.py`, `docs/reports/benchmark_results.json`

## Additional Observations

- A more advanced BCH-based implementation (`src/biometrics/fuzzy_extractor_v2.py` and related modules) exists under `src/biometrics/` along with extensive tests, but it is not imported by the installable package.
- Updated roadmap (`docs/roadmap.md`) and deployment artifacts (`docs/PRODUCTION_DEPLOYMENT_GUIDE.md`, `.env.*`, automation scripts) now track the deterministic DID rollout; remaining references to BCH-specific behaviour are isolated to legacy validation reports under `docs/reports/`.
- Tests under `tests/` reference both the shipped SDK (`decentralized_did`) and the experimental modules; running the full suite will fail until dependencies like `galois` are installed and the BCH pipeline is wired into the package export.
- Storage backends (inline/file/IPFS) operate as documented; helper data handling matches the CLI behaviour rather than the audit narrative.

## Corrective Actions Completed

- Replaced `README.md` with an accurate description of current functionality, limitations, and integration points.
- Delivered deterministic DID integration for the demo wallet (Phase 4.6 Task 1) with updated fixtures, documentation, and automated coverage.
- Added `benchmark_api.py` harness and captured reference metrics in `docs/reports/benchmark_results.json`.
- Authored production deployment assets (`Dockerfile.backend`, `docker-compose.yml`, environment templates, automation scripts) and the accompanying `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`.

## Recommended Follow-Up

1. Decide whether to migrate the public SDK to the BCH-backed extractor (import from `src/biometrics`) or update the audit narrative to reflect the current salted-hash workflow permanently.
2. Implement multi-provider fallback for Koios-dependent operations and document operational runbooks for outage scenarios.
3. Add explicit regression tests for the helper data format consumed by the CLI to ensure future refactors retain compatibility.
4. Surface the absence of liveness detection and mobile enrollment flows prominently in public documentation until corresponding features ship.
