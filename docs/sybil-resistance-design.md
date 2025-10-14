# Sybil Resistance & Deterministic DID Generation

**Problem**: Preventing users from creating multiple DIDs with the same biometric data across different wallets.

**Solution**: Generate DID deterministically from biometric commitment, allowing the same DID to be controlled by multiple wallets.

---

## Table of Contents

1. [The Sybil Attack Problem](#the-sybil-attack-problem)
2. [Why Current Approach is Vulnerable](#why-current-approach-is-vulnerable)
3. [Deterministic DID Generation](#deterministic-did-generation)
4. [Multi-Wallet Controller Model](#multi-wallet-controller-model)
5. [Implementation Details](#implementation-details)
6. [Security Analysis](#security-analysis)
7. [Privacy Considerations](#privacy-considerations)
8. [Comparison with Alternative Approaches](#comparison-with-alternative-approaches)
9. [Migration Strategy](#migration-strategy)
10. [W3C DID Compliance](#w3c-did-compliance)

---

## The Sybil Attack Problem

### Attack Scenario

**Without Sybil resistance**:
```
User Alice:
1. Enrolls fingerprints with Wallet A → did:cardano:mainnet:random1
2. Enrolls SAME fingerprints with Wallet B → did:cardano:mainnet:random2
3. Enrolls SAME fingerprints with Wallet C → did:cardano:mainnet:random3

Result: Alice has 3 separate identities
```

### Why This Breaks Identity Systems

| Use Case | Impact of Sybil Attack |
|----------|------------------------|
| **Voting** | One person votes multiple times |
| **Airdrops** | One person claims multiple times |
| **KYC/AML** | Bypass restrictions with new wallet |
| **Reputation** | Escape bad reputation, start fresh |
| **Access Control** | Circumvent bans/blocks |
| **Quadratic Funding** | Game the system for more funding |
| **Social Networks** | Create fake followers/endorsements |

**Critical**: This undermines the entire purpose of decentralized identity!

---

## Why Current Approach is Vulnerable

### Current Implementation (Phase 4 Task 2)

```python
# Current: DID is random or wallet-derived
did_id = f"did:cardano:testnet:sample{random_suffix}"

# Problem: No link to biometric data
# Same fingerprints → Different DIDs (if random)
```

**Vulnerability**:
- DID generation independent of biometric data
- No global registry checking for duplicate enrollments
- User can create unlimited DIDs with same fingerprints
- Each wallet can create separate identity

---

## Deterministic DID Generation

### Core Principle

**Same Biometrics → Same DID (Always)**

```
DID Identifier = Hash(Biometric Commitment)
```

### Mathematical Foundation

```python
# Step 1: Fuzzy commitment extraction (already implemented)
commitment = fuzzy_commitment(fingerprint_templates)
# commitment is stable for same fingerprints (±error correction)

# Step 2: Deterministic hash
did_hash = blake2b(commitment, digest_size=32)
did_id = base58.encode(did_hash)

# Step 3: Construct DID
did = f"did:cardano:mainnet:{did_id}"
```

### Key Properties

✅ **Deterministic**: Same fingerprints → Same DID
✅ **Collision-resistant**: Different fingerprints → Different DIDs (cryptographic hash)
✅ **Privacy-preserving**: DID reveals nothing about biometric data
✅ **Wallet-agnostic**: DID independent of blockchain address
✅ **Self-sovereign**: User controls DID via biometrics, not just wallet keys

---

## Multi-Wallet Controller Model

### Concept

**One DID, Multiple Controllers**

```
Person (Biometrics) → DID
           ↓
    Controlled by Multiple Wallets
           ↓
    [Wallet A, Wallet B, Wallet C, ...]
```

### DID Document Structure

```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:cardano:mainnet:zQmXyZ...",

  "controller": [
    "did:cardano:mainnet:zQmXyZ...",
    "addr1qx8z3...",  // Wallet A (primary)
    "addr1qy9a4...",  // Wallet B (backup)
    "addr1qz1b5..."   // Wallet C (recovery)
  ],

  "verificationMethod": [
    {
      "id": "did:cardano:mainnet:zQmXyZ...#biometric-1",
      "type": "BiometricVerificationMethod2024",
      "controller": "did:cardano:mainnet:zQmXyZ...",
      "biometricCommitment": "0x1a2b3c..."
    },
    {
      "id": "did:cardano:mainnet:zQmXyZ...#wallet-a",
      "type": "Ed25519VerificationKey2020",
      "controller": "addr1qx8z3...",
      "publicKeyMultibase": "zH3C2..."
    }
  ],

  "authentication": [
    "did:cardano:mainnet:zQmXyZ...#biometric-1",
    "did:cardano:mainnet:zQmXyZ...#wallet-a"
  ]
}
```

### Controller Management

#### Adding a New Wallet

```
Prerequisites:
- Must prove biometric ownership (scan fingerprints)
- OR sign with existing controller wallet

Transaction:
1. Create update transaction
2. Sign with existing wallet OR prove biometric
3. Add new wallet address to controller list
4. Submit to blockchain
```

#### Removing a Wallet (Revocation)

```
Use Cases:
- Wallet compromised
- Wallet lost
- Device stolen

Process:
1. Sign removal transaction with OTHER wallet
2. Update controller list (remove address)
3. Optionally add new wallet simultaneously
```

#### Recovery Scenario

```
Problem: All wallets lost/compromised

Solution:
1. Re-enroll fingerprints (same biometric data)
2. System computes DID (deterministic)
3. Finds existing DID on blockchain
4. User proves biometric ownership
5. Add new wallet as controller
6. Remove compromised wallets
```

---

## Implementation Details

### Phase 1: Generate Deterministic DID

**File**: `src/decentralized_did/did/generator.py`

```python
from hashlib import blake2b
import base58

def generate_deterministic_did(
    commitment: bytes,
    network: str = "mainnet"
) -> str:
    """
    Generate deterministic DID from biometric commitment.

    Args:
        commitment: Fuzzy commitment bytes (stable representation)
        network: "mainnet" or "testnet"

    Returns:
        DID string: did:cardano:{network}:{hash}
    """
    # Hash the commitment (32-byte output)
    did_hash = blake2b(commitment, digest_size=32).digest()

    # Base58 encode (human-readable)
    did_id = base58.b58encode(did_hash).decode('ascii')

    # Construct DID
    did = f"did:cardano:{network}:{did_id}"

    return did
```

### Phase 2: Multi-Controller Storage

**On-chain storage** (Transaction Metadata):

```json
{
  "674": {
    "version": "1.0",
    "did": "did:cardano:mainnet:zQmXyZ...",
    "controllers": [
      "addr1qx8z3...",  // Wallet addresses
      "addr1qy9a4..."
    ],
    "biometricCommitment": "0x1a2b3c...",
    "helperData": "...",
    "timestamp": "2025-10-14T16:00:00Z",
    "updateType": "enrollment"  // or "add_controller", "remove_controller"
  }
}
```

### Phase 3: DID Resolution

**Query Process**:

```python
def resolve_did(did: str) -> DIDDocument:
    """
    Resolve DID to latest document by querying blockchain.

    Process:
    1. Search for transactions with metadata label 674
    2. Filter by DID identifier
    3. Reconstruct DID document from metadata history
    4. Apply updates chronologically
    5. Return current state
    """
    # Query all transactions for this DID
    txs = query_transactions_by_did(did)

    # Sort by block height (chronological)
    txs.sort(key=lambda tx: tx.block_height)

    # Start with initial enrollment
    doc = create_initial_document(txs[0])

    # Apply updates
    for tx in txs[1:]:
        metadata = tx.metadata["674"]

        if metadata["updateType"] == "add_controller":
            doc.controllers.append(metadata["newController"])
        elif metadata["updateType"] == "remove_controller":
            doc.controllers.remove(metadata["removedController"])

    return doc
```

### Phase 4: On-Chain DID Registry (Optional)

For faster lookups, we can create a **reference NFT** (CIP-68):

```
Policy ID: Unique per DID
Asset Name: DID hash
Datum: Latest DID document CBOR
Metadata: Controller list
```

**Benefits**:
- O(1) lookup (query by policy + asset)
- No need to scan all transactions
- Datum can be updated (mutable NFT)
- NFT ownership = proof of DID control

**Trade-offs**:
- Costs ~2 ADA per DID (min UTXO)
- More complex implementation
- Requires Plutus smart contract

---

## Security Analysis

### Threat Model

| Attack | Defense | Status |
|--------|---------|--------|
| **Create multiple DIDs with same fingerprints** | Deterministic generation | ✅ Prevented |
| **Steal DID by stealing wallet** | Multi-controller model | ✅ Mitigated (use other wallet) |
| **Reconstruct fingerprints from DID** | One-way cryptographic hash | ✅ Prevented |
| **Link DID to transactions** | Separate DID from wallet address | ⚠️ Metadata still on-chain |
| **Forge biometric proof** | Zero-knowledge proof required | 🔄 Phase 6 |
| **Replay old DID state** | Block height ordering | ✅ Prevented |
| **Front-run enrollment** | No value in front-running DID creation | ✅ Not applicable |

### Attack Scenario 1: Attempt Multiple DIDs

```
Attacker Strategy:
1. Enroll fingerprints with Wallet A
2. Try to enroll SAME fingerprints with Wallet B

System Response:
1. Compute DID from fingerprints → did:cardano:mainnet:abc123
2. Query blockchain for existing DID abc123
3. Found! DID already exists
4. Options:
   a. Reject (if policy is 1 DID per biometric)
   b. Add Wallet B as additional controller (if multi-wallet allowed)

Result: Cannot create separate identity ✅
```

### Attack Scenario 2: Wallet Compromise

```
Attacker Strategy:
1. Steal Wallet A private key
2. Try to control Alice's DID

Alice's Response:
1. Use Wallet B (backup) to sign removal transaction
2. Remove Wallet A from controller list
3. Add new Wallet C (fresh keys)

Result: Attacker loses access, Alice retains control ✅
```

### Attack Scenario 3: All Wallets Lost

```
Problem:
- All wallet private keys lost
- No way to sign transactions

Recovery Process:
1. Re-scan fingerprints (same biometric data)
2. System computes DID → did:cardano:mainnet:abc123 (same as before)
3. System finds existing DID on blockchain
4. User proves biometric ownership (ZK proof or trusted enrollment)
5. Add new wallet as controller
6. Remove old wallets

Challenge: How to prove biometric ownership without existing controller?
Solutions:
- Trusted enrollment service (with legal agreements)
- Social recovery (N-of-M other DIDs vouch)
- Time-locked recovery mechanism
```

---

## Privacy Considerations

### What's Public on Blockchain

| Data | Visibility | Privacy Risk |
|------|-----------|--------------|
| **DID Hash** | Public | Low (cryptographic hash, no biometric info) |
| **Controller Wallets** | Public | Medium (links wallet to DID) |
| **Transaction History** | Public | High (all DID updates visible) |
| **Biometric Commitment** | Public | Low (fuzzy, cannot reconstruct) |
| **Helper Data** | Public | Low (useless without fingerprints) |

### Privacy Enhancements

#### 1. Stealth Addresses (Future)

```
Instead of:
  "controller": ["addr1qx8z3..."]

Use:
  "controller": ["stealth_addr_generated_per_tx"]
```

**Benefit**: Cannot link all transactions to same wallet

#### 2. Off-Chain Storage (IPFS)

```json
{
  "674": {
    "did": "did:cardano:mainnet:abc123",
    "documentURI": "ipfs://Qm...",  // DID document stored off-chain
    "documentHash": "0x1a2b..."     // Integrity proof
  }
}
```

**Benefit**: Reduces on-chain data, improves privacy

#### 3. Zero-Knowledge Controller Proofs

```
Prove: "I control this DID"
Without revealing: Which wallet address I'm using

Implementation: ZK-SNARK with wallet key as witness
```

---

## Comparison with Alternative Approaches

### Approach 1: Deterministic DID (Recommended)

✅ **Pros**:
- Simple to implement
- No global registry queries needed
- Supports multi-wallet use case
- Privacy-preserving (DID is just hash)
- Enables biometric recovery

❌ **Cons**:
- All DID history public on blockchain
- Cannot prevent wallet linking via transaction analysis

**Verdict**: Best balance of simplicity, security, and privacy

---

### Approach 2: Global Registry with Privacy

**Concept**: Store biometric commitment hashes in smart contract, check for duplicates before enrollment.

```solidity
// Plutus pseudocode
contract DIDRegistry {
    mapping(bytes32 => address) commitmentToOwner;

    function enroll(bytes32 commitment) {
        require(commitmentToOwner[commitment] == 0, "Already enrolled");
        commitmentToOwner[commitment] = msg.sender;
    }
}
```

✅ **Pros**:
- Explicit duplicate prevention
- Can enforce single-wallet-per-DID policy
- Clear ownership model

❌ **Cons**:
- Smart contract complexity
- Gas costs for every lookup
- Global state bloat (all commitments forever)
- Privacy risk: Can track enrollment attempts
- Doesn't support multi-wallet recovery

**Verdict**: More complex, no clear advantages over deterministic approach

---

### Approach 3: Zero-Knowledge Set Non-Membership Proof

**Concept**: Prove "my fingerprints have NOT been enrolled before" without revealing them.

```
Technology: ZK-SNARKs with set membership proofs
```

✅ **Pros**:
- Maximum privacy (no biometric data on-chain)
- Cryptographically enforced uniqueness
- No linkability between enrollments

❌ **Cons**:
- Extremely complex implementation
- High computational cost (minutes per proof)
- Requires trusted setup (circuit-specific)
- Difficult to support multi-wallet recovery
- No existing libraries for Cardano

**Verdict**: Too complex for current phase, revisit in Phase 6

---

### Approach 4: Hybrid (Deterministic + ZK)

**Concept**: Deterministic DID (Phase 4), add ZK proofs later (Phase 6).

```
Phase 4-5: Use deterministic DID (functional)
Phase 6: Add ZK proofs for privacy
```

✅ **Pros**:
- Incremental implementation
- Can deploy basic system now
- Upgrade privacy later
- Backward compatible

❌ **Cons**:
- Migration complexity
- Two security models to maintain

**Verdict**: Recommended implementation path

---

## Migration Strategy

### Current System (Phase 4 Complete)

```python
# Current: Random DID
did = "did:cardano:testnet:sample123"
```

### Phase 4.5: Add Deterministic Generation

**Step 1**: Update DID generator
```python
# New: Deterministic DID
commitment = fuzzy_commitment(templates)
did = generate_deterministic_did(commitment)
```

**Step 2**: Backward compatibility
```python
def generate_did(templates, mode="deterministic"):
    if mode == "deterministic":
        return generate_deterministic_did(commitment)
    elif mode == "random":
        return f"did:cardano:testnet:sample{random()}"
```

**Step 3**: Update enrollment flow
```python
# Before enrollment, check if DID exists
existing_did = query_blockchain(did)

if existing_did:
    # Option A: Reject duplicate
    raise DuplicateEnrollmentError(did)

    # Option B: Add as new controller
    add_controller(did, new_wallet_address)
```

### Phase 4.6: Multi-Controller Support

**Step 1**: Update metadata schema
```json
{
  "674": {
    "version": "1.1",  // Increment version
    "controllers": ["addr1...", "addr2..."],  // New field
    "updateType": "add_controller"  // New field
  }
}
```

**Step 2**: Implement controller management
```python
def add_controller(did, new_address, signer_address):
    # Verify signer is current controller
    doc = resolve_did(did)
    if signer_address not in doc.controllers:
        raise UnauthorizedError()

    # Create update transaction
    metadata = {
        "674": {
            "version": "1.1",
            "did": did,
            "updateType": "add_controller",
            "newController": new_address
        }
    }

    # Sign and submit
    tx = build_transaction(metadata)
    tx.sign(signer_key)
    submit(tx)
```

### Phase 4.7: DID Resolution Service

**Step 1**: Index existing DIDs
```python
# Scan blockchain for metadata label 674
all_dids = scan_blockchain(label=674)

# Build index: DID → [tx1, tx2, ...]
did_index = {}
for tx in all_dids:
    did = tx.metadata["674"]["did"]
    did_index.setdefault(did, []).append(tx)
```

**Step 2**: Implement resolver
```python
@app.get("/resolve/{did}")
def resolve(did: str):
    # Get transaction history
    txs = did_index.get(did, [])

    # Reconstruct document
    doc = reconstruct_did_document(txs)

    return doc
```

---

## W3C DID Compliance

### DID Method Specification

**Method Name**: `cardano`

**Method-Specific Identifier**: Base58-encoded BLAKE2b-256 hash of biometric commitment

**DID Format**:
```
did:cardano:<network>:<base58-identifier>

Examples:
- did:cardano:mainnet:zQmXyZ1a2B3c4D5e6F7g8H
- did:cardano:testnet:zQmAbC9dEfGh8IjKlMn2Op3
```

### W3C DID Core Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Decentralization** | ✅ | No central authority, blockchain-based |
| **Control** | ✅ | User controls via biometrics + wallet keys |
| **Privacy** | ✅ | Biometric data never leaves device |
| **Security** | ✅ | Cryptographic proofs, multi-controller model |
| **Proof-based** | ✅ | Digital signatures, biometric verification |
| **Discoverability** | ✅ | On-chain metadata, resolver service |
| **Interoperability** | ✅ | Standard DID format, JSON-LD |
| **Portability** | ✅ | Export/import DID documents |
| **Simplicity** | ✅ | Human-readable format |
| **Extensibility** | ✅ | Additional verification methods supported |

### DID Document Example (W3C Compliant)

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1",
    "https://identity.foundation/biometric-verification/v1"
  ],
  "id": "did:cardano:mainnet:zQmXyZ1a2B3c4D5e6F7g8H",
  "controller": [
    "did:cardano:mainnet:zQmXyZ1a2B3c4D5e6F7g8H",
    "addr1qx8z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0",
    "addr1qy9a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1"
  ],
  "verificationMethod": [
    {
      "id": "did:cardano:mainnet:zQmXyZ...#biometric-1",
      "type": "BiometricVerificationMethod2024",
      "controller": "did:cardano:mainnet:zQmXyZ...",
      "biometricCommitment": "0x1a2b3c4d...",
      "helperData": "0x5e6f7g8h...",
      "captureDevice": {
        "make": "ZKTeco",
        "model": "ZK9500",
        "serialNumber": "SN123456"
      }
    },
    {
      "id": "did:cardano:mainnet:zQmXyZ...#wallet-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "addr1qx8z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0",
      "publicKeyMultibase": "zH3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV"
    }
  ],
  "authentication": [
    "did:cardano:mainnet:zQmXyZ...#biometric-1",
    "did:cardano:mainnet:zQmXyZ...#wallet-1"
  ],
  "assertionMethod": [
    "did:cardano:mainnet:zQmXyZ...#biometric-1"
  ],
  "created": "2025-10-14T16:00:00Z",
  "updated": "2025-10-14T18:30:00Z",
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2025-10-14T16:00:00Z",
    "verificationMethod": "did:cardano:mainnet:zQmXyZ...#wallet-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z5CwPpSP8..."
  }
}
```

---

## Implementation Roadmap

### Phase 4.5 (Current Priority)

**Goal**: Add deterministic DID generation

- [ ] **Task 1**: Implement `generate_deterministic_did()`
- [ ] **Task 2**: Update enrollment flow to use deterministic DIDs
- [ ] **Task 3**: Add duplicate detection (query blockchain for existing DID)
- [ ] **Task 4**: Write tests for deterministic generation
- [ ] **Task 5**: Deploy to testnet with deterministic DIDs
- [ ] **Task 6**: Update documentation

**Estimated Time**: 1-2 weeks

---

### Phase 4.6 (Next Sprint)

**Goal**: Multi-controller support

- [ ] **Task 1**: Update metadata schema (version 1.1)
- [ ] **Task 2**: Implement `add_controller()` function
- [ ] **Task 3**: Implement `remove_controller()` function
- [ ] **Task 4**: Build DID resolver (reconstruct from tx history)
- [ ] **Task 5**: Add controller management UI
- [ ] **Task 6**: Write integration tests
- [ ] **Task 7**: Deploy multi-controller demo to testnet

**Estimated Time**: 2-3 weeks

---

### Phase 4.7 (Future)

**Goal**: DID resolution service

- [ ] **Task 1**: Build blockchain indexer (scan for label 674)
- [ ] **Task 2**: Implement REST API for DID resolution
- [ ] **Task 3**: Add caching layer (Redis)
- [ ] **Task 4**: Deploy public resolver service
- [ ] **Task 5**: Publish DID method specification
- [ ] **Task 6**: Register with W3C DID registry

**Estimated Time**: 3-4 weeks

---

## Conclusion

### Summary

**Problem**: Users can create multiple DIDs with same fingerprints across different wallets.

**Solution**: Deterministic DID generation from biometric commitment.

**Key Insight**: The same person SHOULD have the same DID across all wallets. What changes is which wallets control that DID.

### Benefits

✅ **Sybil Resistance**: One person = One DID (cryptographically enforced)
✅ **Multi-Wallet Support**: Legitimate use case (multiple devices, backup)
✅ **Recovery**: Lost wallet? Re-enroll fingerprints, recover DID
✅ **Privacy**: DID reveals nothing about biometrics
✅ **Simplicity**: No global registry, no complex ZK proofs (yet)
✅ **W3C Compliant**: Standard DID format and resolution
✅ **Open Source**: All components Apache 2.0 / MIT licensed

### Next Steps

1. ✅ Document approach (this file)
2. 🔄 Implement deterministic DID generation (Phase 4.5)
3. 🔄 Add multi-controller support (Phase 4.6)
4. 🔄 Build DID resolver service (Phase 4.7)
5. ⏳ Add zero-knowledge proofs for privacy (Phase 6)

---

## References

- [W3C DID Core Specification](https://www.w3.org/TR/did-core/)
- [W3C DID Method Registry](https://w3c.github.io/did-spec-registries/)
- [CIP-20: Transaction Message/Comment Metadata](https://cips.cardano.org/cip/CIP-20)
- [CIP-68: Datum Metadata Standard](https://cips.cardano.org/cip/CIP-68)
- [Cardano Foundation: Identity Solutions](https://cardanofoundation.org/en/news/digital-identity-on-cardano/)
- [Fuzzy Extractors (Dodis et al.)](https://eprint.iacr.org/2003/235)
- [BLAKE2b Hash Function](https://www.blake2.net/)
- [Base58 Encoding](https://en.bitcoin.it/wiki/Base58Check_encoding)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Author**: Decentralized DID Team
**License**: Apache 2.0 (this documentation)
