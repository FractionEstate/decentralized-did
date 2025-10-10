# Cardano Metadata Standards and Ecosystem Analysis

**Phase 0, Task 4 Deliverable**
**Date:** October 10, 2025
**Status:** Complete

**PROJECT CONSTRAINT: All Cardano tools and services must be open-source. No paid APIs or commercial services.**

## Executive Summary

This document provides comprehensive research on Cardano Improvement Proposals (CIPs), metadata standards, transaction constraints, and ecosystem tools relevant to the decentralized biometric DID system. Key findings indicate that CIP-68 datum-based metadata provides the most flexible approach for biometric helper data storage, while CIP-30 enables seamless wallet integration. The Cardano ecosystem offers robust open-source tooling (cardano-cli, PyCardano, Ogmios) for building decentralized identity solutions without reliance on paid services.

**Critical Constraints:**
- **Metadata Size**: 16 KB per transaction (soft limit)
- **Transaction Cost**: ~0.17-0.4 ADA per transaction (depends on size)
- **On-chain Storage**: Expensive for large data; prefer off-chain with on-chain commitments
- **Smart Contract Memory**: 14 MB execution memory limit per transaction

---

## 1. CIP-20: Transaction Message/Comment Metadata

### 1.1 Standard Overview

**CIP-20** defines a standard for adding human-readable messages and structured metadata to Cardano transactions using metadata label **674**.

**Specification:** https://cips.cardano.org/cips/cip20/

### 1.2 Metadata Structure

```json
{
  "674": {
    "msg": ["Invoice for biometric DID enrollment", "User: alice@example.com"]
  }
}
```

**Key Features:**
- **Label**: 674 (registered for transaction messages)
- **Format**: Array of strings (each ≤64 bytes for efficiency)
- **Use Case**: Audit trails, transaction descriptions, receipts

### 1.3 Relevance to Our System

**Potential Uses:**
- ✅ Enrollment transaction descriptions ("Biometric DID enrollment for wallet addr1...")
- ✅ Revocation messages ("DID revocation requested by user")
- ✅ Audit trail metadata (timestamps, client versions, SDK versions)

**Limitations:**
- Not suitable for large biometric helper data (too verbose)
- Intended for human-readable messages, not binary data

**Recommendation:** Use CIP-20 for audit logging and transaction descriptions, not for helper data storage.

---

## 2. CIP-25: NFT Metadata Standard

### 2.1 Standard Overview

**CIP-25** defines the metadata standard for Non-Fungible Tokens (NFTs) on Cardano, using metadata label **721**.

**Specification:** https://cips.cardano.org/cips/cip25/

### 2.2 Metadata Structure

```json
{
  "721": {
    "<policy_id>": {
      "<asset_name>": {
        "name": "Biometric DID #12345",
        "image": "ipfs://QmHash...",
        "mediaType": "image/png",
        "description": "Decentralized identity credential",
        "attributes": {
          "did_method": "did:cardano:mainnet:addr1...",
          "enrollment_date": "2025-10-10T12:00:00Z",
          "biometric_type": "fingerprint"
        }
      }
    }
  }
}
```

**Key Features:**
- **Label**: 721 (registered for NFT metadata)
- **Format**: Nested JSON with policy ID and asset name
- **Fields**: name, image, mediaType, description, files, attributes (custom key-value pairs)
- **Rich Metadata**: Supports arrays, nested objects, URLs, IPFS hashes

### 2.3 CIP-25 Version 2 Enhancements

**Specification:** https://cips.cardano.org/cips/cip25/ (Version 2)

**New Features:**
- **Multiple Files**: Array of file objects (main image + supplementary files)
- **3D Models**: Support for .glb, .gltf formats
- **Standard Attributes**: Rarity, edition number, creator

**Example with Multiple Files:**
```json
{
  "721": {
    "<policy_id>": {
      "<asset_name>": {
        "name": "Biometric DID Credential",
        "image": "ipfs://Qm...",
        "files": [
          {
            "name": "DID Document",
            "mediaType": "application/json",
            "src": "ipfs://QmDidDocument..."
          },
          {
            "name": "Helper Data",
            "mediaType": "application/octet-stream",
            "src": "ipfs://QmHelperData..."
          }
        ],
        "attributes": {
          "did": "did:cardano:mainnet:addr1...",
          "revoked": false
        }
      }
    }
  }
}
```

### 2.4 Relevance to Our System

**Potential Uses:**
- ✅ Represent DID as NFT (unique, non-transferable identity credential)
- ✅ Store metadata about biometric enrollment (date, type, version)
- ✅ Link to off-chain helper data via IPFS or Arweave
- ✅ Revocation status tracking (update metadata or burn NFT)

**Advantages:**
- Well-established standard (wide wallet support)
- Rich metadata structure (custom attributes)
- NFT uniqueness guarantees (one DID per user)

**Limitations:**
- 16 KB metadata limit still applies (helper data must be off-chain)
- Metadata updates require new transactions
- Policy ID must allow metadata updates (versioned policies)

**Recommendation:** Use CIP-25 NFT as the **on-chain DID representation** with IPFS/Arweave links to helper data. This provides wallet compatibility and rich metadata support.

---

## 3. CIP-68: Datum Metadata Standard

### 3.1 Standard Overview

**CIP-68** defines a standard for storing rich metadata in **Plutus datums** (UTXOs locked by smart contracts) rather than transaction metadata. This approach provides greater flexibility, composability, and efficiency.

**Specification:** https://cips.cardano.org/cips/cip68/

### 3.2 Asset Class Prefixes

CIP-68 introduces **asset name prefixes** to indicate metadata storage location:

| Prefix | Asset Class | Metadata Location | Use Case |
|--------|-------------|-------------------|----------|
| `(100)` | Reference NFT | Plutus datum at UTxO | Rich metadata, updatable |
| `(222)` | User Token NFT | No metadata | Transferable token representing ownership |
| `(333)` | Reference FT | Plutus datum at UTxO | Fungible token with metadata |
| `(444)` | User RFT | No metadata | Rich Fungible token |

**Key Concept:**
- **Reference NFT (100)**: Locked at smart contract, holds metadata in datum
- **User Token NFT (222)**: Held by user, references the (100) asset for metadata
- **Reference FT (333)**: Fungible token with metadata in datum
- **User RFT (444)**: Fungible token held by user, can represent fractional ownership and looks like a NFT

### 3.3 Datum Structure

