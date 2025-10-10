# DID Method Specification: `did:cardano`

**PROJECT CONSTRAINT**: This design uses **ONLY OPEN-SOURCE** technologies (Apache 2.0, MIT, BSD, GPL, LGPL). No paid services, commercial APIs, or proprietary protocols.

**Document Version**: 1.0
**Last Updated**: October 10, 2025
**Status**: Phase 1, Task 4 - Architecture Design
**Related Documents**:
- `docs/design/quantization-algorithm.md` (biometric processing)
- `docs/design/fuzzy-extractor-spec.md` (key derivation)
- `docs/design/aggregation-scheme.md` (multi-finger keys)
- W3C DID Core Specification v1.0
- CIP-68 (Cardano NFT metadata standard)

---

## Executive Summary

This document specifies the **`did:cardano` method** for decentralized identifiers anchored on the Cardano blockchain, with biometric keys derived from fingerprint scans.

**Core Design Principles**:
- **Decentralization**: No trusted third parties (TTP)
- **Persistence**: DIDs survive beyond issuer lifetimes
- **Cryptographic Verifiability**: All operations use on-chain proofs
- **Privacy**: Biometric templates never leave user devices
- **Open Standards**: W3C DID Core + CIP-68 compliance

**DID Format**:
```
did:cardano:<network>:<policy_id>
```

**Example**:
```
did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a
```

**Key Properties**:
- **Resolution**: On-chain (Cardano UTxO query)
- **Updates**: Plutus smart contract validation
- **Helper Data**: Hybrid storage (on-chain metadata + IPFS)
- **Revocation**: Time-locked burn transactions
- **Cost**: ~2 ADA per DID lifecycle (creation + updates)

---

## 1. DID Syntax

### 1.1 Method Name

**Method**: `cardano`

**Namespace**: Cardano blockchain network

**Rationale**: Clear association with Cardano ecosystem, aligns with existing conventions (`did:ethr`, `did:btc`).

### 1.2 Method-Specific Identifier

**ABNF Grammar** (RFC 5234):
```abnf
did-cardano        = "did:cardano:" network ":" policy-id
network            = "mainnet" / "preprod" / "preview" / "testnet"
policy-id          = 56*56(HEXDIG)  ; 56 hex characters (28 bytes)
HEXDIG             = "0" / "1" / ... / "9" / "a" / "b" / ... / "f"
```

**Components**:

1. **Network Identifier**:
   - `mainnet`: Cardano production network
   - `preprod`: Long-lived testnet (stable for development)
   - `preview`: Short-lived testnet (protocol upgrades)
   - `testnet`: Legacy testnet (deprecated)

2. **Policy ID**:
   - 28-byte (224-bit) hash of minting policy script
   - Derived from Plutus validator hash
   - Format: lowercase hexadecimal (56 characters)
   - Uniquely identifies DID within network

**Example DIDs**:
```
did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a
did:cardano:preprod:a1b2c3d4e5f6789012345678901234567890abcdefabcdefabcdef01
```

### 1.3 DID Uniqueness

**Guarantee**: Policy ID uniqueness enforced by Cardano ledger.

**Mechanism**:
1. Policy script includes user's public key hash
2. Cardano prevents duplicate policy IDs (cryptographic collision resistance)
3. One DID per policy ID per network

**Collision Probability**:
```
P(collision) ≈ q^2 / (2 × 2^224)

For q = 10^9 DIDs:
P(collision) ≈ 10^18 / 2^225 ≈ 2^(-165) (negligible)
```

---

## 2. DID Document Structure

### 2.1 Core DID Document

