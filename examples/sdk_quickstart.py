#!/usr/bin/env python3
"""
SDK Quick Start Examples
=========================

This file demonstrates the core SDK functionality for the decentralized-did toolkit.

Installation
------------
    pip install decentralized-did

Usage
-----
    python examples/sdk_quickstart.py
"""

import asyncio
from decentralized_did import (
    # Biometrics
    FuzzyExtractor,
    HelperData,
    Minutia,
    FingerTemplate,
    aggregate_finger_digests,

    # DID generation
    build_did,
    build_metadata_payload,

    # Storage
    InlineStorage,
    FileStorage,
    IPFSStorage,
)


# ============================================================================
# Helper: Create sample fingerprint templates
# ============================================================================

def create_sample_template(finger_id: str, seed: int = 0) -> FingerTemplate:
    """Create a sample fingerprint template for demonstration."""
    import random
    random.seed(seed)

    # Generate 20-30 random minutiae points
    num_minutiae = random.randint(20, 30)
    minutiae = []

    for i in range(num_minutiae):
        minutiae.append(Minutia(
            x=random.randint(0, 500),
            y=random.randint(0, 500),
            angle=random.uniform(0, 360),
            type=random.choice(["ending", "bifurcation"])
        ))

    return FingerTemplate(
        finger_id=finger_id,
        minutiae=minutiae,
        quality=random.uniform(0.7, 0.95),
        grid_size=10.0,
        angle_bins=8
    )
# ============================================================================
# Example 1: Basic Enrollment and Verification
# ============================================================================


def example_basic_enrollment():
    """Demonstrate single-finger enrollment and verification."""
    print("=" * 70)
    print("Example 1: Basic Enrollment and Verification")
    print("=" * 70)

    # Initialize fuzzy extractor
    extractor = FuzzyExtractor()

    # Simulate biometric template (in practice, from fingerprint scanner)
    # This would be minutiae data from actual fingerprint capture
    template = b"simulated_fingerprint_minutiae_data_32bytes_long_12345"

    # ENROLLMENT: Generate digest and helper data
    print("\n1. Enrollment Phase:")
    print(f"   Template length: {len(template)} bytes")

    digest, helper = extractor.gen(template)

    print(f"   Digest: {digest.hex()[:32]}... ({len(digest)} bytes)")
    print(f"   Helper data size: {len(helper.sketch)} bytes")
    print(f"   Salt: {helper.salt.hex()[:16]}...")

    # VERIFICATION: Reproduce digest from noisy template
    print("\n2. Verification Phase:")

    # Simulate noisy recapture (slight variations in template)
    noisy_template = template[:28] + b"noise123"  # Slight modification

    try:
        verified_digest = extractor.rep(noisy_template, helper)

        if digest == verified_digest:
            print("   ✅ Verification successful!")
            print(
                f"   Reproduced digest matches: {verified_digest.hex()[:32]}...")
        else:
            print("   ❌ Verification failed: digests don't match")

    except Exception as e:
        print(f"   ❌ Verification error: {e}")

    print()


# ============================================================================
# Example 2: Multi-Finger Aggregation
# ============================================================================

