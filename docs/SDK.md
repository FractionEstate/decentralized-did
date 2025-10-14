# SDK Documentation

## Overview

The **decentralized-did** SDK provides a Python library for generating decentralized identifiers (DIDs) from biometric data using fuzzy extractors and Cardano blockchain integration.

## Installation

```bash
pip install decentralized-did
```

Or install from source:

```bash
git clone https://github.com/FractionEstate/decentralized-did
cd decentralized-did
pip install -e .
```

## Quick Start

```python
from decentralized_did import FuzzyExtractor, build_did, aggregate_finger_digests

# 1. Generate digest from biometric template
extractor = FuzzyExtractor()
digest, helper = extractor.gen(biometric_template)

# 2. Create DID
wallet_address = "addr1qx..."
did = build_did(wallet_address, digest)

# 3. Verify later with noisy recapture
verified_digest = extractor.rep(noisy_template, helper)
assert digest == verified_digest
```

## Core Components

### Biometrics Module

#### FuzzyExtractor

The core primitive for generating reproducible cryptographic keys from noisy biometric data.

```python
from decentralized_did import FuzzyExtractor

extractor = FuzzyExtractor()

# Enrollment
digest, helper = extractor.gen(template)

# Verification
verified = extractor.rep(noisy_template, helper)
```

**Methods:**

- `gen(template: bytes) -> Tuple[bytes, HelperData]`
  - **Input**: Biometric template (quantized minutiae data)
  - **Output**: (digest, helper_data)
  - **Purpose**: Enrollment phase - generate reproducible digest and helper data

- `rep(template: bytes, helper: HelperData) -> bytes`
  - **Input**: Noisy template and helper data from enrollment
  - **Output**: Reproduced digest (matches enrollment if template is similar)
  - **Purpose**: Verification phase - reproduce digest from noisy input

**Properties:**

- **Entropy**: 256 bits (for 4-finger aggregation)
- **Error Correction**: Up to 10-bit errors tolerated
- **Performance**: 41ms median gen(), 43ms median rep()
- **Security**: Cryptographically unlinkable across enrollments

#### HelperData

Data structure containing error correction information.

```python
class HelperData:
    sketch: bytes      # BCH syndrome (error correction data)
    salt: bytes        # 16-byte random salt
    auth_tag: bytes    # HMAC authentication tag
```

**Size**: 105 bytes total

**Serialization**: Use `helper.to_dict()` and `HelperData.from_dict()`

#### Multi-Finger Aggregation

Combine multiple finger digests for enhanced security.

```python
from decentralized_did import aggregate_finger_digests

# Aggregate 4 fingers
finger_digests = [
    ("thumb", digest1),
    ("index", digest2),
    ("middle", digest3),
    ("ring", digest4),
]

aggregated = aggregate_finger_digests(finger_digests)
```

**Properties:**

- **Entropy**: 64 bits per finger × 4 fingers = 256 bits total
- **Method**: XOR-based (commutative, associative)
- **Quality Threshold**: Minimum 2 fingers at ≥85% quality

### DID Module

#### build_did

Construct a W3C-compliant DID from wallet address and biometric digest.

```python
from decentralized_did import build_did

did = build_did(wallet_address, digest)
# Output: "did:cardano:mainnet:addr1qx...:Base64url(digest)"
```

**Format**: `did:cardano:{network}:{address}:{digest}`

**Parameters:**

- `wallet_address` (str): Bech32-encoded Cardano address
- `digest` (bytes): 32-byte biometric digest

**Returns**: str - Formatted DID string

#### build_metadata_payload

Create Cardano transaction metadata payload for DID registration.

```python
from decentralized_did import build_metadata_payload

metadata = build_metadata_payload(
    did="did:cardano:mainnet:addr1qx...",
    helper_storage={"type": "ipfs", "cid": "Qm..."},
    timestamp="2025-10-14T12:00:00Z"
)
```

**Metadata Label**: 674 (registered for biometric DIDs)

**Structure**:
```json
{
  "674": {
    "did": "did:cardano:mainnet:...",
    "helper": {"type": "ipfs", "cid": "Qm..."},
    "ts": "2025-10-14T12:00:00Z",
    "v": "1.0"
  }
}
```