```haskell
-- Plutus datum structure for CIP-68 metadata
data Metadata = Metadata
  { metadata :: Map ByteString MetadataValue
  , version  :: Integer
  , extra    :: BuiltinData  -- Arbitrary extra data
  }

data MetadataValue
  = MetadataMap (Map ByteString MetadataValue)
  | MetadataList [MetadataValue]
  | MetadataInt Integer
  | MetadataBytes ByteString
  | MetadataText Text
```

**Example Datum (JSON representation):**
```json
{
  "constructor": 0,
  "fields": [
    {
      "map": [
        {
          "k": {"bytes": "6e616d65"},  // "name" in hex
          "v": {"bytes": "4269..."}     // "Biometric DID" in hex
        },
        {
          "k": {"bytes": "646964"},     // "did" in hex
          "v": {"bytes": "6469643a..."}  // "did:cardano:..." in hex
        },
        {
          "k": {"bytes": "68656c706572..."},  // "helper_data_hash"
          "v": {"bytes": "a3b5c9..."}         // BLAKE2b-256 hash
        }
      ]
    },
    {"int": 1},  // version
    {"bytes": ""}  // extra data (empty)
  ]
}
```

### 3.4 Advantages Over CIP-25

**CIP-68 Advantages:**
1. **No 16 KB Metadata Limit**: Datums can store more data (limited by tx size ~16 KB)
2. **Updatable Metadata**: Smart contract can update datum without changing asset
3. **Composability**: Other smart contracts can read and interact with metadata
4. **Efficient Queries**: Datums indexed by blockchain explorers and query layers
5. **Atomic Updates**: Metadata changes happen in same transaction as state changes

**CIP-25 Advantages:**
1. **Simpler**: No smart contract required (pure metadata)
2. **Wallet Support**: Wide support in existing wallets (Eternl, Nami, Yoroi)
3. **Off-chain Accessibility**: Metadata visible without querying UTXOs

### 3.5 Relevance to Our System

**Potential Uses:**
- ✅ **Primary Recommendation**: Store helper data hash in (100) Reference NFT datum
- ✅ User holds (222) User Token in wallet (represents DID ownership)
- ✅ Smart contract validates helper data hash on-chain during verification
- ✅ Updatable metadata (revocation status, helper data version)

**Architecture:**
```
User Wallet:
  └─ (222) User Token: "BiometricDID_user"
       └─ References → (100) Reference NFT

Smart Contract UTxO:
  └─ (100) Reference NFT: "BiometricDID_ref"
       └─ Datum: {
            "did": "did:cardano:...",
            "helper_data_hash": "a3b5c9...",
            "helper_data_ipfs": "QmHash...",
            "revoked": false,
            "enrollment_date": 1728561600,
            "version": 1
          }
```

**Benefits:**
- User owns transferable (222) token (can move between wallets)
- Metadata stored in tamper-proof (100) Reference NFT datum
- Smart contract enforces update rules (e.g., only owner can revoke)
- Helper data stored off-chain (IPFS), hash verified on-chain

**Recommendation:** Use **CIP-68 with (100)/(222) pattern** for maximum flexibility and smart contract integration. This is the most powerful approach for biometric DID credentials.

---

## 4. CIP-30: Cardano dApp-Wallet Web Bridge

### 4.1 Standard Overview

**CIP-30** (formerly "Cardano dApp Connector") defines the JavaScript API for web applications (dApps) to interact with Cardano wallets in the browser.

**Specification:** https://cips.cardano.org/cips/cip30/

### 4.2 API Overview

**Wallet Detection:**
```javascript
// Check if wallet is available
if (window.cardano && window.cardano.eternl) {
  const walletApi = await window.cardano.eternl.enable();
  console.log("Eternl wallet connected!");
}
```

**Core API Methods:**

| Method | Description | Return Type |
|--------|-------------|-------------|
| `getNetworkId()` | Get network ID (1=mainnet, 0=testnet) | `Promise<number>` |
| `getUtxos()` | Get wallet UTXOs | `Promise<string[]>` |
| `getBalance()` | Get wallet balance | `Promise<string>` |
| `getUsedAddresses()` | Get used addresses | `Promise<string[]>` |
| `getUnusedAddresses()` | Get unused addresses | `Promise<string[]>` |
| `getChangeAddress()` | Get change address | `Promise<string>` |
| `getRewardAddresses()` | Get stake addresses | `Promise<string[]>` |
| `signTx(tx, partialSign)` | Sign transaction | `Promise<string>` |
| `signData(addr, payload)` | Sign arbitrary data | `Promise<{signature, key}>` |
| `submitTx(tx)` | Submit signed transaction | `Promise<string>` |

### 4.3 CIP-30 Extensions

**CIP-95: Web-Wallet Bridge - Governance**
- Extended API for governance participation (voting, delegation)
- Not directly relevant to biometric DID enrollment

**CIP-30 Multi-Delegation:**
- Support for multi-stake pool delegation
- Future consideration for decentralized governance of DID registry

### 4.4 Relevance to Our System

**Enrollment Flow Using CIP-30:**

```javascript
// 1. Connect wallet
const walletApi = await window.cardano.eternl.enable();

// 2. Get user's address
const usedAddresses = await walletApi.getUsedAddresses();
const userAddress = usedAddresses[0]; // CBOR-encoded

// 3. Capture biometric data (fingerprint via WebAuthn or device API)
const biometricData = await captureBiometric();

// 4. Generate helper data and DID (off-chain processing)
const { helperData, commitment, did } = await generateDID(biometricData, userAddress);

// 5. Build transaction with CIP-68 metadata
const tx = await buildEnrollmentTransaction({
  userAddress,
  did,
  helperDataHash: blake2b(helperData),
  helperDataIPFS: await uploadToIPFS(helperData),
});

// 6. Request wallet signature
const signedTx = await walletApi.signTx(tx, false);

// 7. Submit transaction
const txHash = await walletApi.submitTx(signedTx);
console.log(`DID enrolled! Transaction: ${txHash}`);
```

**Advantages:**
- ✅ No wallet seed export (secure signing in wallet)
- ✅ User controls transaction approval
- ✅ Wide wallet support (Eternl, Nami, Yoroi, Flint, Gero, Typhon)
- ✅ Browser-based enrollment (no CLI required)

**Limitations:**
- Requires web browser (not suitable for CLI-only flows)
- Wallet must support CIP-30 (most modern wallets do)
- User must have ADA for transaction fees

**Recommendation:** Use **CIP-30 as the primary enrollment interface** for user-friendly web-based DID registration. Provide CLI fallback using cardano-cli for advanced users.

---

## 5. Transaction Metadata Constraints

### 5.1 Size Limits

**Metadata Size Limit:**
- **Soft Limit**: 16 KB (16,384 bytes) per transaction
- **Hard Limit**: Enforced by protocol parameters
- **Overhead**: CBOR encoding adds ~10-30% size overhead

