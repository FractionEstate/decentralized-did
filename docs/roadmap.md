# Roadmap

## Current Sprint (Oct 2025)
- Finalize the biometric metadata ingestion plan for the bundled `demo-wallet` (Veridian fork).
- Define the experimental CIP-30 bridge (store metadata bundle, surface approval UX, persist helper URI).
- Publish contributor guidance (`copilot-instructions.md`) and keep roadmap/docs cross-referenced.
- Capture integration test scenarios that exercise Python CLI output against the wallet flow.
- Deliver the CLI "demo-kit" packaging command so demo operators can share consistent artifacts.

## Near-Term (Quarter 1)
- Land biometric metadata storage and approval UI inside the demo wallet (peer connection + signing screens).
- Publish TypeScript bindings (or JSON schema) for wallet integrators beyond Veridian.
- Build automated fixtures that validate CLI-generated bundles round-trip inside the wallet (unit + e2e).
- Conduct informal security review with community experts focusing on helper data handling.

## Mid-Term (Quarter 2)
- Launch managed enrollment node with secure hardware support (YubiKey Bio, Apple Secure Enclave).
- Draft CIP for standardized biometric metadata structure.
- Build Plutus validator that requires matching biometric digest for access-controlled actions.
- Implement zero-knowledge proof flow for selective disclosure (e.g., age attestations).

## Long-Term (Quarter 3+)
- Formal audits of biometric pipeline and helper data storage.
- Multi-factor composability (biometric digest + social recovery + device attestations).
- Decentralized registry anchored on Cardano sidechain or Mithril snapshots.
- Explore interoperability with W3C DID Core and verifiable credentials.