### Storage Module

Pluggable storage backends for helper data persistence.

#### InlineStorage

Embed helper data directly in transaction metadata (< 16 KB limit).

```python
from decentralized_did import InlineStorage

storage = InlineStorage()
ref = await storage.store(helper)
# ref.type = "inline"
# ref.location = "base64:..."

retrieved = await storage.retrieve(ref)
```

**Pros**: No external dependencies, atomic with DID registration
**Cons**: Increases transaction size and cost

#### FileStorage

Store helper data in local filesystem.

```python
from decentralized_did import FileStorage

storage = FileStorage(base_dir="./helper_data")
ref = await storage.store(helper)
# ref.type = "file"
# ref.location = "./helper_data/abc123.helper"

retrieved = await storage.retrieve(ref)
```

**Pros**: Simple, fast, no external services
**Cons**: Not decentralized, requires backup strategy

#### IPFSStorage

Store helper data on IPFS decentralized network.

```python
from decentralized_did import IPFSStorage

storage = IPFSStorage(api_url="http://localhost:5001")
ref = await storage.store(helper)
# ref.type = "ipfs"
# ref.location = "QmHash..."

retrieved = await storage.retrieve(ref)
```

**Pros**: Decentralized, content-addressed, resilient
**Cons**: Requires IPFS node, potential latency

#### Custom Storage Backend

Implement your own storage backend:

```python
from decentralized_did import StorageBackend, StorageReference, HelperData

class MyStorage(StorageBackend):
    async def store(self, helper: HelperData) -> StorageReference:
        # Your storage logic
        return StorageReference(type="my_storage", location="...")

    async def retrieve(self, ref: StorageReference) -> HelperData:
        # Your retrieval logic
        return helper
```

## Usage Patterns

### Pattern 1: Single-Finger Enrollment

```python
from decentralized_did import FuzzyExtractor, build_did, InlineStorage

# 1. Capture biometric
template = capture_fingerprint()  # Your capture code

# 2. Generate digest
extractor = FuzzyExtractor()
digest, helper = extractor.gen(template)

# 3. Generate DID
wallet_address = get_user_wallet_address()
did = build_did(wallet_address, digest)

# 4. Store helper data
storage = InlineStorage()
ref = await storage.store(helper)

# 5. Register on Cardano
metadata = build_metadata_payload(did, {"type": ref.type, "location": ref.location})
tx_id = await submit_cardano_transaction(wallet_address, metadata)

print(f"DID registered: {did}")
print(f"Transaction: {tx_id}")
```

### Pattern 2: Multi-Finger Enrollment

```python
from decentralized_did import (
    FuzzyExtractor,
    aggregate_finger_digests,
    build_did,
    FileStorage,
)

# 1. Capture multiple fingers
fingers = {
    "thumb": capture_fingerprint("thumb"),
    "index": capture_fingerprint("index"),
    "middle": capture_fingerprint("middle"),
    "ring": capture_fingerprint("ring"),
}

# 2. Generate digests for each finger
extractor = FuzzyExtractor()
finger_digests = []
helpers = {}

for name, template in fingers.items():
    digest, helper = extractor.gen(template)
    finger_digests.append((name, digest))
    helpers[name] = helper

# 3. Aggregate digests
aggregated = aggregate_finger_digests(finger_digests)

# 4. Generate DID
wallet_address = get_user_wallet_address()
did = build_did(wallet_address, aggregated)

# 5. Store helper data
storage = FileStorage(base_dir="./helpers")
helper_refs = {}

for name, helper in helpers.items():
    ref = await storage.store(helper)
    helper_refs[name] = ref

# 6. Register on Cardano
metadata = build_metadata_payload(
    did,
    {"type": "file", "refs": helper_refs}
)
tx_id = await submit_cardano_transaction(wallet_address, metadata)

print(f"DID registered: {did}")
```

### Pattern 3: Verification

