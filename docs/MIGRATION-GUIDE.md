# Migration Guide: Wallet-Based → Deterministic DIDs

**Date**: October 14, 2025
**Version**: Phase 4.5
**Status**: Required for tamper-proof identity security

## Overview

This guide helps developers migrate from the old **wallet-based DID format** (vulnerable to Sybil attacks) to the new **deterministic DID format** (cryptographically enforces one person = one identity).

---

## Why Migrate?

### Old Approach (Wallet-Based) - DEPRECATED ❌

```python
from decentralized_did import build_did

wallet_address = "addr1qx2kd88c92..."
digest = biometric_digest
did = build_did(wallet_address, digest)
# Output: did:cardano:addr1qx2kd88c92...#AQIDBAUGBw
```

**Problems**:
- ✗ Different wallets = different DIDs (same person)
- ✗ Sybil attack: One person can create multiple identities
- ✗ Wallet address exposed in DID (privacy risk)
- ✗ Cannot vote once per person
- ✗ Cannot enforce "one account per person" for KYC

### New Approach (Deterministic) - REQUIRED ✅

```python
from decentralized_did.did import generate_deterministic_did

commitment = fuzzy_commitment  # From fuzzy extractor
network = "mainnet"
did = generate_deterministic_did(commitment, network)
# Output: did:cardano:mainnet:zQmXyZ1a2B3c4D5e6F7g8H9i0J
```

**Benefits**:
- ✓ Same fingerprints = same DID (always)
- ✓ Sybil resistance: One person = one identity (cryptographically enforced)
- ✓ Privacy-preserving: No wallet address in DID
- ✓ Voting: Provably one vote per person
- ✓ KYC/AML: Provably one account per person
- ✓ Multi-wallet support: Control same DID from multiple devices

---

## Breaking Changes

### 1. DID Format

| Aspect | Old Format | New Format |
|--------|-----------|------------|
| **Pattern** | `did:cardano:{wallet}#{digest}` | `did:cardano:{network}:{hash}` |
| **Example** | `did:cardano:addr1qx...#AQID` | `did:cardano:mainnet:zQmXyZ...` |
| **Length** | 100-120 chars | 60-70 chars |
| **Privacy** | Exposes wallet address | Hash only (unlinkable) |
| **Uniqueness** | Per wallet | Per person (biometric-based) |

### 2. Input Parameters

```python
# OLD: Requires wallet address + digest
build_did(wallet_address: str, digest: bytes) -> str

# NEW: Requires commitment + network
generate_deterministic_did(commitment: bytes, network: str) -> str
```

### 3. Output Encoding

| Aspect | Old Format | New Format |
|--------|-----------|------------|
| **Digest Encoding** | Base64 URL-safe | Base58 (Bitcoin/IPFS) |
| **Hash Algorithm** | SHA-256 (implicit) | BLAKE2b-256 (explicit) |
| **Collision Resistance** | 128-bit | 128-bit (same) |

---

## Step-by-Step Migration

### Step 1: Update Imports

**Before**:
```python
from decentralized_did import build_did
```

**After**:
```python
from decentralized_did.did.generator import generate_deterministic_did
```

### Step 2: Change DID Generation Call

**Before**:
```python
# Generate digest from fuzzy extractor
extractor = FuzzyExtractor()
digest, helper = extractor.generate(template)

# Generate DID (old way - uses wallet address)
wallet_address = "addr1qx2kd88c92..."
did = build_did(wallet_address, digest)
```

**After**:
```python
# Generate commitment from fuzzy extractor
extractor = FuzzyExtractor()
digest, helper = extractor.generate(template)

# Extract commitment from helper data
# (In production, fuzzy extractor should return commitment directly)
commitment = helper.get_commitment()  # Or use digest as commitment for now

# Generate DID (new way - uses commitment only)
network = "mainnet"  # or "testnet", "preprod"
did = generate_deterministic_did(commitment, network)
```

### Step 3: Update Metadata Construction

**Before (v1.0 schema)**:
```python
metadata = {
    "version": 1,
    "walletAddress": "addr1...",  # Single controller
    "biometric": {
        "idHash": base64.urlsafe_b64encode(digest).decode(),
        "helperStorage": "inline",
        "helperData": {...}
    }
}
```

