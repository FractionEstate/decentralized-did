# Cardano Integration Guide

## Objectives
- Describe how biometric digests map into Cardano metadata standards.
- Provide reference flows for wallets (CIP-30) and on-chain consumers (Plutus, CIP-68).
- Highlight operational considerations for storing helper data externally (IPFS, Arweave, centralized vaults).

## Metadata Layout

### Schema v1.1 (RECOMMENDED)
```json
{
  "674": {
    "version": "1.1",
    "did": "did:cardano:mainnet:zQmNhFJPjg3MqLzM7CzZGVvjV5fCDuWnQ5Lzg3FHKfNm4tS",
    "controllers": ["addr1qx...", "addr1qy..."],
    "biometric": {
      "idHash": "<base58 encoded digest>",
      "helperStorage": "inline|external",
      "helperUri": "ipfs://… (optional)",
      "helperData": {
        "left_thumb": { "finger_id": "left_thumb", "salt_b64": "…", "auth_b64": "…" }
        // ... other fingers when helperStorage == "inline"
      }
    },
    "enrollmentTimestamp": "2025-10-14T12:00:00Z",
    "revoked": false,
    "revokedAt": null
  }
}
```

### Schema v1.0 (DEPRECATED)
```json
{
  "674": {
    "version": 1,
    "walletAddress": "addr1…",
    "biometric": {
      "idHash": "<base64-url digest>",
      "helperStorage": "inline|external",
      "helperUri": "ipfs://…",
      "helperData": { /* ... */ }
    }
  }
}
```

**Key Differences:**
- **v1.1**: Uses deterministic DIDs, multi-controller support, enrollment timestamps, revocation mechanism
- **v1.0**: Uses wallet-based DIDs (Sybil vulnerable), single controller only
- **Label**: CIP-20 label `674` is used for biometric DID metadata
- `helperStorage` communicates whether helper data is embedded or must be fetched externally.
- `helperUri` can be an IPFS CID, HTTPS link, or custom URI recognized by verifiers.

## Wallet Metadata Flow (CIP-30)
1. CLI generates metadata JSON and optional helper file.
2. DApp uses `cardano.signData` or transaction-building APIs to attach metadata under agreed label.
3. Wallet signs transaction; metadata becomes accessible on-chain.
4. Verifiers fetch transaction metadata (using our Koios client, `ogmios`, or cardano-node) and reconstruct the DID digest.

## CIP-68 NFT Pattern (Roadmap)
- Mint a reference NFT whose datum stores `idHash` and `helperUri`.
- Use inline datum or reference scripts so dApps can reference the biometric commitment without scanning transaction history.
- Consider off-chain governance to handle rotations (new biometrics -> update CIP-68 mutable fields).

## Plutus Validator for On-Chain Verification
To enable trustless on-chain verification, we use a Plutus V3 validator script.

### Validator Logic
The validator script, located at `plutus/validator.py`, uses a signature-based verification model:
-   **Datum**: The datum locked with a UTXO at the script address contains the public key derived from the user's biometrics.
-   **Redeemer**: To spend the UTXO, the user must provide a redeemer containing a message and a valid signature over that message.
-   **Verification**: The validator uses the `verify_ed25519_signature` function to check if the signature in the redeemer was created by the private key corresponding to the public key in the datum.

### Off-Chain Code
The `opshin` tool compiles the Python-based validator into a Plutus script. The off-chain code then uses PyCardano to build a transaction that includes the script, datum, and redeemer.

### Compiling the Validator
To compile the validator, run the following command from the root of the repository:
```bash
/workspaces/decentralized-did/.venv/bin/python -m opshin build plutus/validator.py
```
This will create the compiled Plutus script in the `build/validator/` directory.

## Blockchain Query Layer
The `CardanoQuery` class in `src/decentralized_did/cardano/query.py` provides a high-level API for querying DID information from the blockchain. It now uses the Koios REST API exclusively via the shared `KoiosClient` and `KoiosMetadataScanner`, removing the previous Blockfrost dependency.

### DID Resolution
The `resolve_did` method checks for the existence of a DID by querying the selected backend for transactions with the metadata label `674` and searching for a match. This is useful for preventing duplicate enrollments and for verifying that a DID has been anchored on-chain.

### Enrollment History
The `get_enrollment_history` method retrieves all metadata updates for a given DID, providing a full audit trail of the identity's on-chain history.


## External Helper Storage
### IPFS/IPNS
- Use `--helpers-output` to dump helper JSON.
- Pin the file to IPFS, record CID.
- Supply `--helper-uri ipfs://<CID>` so verifiers know where to fetch helper data.

### Secure Vaults
- Wallet custodians may store helper data in confidential enclaves.
- Metadata includes `helperStorage=external` and `helperUri=vault://tenant/id` (custom scheme).
- Verifiers authenticate to vault before retrieving helper JSON.

### No Helper Publication
- Advanced users can keep helper data entirely offline.
- They must distribute helper JSON to verifiers through side channels.
- Metadata should then include `helperStorage=external` without `helperUri`; CLI enforces manual sharing during verification.

## Demo Kit Packaging
- Use `python -m decentralized_did.cli demo-kit` (or `dec-did demo-kit`) to emit inline/external `wallet` and `cip30` metadata variants, helper JSON, and a presenter summary in a single directory.
- Supply `--zip demo-kit.zip` when sharing artifacts with demo operators or wallet teams.
- Override `--helper-uri` once helper data is hosted on IPFS or another storage backend so downstream verifiers know where to fetch it.
- Consume the generated `cip30_payload.ts` in sample dApps to bootstrap `cip30MetadataMap` (`Map<bigint, Metadatum>`) construction without manual JSON wrangling, or import the ready-made `cip30_demo.ts` helper to call `attachBiometricMetadata` against a CIP-30 wallet.
- Use the machine-readable `demo_summary.json` inventory when scripting deployments (e.g., uploading helper data to IPFS or injecting metadata into CI pipelines).

## Operational Checklist
- [ ] Agree on metadata label with counterparties.
- [ ] Ensure helper data is available (inline or via `helperUri`).
- [ ] Validate digest re-computation using `python -m decentralized_did.cli verify` prior to on-chain submission.
- [ ] Keep audit logs of helper data access, especially when stored externally.

## Tooling Roadmap
- Build CIP-30 reference DApp using `lucid` or `mesh.js` to sign enrollment transactions.
- Automate IPFS pinning from CLI (e.g., via `--ipfs-endpoint`).
- Provide Plutus scripts + tests showcasing identity-gated spending flows.
