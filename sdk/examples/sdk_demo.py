#!/usr/bin/env python3
"""
SDK Demo - Working Examples
============================

Demonstrates the decentralized-did SDK with actual working code.
"""

from decentralized_did import (
    FuzzyExtractor,
    Minutia,
    FingerTemplate,
    aggregate_finger_digests,
    generate_deterministic_did,
)


# Example 1: Basic workflow
print("=" * 70)
print("SDK Demo: Biometric DID Generation")
print("=" * 70)

# Step 1: Create biometric templates (simulated)
print("\n1️⃣  Creating biometric templates...")
minutiae_thumb = [
    Minutia(x=100.5, y=200.3, angle=45.0),
    Minutia(x=150.2, y=180.9, angle=90.5),
    Minutia(x=200.7, y=250.1, angle=135.2),
]

template_thumb = FingerTemplate(
    finger_id="thumb",
    minutiae=minutiae_thumb,
    grid_size=10.0,
    angle_bins=8
)
print(f"   ✅ Thumb template: {len(template_thumb)} quantized minutiae")

# Step 2: Generate digest (enrollment)
print("\n2️⃣  Enrollment phase...")
extractor = FuzzyExtractor()
digest_thumb, helper_thumb = extractor.generate(template_thumb)
print(f"   ✅ Digest: {digest_thumb.hex()[:32]}...")
print(f"   ✅ Helper finger: {helper_thumb.finger_id}")

# Step 3: Verify (reproduce digest)
print("\n3️⃣  Verification phase...")
verified_digest = extractor.reproduce(template_thumb, helper_thumb)
if digest_thumb == verified_digest:
    print(f"   ✅ SUCCESS - Digests match!")
else:
    print(f"   ❌ FAILED")

# Step 4: Multi-finger aggregation
print("\n4️⃣  Multi-finger aggregation...")
# Create more fingers
minutiae_index = [Minutia(x=110.0, y=210.0, angle=50.0)]
template_index = FingerTemplate("index", minutiae_index)
digest_index, helper_index = extractor.generate(template_index)

minutiae_middle = [Minutia(x=120.0, y=220.0, angle=60.0)]
template_middle = FingerTemplate("middle", minutiae_middle)
digest_middle, helper_middle = extractor.generate(template_middle)

# Aggregate
digests = [
    ("thumb", digest_thumb),
    ("index", digest_index),
    ("middle", digest_middle),
]
aggregated = aggregate_finger_digests(digests)
print(f"   ✅ Aggregated: {aggregated.hex()[:32]}... ({len(aggregated)} bytes)")

# Step 5: Generate DID
print("\n5️⃣  Generating DID...")
did = generate_deterministic_did(aggregated, network="mainnet")
print(f"   ✅ DID: {did}")

print("\n" + "=" * 70)
print("Demo complete! SDK is working correctly.")
print("=" * 70)
print("\nNext steps:")
print("  • Read full documentation: docs/SDK.md")
print("  • Try CLI: dec-did --help")
print("  • See real hardware capture: examples/capture_with_libfprint.py")
print()