**After (v1.1 schema)**:
```python
metadata = {
    "version": "1.1",
    "controllers": ["addr1...", "addr2..."],  # Multi-controller array
    "enrollmentTimestamp": "2025-10-14T12:00:00Z",
    "revoked": False,
    "revokedAt": None,
    "biometric": {
        "idHash": base58.b58encode(did_hash).decode(),
        "helperStorage": "inline",
        "helperData": {...}
    }
}
```

### Step 4: Update DID Parsing

**Before**:
```python
# Parse old format: did:cardano:{wallet}#{digest}
parts = did.split("#")
wallet_address = parts[0].replace("did:cardano:", "")
digest_b64 = parts[1]
```

**After**:
```python
# Parse new format: did:cardano:{network}:{hash}
parts = did.split(":")
method = parts[0]  # "did"
blockchain = parts[1]  # "cardano"
network = parts[2]  # "mainnet", "testnet", "preprod"
did_id = parts[3]  # Base58-encoded hash

# Decode hash
did_hash = base58.b58decode(did_id)
```

### Step 5: Update Verification Logic

**Before**:
```python
# Verify by regenerating DID
expected_did = build_did(wallet_address, digest)
if did == expected_did:
    print("Verified!")
```

**After**:
```python
# Verify by regenerating DID from commitment
expected_did = generate_deterministic_did(commitment, network)
if did == expected_did:
    print("Verified!")

# Or use built-in verification function
from decentralized_did.did.generator import verify_did_determinism
if verify_did_determinism(commitment, did, network):
    print("Verified!")
```

---

## Code Examples

### Full Enrollment Flow

```python
from decentralized_did import FuzzyExtractor
from decentralized_did.did.generator import generate_deterministic_did
from decentralized_did.cardano.transaction import CardanoTransactionBuilder

# 1. Capture biometric data
extractor = FuzzyExtractor()
template = capture_fingerprint()  # Your capture logic

# 2. Generate digest and helper data
digest, helper = extractor.generate(template)

# 3. Get commitment (for now, use digest as commitment)
# TODO: Update FuzzyExtractor to return commitment directly
commitment = digest  # Temporary workaround

# 4. Generate deterministic DID
network = "preprod"  # For testnet deployment
did = generate_deterministic_did(commitment, network)

print(f"Generated DID: {did}")
# Output: did:cardano:testnet:zQmXyZ1a2B3c4D5e6F7g8H9i0J

# 5. Build transaction metadata (v1.1 schema)
wallet_address = "addr_test1..."
metadata = {
    "version": "1.1",
    "controllers": [wallet_address],
    "enrollmentTimestamp": datetime.now(timezone.utc).isoformat(),
    "revoked": False,
    "revokedAt": None,
    "biometric": {
        "idHash": did.split(":")[-1],  # Extract hash from DID
        "helperStorage": "inline",
        "helperData": helpers_to_dict(helper)
    }
}

# 6. Check for duplicate enrollment (NEW!)
from decentralized_did.cardano.blockfrost import check_did_exists

existing = await check_did_exists(did, blockfrost_client)
if existing:
    raise ValueError(
        f"DID already enrolled on {existing['timestamp']}\n"
        f"Use add_controller() to add this wallet."
    )

# 7. Submit transaction
builder = CardanoTransactionBuilder(...)
result = builder.build_enrollment_transaction(
    did_document=did,
    metadata=metadata,
    recipient_address=wallet_address
)

print(f"Transaction: {result.tx_hash}")
```

### Full Verification Flow

```python
from decentralized_did import FuzzyExtractor
from decentralized_did.did.generator import generate_deterministic_did

# 1. Load helper data from enrollment
helper = load_helper_data(did)

# 2. Capture new biometric sample
template = capture_fingerprint()

# 3. Reproduce digest
extractor = FuzzyExtractor()
reproduced_digest = extractor.reproduce(template, helper)

# 4. Regenerate DID
commitment = reproduced_digest  # Use as commitment
network = "preprod"
verified_did = generate_deterministic_did(commitment, network)

# 5. Compare DIDs
if verified_did == did:
    print("✅ Biometric verification successful!")
else:
    print("❌ Biometric verification failed!")
```

---

## Multi-Wallet Scenario

The deterministic approach enables multi-wallet control of the same DID:

```python
# Alice enrolls with Wallet A
wallet_a = "addr1_alice_desktop..."
did = generate_deterministic_did(commitment, "mainnet")
# Output: did:cardano:mainnet:zQmAlice123

# Later, Alice adds Wallet B (mobile device)
wallet_b = "addr1_alice_mobile..."
add_controller(did, wallet_b, signed_by=wallet_a)

# Metadata now shows:
{
    "version": "1.1",
    "controllers": [
        "addr1_alice_desktop...",
        "addr1_alice_mobile..."
    ],
    ...
}

# Alice can use EITHER wallet to control her DID
# But her DID remains the same: did:cardano:mainnet:zQmAlice123
```

---

## Backward Compatibility

### Transition Period (6 months)

We support both formats during the transition:

```python
def build_did(
    wallet_address: str,
    digest: bytes,
    deterministic: bool = True,
    network: str = "mainnet"
) -> str:
    """
    Generate DID (supports both old and new formats).

    Args:
        deterministic: If True (default), uses new deterministic format.
                      If False, uses old wallet-based format (DEPRECATED).
    """
    if not deterministic:
        warnings.warn(
            "Wallet-based DID format is deprecated and vulnerable to "
            "Sybil attacks. Use deterministic=True (default).",
            DeprecationWarning,
            stacklevel=2
        )
        # Old format (DEPRECATED)
        fingerprint = _encode_digest(digest)
        return f"did:cardano:{wallet_address}#{fingerprint}"

    # New format (RECOMMENDED)
    commitment = digest  # Use digest as commitment for now
    return generate_deterministic_did(commitment, network)
```

### Detecting Format in Code

```python
def parse_did(did: str) -> Dict[str, str]:
    """Parse DID and detect format version."""
    parts = did.split(":")

    if len(parts) == 3:
        # Old format: did:cardano:{wallet}#{digest}
        method, blockchain, wallet_and_digest = parts
        if "#" in wallet_and_digest:
            wallet, digest = wallet_and_digest.split("#")
            return {
                "format": "v1.0",
                "method": method,
                "blockchain": blockchain,
                "wallet": wallet,
                "digest": digest
            }

    elif len(parts) == 4:
        # New format: did:cardano:{network}:{hash}
        method, blockchain, network, did_id = parts
        return {
            "format": "v1.1",
            "method": method,
            "blockchain": blockchain,
            "network": network,
            "did_id": did_id
        }

    raise ValueError(f"Invalid DID format: {did}")
```

---

## Testing Your Migration

### Unit Tests

```python
import pytest
from decentralized_did.did.generator import generate_deterministic_did

def test_deterministic_generation():
    """Test that same commitment produces same DID."""
    commitment = b"test_commitment_12345678901234567890"
    network = "testnet"

    did1 = generate_deterministic_did(commitment, network)
    did2 = generate_deterministic_did(commitment, network)

    assert did1 == did2, "Deterministic generation failed!"

def test_sybil_resistance():
    """Test that same biometrics with different wallets produce same DID."""
    commitment = b"alice_fingerprints_commitment_32bytes"
    network = "mainnet"

    # Alice tries with 3 different wallets
    did_wallet_a = generate_deterministic_did(commitment, network)
    did_wallet_b = generate_deterministic_did(commitment, network)
    did_wallet_c = generate_deterministic_did(commitment, network)

    # All should be the same DID
    assert did_wallet_a == did_wallet_b == did_wallet_c
    print("✅ Sybil attack prevented!")

def test_different_people_different_dids():
    """Test that different people get different DIDs."""
    alice_commitment = b"alice_commitment_32_bytes_long_xxx"
    bob_commitment = b"bob_commitment_32_bytes_long_xxxxx"
    network = "mainnet"

    alice_did = generate_deterministic_did(alice_commitment, network)
    bob_did = generate_deterministic_did(bob_commitment, network)

    assert alice_did != bob_did
    print("✅ Different people have different DIDs!")
```

### Integration Tests

```python
async def test_end_to_end_enrollment():
    """Test complete enrollment flow with deterministic DID."""
    # 1. Generate biometric data
    extractor = FuzzyExtractor()
    template = create_sample_template("thumb")
    digest, helper = extractor.generate(template)

    # 2. Generate deterministic DID
    commitment = digest
    network = "preprod"
    did = generate_deterministic_did(commitment, network)

    # 3. Check for duplicates (should be none)
    existing = await check_did_exists(did, blockfrost_client)
    assert existing is None, "DID should not exist yet"

    # 4. Enroll
    wallet_address = "addr_test1..."
    result = await enroll_did(did, wallet_address, metadata)
    assert result.success, "Enrollment failed"

    # 5. Try to enroll again (should be rejected)
    with pytest.raises(DIDAlreadyExistsError):
        await enroll_did(did, wallet_address, metadata)

    print("✅ End-to-end test passed!")
```

