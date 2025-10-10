# Frequently Asked Questions

## What biometric data leaves the user's device?
Only quantized minutiae hashes and optional helper data (salted HMACs) ever leave the device. Raw fingerprint images or point clouds remain local.

## How is helper data stored?
By default helper data is embedded in metadata (`helperStorage=inline`). Users can exclude it and provide a `helperUri` pointing to IPFS, a secure vault, or keep it offline for selective sharing.

## Can the biometric digest be reversed to recreate a fingerprint?
No. Quantization, hashing (BLAKE2b), and salted helper data make inversion computationally infeasible. Helper data is integrity-only, not a reconstruction aid.

## What happens if a finger is injured?
The fuzzy extractor tolerates small perturbations, but major changes require re-enrollment. Governance docs outline rotation procedures so new metadata supersedes old digests.

## How are false positives/negatives handled?
Quantization parameters are conservative. If verification fails, users can retry capture; persistent mismatch triggers re-enrollment. False positives are unlikely because ten fingers must match simultaneously.

## Do verifiers need full helper data?
Yes, to reproduce the digest locally. When helper data is stored externally, verifiers retrieve it (with user consent) before running verification.

## Which Cardano metadata label is used?
Label `1990` by default, override via CLI `--label`. Teams should coordinate label usage through governance to avoid conflicts.

## How does this integrate with Cardano wallets?
Wallets can attach the metadata during sign/submit flows (CIP-30). The `docs/cardano-integration.md` guide covers metadata layout and roadmap for CIP-68 and Plutus hooks.

## What about privacy regulations?
No personal identifiers are stored. Still, deployments should collect consent, maintain access logs when hosting helper data, and comply with local biometric laws.

## Is zero-knowledge proof support planned?
Yes. Roadmap includes Poseidon-hash compatibility and ZK circuits so verifiers can trust membership proofs without seeing helper data.
