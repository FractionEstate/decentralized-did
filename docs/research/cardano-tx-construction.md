# Cardano Transaction Construction Research

**Phase 4 Task 1**: Research document for building Cardano transactions with biometric DID metadata.

**Date**: October 14, 2025
**Status**: Research Phase
**Goal**: Understand Cardano transaction construction for deploying biometric DIDs on testnet/mainnet

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Cardano Transaction Basics](#cardano-transaction-basics)
3. [Metadata Specification](#metadata-specification)
4. [Tools & Libraries](#tools--libraries)
5. [Transaction Building Process](#transaction-building-process)
6. [Implementation Strategy](#implementation-strategy)
7. [Open-Source Requirements](#open-source-requirements)
8. [Next Steps](#next-steps)

---

## Executive Summary

### Research Objectives
- Understand Cardano transaction structure and metadata encoding
- Identify open-source tools for transaction construction
- Design Python-based transaction builder for biometric DID metadata
- Plan testnet deployment strategy

### Key Findings
✅ **CIP-20** defines transaction metadata structure (label 674 available)
✅ **cardano-serialization-lib** provides WASM-based transaction building
✅ **PyCardano** offers native Python transaction construction
✅ **Blockfrost** provides open-source API for chain interaction
✅ **Ogmios** offers WebSocket-based node communication

### Recommended Approach
**Primary**: Use **PyCardano** (pure Python, Apache 2.0 license)
**Fallback**: Python bindings for cardano-serialization-lib
**API**: Blockfrost for testnet queries (free tier available)

---

## Cardano Transaction Basics

### Transaction Structure

A Cardano transaction consists of:

```
Transaction {
  body: TransactionBody {
    inputs: [TxIn],           // UTXOs being spent
    outputs: [TxOut],         // New UTXOs created
    fee: Coin,                // Transaction fee in lovelace
    ttl: Slot,                // Time-to-live (optional)
    certificates: [],         // Staking certificates (optional)
    metadata: AuxiliaryData   // ← Biometric DID metadata goes here
  },
  witnesses: TransactionWitnesses {
    vkeys: [VKeyWitness],     // Signature witnesses
    scripts: [],              // Smart contracts (optional)
  },
  auxiliary_data: AuxiliaryData  // Metadata payload
}
```

### Key Concepts

**UTXO Model**
- Cardano uses Unspent Transaction Output (UTXO) model
- Each transaction consumes inputs and produces outputs
- Must select UTXOs with sufficient balance (ADA + fee)

**Transaction Fees**
- Calculated based on size: `a + b × size` (a=155381, b=44 for current era)
- Metadata increases transaction size → higher fees
- Typical DID metadata: ~500-2000 bytes → ~0.3-0.5 ADA fee

**Metadata Limits**
- Maximum metadata size: **16 KB** per transaction
- Biometric helper data: ~105 bytes per finger
- 4-finger enrollment: ~500 bytes total (well under limit)
- Large enrollments: Use external storage (IPFS) with URI reference

---

## Metadata Specification

### CIP-20: Transaction Message/Comment Metadata

**Standard**: [CIP-20](https://cips.cardano.org/cips/cip20/)
**Purpose**: Attach arbitrary messages to transactions
**Label**: We'll use **label 674** (available, aligns with "DID" in hex: 0x02AA)

### Metadata Structure

```json
{
  "674": {
    "msg": [
      "Biometric DID Enrollment",
      {
        "version": "1.0",
        "did": "did:cardano:addr1qx2kd88...#base64digest",
        "helperStorage": "inline",
        "helperData": [
          {
            "fingerId": "thumb",
            "sketch": "base64...",
            "salt": "base64...",
            "authTag": "base64..."
          }
        ],
        "timestamp": "2025-10-14T12:00:00Z",
        "signature": "optional_wallet_signature"
      }
    ]
  }
}
```

### CBOR Encoding

Cardano metadata must be CBOR-encoded:
- Strings: UTF-8 encoded
- Byte arrays: Base64 or hex encoding
- Maps: JSON-like key-value pairs
- Arrays: Ordered lists

**Encoding library**: `cbor2` (Python, MIT license)

### Size Optimization

For large enrollments (10 fingers, ~1050 bytes):

**Option 1**: External storage
```json
{
  "674": {
    "msg": ["Biometric DID Enrollment", {
      "version": "1.0",
      "did": "did:cardano:addr1qx...#digest",
      "helperStorage": "external",
      "helperUri": "ipfs://QmX7K8eFJm9vVPqS8wP3ZYcZ9...",
      "helperHash": "sha256:abc123..."
    }]
  }
}
```

**Option 2**: Multiple transactions
- Split enrollment across multiple transactions
- Each transaction: 1-2 fingers
- Final transaction: Reference all prior transactions

---

## Tools & Libraries

### 1. PyCardano (Recommended)

**Repository**: https://github.com/Python-Cardano/pycardano
**License**: Apache 2.0 ✅
**Language**: Pure Python
**Status**: Active development (500+ stars)

**Features**:
- Native Python transaction building
- Address generation and validation
- CBOR encoding/decoding
- Blockfrost integration
- Plutus script support
- **No external dependencies** (no WASM, no Rust)

**Installation**:
```bash
pip install pycardano
```

**Example**:
```python
from pycardano import (
    BlockFrostChainContext,
    TransactionBuilder,
    TransactionOutput,
    AuxiliaryData,
    Metadata,
)

# Connect to testnet
context = BlockFrostChainContext(
    project_id="YOUR_BLOCKFROST_API_KEY",
    network=Network.TESTNET
)

# Build transaction
builder = TransactionBuilder(context)
builder.add_input_address(source_address)
builder.add_output(TransactionOutput(target_address, amount))

# Add biometric DID metadata
metadata = Metadata({
    674: {
        "msg": ["Biometric DID Enrollment", {
            "did": "did:cardano:...",
            "helperData": [...]
        }]
    }
})
builder.auxiliary_data = AuxiliaryData(metadata=metadata)

# Build and sign
tx_body = builder.build()
tx = builder.build_and_sign([signing_key], change_address)

# Submit
tx_id = context.submit_tx(tx.to_cbor())
```

### 2. cardano-serialization-lib

**Repository**: https://github.com/Emurgo/cardano-serialization-lib
**License**: MIT ✅
**Language**: Rust (WASM bindings)
**Status**: Official Emurgo library

**Features**:
- Low-level CBOR primitives
- Transaction building
- Used by most Cardano wallets
- **Requires WASM runtime**

**Python Bindings**: Available but requires compilation

**Installation**:
```bash
pip install cardano-serialization-lib
```

**Use Case**: If PyCardano lacks specific features

### 3. Blockfrost API

**Website**: https://blockfrost.io
**Repository**: https://github.com/blockfrost/blockfrost-backend-ryo
**License**: Apache 2.0 ✅
**Type**: REST API + Python SDK

**Features**:
- Query blockchain data (UTXOs, addresses, transactions)
- Submit transactions
- **Free tier**: 50,000 requests/day (sufficient for development)
- Open-source backend (self-hostable)

**Installation**:
```bash
pip install blockfrost-python
```

**Example**:
```python
from blockfrost import BlockFrostApi, ApiError

api = BlockFrostApi(
    project_id='YOUR_PROJECT_ID',
    base_url='https://cardano-testnet.blockfrost.io/api/v0'
)

# Get address UTXOs
utxos = api.address_utxos('addr_test1...')

# Submit transaction
tx_hash = api.tx_submit('signed_tx_cbor')
```

### 4. Ogmios

**Repository**: https://github.com/CardanoSolutions/ogmios
**License**: MPL-2.0 ✅
**Type**: WebSocket server (JSON-RPC)

**Features**:
- Direct cardano-node communication
- Real-time chain sync
- Transaction submission
- Mempool monitoring
- **Requires running cardano-node**

**Use Case**: Advanced integration, lower-level control

**Installation**:
```bash
docker run -p 1337:1337 cardanosolutions/ogmios
```

**Python Client**:
```python
import websockets
import json

async def submit_tx(tx_cbor):
    uri = "ws://localhost:1337"
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "jsonwsp/request",
            "version": "1.0",
            "servicename": "ogmios",
            "methodname": "SubmitTx",
            "args": {"submit": tx_cbor}
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        return json.loads(response)
```

### 5. Kupo (DID Indexing)

**Repository**: https://github.com/CardanoSolutions/kupo
**License**: MPL-2.0 ✅
**Type**: Lightweight chain indexer

**Features**:
- Pattern-based UTXO indexing
- Query by address, policy ID, or metadata label
- **Optimized for DID lookups** (metadata label 674)
- REST API

**Use Case**: Fast DID resolution and discovery

**Installation**:
```bash
docker run -p 1442:1442 cardanosolutions/kupo \
  --match "*@674" \
  --since origin
```

**Query Example**:
```bash
# Find all DIDs by metadata label
curl http://localhost:1442/matches/674

# Find DIDs for specific address
curl http://localhost:1442/matches/addr1qx2kd88...
```

---

## Transaction Building Process

### Step 1: Address and Key Generation

```python
from pycardano import (
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    Network,
)

# Generate signing key
signing_key = PaymentSigningKey.generate()
verification_key = PaymentVerificationKey.from_signing_key(signing_key)

# Derive address
address = Address(verification_key.hash(), network=Network.TESTNET)

print(f"Address: {address}")
print(f"Signing key: {signing_key.to_bech32()}")
```

### Step 2: UTXO Selection

```python
from pycardano import BlockFrostChainContext

context = BlockFrostChainContext(
    project_id="testnet_api_key",
    network=Network.TESTNET
)

# Get available UTXOs
utxos = context.utxos(str(address))

# Select UTXO with sufficient balance
def select_utxo(utxos, required_amount):
    for utxo in utxos:
        if utxo.output.amount.coin >= required_amount:
            return utxo
    raise ValueError("Insufficient funds")

utxo = select_utxo(utxos, 2_000_000)  # 2 ADA
```

### Step 3: Metadata Construction

```python
from decentralized_did import build_metadata_payload

# Generate biometric DID metadata
metadata_payload = build_metadata_payload(
    did="did:cardano:addr_test1qx...#digest",
    helper_data=[
        {
            "fingerId": "thumb",
            "sketch": base64.b64encode(sketch_bytes).decode(),
            "salt": base64.b64encode(salt_bytes).decode(),
            "authTag": base64.b64encode(tag_bytes).decode(),
        }
    ],
    storage="inline",
    timestamp=datetime.utcnow().isoformat() + "Z"
)

# Wrap in CIP-20 format
metadata = Metadata({
    674: {
        "msg": ["Biometric DID Enrollment", metadata_payload]
    }
})
```

### Step 4: Transaction Building

```python
from pycardano import TransactionBuilder, TransactionOutput

builder = TransactionBuilder(context)

# Add inputs
builder.add_input(utxo)

# Add output (send change back to self)
output = TransactionOutput(address, utxo.output.amount.coin - 500_000)
builder.add_output(output)

# Add metadata
builder.auxiliary_data = AuxiliaryData(metadata=metadata)

# Build transaction body
tx_body = builder.build(change_address=address)
```

### Step 5: Signing

```python
# Sign transaction
signed_tx = tx_body.sign([signing_key])

# Serialize to CBOR
tx_cbor = signed_tx.to_cbor()

print(f"Transaction size: {len(tx_cbor)} bytes")
print(f"Estimated fee: {tx_body.fee / 1_000_000} ADA")
```

### Step 6: Submission

```python
# Submit to testnet
tx_id = context.submit_tx(signed_tx)

print(f"✅ Transaction submitted!")
print(f"TX ID: {tx_id}")
print(f"Explorer: https://testnet.cardanoscan.io/transaction/{tx_id}")
```

### Step 7: Verification

```python
import time

# Wait for confirmation
time.sleep(20)  # Wait for block inclusion

# Query transaction
tx = context.api.transaction(tx_id)

print(f"Confirmations: {tx.block_height}")
print(f"Metadata: {tx.metadata}")
```

---

## Implementation Strategy

### Phase 4.1: Core Transaction Builder

**Goal**: Python module for Cardano transaction construction

**Module**: `src/decentralized_did/cardano/transaction.py`

**Features**:
- Transaction building with metadata
- UTXO selection algorithm
- Fee estimation
- Multi-signature support (optional)
- Dry-run mode (validation without submission)

**API Design**:
```python
from decentralized_did.cardano import CardanoTransactionBuilder

builder = CardanoTransactionBuilder(
    network="testnet",
    api_key="blockfrost_key"
)

# Build enrollment transaction
tx = builder.build_enrollment_tx(
    wallet_address="addr_test1...",
    signing_key="ed25519_key",
    did_metadata=metadata_payload,
    dry_run=True  # Validate without submitting
)

if tx.valid:
    tx_id = tx.submit()
    print(f"Submitted: {tx_id}")
```

### Phase 4.2: CLI Integration

**Goal**: Extend `dec-did` CLI with transaction commands

**New Commands**:
```bash
# Deploy DID to testnet
dec-did deploy \
  --network testnet \
  --wallet-key wallet.skey \
  --enrollment enrollment.json \
  --api-key $BLOCKFROST_KEY

# Query DID from chain
dec-did query \
  --network testnet \
  --address addr_test1... \
  --api-key $BLOCKFROST_KEY

# Verify DID on-chain
dec-did verify-onchain \
  --network testnet \
  --tx-hash abc123... \
  --api-key $BLOCKFROST_KEY
```

### Phase 4.3: Demo Wallet Integration

**Goal**: Integrate transaction builder into demo wallet

**Components**:
1. **Transaction Service** (`demo-wallet/src/services/cardano-tx.ts`)
   - Call Python backend for transaction building
   - Bridge TypeScript ↔ Python via REST API or IPC

2. **DID Deployment UI** (`demo-wallet/src/ui/pages/DeployDID/`)
   - Enrollment flow with testnet deployment
   - Transaction status tracking
   - Explorer link display

3. **Backend API** (optional Node.js wrapper)
   - Express server wrapping Python transaction builder
   - WebSocket for real-time updates

### Phase 4.4: Testing Strategy

**Test Levels**:
1. **Unit Tests**: Transaction building logic
2. **Integration Tests**: Blockfrost API interactions
3. **Testnet Tests**: Real blockchain deployment
4. **Regression Tests**: Fee estimation accuracy

**Test Data**:
- Mock UTXOs
- Sample biometric metadata
- Testnet faucet addresses (free test ADA)

---

## Open-Source Requirements

### License Compliance ✅

All tools meet the open-source constraint:

| Tool | License | Status |
|------|---------|--------|
| PyCardano | Apache 2.0 | ✅ Open |
| cardano-serialization-lib | MIT | ✅ Open |
| Blockfrost | Apache 2.0 | ✅ Open + Free tier |
| Ogmios | MPL-2.0 | ✅ Open |
| Kupo | MPL-2.0 | ✅ Open |
| cbor2 | MIT | ✅ Open |

**No paid services required!**
- Blockfrost free tier: 50,000 req/day
- Self-hostable alternatives: Ogmios + Kupo + cardano-node
- Testnet ADA: Free from faucet

### Self-Hosting Option

For complete independence:

```yaml
# docker-compose.yml
version: '3.8'
services:
  cardano-node:
    image: inputoutput/cardano-node:latest
    network_mode: host

  ogmios:
    image: cardanosolutions/ogmios:latest
    ports:
      - "1337:1337"
    depends_on:
      - cardano-node

  kupo:
    image: cardanosolutions/kupo:latest
    ports:
      - "1442:1442"
    command: --match "*@674" --since origin
    depends_on:
      - cardano-node
```

**Trade-offs**:
- ✅ Complete independence
- ✅ No API rate limits
- ❌ Requires ~30GB disk space
- ❌ ~6 hours sync time (testnet)

**Recommendation**: Use Blockfrost for development, self-host for production.

---

## Next Steps

### Immediate (Phase 4 Task 2)
1. ✅ Research complete → Create this document
2. ⏳ Install PyCardano and dependencies
3. ⏳ Implement `CardanoTransactionBuilder` class
4. ⏳ Add fee estimation algorithm
5. ⏳ Write unit tests for transaction building

### Short-term (Phase 4 Task 3)
1. Deploy test transaction to testnet
2. Verify metadata on explorer
3. Integrate with CLI (`dec-did deploy`)
4. Create demo wallet deployment UI

### Medium-term (Phase 4 Task 4-6)
1. Draft CIP for biometric DID method
2. Build CIP-30 wallet connector
3. Test with Nami, Eternl, Yoroi wallets
4. Optimize transaction fees

### Long-term (Phase 5+)
1. Mainnet deployment
2. Plutus verification scripts
3. On-chain DID registry
4. Revocation mechanisms

---

## References

### Cardano Documentation
- **CIP-20**: https://cips.cardano.org/cips/cip20/
- **Transaction Format**: https://docs.cardano.org/cardano-components/cardano-serialization-lib
- **Metadata**: https://developers.cardano.org/docs/transaction-metadata/

### Open-Source Tools
- **PyCardano**: https://github.com/Python-Cardano/pycardano
- **Blockfrost**: https://blockfrost.io
- **Ogmios**: https://ogmios.dev
- **Kupo**: https://cardanosolutions.github.io/kupo/

### Standards
- **W3C DID Core**: https://www.w3.org/TR/did-core/
- **DID Resolution**: https://w3c-ccg.github.io/did-resolution/
- **CIP Index**: https://cips.cardano.org/

---

## Conclusion

**Phase 4 Task 1 complete!** We have:
- ✅ Researched Cardano transaction structure
- ✅ Identified open-source tools (PyCardano + Blockfrost)
- ✅ Designed implementation strategy
- ✅ Validated open-source compliance
- ✅ Defined next steps

**Recommendation**: Proceed with **PyCardano** for pure Python transaction building. Use **Blockfrost free tier** for testnet API. Self-host infrastructure for production mainnet deployment.

**Next**: Implement `CardanoTransactionBuilder` class (Phase 4 Task 2).