**Minimal DID Document** (on-chain representation):

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1"
  ],
  "id": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",
  "controller": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",
  "verificationMethod": [
    {
      "id": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",
      "publicKeyMultibase": "z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"
    }
  ],
  "authentication": [
    "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1"
  ],
  "assertionMethod": [
    "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1"
  ],
  "created": "2025-10-10T12:00:00Z",
  "updated": "2025-10-10T12:00:00Z",
  "proof": {
    "type": "CardanoSignature2025",
    "created": "2025-10-10T12:00:00Z",
    "verificationMethod": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1",
    "proofPurpose": "assertionMethod",
    "cardanoTxHash": "a1b2c3d4e5f6789012345678901234567890abcdefabcdefabcdefabcdef0123"
  }
}
```

**Key Fields**:

| Field | Description | W3C Required | Cardano-Specific |
|-------|-------------|--------------|------------------|
| `@context` | JSON-LD context | ✅ Yes | Standard |
| `id` | DID identifier | ✅ Yes | `did:cardano:...` |
| `controller` | Self-sovereign by default | No (recommended) | Self-referential |
| `verificationMethod` | Ed25519 public key | ✅ Yes | Derived from biometric key |
| `authentication` | Authentication capability | No (recommended) | Links to verification method |
| `assertionMethod` | Assertion capability | No | For signing credentials |
| `created` | Creation timestamp | No | ISO 8601 UTC |
| `updated` | Last update timestamp | No | ISO 8601 UTC |
| `proof` | Cardano transaction proof | No | On-chain anchoring |

### 2.2 Extended DID Document (with Helper Data)

**Full DID Document** (with biometric metadata):

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://w3id.org/security/suites/ed25519-2020/v1",
    "https://decentralized-did.github.io/context/biometric/v1"
  ],
  "id": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",
  "controller": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",

  "verificationMethod": [
    {
      "id": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",
      "publicKeyMultibase": "z6MkpTHR8VNsBxYAAWHut2Geadd9jSwuBV8xRoAnwWsdvktH"
    }
  ],

  "authentication": [
    "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1"
  ],

  "assertionMethod": [
    "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1"
  ],

  "biometricMetadata": {
    "type": "BiometricHelperData",
    "version": "1.0",
    "algorithm": "fuzzy-extractor-bch127-blake2b",
    "fingers": 4,
    "helperDataRefs": [
      {
        "fingerId": 0,
        "uri": "ipfs://Qmb1Z2Y3X4W5V6U7T8S9R0Q1P2O3N4M5L6K7J8I9H0G1F2E3D4",
        "hash": "blake2b-256:a1b2c3d4e5f6...",
        "size": 113
      },
      {
        "fingerId": 1,
        "uri": "ipfs://Qmc2A3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W",
        "hash": "blake2b-256:b2c3d4e5f6a1...",
        "size": 113
      },
      {
        "fingerId": 2,
        "uri": "ipfs://Qmd3B4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W5X",
        "hash": "blake2b-256:c3d4e5f6a1b2...",
        "size": 113
      },
      {
        "fingerId": 3,
        "uri": "ipfs://Qme4C5D6E7F8G9H0I1J2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6Y",
        "hash": "blake2b-256:d4e5f6a1b2c3...",
        "size": 113
      }
    ],
    "aggregationMethod": "xor",
    "minFingers": 2,
    "fallbackQualityThreshold": 70
  },

  "serviceEndpoint": [
    {
      "id": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#ipfs-gateway",
      "type": "IPFSGateway",
      "serviceEndpoint": "https://ipfs.io/ipfs/"
    }
  ],

  "created": "2025-10-10T12:00:00Z",
  "updated": "2025-10-10T12:00:00Z",

  "proof": {
    "type": "CardanoSignature2025",
    "created": "2025-10-10T12:00:00Z",
    "verificationMethod": "did:cardano:mainnet:f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a#key-1",
    "proofPurpose": "assertionMethod",
    "cardanoTxHash": "a1b2c3d4e5f6789012345678901234567890abcdefabcdefabcdefabcdef0123",
    "cardanoSlot": 123456789,
    "cardanoEpoch": 450
  }
}
```

**Size Analysis**:
- **Minimal Document**: ~600 bytes (on-chain)
- **Extended Document**: ~1,200 bytes (on-chain metadata + IPFS refs)
- **Helper Data**: 4 × 113 bytes = 452 bytes (IPFS only)

---

## 3. Helper Data Storage Options

### 3.1 Storage Strategy Comparison

| Strategy | On-Chain Size | IPFS Size | Cost | Privacy | Availability |
|----------|---------------|-----------|------|---------|--------------|
| **Inline** | ~1,650 bytes | 0 bytes | ~3 ADA | Low (public) | High (permanent) |
| **External** | ~800 bytes | 452 bytes | ~1.5 ADA | Medium (hashed) | Medium (pinning) |
| **Hybrid** | ~1,200 bytes | 452 bytes | ~2 ADA | Medium | High |

**Selected: Hybrid (Recommended)**

**Rationale**:
- On-chain: DID Document + Helper data references (hashes + URIs)
- IPFS: Actual helper data (452 bytes per enrollment)
- Balance: Reasonable cost (~2 ADA) with good availability
- Privacy: Helper data content not directly on-chain (only hashes)

### 3.2 Inline Storage (Option 1)

**Approach**: Store all helper data directly in on-chain metadata.

**Structure**:
```json
{
  "biometricMetadata": {
    "helperData": [
      {
        "fingerId": 0,
        "version": 1,
        "salt": "a1b2c3d4...",  // 32 bytes hex (64 chars)
        "personalization": "b2c3d4e5...",  // 32 bytes hex
        "bchSyndrome": "c3d4e5f6...",  // 16 bytes hex
        "hmac": "d4e5f6a1..."  // 32 bytes hex
      },
      // ... 3 more fingers
    ]
  }
}
```