**Example Calculation:**
```python
import cbor2

metadata = {
    721: {
        "policy_id_hex": {
            "asset_name": {
                "name": "Biometric DID",
                "did": "did:cardano:mainnet:addr1...",
                "helper_data_hash": "a3b5c9..." * 10  # 640 bytes
            }
        }
    }
}

cbor_encoded = cbor2.dumps(metadata)
print(f"CBOR size: {len(cbor_encoded)} bytes")
# Output: CBOR size: ~800 bytes (before compression)
```

**Helper Data Size Analysis:**
- BCH(127,64) helper data: 127 bits = 16 bytes per finger
- Ten-finger helper data: 160 bytes
- HMAC authentication tag: 32 bytes
- Total helper data: ~192 bytes
- CBOR overhead: ~250-300 bytes total

**Verdict:** Helper data fits comfortably in metadata, but **storing off-chain is still recommended** to minimize transaction costs and enable future upgrades.

### 5.2 Transaction Size Limits

**Overall Transaction Size:**
- **Max Size**: 16 KB (16,384 bytes) total transaction size
- **Includes**: Inputs, outputs, metadata, witnesses (signatures), scripts
- **Typical Breakdown**:
  - Inputs: ~100-200 bytes each
  - Outputs: ~50-100 bytes each
  - Metadata: Variable (0-16 KB)
  - Witnesses: ~100-200 bytes per signature
  - Scripts: ~1-10 KB per Plutus script reference

**Example Transaction Budget:**
```
Inputs (2x):         400 bytes
Outputs (2x):        200 bytes
Metadata (CIP-68):  2000 bytes
Witnesses (1x):      150 bytes
Script Reference:   5000 bytes
-----------------------------------
Total:              7750 bytes (47% of limit)
```

**Recommendation:** Keep metadata under 8 KB to leave room for multi-input transactions and script witnesses.

### 5.3 Cost Analysis

**Transaction Fees Formula:**
```
fee = a + b × size
where:
  a = 155,381 lovelace (0.155381 ADA) - minimum fee
  b = 44 lovelace/byte - size coefficient
  size = transaction size in bytes
```

**Cost Examples:**

| Transaction Type | Size | Fee (ADA) | Fee (USD @ $0.50/ADA) |
|-----------------|------|-----------|---------------------|
| Simple transfer | 300 bytes | 0.17 | $0.085 |
| With 1 KB metadata | 1300 bytes | 0.21 | $0.105 |
| With 8 KB metadata | 8300 bytes | 0.52 | $0.26 |
| With Plutus script | 10000 bytes | 0.60 | $0.30 |

**Cost Optimization:**
- Store helper data off-chain (IPFS/Arweave): Only hash on-chain (~32 bytes)
- Use CIP-68 datum instead of metadata (more efficient CBOR encoding)
- Batch enrollments (multiple DIDs per transaction): Amortize fixed costs

**Estimated DID Enrollment Cost:**
- **On-chain helper data**: ~0.21 ADA ($0.10)
- **Off-chain helper data (hash only)**: ~0.17 ADA ($0.085)
- **With Plutus validator**: ~0.40 ADA ($0.20)

**Recommendation:** Use **off-chain storage + on-chain hash** to minimize costs. For hackathon demo, on-chain storage is acceptable (~$0.10 per enrollment).

---

## 6. Plutus Smart Contract Capabilities

### 6.1 Plutus Overview

**Plutus** is Cardano's smart contract platform, based on Haskell. Plutus scripts validate transactions and enforce business logic.

**Languages:**
- **Plutus Core**: Low-level IR (intermediate representation)
- **PlutusTx**: Haskell embedded DSL (domain-specific language)
- **Aiken**: Rust-like language (modern, ergonomic) - **Recommended**
- **OpShin**: Python-to-Plutus compiler (experimental)
- **Helios**: TypeScript-like language

**Open-Source Status:**
- ✅ Plutus: Apache 2.0 (IOG)
- ✅ Aiken: Apache 2.0 (TxPipe)
- ✅ OpShin: MIT (OpShin team)
- ✅ Helios: BSD-3-Clause

### 6.2 Plutus Script Types

**Validator Scripts:**
- Lock UTXOs at script address
- Validate spending conditions (datum, redeemer, script context)
- Use case: CIP-68 Reference NFT validator

**Minting Policies:**
- Control asset minting/burning
- One-time minting (enrollment) + burn-only (revocation)
- Use case: DID credential NFT minting policy

**Staking Scripts:**
- Validate staking rewards withdrawal
- Not directly relevant to biometric DID

### 6.3 Execution Limits

**Protocol Parameters (Mainnet as of Oct 2025):**
- **Max Execution Units**: 14,000,000 CPU steps, 14,000,000 memory units
- **Max Script Size**: 16 KB per script
- **Max Transaction Size**: 16 KB (shared with metadata)

**Typical Script Costs:**
- Simple validator (pay-to-pubkey-hash check): ~500,000 CPU, ~200,000 mem
- Complex validator (merkle proof, cryptography): ~5,000,000 CPU, ~2,000,000 mem
- **Budget Headroom**: 2-3 complex validators per transaction

### 6.4 Cryptographic Primitives in Plutus

**Built-in Functions:**
- ✅ `blake2b_256`: BLAKE2b-256 hashing (32-byte output)
- ✅ `sha2_256`, `sha3_256`: SHA-2 and SHA-3 hashing
- ✅ `verifyEd25519Signature`: Ed25519 signature verification
- ✅ `verifyEcdsaSecp256k1Signature`: ECDSA signature verification (Bitcoin/Ethereum curves)
- ❌ **Not available**: BCH decoding, fuzzy matching, biometric processing

**Implications for Biometric DID:**
- ✅ Can verify helper data hash on-chain
- ✅ Can verify cryptographic signatures (key derivation proof)
- ❌ **Cannot** perform biometric matching on-chain (too complex)
- ❌ **Cannot** decode BCH codewords on-chain (no built-in support)

**Architecture Decision:**
- **On-chain**: Store helper data hash, verify hash integrity
- **Off-chain**: Perform biometric matching, BCH decoding, key derivation
- **Proof Submission**: Submit derived key signature to prove successful match

### 6.5 Aiken Example: DID Validator

