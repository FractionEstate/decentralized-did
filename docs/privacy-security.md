# Privacy & Security Blueprint

## Guiding Principles
- **Data Minimization**: Only derived, quantized minutiae hashes leave the capture device.
- **User Control**: Enrollment requires explicit consent; helper data publishing is opt-in.
- **Transparency**: All algorithms, parameters, and governance flows are open source.

## Threat Model
| Actor | Goal | Mitigation |
|-------|------|------------|
| Malicious verifier | Forge a biometric digest to impersonate a wallet | Requires reproducing ten-finger quantized template; enforced via deterministic hashing and wallet signature checks |
| Insider attacker | Access raw biometric data | Raw data never leaves device; recommended use of local secure enclaves for production |
| Replay attacker | Reuse leaked helper data | Helper data bound to wallet address + per-finger salt; verification requires fresh biometric scan |
| Collusion of verifiers | Deanonymize user | Digests are non-invertible; no personal info shared. Encourage use of differential privacy when aggregating statistics |

## Privacy Features
- Quantization collapses small variations, meaning templates cannot be reverse-engineered to recreate fingerprints reliably.
- Helper data stores only salted HMACs to validate template integrity; no minutiae coordinates are published.
- Wallet metadata does not expose biometric digest unless user explicitly anchors it on-chain.
- Users can keep helper data entirely offline by marking `helperStorage` as `external`, sharing JSON only with trusted verifiers.

## Security Hardening Roadmap
1. Integrate secure enclaves or hardware-backed key stores for enrollment devices.
2. Support threshold cryptography for multi-party biometric escrow (e.g., community guardians).
3. Explore Poseidon or Rescue hash functions for compatibility with zero-knowledge proof systems.
4. Commission third-party audits once code base stabilizes; include fuzz testing and side-channel analysis.

## Compliance Considerations
- No storage of personal identifiers means GDPR/CCPA obligations are limited, but consent logs should be maintained.
- Document data processing agreements for teams offering hosted enrollment services.
- Provide deletion flows: users can overwrite helper data or rotate to new metadata entries whenever desired.

## Incident Response
- Publish vulnerabilities via responsible disclosure channel (PGP key + security.txt).
- Maintain versioned registry of algorithm parameters so wallets can force users to re-enroll if a weakness is found.
- Encourage use of multi-factor controls (e.g., device attestation) alongside biometric digest checks.