def example_multi_finger():
    """Demonstrate multi-finger aggregation for enhanced security."""
    print("=" * 70)
    print("Example 2: Multi-Finger Aggregation")
    print("=" * 70)

    extractor = FuzzyExtractor()

    # Simulate 4 finger templates
    fingers = {
        "thumb": b"thumb_minutiae_data_32_bytes_" + b"0" * 8,
        "index": b"index_minutiae_data_32_bytes_" + b"1" * 8,
        "middle": b"middle_minutiae_data_32_bytes" + b"2" * 8,
        "ring": b"ring_minutiae_data_32_bytes__" + b"3" * 8,
    }

    print("\n1. Enrolling 4 fingers:")
    finger_digests = []
    helpers = {}

    for name, template in fingers.items():
        digest, helper = extractor.gen(template)
        finger_digests.append((name, digest))
        helpers[name] = helper
        print(f"   ✅ {name.capitalize()}: {digest.hex()[:16]}...")

    # Aggregate digests
    print("\n2. Aggregating digests:")
    aggregated = aggregate_finger_digests(finger_digests)
    print(
        f"   Combined digest: {aggregated.hex()[:32]}... ({len(aggregated)} bytes)")

    # Verification with all 4 fingers
    print("\n3. Verification with all 4 fingers:")
    verified_digests = []

    for name, template in fingers.items():
        # Simulate slight noise
        noisy = template[:-4] + b"nsyn"
        try:
            verified = extractor.rep(noisy, helpers[name])
            verified_digests.append((name, verified))
            print(f"   ✅ {name.capitalize()} verified")
        except Exception as e:
            print(f"   ❌ {name.capitalize()} failed: {e}")

    # Re-aggregate verified digests
    verified_aggregated = aggregate_finger_digests(verified_digests)

    if aggregated == verified_aggregated:
        print(f"\n   ✅ Aggregated verification successful!")
    else:
        print(f"\n   ❌ Aggregated verification failed")

    print()


# ============================================================================
# Example 3: DID Generation
# ============================================================================

def example_did_generation():
    """Demonstrate DID generation from biometric digest."""
    print("=" * 70)
    print("Example 3: DID Generation")
    print("=" * 70)

    # Generate biometric digest (from Example 1 or 2)
    extractor = FuzzyExtractor()
    template = b"biometric_template_data_32_bytes_long_padding123"
    digest, helper = extractor.gen(template)

    # Cardano wallet address (from user's wallet)
    wallet_address = "addr1qx2kd88c92l6j5jhkjehfvjdj2gvfe5g8c4v7y4k3hl2p8jv2kd88c92l6"

    print("\n1. Input:")
    print(f"   Wallet address: {wallet_address}")
    print(f"   Biometric digest: {digest.hex()[:32]}...")

    # Build DID
    did = build_did(wallet_address, digest)

    print(f"\n2. Generated DID:")
    print(f"   {did}")

    # Build metadata payload
    metadata = build_metadata_payload(
        did=did,
        helper_storage={"type": "ipfs", "cid": "QmExampleCID123"},
        timestamp="2025-10-14T12:00:00Z"
    )

    print(f"\n3. Metadata payload:")
    print(f"   Label: {metadata['674']['did']}")
    print(f"   Helper storage: {metadata['674']['helper']}")
    print(f"   Timestamp: {metadata['674']['ts']}")

    print()


# ============================================================================
# Example 4: Storage Backends
# ============================================================================

async def example_storage_backends():
    """Demonstrate different storage backend options."""
    print("=" * 70)
    print("Example 4: Storage Backends")
    print("=" * 70)

    # Generate helper data
    extractor = FuzzyExtractor()
    template = b"fingerprint_template_data_for_storage_examples123"
    digest, helper = extractor.gen(template)

    print(f"\n1. Helper data to store:")
    print(f"   Size: {len(helper.sketch)} bytes")
    print(f"   Salt: {helper.salt.hex()[:16]}...")

    # ---- Inline Storage ----
    print(f"\n2. Inline Storage (embed in metadata):")
    inline = InlineStorage()
    ref_inline = await inline.store(helper)
    print(f"   Type: {ref_inline.type}")
    print(f"   Location: {ref_inline.location[:40]}...")

    # Retrieve
    retrieved = await inline.retrieve(ref_inline)
    assert retrieved.sketch == helper.sketch
    print(f"   ✅ Retrieved and verified")

    # ---- File Storage ----
    print(f"\n3. File Storage (local filesystem):")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        file_storage = FileStorage(base_dir=tmpdir)
        ref_file = await file_storage.store(helper)
        print(f"   Type: {ref_file.type}")
        print(f"   Location: {ref_file.location}")

        # Retrieve
        retrieved = await file_storage.retrieve(ref_file)
        assert retrieved.sketch == helper.sketch
        print(f"   ✅ Retrieved and verified")

    # ---- IPFS Storage (demo mode) ----
    print(f"\n4. IPFS Storage (requires running IPFS node):")
    print(f"   ⏭️  Skipped (requires IPFS daemon)")
    print(f"   Usage:")
    print(f"      ipfs = IPFSStorage(api_url='http://localhost:5001')")
    print(f"      ref = await ipfs.store(helper)")
    print(f"      # Returns: StorageReference(type='ipfs', location='Qm...')")

    print()