```aiken
// Aiken validator for CIP-68 Reference NFT (Biometric DID metadata)

use aiken/hash.{Blake2b_256, Hash}
use aiken/transaction.{ScriptContext, Spend}
use aiken/transaction/credential.{VerificationKey}

// Datum: Stores DID metadata
type Datum {
  owner: Hash<Blake2b_256, VerificationKey>,  // Wallet pubkey hash
  did: ByteArray,                              // DID string
  helper_data_hash: ByteArray,                 // BLAKE2b-256(helper_data)
  helper_data_uri: ByteArray,                  // IPFS CID
  revoked: Bool,
  version: Int,
}

// Redeemer: Action to perform
type Redeemer {
  Update { new_revoked: Bool }
  Burn
}

validator {
  fn validate_did_metadata(datum: Datum, redeemer: Redeemer, ctx: ScriptContext) -> Bool {
    expect Spend(own_ref) = ctx.purpose

    when redeemer is {
      // Update revocation status
      Update { new_revoked } -> {
        // Must be signed by owner
        let signed_by_owner = list.has(ctx.transaction.extra_signatories, datum.owner)

        // Find continuing output (updated datum)
        expect Some(output) = list.find(
          ctx.transaction.outputs,
          fn(o) { o.address == own_ref.address }
        )

        expect new_datum: Datum = output.datum

        // Verify only revocation status changed
        let metadata_unchanged =
          new_datum.owner == datum.owner &&
          new_datum.did == datum.did &&
          new_datum.helper_data_hash == datum.helper_data_hash &&
          new_datum.version == datum.version

        signed_by_owner && metadata_unchanged && new_datum.revoked == new_revoked
      }

      // Burn Reference NFT (permanent DID revocation)
      Burn -> {
        let signed_by_owner = list.has(ctx.transaction.extra_signatories, datum.owner)
        let nft_burned = // Check minting policy burns token

        signed_by_owner && nft_burned
      }
    }
  }
}
```

**Key Takeaways:**
- Owner (wallet pubkey hash) required to update or burn
- Metadata immutability enforced (only revocation status changeable)
- Helper data hash never changes (immutable enrollment)
- Burn action enables permanent revocation

### 6.6 Recommendation

**Smart Contract Strategy:**
- Use **Aiken** for validator development (modern, ergonomic, active community)
- Implement **CIP-68 Reference NFT validator** for metadata storage
- Enforce **owner-only updates** (revocation status)
- Keep validators simple to minimize execution costs (<1M CPU steps)
- Provide **reference implementation** in repository for transparency

---

## 7. Off-Chain Data Storage: IPFS and Arweave

### 7.1 IPFS (InterPlanetary File System)

**Overview:**
- Decentralized peer-to-peer file storage
- Content-addressed (hash = address)
- Open-source (MIT/Apache 2.0 dual license)

**Architecture:**
- **CID (Content Identifier)**: `Qm...` (base58) or `bafy...` (base32)
- **Distributed Hash Table (DHT)**: Peer discovery
- **Bitswap Protocol**: Block exchange between peers

**Open-Source Tools:**
- ✅ **IPFS Kubo** (Go implementation): Apache 2.0 + MIT
- ✅ **js-ipfs** (JavaScript implementation): Apache 2.0 + MIT
- ✅ **py-ipfs-http-client** (Python client): MIT
- ✅ **IPFS Cluster**: Pinning coordination (Apache 2.0 + MIT)

**Self-Hosting:**
```bash
# Install IPFS Kubo
wget https://dist.ipfs.io/kubo/v0.24.0/kubo_v0.24.0_linux-amd64.tar.gz
tar -xvzf kubo_v0.24.0_linux-amd64.tar.gz
cd kubo && sudo bash install.sh

# Initialize and start daemon
ipfs init
ipfs daemon

# Add file
ipfs add helper_data.bin
# Output: QmHash... (CID)

# Pin file (keep in local storage)
ipfs pin add QmHash...
```

**Advantages:**
- ✅ Free and decentralized
- ✅ Content-addressed (integrity guaranteed)
- ✅ Self-hostable (no third-party dependency)
- ✅ Open-source clients and gateways

**Limitations:**
- ❌ No persistence guarantee (requires pinning)
- ❌ Garbage collection (unpinned files deleted)
- ❌ Requires pinning service for reliability

**Pinning Services (Open-Source Options):**
- ✅ **IPFS Cluster**: Self-hosted multi-node pinning (Apache 2.0 + MIT)
- ✅ **Estuary**: Open-source pinning + Filecoin integration (MIT) - Project paused but code available
- ❌ Pinata, Web3.Storage: Paid/freemium services (not acceptable per project constraint)

**Recommendation:** Self-host IPFS node + IPFS Cluster for helper data storage. For hackathon demo, single IPFS node acceptable.

### 7.2 Arweave

**Overview:**
- Permanent data storage blockchain
- One-time payment for perpetual storage
- Open-source protocol (MIT License for some components)

**Architecture:**
- **Blockweave**: Modified blockchain with data locality
- **Proof of Access**: Miners prove access to random old data
- **Permaweb**: Permanent web applications

**Open-Source Tools:**
- ✅ **arweave-js**: JavaScript SDK (MIT)
- ✅ **ar-gql**: GraphQL query API (MIT)
- ❌ **Arweave node**: Partially open-source (some components proprietary)

**Cost:**
- **One-time payment**: ~$0.005 per MB (as of Oct 2025)
- Helper data (200 bytes): ~$0.000001 (negligible)
- **Perpetual storage**: No recurring fees

**Advantages:**
- ✅ Permanent storage (ideal for immutable helper data)
- ✅ Low cost for small files
- ✅ HTTP gateway access (easy retrieval)
- ✅ No pinning required

**Limitations:**
- ❌ Centralized miners (not fully decentralized)
- ❌ Requires AR tokens for payment
- ❌ 5-10 minute confirmation time

