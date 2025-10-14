# Architecture Overview

## High-Level Components
- **Capture Layer**: Fingerprint sensor or SDK that produces minutiae-level vectors for all ten fingers.
- **Normalization Layer**: Local processor (library in this repo) that rotates, scales, and quantizes minutiae for reproducibility.
- **Fuzzy Extractor**: Deterministic cryptographic primitive that transforms noisy biometric vectors into a stable 256-bit digest while emitting privacy-preserving helper data.
- **Aggregation Service**: Combines the ten finger digests into a single biometric commitment tied to a wallet address.
- **DID Generator**: Produces a `did:cardano` identifier fragment plus structured metadata ready for wallet inclusion.
- **Metadata Publisher**: Pushes the metadata to Cardano (wallet metadata, CIP-68 assets, or sidechain storage) as decided by integrators.
- **Verification Client**: Repeats the local pipeline and compares digests without revealing raw biometric inputs.

## Data Flow
```
[Sensor SDK]
    ↓ (minutiae points per finger)
[Normalization & Quantization]
    ↓ (canonical templates)
[Fuzzy Extractor]
    ↓ digest + helper per finger
[Aggregator]
    ↓ master biometric digest
[DID Generator]
    ↓ DID fragment + metadata payload
[Wallet/Chain]
```

## Cryptography & Helper Data
- **Quantization**: Round minutiae coordinates to configurable grids (default 50µm) and angles into 32 bins to absorb minor scan differences.
- **Digest**: BLAKE2b-256 with per-finger personalization tag, concatenated and re-hashed for the master digest.
- **Helper Data**: Includes a salt and truncated HMAC to allow validity checks without leaking minutiae; helper data is optional to publish and can instead remain client-side.
- **Verification**: Recompute digest locally; comparison is equality check on the aggregate digest plus HMAC validation on each finger helper.

## Cardano Integration Options
| Layer | Description | Hackathon Prototype |
|-------|-------------|---------------------|
| Wallet metadata | Attach JSON metadata to a transaction referencing the wallet | Provided via CLI JSON output |
| CIP-68 NFT | Mint an NFT containing the biometric commitment as on-chain reference | Documented for roadmap |
| Sidechain / Hydra | Use fast settlement layer for enrollment ceremonies | Deferred |

### Metadata Schema Highlights
- `idHash`: base64-url digest derived from aggregated fingerprints.
- `helperStorage`: signals whether helper data is `inline` or `external`.
- `helperUri`: optional pointer (IPFS CID, vault URI) when helper data is stored elsewhere.
- `helperData`: populated when `helperStorage == "inline"`; omitted when externalized.

## Trust Model
- Users control enrollment; raw biometrics never exit the device.
- Verifiers only receive digests and helper data; they can prove wallet control by signing metadata with the wallet keys.
- Governance decisions (algorithm upgrades, parameter changes) flow through an open RFC process documented in `docs/governance.md`.

## Developer SDK

The Python toolkit provides a clean public API (`decentralized_did` package) for integrating biometric DIDs:

### Core Modules

**Biometrics** (`decentralized_did.biometrics`)
- `FuzzyExtractor`: Main enrollment/verification interface
  - `generate(template)` → `(digest, helper_data)` — Enrollment
  - `reproduce(template, helper_data)` → `digest` — Verification
- `FingerTemplate`: Quantized biometric representation
- `aggregate_finger_digests()`: Multi-finger XOR combination
- Performance: 41ms enrollment, 43ms verification (23 ops/sec)

**DID Generation** (`decentralized_did.did`)
- `build_did(wallet_address, digest)` → W3C compliant `did:cardano:` string
- `build_metadata_payload()` → CIP-20 transaction metadata

**Storage Backends** (`decentralized_did.storage`)
- Abstract: `StorageBackend`, `StorageReference`, `StorageError`
- Concrete: `InlineStorage`, `FileStorage`, `IPFSStorage`
- Factory: `create_storage_backend()`, `get_available_backends()`

**CLI** (`decentralized_did.cli`)
- Commands: `generate`, `verify`, `demo-kit`
- Console script: `dec-did`

### Usage Example
```python
from decentralized_did import (
    FuzzyExtractor, FingerTemplate, Minutia,
    aggregate_finger_digests, build_did
)

# Create template from scanner
minutiae = [Minutia(x=100.5, y=200.3, angle=45.0), ...]
template = FingerTemplate(finger_id="thumb", minutiae=minutiae)

# Enroll
extractor = FuzzyExtractor()
digest, helper = extractor.generate(template)

# Verify (from noisy recapture)
verified_digest = extractor.reproduce(template, helper)
assert digest == verified_digest  # Reproducible!

# Generate DID
did = build_did("addr1qx...", digest)
```

**Full API reference**: [`docs/SDK.md`](SDK.md)
**Working examples**: [`examples/sdk_demo.py`](../examples/sdk_demo.py)

## Deployment View
- **Edge**: Laptop or mobile device containing capture hardware and the Python library.
- **Back end**: Optional aggregator service to store opt-in decentralized registries (could be IPFS gateway or Catalyst dApp).
- **Cardano Node**: Used to submit metadata transactions or interact with Plutus smart contracts if extended.

## Extensibility Hooks
- Pluggable quantization parameters for new sensor models.
- Alternate digest algorithms (e.g., Poseidon hash) for ZK-friendly circuits.
- Optional zero-knowledge proof generator emitting statements like “Digest belongs to wallet X” without exposing helper data.