**Advantages**:
- ✅ Maximum availability (Cardano's permanence)
- ✅ No external dependencies
- ✅ Simple resolution (single query)

**Disadvantages**:
- ❌ High cost (~3 ADA per DID due to UTxO size)
- ❌ Privacy leak (helper data publicly visible)
- ❌ Inflexible (can't update without transaction)

**Recommendation**: Use for high-value identities only (Phase 3+).

### 3.3 External Storage (Option 2)

**Approach**: Store helper data entirely on IPFS, reference by CID.

**Structure**:
```json
{
  "biometricMetadata": {
    "helperDataURI": "ipfs://QmRootCID123456789abcdefghijklmnopqrstuvwxyz",
    "helperDataHash": "blake2b-256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
  }
}
```

**IPFS Content** (452 bytes):
```json
{
  "version": "1.0",
  "fingers": [
    {
      "fingerId": 0,
      "salt": "a1b2c3d4...",
      "personalization": "b2c3d4e5...",
      "bchSyndrome": "c3d4e5f6...",
      "hmac": "d4e5f6a1..."
    },
    // ... 3 more fingers
  ]
}
```

**Advantages**:
- ✅ Low on-chain cost (~1.5 ADA)
- ✅ Privacy-preserving (content not directly visible)
- ✅ Flexible (update IPFS without on-chain tx)

**Disadvantages**:
- ❌ IPFS availability risk (requires pinning)
- ❌ Two-step resolution (DID Document → IPFS fetch)
- ❌ Gateway dependency (unless running local node)

**Recommendation**: Use for cost-sensitive deployments (Phase 1-2).

### 3.4 Hybrid Storage (Option 3, Selected)

**Approach**: Store references + hashes on-chain, full data on IPFS.

**On-Chain Structure** (Section 2.2):
```json
{
  "biometricMetadata": {
    "helperDataRefs": [
      {
        "fingerId": 0,
        "uri": "ipfs://QmFinger0CID...",
        "hash": "blake2b-256:a1b2c3d4...",
        "size": 113
      }
      // ... 3 more fingers (per-finger CIDs)
    ]
  }
}
```

**IPFS Content** (113 bytes per finger):
```
Version (1 byte) || Salt (32 bytes) || Personalization (32 bytes) ||
Syndrome (16 bytes) || HMAC (32 bytes)
```

**Advantages**:
- ✅ Moderate cost (~2 ADA)
- ✅ Per-finger granularity (update one finger without affecting others)
- ✅ Integrity verification (on-chain hashes prevent tampering)
- ✅ Graceful degradation (fallback to 3/4 fingers if one IPFS fetch fails)

**Disadvantages**:
- ❌ Slightly more complex resolution (4 IPFS fetches)
- ❌ Still requires IPFS pinning

**Recommendation**: **Selected for Phase 1-3** (best balance).

---

## 4. URI Scheme for External References

### 4.1 Supported URI Schemes

**Primary**: `ipfs://`
**Fallbacks**: `https://`, `ar://` (Arweave)

### 4.2 IPFS URI Format

**Syntax**:
```
ipfs://<CID>
```

**Example**:
```
ipfs://QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
```

**CID Version**: CIDv1 (recommended)
- Base32 encoding (lowercase)
- Multihash: BLAKE2b-256 or SHA-256
- Multicodec: `dag-pb` (Protocol Buffers) or `raw`

**Resolution**:
1. Local IPFS node (if available): `ipfs cat <CID>`
2. Public gateway: `https://ipfs.io/ipfs/<CID>`
3. Pinning service gateway: `https://<CID>.ipfs.dweb.link/`

### 4.3 HTTPS URI Format (Fallback)

**Syntax**:
```
https://<domain>/path/to/helper-data
```

**Example**:
```
https://did.example.com/helper-data/f0ff48bb-finger0.bin
```

**Security Requirements**:
- ✅ HTTPS (TLS 1.3)
- ✅ BLAKE2b-256 hash verification (must match on-chain hash)
- ✅ Content-Type: `application/octet-stream`

**Use Cases**:
- User-hosted helper data (personal domain)
- Enterprise deployments (private infrastructure)
- Temporary storage during migration

### 4.4 Arweave URI Format (Phase 3+)

**Syntax**:
```
ar://<transaction_id>
```

**Example**:
```
ar://z5b9Z6QQqQ7Q8Q9R0S1T2U3V4W5X6Y7Z8A9B0C1D2E3F4
```

**Advantages**:
- ✅ Permanent storage (pay once, store forever)
- ✅ Cryptographic proof of permanence
- ✅ No ongoing pinning costs

**Disadvantages**:
- ❌ Higher upfront cost (~$0.01 per KB)
- ❌ Slower initial writes (block confirmation ~2 minutes)

**Recommendation**: Use for long-term archival (Phase 3+ mainnet).

---

## 5. Metadata Schema Versioning

### 5.1 Version Header

**All metadata includes version field**:

```json
{
  "version": "1.0",
  "algorithm": "fuzzy-extractor-bch127-blake2b",
  // ... rest of metadata
}
```

**Semantic Versioning**:
- **Major** (1.x.x): Breaking changes (incompatible format)
- **Minor** (x.1.x): New fields (backward compatible)
- **Patch** (x.x.1): Bug fixes (no schema changes)

### 5.2 Schema Evolution Rules

**Backward Compatibility Guidelines**:

1. **Adding Fields** (Minor version bump):
   ```json
   // v1.0 → v1.1
   {
     "version": "1.1",
     "newField": "value",  // New optional field
     // ... existing fields unchanged
   }
   ```
   - ✅ Old clients ignore unknown fields
   - ✅ New clients provide default values

2. **Deprecating Fields** (Minor version bump + warning):
   ```json
   {
     "version": "1.2",
     "oldField": "value",  // Deprecated, use newField
     "oldField_deprecated": true,
     "newField": "value"
   }
   ```
   - ✅ Support both fields for 2 major versions
   - ⚠️ Log deprecation warning

3. **Removing Fields** (Major version bump):
   ```json
   // v1.x → v2.0
   {
     "version": "2.0",
     // oldField removed entirely
   }
   ```
   - ❌ Breaking change requires migration

4. **Changing Field Types** (Major version bump):
   ```json
   // v1.0: "fingers": 4
   // v2.0: "fingers": [0, 1, 2, 3]  (int → array)
   ```
   - ❌ Breaking change requires migration

### 5.3 Migration Strategy

**On-Chain Migration** (for breaking changes):

1. User enrolls with new biometric (v2.0)
2. Submit update transaction with new metadata version
3. Old DID Document remains accessible (historical record)
4. New DID Document becomes canonical (latest state)

**No Automatic Migration**: Users must explicitly re-enroll.

**Rationale**: Biometric re-capture ensures security (prevent replay attacks).

---

## 6. Metadata Size Optimization

### 6.1 Current Sizes

**Unoptimized** (JSON, pretty-printed):
```json
{
  "biometricMetadata": {
    "helperDataRefs": [ /* ... */ ]
  }
}
```
- Size: ~1,200 bytes (on-chain)

**Optimized** (JSON, minified):
```json
{"biometricMetadata":{"helperDataRefs":[...]}}
```
- Size: ~1,050 bytes (on-chain)
- Savings: 12.5%

### 6.2 CBOR Encoding (Phase 2+)

**Binary Format** (Concise Binary Object Representation):

**CBOR Schema**:
```cddl
biometric-metadata = {
  1: uint,              ; version
  2: tstr,              ; algorithm
  3: uint,              ; fingers
  4: [* helper-ref],    ; helperDataRefs
  5: tstr,              ; aggregationMethod
  6: uint,              ; minFingers
  7: uint               ; fallbackQualityThreshold
}

helper-ref = {
  1: uint,              ; fingerId
  2: tstr,              ; uri
  3: bstr,              ; hash (32 bytes)
  4: uint               ; size
}
```

**Size Comparison**:
- JSON: ~1,050 bytes
- CBOR: ~650 bytes
- **Savings: 38%**

**Cost Impact**:
- JSON: ~2 ADA per DID
- CBOR: ~1.5 ADA per DID
- **Savings: 0.5 ADA per DID**

**Implementation**: Phase 2 (requires CBOR parsers in wallet)

### 6.3 Compression (Phase 3+)

**Gzip Compression**:
```
Original CBOR: 650 bytes
Gzipped CBOR:  420 bytes
Savings:       35%
```

**Trade-offs**:
- ✅ Additional 35% size reduction
- ❌ Decompression overhead (~1ms)
- ❌ Complexity (compression/decompression logic)

**Recommendation**: Only for very large DID Documents (>5KB, Phase 3+)

---

## 7. DID Operations

### 7.1 Create (Register)

**Workflow**:

```
1. User Enrollment:
   ┌─────────────────────────────┐
   │ Capture 4 fingerprints      │
   │ Generate helper data (452B) │
   │ Derive master key (256-bit) │
   └─────────────────────────────┘
             ↓
2. Key Derivation:
   ┌─────────────────────────────┐
   │ Derive Ed25519 keypair      │
   │ Public key for DID Doc      │
   │ Private key for signing     │
   └─────────────────────────────┘
             ↓
3. IPFS Upload:
   ┌─────────────────────────────┐
   │ Upload helper data (4 CIDs) │
   │ Pin on IPFS (local + remote)│
   │ Get CIDs + content hashes   │
   └─────────────────────────────┘
             ↓
4. DID Document Creation:
   ┌─────────────────────────────┐
   │ Construct DID Document JSON │
   │ Include IPFS refs + hashes  │
   │ Sign with derived key       │
   └─────────────────────────────┘
             ↓
5. Cardano Transaction:
   ┌─────────────────────────────┐
   │ Mint CIP-68 (100) ref token │
   │ Mint CIP-68 (222) user token│
   │ Attach metadata to ref token│
   │ Submit transaction          │
   └─────────────────────────────┘
             ↓
6. DID Registration:
   ┌─────────────────────────────┐
   │ Transaction confirmed       │
   │ DID = did:cardano:<network>:│
   │       <policy_id>           │
   └─────────────────────────────┘
```

**On-Chain Representation** (CIP-68):
```json
{
  "100": {
    "did": "did:cardano:mainnet:f0ff48bb...",
    "didDocument": { /* DID Document JSON */ }
  }
}
```

**Cost Breakdown**:
- Min UTxO: ~1.5 ADA (Babbage era)
- Transaction fee: ~0.3 ADA
- Metadata overhead: ~0.2 ADA (size-dependent)
- **Total**: ~2 ADA

### 7.2 Read (Resolve)

**Workflow**:

```
1. DID Resolution Request:
   Input: did:cardano:mainnet:f0ff48bb...
             ↓
2. Extract Policy ID:
   policy_id = "f0ff48bb..."
             ↓
3. Query Cardano UTxO:
   ┌─────────────────────────────┐
   │ Find UTxO with asset:       │
   │ policy_id + name (100)      │
   │ Extract metadata            │
   └─────────────────────────────┘
             ↓
4. Parse DID Document:
   ┌─────────────────────────────┐
   │ Deserialize JSON            │
   │ Extract helperDataRefs      │
   └─────────────────────────────┘
             ↓
5. Fetch Helper Data (if needed):
   ┌─────────────────────────────┐
   │ For each IPFS URI:          │
   │   - Fetch from IPFS         │
   │   - Verify BLAKE2b hash     │
   │   - Return helper data      │
   └─────────────────────────────┘
             ↓
6. Return DID Document:
   Output: Complete DID Document + helper data
```

**Caching Strategy**:
- DID Documents: Cache for 1 hour (updates are infrequent)
- Helper Data: Cache indefinitely (immutable, content-addressed)

**Performance**:
- On-chain query: ~100ms (Blockfrost API)
- IPFS fetch: ~500ms (public gateway)
- Total resolution: ~600ms ✅ (<3s requirement)

### 7.3 Update

**Supported Updates**:
1. Add/remove verification methods
2. Update service endpoints
3. Rotate individual fingers (Section 7.3.1)
4. Revoke DID (Section 7.4)

**Workflow** (Verification Method Update):

```
1. User Authentication:
   ┌─────────────────────────────┐
   │ Verify with biometrics      │
   │ Derive master key           │
   │ Sign update request         │
   └─────────────────────────────┘
             ↓
2. Construct Update:
   ┌─────────────────────────────┐
   │ Modify DID Document         │
   │ Increment version           │
   │ Update "updated" timestamp  │
   └─────────────────────────────┘
             ↓
3. Submit Transaction:
   ┌─────────────────────────────┐
   │ Update CIP-68 (100) metadata│
   │ Plutus validator checks:    │
   │   - Valid signature         │
   │   - Policy ID match         │
   │   - Nonce increment         │
   └─────────────────────────────┘
             ↓
4. Confirmation:
   ┌─────────────────────────────┐
   │ Transaction confirmed       │
   │ New DID Document active     │
   └─────────────────────────────┘
```

**Cost**: ~0.5 ADA per update (transaction fee only, no new UTxO)

#### 7.3.1 Finger Rotation

**Scenario**: Replace one finger (e.g., injury, quality degradation).

**Workflow**:

```
1. Verify with 3 Remaining Fingers:
   ┌─────────────────────────────┐
   │ Use fallback mode (3/4)     │
   │ Derive K_old = K1⊕K2⊕K3⊕K4  │
   └─────────────────────────────┘
             ↓
2. Enroll New Finger:
   ┌─────────────────────────────┐
   │ Capture new finger          │
   │ Generate new helper data    │
   │ Derive K4_new               │
   └─────────────────────────────┘
             ↓
3. Compute New Master Key:
   ┌─────────────────────────────┐
   │ K_new = K1⊕K2⊕K3⊕K4_new     │
   │ Derive new Ed25519 keypair  │
   └─────────────────────────────┘
             ↓
4. Upload New Helper Data:
   ┌─────────────────────────────┐
   │ Upload to IPFS (finger 3)   │
   │ Get new CID and hash        │
   └─────────────────────────────┘
             ↓
5. Update DID Document:
   ┌─────────────────────────────┐
   │ Replace helperDataRefs[3]   │
   │ Update verification method  │
   │ Sign with K_old (authorize) │
   └─────────────────────────────┘
             ↓
6. Submit Transaction:
   ┌─────────────────────────────┐
   │ Update CIP-68 metadata      │
   │ Old key authorizes change   │
   │ New key becomes active      │
   └─────────────────────────────┘
```

**Key Rotation**: After update, all new operations use K_new.

**Backward Compatibility**: Old signatures remain valid (historical verification).

### 7.4 Delete (Revoke)

**Approach**: Burn CIP-68 tokens to mark DID as revoked.

**Workflow**:

```
1. User Initiates Revocation:
   ┌─────────────────────────────┐
   │ Verify with biometrics      │
   │ Sign revocation request     │
   └─────────────────────────────┘
             ↓
2. Construct Revocation Transaction:
   ┌─────────────────────────────┐
   │ Burn (100) reference token  │
   │ Burn (222) user token       │
   │ Add "revoked" metadata      │
   └─────────────────────────────┘
             ↓
3. Submit Transaction:
   ┌─────────────────────────────┐
   │ Plutus validator checks:    │
   │   - Valid signature         │
   │   - Owner authorization     │
   │ Burn tokens                 │
   └─────────────────────────────┘
             ↓
4. DID Revoked:
   ┌─────────────────────────────┐
   │ DID resolution returns:     │
   │ "revoked": true             │
   │ "revokedAt": "2025-10-15"   │
   └─────────────────────────────┘
```

**Revocation Metadata**:
```json
{
  "revoked": true,
  "revokedAt": "2025-10-15T10:30:00Z",
  "revocationReason": "user-requested",
  "finalTxHash": "a1b2c3d4..."
}
```

**Cost**: ~0.3 ADA (transaction fee only, no UTxO remains)

**Irreversibility**: Once revoked, DID cannot be reactivated (create new DID instead).

---

## 8. Resolution Algorithm

### 8.1 Resolution Steps

**Input**: `did:cardano:<network>:<policy_id>`

**Output**: DID Document (JSON) or error

**Algorithm**:

```python
def resolve_did(did: str) -> dict:
    """
    Resolve a did:cardano DID to its DID Document.

    Args:
        did: DID string (e.g., "did:cardano:mainnet:f0ff48bb...")

    Returns:
        DID Document (dict)

    Raises:
        ValueError: Invalid DID format
        ResolutionError: DID not found or revoked
    """
    # Step 1: Parse DID
    method, network, policy_id = parse_did(did)

    if method != "cardano":
        raise ValueError(f"Unsupported method: {method}")

    if network not in ["mainnet", "preprod", "preview"]:
        raise ValueError(f"Unsupported network: {network}")

    if len(policy_id) != 56:
        raise ValueError(f"Invalid policy ID length: {len(policy_id)}")

    # Step 2: Query Cardano blockchain
    utxo = query_cardano_utxo(network, policy_id, asset_name="000643b0")  # "100" hex

    if utxo is None:
        raise ResolutionError(f"DID not found: {did}")

    # Step 3: Extract metadata
    metadata = utxo["datum"]["fields"][0]["map"]
    did_document_json = metadata["didDocument"]

    # Step 4: Parse DID Document
    did_document = json.loads(did_document_json)

    # Step 5: Check revocation
    if did_document.get("revoked", False):
        raise ResolutionError(f"DID revoked: {did}")

    # Step 6: Return DID Document
    return did_document
```

### 8.2 Resolution Metadata

**W3C DID Resolution Metadata**:

```json
{
  "contentType": "application/did+json",
  "retrieved": "2025-10-10T12:00:00Z",
  "cardanoMetadata": {
    "network": "mainnet",
    "policyId": "f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002ec48f232b49ca0fb9a",
    "txHash": "a1b2c3d4e5f6789012345678901234567890abcdefabcdefabcdefabcdef0123",
    "slot": 123456789,
    "blockHeight": 9876543,
    "epoch": 450
  }
}
```

### 8.3 Error Handling

**Error Types**:

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `invalidDid` | 400 | Malformed DID syntax |
| `notFound` | 404 | DID not on blockchain |
| `revoked` | 410 | DID explicitly revoked |
| `networkError` | 503 | Blockchain query failed |

**Error Response**:
```json
{
  "error": "notFound",
  "message": "DID not found on Cardano mainnet",
  "did": "did:cardano:mainnet:f0ff48bb..."
}
```

---

## 9. Security Considerations

### 9.1 Threat Model

**Threats**:

1. **DID Hijacking**: Attacker steals biometric enrollment
   - **Mitigation**: Multi-finger requirement (4 fingers), liveness detection

2. **Helper Data Tampering**: Attacker modifies IPFS content
   - **Mitigation**: On-chain BLAKE2b-256 hashes, verify before use

3. **Replay Attacks**: Attacker replays old transactions
   - **Mitigation**: Nonce increment in Plutus validator

4. **Privacy Leakage**: Helper data reveals biometric info
   - **Mitigation**: Fuzzy extractor unlinkability (Task 2)

5. **IPFS Unavailability**: Helper data lost (unpinned)
   - **Mitigation**: Multi-gateway fallback, user backup

### 9.2 Plutus Validator Security

**Validator Checks** (on-chain):

```haskell
-- Simplified pseudo-Haskell
validateUpdate :: Datum -> Redeemer -> ScriptContext -> Bool
validateUpdate oldDatum redeemer ctx =
    -- Check 1: Valid signature from current controller
    traceIfFalse "Invalid signature" (checkSignature currentKey redeemer)

    -- Check 2: Policy ID unchanged
    && traceIfFalse "Policy ID mismatch" (oldPolicyId == newPolicyId)

    -- Check 3: Nonce incremented (prevent replay)
    && traceIfFalse "Invalid nonce" (newNonce == oldNonce + 1)

    -- Check 4: Reference token preserved
    && traceIfFalse "Reference token missing" (hasReferenceToken ctx)

    -- Check 5: Reasonable metadata size (<16KB)
    && traceIfFalse "Metadata too large" (metadataSize < 16384)
```

**Cost**: ~0.1 ADA execution units (typical update)

### 9.3 Privacy Properties

**Guarantees**:

1. **Unlinkability**: Multiple enrollments indistinguishable
   - Helper data uses unique salts (256-bit random)
   - 50% Hamming distance between enrollments (Task 2)

2. **Template Irreversibility**: Cannot reconstruct fingerprint
   - Biometric template never stored
   - Helper data + key → fingerprint: 2^256 search space

3. **Confidentiality**: Biometric never leaves device
   - All processing local (quantization → fuzzy extractor)
   - Only derived keys and helper data stored

---

## 10. Implementation Roadmap

### 10.1 Phase 1 (Hackathon Demo)

**Deliverables**:
- ✅ DID syntax specification
- ✅ Minimal DID Document schema
- ✅ Hybrid storage design (IPFS + on-chain refs)
- ⏳ Python DID creation/resolution library
- ⏳ Mock Cardano transaction (testnet)

**Limitations**:
- No Plutus validator (manual transaction construction)
- Single IPFS gateway (ipfs.io)
- No revocation support

### 10.2 Phase 2 (Testnet)

**Deliverables**:
- Plutus validator (minting policy + update logic)
- DID update operations (finger rotation)
- Multi-gateway IPFS (3+ gateways)
- DID revocation (token burning)
- CBOR metadata encoding

**Targets**:
- 100 test DIDs created
- <2 ADA per DID lifecycle cost
- 99.9% resolution success rate

### 10.3 Phase 3 (Mainnet)

**Deliverables**:
- Production Plutus validator (audited)
- Arweave permanent storage option
- DID recovery mechanisms
- Governance (method updates via CIP)
- Performance optimizations (<500ms resolution)

**Targets**:
- 10,000+ DIDs on mainnet
- <1.5 ADA per DID cost (CBOR + optimizations)
- 99.99% availability

---

## 11. JSON Schema Definitions

### 11.1 DID Document Schema

**File**: `schemas/did-document-v1.0.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://decentralized-did.github.io/schemas/did-document-v1.0.schema.json",
  "title": "did:cardano DID Document",
  "type": "object",
  "required": ["@context", "id", "verificationMethod"],
  "properties": {
    "@context": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "uri"
      },
      "minItems": 1
    },
    "id": {
      "type": "string",
      "pattern": "^did:cardano:(mainnet|preprod|preview):[0-9a-f]{56}$"
    },
    "controller": {
      "type": "string",
      "pattern": "^did:cardano:(mainnet|preprod|preview):[0-9a-f]{56}$"
    },
    "verificationMethod": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/verificationMethod"
      },
      "minItems": 1
    },
    "authentication": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "assertionMethod": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "biometricMetadata": {
      "$ref": "#/definitions/biometricMetadata"
    },
    "serviceEndpoint": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/serviceEndpoint"
      }
    },
    "created": {
      "type": "string",
      "format": "date-time"
    },
    "updated": {
      "type": "string",
      "format": "date-time"
    },
    "proof": {
      "$ref": "#/definitions/proof"
    }
  },
  "definitions": {
    "verificationMethod": {
      "type": "object",
      "required": ["id", "type", "controller", "publicKeyMultibase"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^did:cardano:(mainnet|preprod|preview):[0-9a-f]{56}#[a-zA-Z0-9_-]+$"
        },
        "type": {
          "type": "string",
          "enum": ["Ed25519VerificationKey2020"]
        },
        "controller": {
          "type": "string",
          "pattern": "^did:cardano:(mainnet|preprod|preview):[0-9a-f]{56}$"
        },
        "publicKeyMultibase": {
          "type": "string",
          "pattern": "^z[1-9A-HJ-NP-Za-km-z]{43,}$"
        }
      }
    },
    "biometricMetadata": {
      "type": "object",
      "required": ["type", "version", "algorithm", "fingers", "helperDataRefs"],
      "properties": {
        "type": {
          "type": "string",
          "const": "BiometricHelperData"
        },
        "version": {
          "type": "string",
          "pattern": "^[0-9]+\\.[0-9]+(\\.[0-9]+)?$"
        },
        "algorithm": {
          "type": "string",
          "enum": ["fuzzy-extractor-bch127-blake2b"]
        },
        "fingers": {
          "type": "integer",
          "minimum": 2,
          "maximum": 10
        },
        "helperDataRefs": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/helperDataRef"
          },
          "minItems": 2,
          "maxItems": 10
        },
        "aggregationMethod": {
          "type": "string",
          "enum": ["xor", "concatenation", "merkle"]
        },
        "minFingers": {
          "type": "integer",
          "minimum": 1,
          "maximum": 10
        },
        "fallbackQualityThreshold": {
          "type": "integer",
          "minimum": 0,
          "maximum": 100
        }
      }
    },
    "helperDataRef": {
      "type": "object",
      "required": ["fingerId", "uri", "hash", "size"],
      "properties": {
        "fingerId": {
          "type": "integer",
          "minimum": 0,
          "maximum": 9
        },
        "uri": {
          "type": "string",
          "format": "uri",
          "pattern": "^(ipfs://|https://|ar://)"
        },
        "hash": {
          "type": "string",
          "pattern": "^blake2b-256:[0-9a-f]{64}$"
        },
        "size": {
          "type": "integer",
          "minimum": 1,
          "maximum": 1024
        }
      }
    },
    "serviceEndpoint": {
      "type": "object",
      "required": ["id", "type", "serviceEndpoint"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^did:cardano:(mainnet|preprod|preview):[0-9a-f]{56}#[a-zA-Z0-9_-]+$"
        },
        "type": {
          "type": "string"
        },
        "serviceEndpoint": {
          "type": "string",
          "format": "uri"
        }
      }
    },
    "proof": {
      "type": "object",
      "required": ["type", "created", "verificationMethod", "proofPurpose", "cardanoTxHash"],
      "properties": {
        "type": {
          "type": "string",
          "const": "CardanoSignature2025"
        },
        "created": {
          "type": "string",
          "format": "date-time"
        },
        "verificationMethod": {
          "type": "string"
        },
        "proofPurpose": {
          "type": "string",
          "enum": ["assertionMethod", "authentication"]
        },
        "cardanoTxHash": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "cardanoSlot": {
          "type": "integer",
          "minimum": 0
        },
        "cardanoEpoch": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```

### 11.2 Helper Data Schema

**File**: `schemas/helper-data-v1.0.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://decentralized-did.github.io/schemas/helper-data-v1.0.schema.json",
  "title": "Biometric Helper Data",
  "type": "object",
  "required": ["version", "fingers"],
  "properties": {
    "version": {
      "type": "string",
      "const": "1.0"
    },
    "fingers": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/fingerHelperData"
      },
      "minItems": 2,
      "maxItems": 10
    }
  },
  "definitions": {
    "fingerHelperData": {
      "type": "object",
      "required": ["fingerId", "salt", "personalization", "bchSyndrome", "hmac"],
      "properties": {
        "fingerId": {
          "type": "integer",
          "minimum": 0,
          "maximum": 9
        },
        "salt": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$",
          "description": "256-bit salt (32 bytes hex)"
        },
        "personalization": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$",
          "description": "256-bit personalization tag (32 bytes hex)"
        },
        "bchSyndrome": {
          "type": "string",
          "pattern": "^[0-9a-f]{32}$",
          "description": "BCH syndrome (16 bytes hex, 127 bits padded)"
        },
        "hmac": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$",
          "description": "BLAKE2b-256 HMAC (32 bytes hex)"
        }
      }
    }
  }
}
```

---

## 12. References

1. **W3C DID Core Specification v1.0**
   https://www.w3.org/TR/did-core/

2. **CIP-68: Datum Metadata Standard**
   https://cips.cardano.org/cips/cip68/

3. **IPFS Specifications**
   https://docs.ipfs.tech/concepts/

4. **Cardano Documentation**
   https://docs.cardano.org/

5. **Phase 1 Design Documents**:
   - `docs/design/quantization-algorithm.md`
   - `docs/design/fuzzy-extractor-spec.md`
   - `docs/design/aggregation-scheme.md`

---

## Appendix: Example DID Lifecycle

### Enrollment (Alice)

```
1. Alice captures fingerprints:
   - Right index (0)
   - Right middle (1)
   - Left index (2)
   - Left middle (3)

2. System generates:
   - Helper data (4 × 113 bytes = 452 bytes)
   - Master key (256 bits)
   - Ed25519 keypair (public: z6Mkp..., private: <secret>)

3. IPFS upload:
   - Finger 0: ipfs://QmABC... (113 bytes)
   - Finger 1: ipfs://QmDEF... (113 bytes)
   - Finger 2: ipfs://QmGHI... (113 bytes)
   - Finger 3: ipfs://QmJKL... (113 bytes)

4. DID Document created:
   - ID: did:cardano:mainnet:a1b2c3d4...
   - Verification method: z6Mkp...
   - Helper data refs: [ipfs://QmABC..., ...]

5. Cardano transaction:
   - Mint policy: a1b2c3d4...
   - (100) ref token: 1 minted, locked in script
   - (222) user token: 1 minted, sent to Alice's wallet
   - Cost: ~2 ADA
```

### Authentication (Alice, 6 months later)

```
1. Alice needs to sign a credential
2. Wallet prompts: "Scan fingerprints"
3. Alice scans 4 fingers
4. System:
   - Resolves DID: did:cardano:mainnet:a1b2c3d4...
   - Fetches helper data from IPFS (4 × 113 bytes)
   - Verifies hashes match on-chain metadata ✅
   - Reproduces master key via fuzzy extractor
   - Derives Ed25519 keypair (same public key: z6Mkp...)
   - Signs credential with private key
5. Verifier:
   - Resolves Alice's DID
   - Checks signature against public key z6Mkp... ✅
   - Credential accepted
```

### Finger Rotation (Alice, 1 year later)

```
1. Alice notices finger 3 quality degraded (injury healed poorly)
2. Initiates rotation:
   - Scans fingers 0, 1, 2 (3/4 fallback mode)
   - System derives old master key
   - Alice authorized ✅
3. Re-enrollment:
   - Scans NEW finger (e.g., right ring finger)
   - Generates new helper data for finger 3
   - Uploads to IPFS: ipfs://QmXYZ... (113 bytes)
4. Update transaction:
   - Replaces helperDataRefs[3] with ipfs://QmXYZ...
   - Updates BLAKE2b hash for finger 3
   - Derives NEW master key (K1⊕K2⊕K3⊕K3_new)
   - Generates NEW Ed25519 keypair
5. DID Document updated:
   - New verification method: z6Mkq... (different public key!)
   - Old public key (z6Mkp...) added to "rotated" field for historical verification
   - Cost: ~0.5 ADA
6. Future authentications use new key (z6Mkq...)
```

### Revocation (Alice leaves ecosystem)

```
1. Alice decides to revoke DID
2. Final authentication:
   - Scans 4 fingers
   - Signs revocation request
3. Revocation transaction:
   - Burns (100) reference token
   - Burns (222) user token
   - Adds revocation metadata:
     {
       "revoked": true,
       "revokedAt": "2027-03-15T14:30:00Z",
       "reason": "user-requested"
     }
   - Cost: ~0.3 ADA
4. DID resolution now returns:
   - Error 410: DID revoked
   - Historical data still available (for audit)
5. Helper data remains on IPFS (immutable record)
```

---

**Document Status**: ✅ Complete
**Next Steps**: Phase 1, Task 5 - Architecture Security Review

*All technologies open-source: W3C DID Core, Cardano, IPFS, CIP-68*