**Upload Example:**
```javascript
import Arweave from 'arweave';

const arweave = Arweave.init({
  host: 'arweave.net',
  port: 443,
  protocol: 'https'
});

const data = Buffer.from(helperData);
const transaction = await arweave.createTransaction({ data });
transaction.addTag('Content-Type', 'application/octet-stream');
transaction.addTag('App-Name', 'BiometricDID');
transaction.addTag('DID', didString);

await arweave.transactions.sign(transaction, wallet);
await arweave.transactions.post(transaction);

console.log(`Arweave TX: ${transaction.id}`);
console.log(`URL: https://arweave.net/${transaction.id}`);
```

**Recommendation:** Use **Arweave for production** (permanent storage, low cost). Use **IPFS for hackathon demo** (free, immediate availability).

### 7.3 Comparison: IPFS vs Arweave

| Feature | IPFS | Arweave |
|---------|------|---------|
| **Cost** | Free (self-hosted) | ~$0.005/MB (one-time) |
| **Persistence** | Requires pinning | Permanent (protocol guarantee) |
| **Availability** | Depends on pinners | Miner network |
| **Confirmation** | Immediate | 5-10 minutes |
| **Decentralization** | High (DHT-based) | Medium (miner-based) |
| **Open-Source** | Fully open-source | Mostly open-source |
| **Self-Hosting** | Easy (Kubo node) | Difficult (requires mining) |

**Recommendation:**
- **Hackathon/Demo**: IPFS (self-hosted, free, immediate)
- **Production**: Hybrid approach
  - Primary: Arweave (permanent storage)
  - Fallback: IPFS Cluster (availability)
  - On-chain: Hash + both CIDs (redundancy)

---

## 8. Query Layers and Indexers

### 8.1 Challenge: Querying Blockchain Data

**Problem:**
- Cardano node stores full blockchain (~150 GB as of Oct 2025)
- Querying UTXOs by datum or metadata is inefficient (requires full scan)
- Web applications need fast, indexed access

**Solution:** Use indexing and query layers.

### 8.2 Open-Source Query Layers

#### 8.2.1 Ogmios

**Overview:**
- Lightweight bridge to cardano-node via WebSocket/JSON-RPC
- Fast queries for UTXOs, datums, transactions
- Open-source: MPL-2.0 (Mozilla Public License)

**Repository:** https://github.com/CardanoSolutions/ogmios

**Features:**
- ✅ Real-time chain sync
- ✅ Query UTXOs by address, asset, datum hash
- ✅ Submit transactions
- ✅ Low overhead (proxies cardano-node)

**Deployment:**
```bash
# Run Ogmios (requires cardano-node running)
docker run -d \
  --name ogmios \
  -p 1337:1337 \
  -v /path/to/node-ipc:/ipc \
  cardanosolutions/ogmios:latest \
  --node-socket /ipc/node.socket \
  --host 0.0.0.0
```

**Query Example (JavaScript):**
```javascript
import { createInteractionContext, queryUtxosByAddress } from '@cardano-ogmios/client';

const context = await createInteractionContext(
  console.error,
  console.log,
  { connection: { host: 'localhost', port: 1337 } }
);

const utxos = await queryUtxosByAddress(context, [userAddress]);
console.log(`Found ${utxos.length} UTXOs`);
```

**Advantages:**
- ✅ Minimal setup (just needs cardano-node)
- ✅ No database required
- ✅ Real-time updates

**Limitations:**
- ❌ Limited historical queries (only current UTXOs)
- ❌ No indexing (queries can be slow for large datasets)

**Recommendation:** Use **Ogmios for real-time queries** (check DID existence, get current metadata).

#### 8.2.2 Kupo

**Overview:**
- Lightweight indexer for Cardano
- Stores only relevant UTXOs (filtered by address/asset)
- Optimized for dApps (fast queries, low storage)
- Open-source: MPL-2.0

**Repository:** https://github.com/CardanoSolutions/kupo

**Features:**
- ✅ Index by address, asset, datum hash, script hash
- ✅ Pattern matching (index only what you need)
- ✅ PostgreSQL backend (efficient queries)
- ✅ REST API (HTTP queries)

**Deployment:**
```bash
# Run Kupo (indexes UTXOs matching patterns)
kupo \
  --node-socket /path/to/node.socket \
  --since 72316896  # Shelley era start slot
  --match "addr1..." \
  --match "<policy_id>*" \
  --workdir /data/kupo \
  --host 0.0.0.0 \
  --port 1442
```

**Query Example:**
```bash
# Query UTXOs by address
curl http://localhost:1442/matches/addr1...

# Query UTXOs by asset (DID NFTs)
curl http://localhost:1442/matches/<policy_id>.BiometricDID*
```

**Advantages:**
- ✅ Fast queries (indexed database)
- ✅ Low storage (only filtered UTXOs)
- ✅ Pattern matching (flexible indexing)
- ✅ Self-hosted (no third-party dependency)

**Limitations:**
- ❌ Must specify patterns upfront (can't query arbitrary addresses later)
- ❌ Requires PostgreSQL

**Recommendation:** Use **Kupo for production** (efficient, indexed queries for DID registry).

#### 8.2.3 Scrolls

**Overview:**
- Full blockchain indexer and query engine
- Stores all transactions, metadata, datums, assets
- Designed for analytics and complex queries
- Open-source: Apache 2.0

**Repository:** https://github.com/txpipe/scrolls

**Features:**
- ✅ Full-text search
- ✅ SQL queries (PostgreSQL backend)
- ✅ Historical data (all transactions since genesis)
- ✅ Kafka streaming (real-time events)

**Deployment:**
```bash
# Run Scrolls (requires cardano-node + PostgreSQL)
scrolls daemon \
  --db postgres://user:pass@localhost/scrolls \
  --socket /path/to/node.socket
```

**Query Example (SQL):**
```sql
-- Find all DID enrollments (CIP-68 minting transactions)
SELECT tx_hash, metadata, block_time
FROM transactions
WHERE metadata ? '721'  -- Check for metadata label 721
  AND metadata->'721' ? '<policy_id>';
```

**Advantages:**
- ✅ Full historical data
- ✅ Complex queries (SQL)
- ✅ Analytics and reporting

**Limitations:**
- ❌ High storage requirements (~500 GB)
- ❌ Complex setup (requires PostgreSQL, Kafka for streaming)

**Recommendation:** Use **Scrolls for analytics dashboard** (track total enrollments, revocations, usage stats). Not required for core DID functionality.

### 8.3 Comparison: Ogmios vs Kupo vs Scrolls

| Feature | Ogmios | Kupo | Scrolls |
|---------|--------|------|---------|
| **Storage** | None (proxies node) | Low (~1-10 GB) | High (~500 GB) |
| **Query Speed** | Medium | Fast | Fast |
| **Indexing** | None | Pattern-based | Full |
| **Historical Data** | No | Limited | Yes |
| **Setup Complexity** | Low | Medium | High |
| **Use Case** | Real-time queries | dApp backend | Analytics |
| **License** | MPL-2.0 | MPL-2.0 | Apache 2.0 |

**Recommendation for Our System:**
- **Development**: Ogmios (simple, fast setup)
- **Production**: Kupo (efficient, indexed queries)
- **Analytics**: Scrolls (optional, for dashboard)

---

## 9. Cardano CLI and PyCardano

### 9.1 cardano-cli

**Overview:**
- Official command-line interface for Cardano node
- Build, sign, submit transactions
- Query blockchain state
- Manage keys and addresses
- Open-source: Apache 2.0

**Repository:** https://github.com/IntersectMBO/cardano-cli

**Installation:**
```bash
# Install via official binaries (recommended)
wget https://github.com/IntersectMBO/cardano-cli/releases/download/cardano-cli-8.23.0.0/cardano-cli-8.23.0.0-x86_64-linux.tar.gz
tar -xvzf cardano-cli-8.23.0.0-x86_64-linux.tar.gz
sudo mv cardano-cli /usr/local/bin/