# ============================================================================
# Example 5: Complete Workflow
# ============================================================================

async def example_complete_workflow():
    """Demonstrate complete enrollment-to-DID workflow."""
    print("=" * 70)
    print("Example 5: Complete Workflow (Enrollment → DID → Storage)")
    print("=" * 70)

    # Step 1: Capture biometrics (4 fingers)
    print("\n📸 Step 1: Capture Biometrics")
    fingers = {
        "thumb": b"thumb_template_" + b"0" * 22,
        "index": b"index_template_" + b"1" * 22,
        "middle": b"middle_template" + b"2" * 22,
        "ring": b"ring_template__" + b"3" * 22,
    }
    print(f"   Captured {len(fingers)} fingers")

    # Step 2: Generate digests and helper data
    print("\n🔐 Step 2: Generate Cryptographic Digests")
    extractor = FuzzyExtractor()
    finger_digests = []
    helpers = {}

    for name, template in fingers.items():
        digest, helper = extractor.gen(template)
        finger_digests.append((name, digest))
        helpers[name] = helper
        print(f"   ✅ {name.capitalize()}: digest generated")

    # Step 3: Aggregate digests
    print("\n🔗 Step 3: Aggregate Multi-Finger Digests")
    aggregated_digest = aggregate_finger_digests(finger_digests)
    print(f"   Combined digest: {aggregated_digest.hex()[:32]}...")

    # Step 4: Generate DID
    print("\n🆔 Step 4: Generate Decentralized Identifier")
    wallet_address = "addr1qx2kd88c92l6j5jhkjehfvjdj2gvfe5g8c4v7y4k3hl2p8jv2kd88c92l6"
    did = build_did(wallet_address, aggregated_digest)
    print(f"   DID: {did}")

    # Step 5: Store helper data
    print("\n💾 Step 5: Store Helper Data")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        file_storage = FileStorage(base_dir=tmpdir)

        # Store all 4 helper data files
        helper_refs = {}
        for name, helper in helpers.items():
            ref = await file_storage.store(helper)
            helper_refs[name] = ref
            print(f"   ✅ {name.capitalize()}: {ref.location}")

    # Step 6: Create metadata payload
    print("\n📝 Step 6: Create Cardano Metadata Payload")
    metadata = build_metadata_payload(
        did=did,
        helper_storage={
            "type": "file",
            "locations": {name: ref.location for name, ref in helper_refs.items()}
        },
        timestamp="2025-10-14T12:00:00Z"
    )
    print(f"   Metadata label 674 created")
    print(f"   DID: {metadata['674']['did']}")

    print("\n✅ Workflow complete! DID ready for Cardano registration.")
    print()


# ============================================================================
# Main Runner
# ============================================================================

def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" DECENTRALIZED DID SDK - QUICK START EXAMPLES")
    print("=" * 70 + "\n")

    # Synchronous examples
    example_basic_enrollment()
    example_multi_finger()
    example_did_generation()

    # Asynchronous examples
    asyncio.run(example_storage_backends())
    asyncio.run(example_complete_workflow())

    print("=" * 70)
    print(" All examples completed successfully!")
    print("=" * 70 + "\n")

    print("Next Steps:")
    print("  • Read the full documentation: docs/")
    print("  • Try the CLI: dec-did --help")
    print("  • Integrate into your application using the SDK")
    print()


if __name__ == "__main__":
    main()
