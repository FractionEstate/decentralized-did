#!/usr/bin/env python3
"""
SDK Quick Start - Simplified Examples
======================================

Simple examples using the actual decentralized-did SDK API.
"""

from decentralized_did import (
    FuzzyExtractor,
    Minutia,
    FingerTemplate,
    aggregate_finger_digests,
    build_did,
)


def create_sample_template(finger_id: str, seed: int = 0) -> FingerTemplate:
    """Create a sample fingerprint template for demonstration."""
    import random
    random.seed(seed)
    
    # Generate 20-25 random minutiae points
    minutiae = []
    for i in range(random.randint(20, 25)):
        minutiae.append(Minutia(
            x=random.uniform(0, 500),
            y=random.uniform(0, 500),
            angle=random.uniform(0, 360)
        ))
    
    return FingerTemplate(
        finger_id=finger_id,
        minutiae=minutiae,
        grid_size=10.0,
        angle_bins=8
    )


def example_1_basic():
    """Example 1: Basic enrollment and verification."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Enrollment and Verification")
    print("=" * 70)
    
    # Create fuzzy extractor
    extractor = FuzzyExtractor()
    
    # Create sample template
    template = create_sample_template("thumb", seed=42)
    print(f"\n✅ Created template: {template.finger_id}")
    print(f"   Minutiae: {len(template.minutiae)}")
    print(f"   Grid size: {template.grid_size}")
    
    # Enrollment
    digest, helper = extractor.generate(template)
    print(f"\n✅ Enrollment complete:")
    print(f"   Digest: {digest.hex()[:32]}...")
    print(f"   Helper finger: {helper.finger_id}")
    
    # Verification (using same template)
    verified = extractor.reproduce(template, helper)
    print(f"\n✅ Verification:")
    if digest == verified:
        print(f"   SUCCESS - Digests match!")
    else:
        print(f"   FAILED - Digests don't match")


def example_2_multi_finger():
    """Example 2: Multi-finger aggregation."""
    print("\n" + "=" * 70)
    print("Example 2: Multi-Finger Aggregation")
    print("=" * 70)
    
    extractor = FuzzyExtractor()
    
    # Create 4 finger templates
    fingers = ["thumb", "index", "middle", "ring"]
    digests = []
    helpers = {}
    
    print("\n✅ Enrolling 4 fingers:")
    for i, finger in enumerate(fingers):
        template = create_sample_template(finger, seed=100+i)
        digest, helper = extractor.generate(template)
        digests.append((finger, digest))
        helpers[finger] = helper
        print(f"   {finger.capitalize()}: {digest.hex()[:16]}...")
    
    # Aggregate
    aggregated = aggregate_finger_digests(digests)
    print(f"\n✅ Aggregated digest:")
    print(f"   {aggregated.hex()[:32]}... ({len(aggregated)} bytes)")


def example_3_did_generation():
    """Example 3: DID generation."""
    print("\n" + "=" * 70)
    print("Example 3: DID Generation")
    print("=" * 70)
    
    extractor = FuzzyExtractor()
    
    # Create biometric digest
    template = create_sample_template("thumb", seed=999)
    digest, helper = extractor.generate(template)
    
    # Generate DID
    wallet_address = "addr1qx2kd88c92l6j5jhkjehfvjdj2gvfe5g8c4v7y4k3hl2p8jv2kd88c92l6"
    did = build_did(wallet_address, digest)
    
    print(f"\n✅ Input:")
    print(f"   Wallet: {wallet_address[:20]}...")
    print(f"   Digest: {digest.hex()[:32]}...")
    
    print(f"\n✅ Generated DID:")
    print(f"   {did}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" DECENTRALIZED DID SDK - QUICK START")
    print("=" * 70)
    
    example_1_basic()
    example_2_multi_finger()
    example_3_did_generation()
    
    print("\n" + "=" * 70)
    print(" All examples completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("  • Read docs/SDK.md for full documentation")
    print("  • Try: dec-did --help")
    print()


if __name__ == "__main__":
    main()