# Or build from source (Haskell + Cabal)
git clone https://github.com/IntersectMBO/cardano-cli.git
cd cardano-cli && cabal build && cabal install
```

**Enrollment Transaction Example:**
```bash
# 1. Build transaction with metadata
cardano-cli transaction build \
  --tx-in <utxo_hash>#<index> \
  --tx-out <recipient_address>+<amount> \
  --change-address <change_address> \
  --metadata-json-file metadata.json \
  --out-file tx.raw \
  --testnet-magic 1

# metadata.json content:
# {
#   "721": {
#     "<policy_id>": {
#       "BiometricDID": {
#         "name": "Biometric DID",
#         "did": "did:cardano:testnet:addr1...",
#         "helper_data_hash": "a3b5c9..."
#       }
#     }
#   }
# }

# 2. Sign transaction
cardano-cli transaction sign \
  --tx-body-file tx.raw \
  --signing-key-file payment.skey \
  --out-file tx.signed

# 3. Submit transaction
cardano-cli transaction submit \
  --tx-file tx.signed \
  --testnet-magic 1
```

**Advantages:**
- ✅ Official tool (well-maintained)
- ✅ Full feature set (all transaction types)
- ✅ Offline signing (hardware wallet support)

**Limitations:**
- ❌ CLI-only (no programmatic API)
- ❌ Verbose commands (steep learning curve)
- ❌ Requires cardano-node running

**Recommendation:** Use **cardano-cli for advanced users and testing**. Provide wrapper scripts for common operations.

### 9.2 PyCardano

**Overview:**
- Python library for building Cardano transactions
- High-level API (easier than cardano-cli)
- Supports Plutus smart contracts
- Open-source: Apache 2.0

**Repository:** https://github.com/Python-Cardano/pycardano

**Installation:**
```bash
pip install pycardano
```

**Enrollment Transaction Example:**
```python
from pycardano import *

# 1. Setup blockchain context (Ogmios or Blockfrost)
context = OgmiosChainContext(ws_url="ws://localhost:1337", network=Network.TESTNET)

# 2. Load wallet
payment_skey = PaymentSigningKey.load("payment.skey")
payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
address = Address(payment_vkey.hash(), network=Network.TESTNET)

# 3. Build transaction with metadata
metadata = {
    721: {
        "policy_id_hex": {
            "BiometricDID": {
                "name": "Biometric DID",
                "did": "did:cardano:testnet:addr1...",
                "helper_data_hash": helper_data_hash.hex(),
            }
        }
    }
}

builder = TransactionBuilder(context)
builder.add_input_address(address)
builder.add_output(TransactionOutput(address, 2_000_000))  # 2 ADA
builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=Metadata(metadata)))

# 4. Sign and submit
signed_tx = builder.build_and_sign([payment_skey], change_address=address)
tx_hash = context.submit_tx(signed_tx)
print(f"Transaction submitted: {tx_hash}")
```

**Advantages:**
- ✅ Pythonic API (easy to integrate)
- ✅ Supports Plutus scripts (CIP-68 validators)
- ✅ Works with Ogmios or Blockfrost (flexible)
- ✅ Active development

**Limitations:**
- ❌ Smaller community than JS libraries (fewer examples)
- ❌ Some advanced features still in development

**Recommendation:** Use **PyCardano for backend implementation** (Python integrates well with biometric processing libraries).

### 9.3 Alternative Libraries

**JavaScript/TypeScript:**
- ✅ **Lucid** (TypeScript): Ergonomic transaction builder (MIT License) - https://github.com/spacebudz/lucid
- ✅ **Cardano Serialization Lib** (Rust WASM): Low-level library (Apache 2.0) - https://github.com/Emurgo/cardano-serialization-lib
- ✅ **Mesh** (TypeScript): React-focused SDK (Apache 2.0) - https://meshjs.dev/

**Rust:**
- ✅ **Pallas** (Rust): Cardano primitives and utils (Apache 2.0) - https://github.com/txpipe/pallas

**Recommendation for Our Stack:**
- **Backend (DID generation)**: PyCardano (Python + biometric libraries)
- **Frontend (enrollment UI)**: Lucid (TypeScript + CIP-30)
- **CLI Tools**: cardano-cli (advanced users)

---

## 10. Mithril: Lightweight Client Verification

### 10.1 Overview

**Mithril** is a stake-based threshold signature protocol that enables fast, trustless synchronization of Cardano blockchain state.

**Problem Solved:**
- Full node sync takes hours/days (download entire blockchain)
- Light clients need to trust third-party nodes (centralization risk)

**Solution:**
- Stake-weighted multi-signature scheme
- Lightweight clients verify snapshots (no full chain sync)
- Trustless (cryptographic proof of stake distribution)

**Specification:** https://mithril.network/doc/
**Repository:** https://github.com/input-output-hk/mithril (Apache 2.0)

### 10.2 Architecture

**Components:**
1. **Mithril Aggregator**: Coordinates signature aggregation
2. **Mithril Signer**: Stake pool operators sign snapshots
3. **Mithril Client**: Verifies and downloads snapshots

**Workflow:**
```
1. Signers (stake pools) sign blockchain snapshot
2. Aggregator combines signatures (Mithril multi-sig)
3. Client verifies aggregate signature (stake threshold met)
4. Client downloads snapshot (~3 GB vs ~150 GB full chain)
```

### 10.3 Relevance to Biometric DID

**Use Cases:**
- ✅ **Mobile Enrollment**: Lightweight client on smartphone (no full node)
- ✅ **Browser Extensions**: Verify DID state without trusted server
- ✅ **Offline Verification**: Download snapshot, verify DIDs offline

**Example: DID Verification with Mithril Client:**
```bash
# 1. Download and verify snapshot
mithril-client snapshot download latest

# 2. Query UTXOs from snapshot (using immutable database)
cardano-cli query utxo \
  --address <did_registry_address> \
  --db-path /path/to/mithril/snapshot/db

