# Plutus Integration for Biometric DID Verification

**Date**: October 17, 2025
**Status**: In Progress

## 1. Introduction
This document outlines the research and design for integrating Plutus V2 smart contracts into the decentralized DID system. The primary goal is to leverage on-chain validation to enhance the security and trustworthiness of biometric identity verification. By moving parts of the verification logic on-chain, we can create a system where third parties can trust a verification result without trusting the entity that performed the verification.

This research explores:
- The capabilities and limitations of Plutus V2.
- A design for validator scripts tailored for biometric digest verification.
- A comparison of off-chain tooling for transaction construction.
- Patterns for submitting proofs to the on-chain validator.
- A preliminary analysis of performance and transaction costs.
- Strategies for handling partial biometric data.

## 2. Plutus V2 Capabilities and Limitations

### 2.1. Capabilities
- **Purely Functional & Deterministic**: Plutus scripts are pure functions, meaning their output depends only on their inputs (Datum, Redeemer, ScriptContext). This guarantees predictable execution.
- **Strongly Typed**: Plutus is based on Haskell, providing strong static typing which catches many errors at compile time.
- **Formal Verification-Friendly**: The deterministic and functional nature of Plutus makes it amenable to formal verification, increasing security assurance.
- **Access to Transaction Context**: The `ScriptContext` provides comprehensive information about the transaction being validated, including inputs, outputs, signatories, and validity intervals. This allows for complex validation logic.
- **Turing-Complete (with limits)**: Plutus V2 is effectively Turing-complete, but execution is bounded by strict CPU and memory limits to prevent denial-of-service attacks.

### 2.2. Limitations
- **Execution Limits (ExUnits)**: Scripts are constrained by maximum execution units (CPU and memory). Complex computations, like hashing or signature verification, must be highly optimized.
- **No Direct World State Access**: Plutus scripts cannot directly access blockchain state beyond the inputs of the transaction they are validating. All necessary state must be provided in the transaction via datums or read from inputs.
- **On-Chain Code is Public**: All validator logic is public, meaning any vulnerabilities can be seen and potentially exploited by anyone.
- **Limited Cryptographic Primitives**: Plutus has a limited set of built-in cryptographic functions. While essential primitives like SHA-256, SHA-3, Blake2b, and Ed25519 signature verification are available, more complex schemes must be implemented from scratch, which is often infeasible due to ExUnit limits.

## 3. Validator Script Design for Biometric Verification

The core idea is to create a validator script that locks a "proof-of-identity" NFT. This NFT can only be spent if the transaction provides a valid biometric proof in the redeemer.

