# Pitch Outline

## 1. Hook (30s)
- Start with a story: decentralized finance lacks a way to trust the human without exposing identity.
- Highlight Cardano's mission for inclusive accountability.

## 2. Problem (45s)
- Anonymous wallets are powerful but enable Sybil attacks and fraud.
- Centralized KYC undermines decentralization and excludes the unbanked.
- Biometrics are typically privacy nightmares when stored centrally.

## 3. Solution (60s)
- Ten-finger biometric digest, hashed and anonymized, anchored to a Cardano wallet.
- Helper data stays with the user; verifiers only need the digest and wallet signature.
- Fully open-source toolkit: CLI, library, docs, governance plan.

## 4. Architecture (60s)
- Walk through capture → quantization → fuzzy extractor → aggregation → DID generation.
- Mention cryptographic choices (BLAKE2b, salted HMACs) and Cardano metadata integration.
- Emphasize external helper storage flexibility (IPFS, vaults).

## 5. Demo (90s)
- Live CLI enrollment using synthetic or hardware data.
- Show metadata JSON and DID string.
- Run verification with and without inline helper data.

## 6. Impact & Differentiation (45s)
- Anonymous yet accountable interactions (voting, SSI, DeFi access control).
- Cardano-native and governance-first approach.
- Extensible roadmap: ZK proofs, CIP-68 assets, secure hardware support.

## 7. Ask & Next Steps (30s)
- Request mentorship, wallet integration partners, and feedback on governance model.
- Outline immediate roadmap items (CIP draft, hardware pilots, audit prep).

## 8. Q&A Prep
- Privacy and regulatory implications.
- False positive/negative handling.
- Recovery and rotation flows for biometric data.
- Attack surfaces (helper data leakage, template inversion attempts).