# 3. Verify DID metadata (extract datum from UTxO)
# (Off-chain: check helper data hash, revocation status)
```

**Advantages:**
- ✅ Fast bootstrap (minutes vs hours)
- ✅ Trustless (cryptographic verification)
- ✅ Low bandwidth (3 GB snapshot vs 150 GB full chain)

**Limitations:**
- ❌ Snapshots lag behind chain tip (~2 hours)
- ❌ Not suitable for real-time queries (use Ogmios/Kupo for that)

**Recommendation:** Use **Mithril for mobile wallets and browser extensions** (Phase 4: Mobile Integration). Not required for hackathon demo.

---

## 11. Hydra: Layer 2 Scaling

### 11.1 Overview

**Hydra** is Cardano's Layer 2 scaling solution, based on state channels. It enables high-throughput, low-latency transactions off-chain with on-chain settlement.

**Specification:** https://hydra.family/head-protocol/
**Repository:** https://github.com/input-output-hk/hydra (Apache 2.0)

### 11.2 Architecture

**Hydra Head:**
- Multi-party state channel (2-N participants)
- Off-chain transactions (instant finality, no fees)
- On-chain settlement (open head, close head, contest)

**Workflow:**
```
1. Open Hydra Head (on-chain transaction, commit UTXOs)
2. Participants transact off-chain (instant, free)
3. Close Hydra Head (on-chain transaction, final state)
```

### 11.3 Relevance to Biometric DID

**Use Case: Mass Enrollment Events**
- **Scenario**: Conference, hackathon, government registration drive
- **Challenge**: Thousands of enrollments in short time (blockchain congestion)
- **Solution**: Hydra Head for batch enrollment

**Example Workflow:**
```
1. Open Hydra Head (enrollment coordinator + users)
2. Users submit biometric data and sign enrollment off-chain
3. Hydra Head processes transactions instantly (no fees, no delays)
4. Close Hydra Head, commit all enrollments to mainnet (single on-chain tx)
```

**Advantages:**
- ✅ High throughput (1000+ tx/sec in Hydra Head)
- ✅ Zero fees (off-chain transactions)
- ✅ Instant finality (within Hydra Head)
- ✅ Batch settlement (amortize on-chain costs)

**Limitations:**
- ❌ Requires all participants online (liveness assumption)
- ❌ Complex setup (on-chain head lifecycle)
- ❌ Not suitable for individual enrollments (overkill)

**Recommendation:** **Phase 3 feature** (not required for hackathon). Hydra useful for mass enrollment scenarios (conferences, government programs).

---

## 12. Open-Source Cardano Ecosystem Tools

### 12.1 Node and Infrastructure

| Tool | Description | License | Repository |
|------|-------------|---------|------------|
| **cardano-node** | Full node implementation | Apache 2.0 | https://github.com/IntersectMBO/cardano-node |
| **cardano-db-sync** | Postgres database indexer | Apache 2.0 | https://github.com/IntersectMBO/cardano-db-sync |
| **cardano-wallet** | Wallet backend (REST API) | Apache 2.0 | https://github.com/cardano-foundation/cardano-wallet |
| **Daedalus** | Desktop wallet | Apache 2.0 | https://github.com/input-output-hk/daedalus |

### 12.2 Development Libraries

| Tool | Language | License | Repository |
|------|----------|---------|------------|
| **PyCardano** | Python | Apache 2.0 | https://github.com/Python-Cardano/pycardano |
| **Lucid** | TypeScript | MIT | https://github.com/spacebudz/lucid |
| **cardano-serialization-lib** | Rust (WASM) | Apache 2.0 | https://github.com/Emurgo/cardano-serialization-lib |
| **Mesh** | TypeScript | Apache 2.0 | https://meshjs.dev/ |
| **Pallas** | Rust | Apache 2.0 | https://github.com/txpipe/pallas |

### 12.3 Smart Contract Platforms

| Tool | Language | License | Repository |
|------|----------|---------|------------|
| **Aiken** | Aiken (Rust-like) | Apache 2.0 | https://github.com/aiken-lang/aiken |
| **Plutus** | Haskell | Apache 2.0 | https://github.com/IntersectMBO/plutus |
| **OpShin** | Python | MIT | https://github.com/OpShin/opshin |
| **Helios** | TypeScript-like | BSD-3-Clause | https://github.com/Hyperion-BT/helios |

### 12.4 Query Layers

| Tool | Description | License | Repository |
|------|-------------|---------|------------|
| **Ogmios** | JSON-RPC bridge | MPL-2.0 | https://github.com/CardanoSolutions/ogmios |
| **Kupo** | Lightweight indexer | MPL-2.0 | https://github.com/CardanoSolutions/kupo |
| **Scrolls** | Full indexer + analytics | Apache 2.0 | https://github.com/txpipe/scrolls |

### 12.5 Wallets (Browser Extensions)

| Wallet | License | Repository |
|--------|---------|------------|
| **Eternl** | Proprietary (but CIP-30 interface is open) | Closed source |
| **Nami** | Apache 2.0 | https://github.com/Berry-Pool/nami |
| **Yoroi** | Apache 2.0 | https://github.com/Emurgo/yoroi-frontend |
| **Flint** | Proprietary | Closed source |

**Note:** While some wallets are closed-source, they all implement CIP-30 (open standard). Users can choose any CIP-30-compatible wallet.

### 12.6 Storage

| Tool | Description | License | Repository |
|------|-------------|---------|------------|
| **IPFS Kubo** | IPFS node | Apache 2.0 + MIT | https://github.com/ipfs/kubo |
| **IPFS Cluster** | IPFS pinning | Apache 2.0 + MIT | https://github.com/ipfs-cluster/ipfs-cluster |
| **Arweave** | Permanent storage | Partially OSS | https://github.com/ArweaveTeam/arweave |

---

## 13. Architecture Recommendation

### 13.1 Technology Stack

**On-Chain Components:**
- **Metadata Standard**: CIP-68 (datum-based metadata)
- **Token Standard**: (100) Reference NFT + (222) User Token
- **Smart Contract Language**: Aiken
- **Minting Policy**: One-time minting (enrollment) + burn-only (revocation)
- **Validator**: CIP-68 Reference NFT validator (owner-only updates)

**Off-Chain Components:**
- **Storage**: IPFS (hackathon) → Arweave (production)
- **Backend**: Python + PyCardano
- **Frontend**: TypeScript + Lucid + CIP-30
- **Query Layer**: Ogmios (dev) → Kupo (prod)

**Development Tools:**
- **Node**: cardano-node (testnet/mainnet)
- **CLI**: cardano-cli (testing, advanced operations)
- **Indexer**: Kupo (filtered UTxO indexing)

### 13.2 Enrollment Flow

```
┌─────────────┐
│   Browser   │ User visits enrollment dApp
│   (React)   │
└──────┬──────┘
       │ 1. Connect wallet (CIP-30)
       ▼