```python
from decentralized_did import FuzzyExtractor, aggregate_finger_digests

# 1. Retrieve helper data from storage
helpers = {}
for finger in ["thumb", "index", "middle", "ring"]:
    ref = get_helper_reference(finger)
    helpers[finger] = await storage.retrieve(ref)

# 2. Recapture biometrics
recaptured = {
    "thumb": capture_fingerprint("thumb"),
    "index": capture_fingerprint("index"),
    "middle": capture_fingerprint("middle"),
    "ring": capture_fingerprint("ring"),
}

# 3. Reproduce digests
extractor = FuzzyExtractor()
verified_digests = []

for name, template in recaptured.items():
    try:
        digest = extractor.rep(template, helpers[name])
        verified_digests.append((name, digest))
        print(f"✅ {name} verified")
    except Exception as e:
        print(f"❌ {name} failed: {e}")

# 4. Aggregate verified digests
verified_aggregated = aggregate_finger_digests(verified_digests)

# 5. Compare with enrolled DID
enrolled_did = get_enrolled_did()
expected_digest = extract_digest_from_did(enrolled_did)

if verified_aggregated == expected_digest:
    print("✅ User authenticated")
else:
    print("❌ Authentication failed")
```

## API Reference

### Biometrics

```python
# Classes
FuzzyExtractor()
HelperData(sketch: bytes, salt: bytes, auth_tag: bytes)
Minutia(x: int, y: int, angle: float, type: str)
FingerTemplate(minutiae: List[Minutia], quality: float)

# Functions
aggregate_finger_digests(digests: Sequence[Tuple[str, bytes]]) -> bytes
helpers_to_dict(helpers: Iterable[HelperData]) -> dict
minutiae_from_dicts(items: Iterable[dict]) -> List[Minutia]
```

### DID

```python
# Functions
build_did(wallet_address: str, digest: bytes) -> str
build_metadata_payload(
    did: str,
    helper_storage: dict,
    timestamp: str
) -> dict
```

### Storage

```python
# Classes
StorageBackend(ABC)
StorageReference(type: str, location: str)
InlineStorage()
FileStorage(base_dir: str)
IPFSStorage(api_url: str)

# Exceptions
StorageError(Exception)

# Factory Functions
create_storage_backend(backend_type: str, **kwargs) -> StorageBackend
get_available_backends() -> List[str]
get_backend_info(backend_type: str) -> dict
register_backend(name: str, backend_class: Type[StorageBackend])
```

## Error Handling

```python
from decentralized_did import FuzzyExtractor, StorageError

try:
    # Enrollment
    digest, helper = extractor.gen(template)

    # Verification
    verified = extractor.rep(noisy_template, helper)

except ValueError as e:
    # Invalid input (wrong size, format, etc.)
    print(f"Input error: {e}")

except RuntimeError as e:
    # Cryptographic error (too many bit errors)
    print(f"Verification failed: {e}")

except StorageError as e:
    # Storage operation failed
    print(f"Storage error: {e}")
```

## Performance

- **FuzzyExtractor.gen()**: 41ms median (17% under 50ms target)
- **FuzzyExtractor.rep()**: 43ms median (14% under 50ms target)
- **Throughput**: 23 operations/second sustained
- **Helper Data Size**: 105 bytes
- **Digest Size**: 32 bytes

## Security

- **Entropy**: 256 bits (4-finger aggregation)
- **Error Correction**: 10-bit capacity (BCH 127,64,10)
- **Unlinkability**: Cryptographically independent enrollments
- **Template Protection**: ISO/IEC 24745 compliant
- **Authentication Level**: NIST AAL2 compatible

## Testing

Run the test suite:

```bash
pytest tests/
```

Run specific test categories:

```bash
# Unit tests
pytest tests/test_fuzzy_extractor.py

# Integration tests
pytest tests/test_integration.py

# Security tests
pytest tests/test_security.py
```

## Examples

See `examples/sdk_quickstart.py` for comprehensive usage examples:

```bash
python examples/sdk_quickstart.py
```

## License

Apache 2.0 - See LICENSE file

## Support

- **Documentation**: docs/
- **GitHub Issues**: https://github.com/FractionEstate/decentralized-did/issues
- **Examples**: examples/

## Changelog

### Version 0.1.0 (2025-10-14)

- Initial SDK release
- Core biometric primitives (FuzzyExtractor, aggregation)
- DID generation and metadata payloads
- Storage backends (inline, file, IPFS)
- Comprehensive documentation and examples