---

## Troubleshooting

### Error: "DID already enrolled"

**Cause**: The biometric commitment you're using has already been enrolled on the blockchain.

**Solutions**:
1. Check if you already have an enrollment with these fingerprints
2. Use `add_controller()` to add a new wallet instead of enrolling again
3. If this is a legitimate re-enrollment, use the revocation mechanism first

```python
# Check existing enrollment
existing = await check_did_exists(did, blockfrost_client)
if existing:
    print(f"DID enrolled on: {existing['timestamp']}")
    print(f"Controllers: {existing['controllers']}")

    # Add new controller instead
    await add_controller(did, new_wallet_address, signed_by=existing['controllers'][0])
```

### Error: "Invalid network parameter"

**Cause**: Network must be "mainnet", "testnet", or "preprod".

**Solution**:
```python
# ❌ WRONG
did = generate_deterministic_did(commitment, "preview")

# ✅ CORRECT
did = generate_deterministic_did(commitment, "preprod")
```

### Error: "Commitment cannot be empty"

**Cause**: You passed an empty bytes object as commitment.

**Solution**:
```python
# Ensure commitment has data
assert len(commitment) > 0, "Commitment is empty!"
assert len(commitment) >= 32, "Commitment too short (need at least 32 bytes)"
```

---

## FAQ

### Q: Can I convert an old wallet-based DID to deterministic format?

**A**: No, they are fundamentally different formats. You need to:
1. Re-enroll with the new deterministic approach
2. Revoke the old wallet-based DID (if on-chain)
3. Update all references to use the new DID

### Q: What happens to my old DIDs?

**A**: Old wallet-based DIDs will continue to work during the 6-month transition period, but:
- They remain vulnerable to Sybil attacks
- They expose wallet addresses (privacy risk)
- They won't benefit from multi-controller support
- **We strongly recommend migrating immediately**

### Q: Can I use the same DID across multiple blockchains?

**A**: The DID method (`did:cardano`) is Cardano-specific. For cross-chain DIDs, you would need:
- Different DID methods (`did:eth`, `did:btc`, etc.)
- But the same biometric commitment can generate different DIDs for different chains

### Q: How do I verify a DID is deterministic?

**A**: Check the format:
```python
def is_deterministic_did(did: str) -> bool:
    """Check if DID uses deterministic format."""
    parts = did.split(":")
    # Deterministic: did:cardano:{network}:{hash} (4 parts)
    # Wallet-based: did:cardano:{wallet}#{digest} (3 parts with #)
    return len(parts) == 4 and "#" not in did
```

### Q: What if I lose my wallet?

**A**: With deterministic DIDs, you can recover:
1. Re-enroll your fingerprints with a new wallet
2. This generates the SAME DID (deterministic property)
3. Add the new wallet as a controller
4. Remove the old (lost) wallet from controllers

You don't lose your identity, just the specific wallet keys.

---

## Additional Resources

- **Audit Report**: [`docs/AUDIT-REPORT.md`](./AUDIT-REPORT.md)
- **Security Architecture**: [`docs/tamper-proof-identity-security.md`](./tamper-proof-identity-security.md)
- **Sybil Resistance Design**: [`docs/sybil-resistance-design.md`](./sybil-resistance-design.md)
- **API Reference**: [`docs/SDK.md`](./SDK.md)
- **Cardano Integration**: [`docs/cardano-integration.md`](./cardano-integration.md)

---

## Support

If you encounter issues during migration:

1. **Check the audit report**: [`docs/AUDIT-REPORT.md`](./AUDIT-REPORT.md)
2. **Review test examples**: [`tests/test_did_generator.py`](../tests/test_did_generator.py)
3. **Ask for help**: Open a GitHub issue with:
   - Current code (old approach)
   - Desired outcome (new approach)
   - Error messages
   - Python version and dependencies

---

**Migration Status**: Required for Phase 4.5+
**Last Updated**: October 14, 2025
**Transition Period**: 6 months (until April 2026)