┌─────────────┐
│   Wallet    │ User approves connection
│  (Eternl)   │
└──────┬──────┘
       │ 2. Get address
       ▼
┌─────────────┐
│  WebAuthn   │ Capture fingerprint (browser API)
│   or SDK    │
└──────┬──────┘
       │ 3. Biometric data (minutiae)
       ▼
┌─────────────┐
│   Backend   │ Generate helper data, DID, hash
│  (Python)   │ Upload helper data to IPFS
└──────┬──────┘
       │ 4. Helper data CID, hash, DID
       ▼
┌─────────────┐
│   Lucid     │ Build transaction (CIP-68 metadata)
│ (TypeScript)│ - Mint (100) Reference NFT + (222) User Token
└──────┬──────┘  - Store datum (DID, hash, IPFS CID, revoked=false)
       │ 5. Unsigned transaction
       ▼
┌─────────────┐
│   Wallet    │ User reviews and signs transaction
│  (CIP-30)   │
└──────┬──────┘
       │ 6. Signed transaction
       ▼
┌─────────────┐
│ cardano-node│ Transaction submitted to blockchain
│  (Testnet)  │
└──────┬──────┘
       │ 7. Transaction confirmed
       ▼
┌─────────────┐
│   Success   │ DID enrolled! NFT in wallet.
│   Screen    │ did:cardano:testnet:addr1...
└─────────────┘
```

### 13.3 Verification Flow

```
┌─────────────┐
│   Browser   │ User authenticates with biometric
│   (React)   │
└──────┬──────┘
       │ 1. Scan fingerprint
       ▼
┌─────────────┐
│  WebAuthn   │ Capture fingerprint (minutiae)
│   or SDK    │
└──────┬──────┘
       │ 2. Biometric data
       ▼
┌─────────────┐
│    Kupo     │ Query DID metadata (by wallet address)
│  (Indexer)  │
└──────┬──────┘
       │ 3. Datum (helper_data_hash, IPFS CID, revoked)
       ▼
┌─────────────┐
│    IPFS     │ Fetch helper data (by CID)
│  (Gateway)  │
└──────┬──────┘
       │ 4. Helper data
       ▼
┌─────────────┐
│   Backend   │ BCH decode + fuzzy matching
│  (Python)   │ Derive key from biometric
└──────┬──────┘
       │ 5. Derived key (or error if no match)
       ▼
┌─────────────┐
│   Result    │ Match: Grant access
│   Screen    │ No Match: Deny access
└─────────────┘
```

### 13.4 Cost Estimate

**Per DID Enrollment:**
- **Transaction Fee**: 0.17 ADA (~$0.085 @ $0.50/ADA)
- **Min UTxO**: 1.5 ADA (returned when NFT burned)
- **IPFS Storage**: Free (self-hosted)
- **Arweave Storage**: ~$0.000001 (200 bytes)

**Total Cost per User:**
- **Initial**: 1.67 ADA (1.5 ADA returnable deposit)
- **Permanent Cost**: 0.17 ADA (~$0.085)

**Scalability:**
- **Mainnet Capacity**: ~250 tx/block (~20 sec) = ~750 enrollments/minute
- **With Hydra**: 1000+ enrollments/second (off-chain batch)

---

## 14. Conclusion

Cardano provides a robust, open-source ecosystem for building decentralized biometric identity systems. The combination of **CIP-68 datum-based metadata**, **CIP-30 wallet integration**, and **open-source tooling** (PyCardano, Aiken, Ogmios, Kupo) enables a fully decentralized, cost-effective DID solution.

**Key Takeaways:**

✅ **CIP-68 (Recommended)**: Datum-based metadata for maximum flexibility and smart contract integration. Use (100) Reference NFT for metadata storage, (222) User Token for wallet ownership.

✅ **CIP-25 (Alternative)**: NFT metadata standard for simpler implementation. Good wallet support but less flexible than CIP-68.

✅ **CIP-30**: Essential for browser-based enrollment. Provides secure wallet interaction without seed export.

✅ **Off-Chain Storage**: IPFS (self-hosted) for hackathon, Arweave for production. Helper data stored off-chain, hash verified on-chain.

✅ **Query Layers**: Ogmios for development, Kupo for production indexing. Scrolls optional for analytics.

✅ **Smart Contracts**: Aiken for validator development. Keep scripts simple to minimize execution costs.

✅ **Cost-Effective**: ~$0.085 per enrollment (0.17 ADA transaction fee). 1.5 ADA returnable deposit for min UTxO.

✅ **Fully Open-Source**: All tools and libraries are open-source (Apache 2.0, MIT, MPL-2.0). No paid services required.

**Next Steps:**
- Proceed to Phase 1, Task 1: Design DID architecture and data model
- Implement CIP-68 Reference NFT validator (Aiken)
- Integrate PyCardano for backend transaction building
- Build React frontend with CIP-30 wallet connector

---

## 15. References

### Cardano Improvement Proposals (CIPs)
1. CIP-20: Transaction Message/Comment Metadata - https://cips.cardano.org/cips/cip20/
2. CIP-25: NFT Metadata Standard - https://cips.cardano.org/cips/cip25/
3. CIP-68: Datum Metadata Standard - https://cips.cardano.org/cips/cip68/
4. CIP-30: Cardano dApp-Wallet Web Bridge - https://cips.cardano.org/cips/cip30/

### Official Documentation
5. Cardano Developer Portal - https://developers.cardano.org/
6. Plutus Documentation - https://plutus.readthedocs.io/
7. Aiken Language Guide - https://aiken-lang.org/language-tour
8. cardano-cli Reference - https://github.com/IntersectMBO/cardano-cli

### Open-Source Tools
9. PyCardano - https://github.com/Python-Cardano/pycardano
10. Ogmios - https://ogmios.dev/
11. Kupo - https://cardanosolutions.github.io/kupo/
12. Lucid - https://github.com/spacebudz/lucid
13. Mithril - https://mithril.network/
14. Hydra - https://hydra.family/head-protocol/

### Storage Solutions
15. IPFS Kubo - https://docs.ipfs.tech/install/command-line/
16. IPFS Cluster - https://ipfscluster.io/
17. Arweave Documentation - https://docs.arweave.org/

### Research Papers
18. "Mithril: Stake-based Threshold Multisignatures" (IOG Research, 2022)
19. "Hydra: Fast Isomorphic State Channels" (IOG Research, 2021)

---

**Document Version:** 1.0
**Last Updated:** October 10, 2025
**Author:** Decentralized DID Research Team
**Status:** ✅ Complete - Ready for design phase (Phase 1)