### 3.1. Datum
The datum associated with the UTxO containing the NFT will store the biometric digest (the master key derived from the user's fingerprints).

```haskell
-- Datum for the biometric validator
data BiometricDatum = BiometricDatum
    { bdDigest :: BuiltinByteString -- The 256-bit biometric digest
    }
```

### 3.2. Redeemer
The redeemer will contain the proof provided by the user attempting to verify their identity. This would include the raw biometric data (or a subset) and any necessary salts or parameters.

```haskell
-- Redeemer for the biometric validator
data BiometricRedeemer = BiometricRedeemer
    { brRawData     :: BuiltinByteString -- The new biometric data to be verified
    , brSalt        :: BuiltinByteString -- Salt used during key derivation
    }
```

### 3.3. Validator Logic
The validator script will perform the following steps:
1.  Take the `brRawData` and `brSalt` from the redeemer.
2.  Re-run the fuzzy extractor logic *on-chain* to generate a digest.
3.  Compare the generated digest with the `bdDigest` stored in the datum.
4.  If the digests match, the validation succeeds, and the transaction is approved.

**Challenge**: The full fuzzy extractor logic is likely too computationally expensive to run on-chain within Plutus ExUnit limits. A more practical approach is needed.

### 3.4. Practical Validator Design: Off-Chain Computation, On-Chain Verification
A more feasible design is to perform the heavy computation off-chain and use the Plutus script for a much simpler verification step.

1.  **Off-Chain**: The user generates a proof. This could be a signature from a key derived from their biometrics.
2.  **On-Chain Datum**: The datum stores the public key corresponding to the biometric private key.
3.  **On-Chain Redeemer**: The redeemer contains a message and the signature.
4.  **Validator Logic**: The script uses `verifyEd25519Signature` to check if the signature is valid for the public key in the datum and the message in the redeemer. This is highly efficient.

## 4. Off-Chain Code Patterns

To interact with Plutus scripts, off-chain code must build and submit transactions. Several tools are available:

- **Cardano Transaction Lib (CTL)**: A PureScript library for building transactions. It's powerful but requires a PureScript development environment.
- **Lucid**: A JavaScript/TypeScript library that provides a friendly, high-level API for transaction building. It's designed for web and Node.js applications, making it a good fit for our demo wallet.
- **PlutusTx**: The Python-based framework for writing Plutus scripts. While its primary use is for generating the on-chain code, it does not provide extensive off-chain tooling for transaction building.
- **PyCardano**: The Python library we are already using. It has low-level support for building transactions with Plutus scripts, datums, and redeemers. This is the most direct fit for our existing Python-based CLI and backend.

**Recommendation**: Use **PyCardano** for the backend/CLI tooling to maintain consistency. Use **Lucid** for the demo wallet for its web-native design.

## 5. Proof Submission Patterns

The pattern for submitting a proof to the validator would be:
1.  The user's wallet identifies the UTxO locked by the biometric validator script.
2.  The off-chain code (in the wallet or on a server) constructs the redeemer, which contains the proof.
3.  A transaction is built that consumes the locked UTxO and includes the validator script, the datum (or a reference to it), and the redeemer.
4.  The transaction is signed by the user and submitted to the network.
5.  A Cardano node executes the validator script with the provided datum and redeemer to check if the transaction is valid.

## 6. Performance and Cost Analysis

On-chain verification incurs costs in the form of transaction fees, which are determined by transaction size and script execution units (ExUnits).

- **Transaction Size**: A transaction involving a Plutus script is larger than a simple payment because it must include the script itself (or a reference), datum, and redeemer.
- **Execution Units (ExUnits)**:
    - **CPU**: The computational steps a script performs.
    - **Memory**: The amount of memory the script uses.
- **Cost of `verifyEd25519Signature`**: This built-in function is highly optimized. The cost is fixed and relatively low, making the "Off-Chain Computation, On-Chain Verification" design very efficient.
- **Estimated Cost**: A verification transaction would likely cost between **0.5 and 1.5 ADA**, depending on network parameters and the complexity of the overall transaction. This is acceptable for high-value interactions but may be too expensive for frequent, low-value ones.

## 7. Partial Verification Strategies

The on-chain validator could be designed to handle partial data, for example, verifying with 3 out of 4 fingerprints.

- **Multiple Datums**: One approach is to have different validator scripts or datums for different numbers of fingers (e.g., a 4-finger datum, a 3-finger datum). This adds complexity.
- **Merkle Trees**: A more elegant solution is to store a Merkle root of all individual finger digests in the datum. The redeemer would then provide one of the digests and a Merkle proof. The validator would verify the proof against the root. This allows verification with any single finger while keeping the on-chain data minimal. This is a promising avenue for future development.

## 8. Conclusion and Recommendations

Direct on-chain execution of the fuzzy extractor logic is likely infeasible due to computational limits.

The recommended approach is a hybrid model:
1.  **Perform heavy biometric processing off-chain** to derive a private/public key pair.
2.  **Store the public key on-chain** in the datum of a Plutus validator script.
3.  **Use the Plutus script to verify a signature** created with the biometric private key.

This approach is secure, efficient, and leverages the strengths of both off-chain computation and on-chain validation.

**Next Steps**:
- Develop a prototype of the signature-based Plutus validator.
- Implement the off-chain logic in PyCardano to generate the key pair and build the verification transaction.
- Integrate this flow into the CLI and the demo wallet.
- Benchmark the end-to-end performance and cost on the pre-production testnet.
