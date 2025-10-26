# Decentralized Biometric DID for Cardano

Deterministic biometric identifiers for Cardano, powered by an open-source Python toolkit, CLI, and a reference demo wallet. Phase 4.6 prioritises reproducible DID generation from fingerprint minutiae, v1.1 metadata packaging, and production-ready deployment automation.

> **Transparency First** – BCH-backed error correction, liveness detection, and mobile capture remain under active development. The public SDK currently ships with a salted-hash fuzzy extractor and BLAKE2b aggregation. See `docs/audit-validation-2025-10-22.md` for live gap tracking.

---

## Project Highlights
- **Deterministic DIDs** – `generate_deterministic_did(commitment, network)` returns `did:cardano:{network}:{base58_hash}` without exposing wallet addresses.
- **Biometric Pipeline** – `FingerTemplate` quantises minutiae (grid `0.05`, 32 angle bins); `FuzzyExtractor` salts and HMACs each finger to produce reproducible digests.
- **Aggregation** – `aggregate_finger_digests` hashes sorted `(finger_id, digest)` pairs with BLAKE2b to derive the master commitment.
- **Metadata Schema v1.1** – `build_metadata_payload` emits multi-controller payloads with enrollment timestamps and revocation flags.
- **CLI Workflow** – `dec-did` supports enrollment, verification, helper storage selection, and deterministic DID inspection.
- **Demo Wallet** – Veridian-based Ionic/React wallet updated in Phase 4.6 to consume deterministic DIDs (`demo-wallet/TASK-1-MANUAL-TESTING-STATUS.md`).
- **Deployment Tooling** – Docker assets, profile-aware Compose files, SSL automation, and runbooks in `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`.
- **Performance Harness** – `benchmark_api.py` records enrollment/verification latency; latest snapshots live in `docs/reports/benchmark_results.json`.

---

## Repository Layout
```
decentralized-did/
├── core/              # Docker Compose stack, deployment scripts, backend API servers
├── demo-wallet/       # Veridian-based demo wallet (deterministic DID flows)
├── docs/              # Architecture notes, audits, deployment guides
└── sdk/               # Python SDK, CLI, tests, examples, notebooks
  ├── src/decentralized_did/   # Installable Python package
  ├── tests/                   # pytest suite
  ├── examples/                # Sample minutiae payloads & SDK demos
  └── benchmark_api.py         # API latency harness
```

---

## Install & Test
```bash
git clone https://github.com/FractionEstate/decentralized-did
cd decentralized-did
pip install -r sdk/requirements.txt
pip install -e sdk
cd sdk
pytest
cd ..
```

Optional: for the demo wallet, install Node.js 18+ and run `npm test` inside `demo-wallet/`.

---

## CLI Quickstart
Generate metadata with inline helper data:
```bash
dec-did generate \
  --input sdk/examples/sample_fingerprints.json \
  --output metadata.json
```

Store helper data externally (file/IPFS) for smaller on-chain payloads:
```bash
dec-did generate \
  --input sdk/examples/sample_fingerprints.json \
  --exclude-helpers \
  --helpers-output helpers.json \
  --helper-uri ipfs://example-cid \
  --output metadata_external.json
```

Verify a follow-up scan:
```bash
dec-did verify \
  --metadata metadata.json \
  --input sdk/examples/sample_fingerprints.json
```

Defaults: metadata label `1990`, deterministic DID generation, inline helper storage unless excluded.

---

## Demo Wallet
```bash
cd demo-wallet
npm install
npm run start:local   # http://localhost:3003
npm test              # Jest unit/integration suites
npm run build:local   # Production bundle
```
Key references:
- `demo-wallet/TASK-1-MANUAL-TESTING-STATUS.md`
- `demo-wallet/tests/e2e/biometric-enrollment.spec.ts`
- `demo-wallet/scripts/did-performance.cjs`

---

## Performance & Monitoring
- `benchmark_api.py` exercises enrollment and verification endpoints; export summaries with `--output`.
- Koios instrumentation (`KoiosMetrics`) exposes `/metrics/koios` for latency, cache hit ratio, and error counts.
- Targets: enrollment <100 ms, verification <50 ms. Latest figures are logged in `docs/reports/benchmark_results.json`.

Run a local benchmark:
```bash
python benchmark_api.py --server http://localhost:8002 --iterations 5 --output docs/reports/benchmark_results.json
```

---

## Current Limitations
- BCH decoding, adaptive minutiae pruning, and weighted multi-finger fusion live in `src/biometrics/` but are not exported.
- No liveness or spoofing detection; deployments must integrate external countermeasures.
- CLI expects minutiae JSON; mobile capture and QR bridge flows are pending.
- Single Koios endpoint with TTL cache; multi-provider failover is on the roadmap.
- Helper data should be treated as a secret; no encrypted storage backend ships by default.

Tracked in `.github/tasks.md` and `docs/audit-validation-2025-10-22.md`.

---

## Documentation Map
- `docs/roadmap.md` – Sprint focus and milestone tracking.
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` – Docker, nginx, SSL renewal, backups.
- `docs/cardano-integration.md` – Metadata schema and transaction builder workflow.
- `docs/wallet-integration.md` – Wallet wiring and deterministic DID handling.
- `docs/reports/` – Audits, benchmarks, deployment readiness artefacts.

---

## Contributing
1. Review `.github/instructions/copilot.instructions.md`, `docs/roadmap.md`, and `.github/tasks.md` before starting work.
2. Update `.github/tasks.md` as tasks are created or completed (task numbers restart at 1 per phase).
3. Add and run targeted tests (`pytest`, `npm test`, benchmarks`) for code changes.
4. Keep documentation synchronised with behaviour changes (README, `docs/`, examples).
5. Use only open-source tooling, libraries, and infrastructure.

Major features (BCH migration, liveness, hardware integration) require a planning issue linked to the relevant roadmap tasks.

---

## License
Apache License 2.0 – see [`LICENSE`](LICENSE).
