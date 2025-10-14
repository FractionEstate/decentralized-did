#!/usr/bin/env python3
"""
Cardano Testnet Deployment Script

Deploys a sample biometric DID to Cardano testnet (preprod) and validates
the transaction on-chain. This script demonstrates the complete enrollment
flow including:

1. Key generation
2. Sample DID document creation
3. Transaction building
4. Submission to testnet
5. Confirmation tracking
6. Result documentation

Prerequisites:
- Blockfrost API key (free tier: https://blockfrost.io)
- Testnet ADA from faucet (https://docs.cardano.org/cardano-testnet/tools/faucet/)

Usage:
    # Set environment variable
    export BLOCKFROST_API_KEY="your_testnet_api_key"

    # Run deployment
    python3 scripts/deploy_testnet.py

    # Or specify key inline
    python3 scripts/deploy_testnet.py --api-key your_testnet_api_key

Open-source compliance: All dependencies are Apache 2.0, MIT, or BSD-3.
"""

from decentralized_did.cardano.blockfrost import BlockfrostClient
from decentralized_did.cardano.transaction import (
    CardanoTransactionBuilder,
    create_payment_keys,
    save_keys,
    TransactionResult,
)
from pycardano import Network, Address
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_sample_did_document() -> Dict[str, Any]:
    """
    Create a sample biometric DID document for testing.

    Returns:
        W3C DID document with sample biometric verification methods
    """
    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/ed25519-2020/v1"
        ],
        "id": "did:cardano:testnet:sample123",
        "verificationMethod": [
            {
                "id": "did:cardano:testnet:sample123#fingerprint-0",
                "type": "BiometricVerificationMethod2024",
                "controller": "did:cardano:testnet:sample123",
                "biometricType": "fingerprint",
                "captureDevice": "ZKTeco ZK9500",
                "templateFormat": "ISO/IEC 19794-2:2011",
                "templateHash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "matchingThreshold": 40,
                "enrollmentDate": "2025-10-14T00:00:00Z",
                "position": "right-index"
            },
            {
                "id": "did:cardano:testnet:sample123#fingerprint-1",
                "type": "BiometricVerificationMethod2024",
                "controller": "did:cardano:testnet:sample123",
                "biometricType": "fingerprint",
                "captureDevice": "ZKTeco ZK9500",
                "templateFormat": "ISO/IEC 19794-2:2011",
                "templateHash": "5f42825b8c5b3a3c9d6c8e7f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
                "matchingThreshold": 40,
                "enrollmentDate": "2025-10-14T00:00:00Z",
                "position": "right-middle"
            },
            {
                "id": "did:cardano:testnet:sample123#fingerprint-2",
                "type": "BiometricVerificationMethod2024",
                "controller": "did:cardano:testnet:sample123",
                "biometricType": "fingerprint",
                "captureDevice": "ZKTeco ZK9500",
                "templateFormat": "ISO/IEC 19794-2:2011",
                "templateHash": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
                "matchingThreshold": 40,
                "enrollmentDate": "2025-10-14T00:00:00Z",
                "position": "right-ring"
            },
            {
                "id": "did:cardano:testnet:sample123#fingerprint-3",
                "type": "BiometricVerificationMethod2024",
                "controller": "did:cardano:testnet:sample123",
                "biometricType": "fingerprint",
                "captureDevice": "ZKTeco ZK9500",
                "templateFormat": "ISO/IEC 19794-2:2011",
                "templateHash": "9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
                "matchingThreshold": 40,
                "enrollmentDate": "2025-10-14T00:00:00Z",
                "position": "right-little"
            }
        ],
        "authentication": [
            "did:cardano:testnet:sample123#fingerprint-0",
            "did:cardano:testnet:sample123#fingerprint-1",
            "did:cardano:testnet:sample123#fingerprint-2",
            "did:cardano:testnet:sample123#fingerprint-3"
        ],
        "created": "2025-10-14T00:00:00Z",
        "updated": "2025-10-14T00:00:00Z"
    }


def print_banner(text: str) -> None:
    """Print a formatted banner."""
    width = 70
    print("\n" + "=" * width)
    print(f"{text:^{width}}")
    print("=" * width + "\n")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 70}")
    print(f"📋 {title}")
    print('─' * 70)


def deploy_to_testnet(
    api_key: str,
    keys_dir: Optional[Path] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Deploy a sample biometric DID to Cardano testnet.

    Args:
        api_key: Blockfrost API key for testnet
        keys_dir: Directory to save payment keys (default: ./testnet-keys)
        dry_run: If True, only validate transaction without submitting

    Returns:
        Deployment results including tx_hash, fees, and metadata
    """
    if keys_dir is None:
        keys_dir = project_root / "testnet-keys"

    keys_dir.mkdir(exist_ok=True)

    # Results dictionary
    results: Dict[str, Any] = {
        "success": False,
        "network": "testnet",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        # Step 1: Generate payment keys
        print_section("Step 1: Generate Payment Keys")

        signing_key_path = keys_dir / "payment.skey"
        verification_key_path = keys_dir / "payment.vkey"

        if signing_key_path.exists():
            print("✅ Using existing payment keys")
            from decentralized_did.cardano.transaction import load_signing_key
            from pycardano import PaymentVerificationKey

            signing_key = load_signing_key(signing_key_path)

            # Recreate address from signing key
            verification_key = PaymentVerificationKey.from_signing_key(
                signing_key)
            address = Address(
                payment_part=verification_key.hash(), network=Network.TESTNET)

            # Save address file if it doesn't exist
            address_file = keys_dir / "payment.addr"
            if not address_file.exists():
                address_file.write_text(str(address))
        else:
            print("🔑 Generating new payment keys...")
            signing_key, verification_key, address = create_payment_keys()

            # Save keys
            save_keys(
                signing_key=signing_key,
                verification_key=verification_key,
                output_dir=str(keys_dir)
            )

            # Save address
            address_file = keys_dir / "payment.addr"
            address_file.write_text(str(address))

            print(f"✅ Keys generated and saved to {keys_dir}")

        print(f"\n📍 Address: {address}")
        results["address"] = str(address)

        # Step 2: Check UTXOs
        print_section("Step 2: Query UTXOs from Blockfrost")

        client = BlockfrostClient(api_key=api_key, network="testnet")
        print(f"🌐 Connected to Blockfrost testnet API")

        utxos = client.get_address_utxos(str(address))

        if not utxos:
            print("\n❌ No UTXOs found at this address!")
            print("\n💰 To get testnet ADA:")
            print("   1. Visit: https://docs.cardano.org/cardano-testnet/tools/faucet/")
            print(f"   2. Request tADA for address: {address}")
            print("   3. Wait for confirmation (usually 1-2 minutes)")
            print("   4. Re-run this script")
            results["error"] = "No UTXOs found"
            return results

        # Calculate total lovelace from UTXOs
        def get_lovelace_amount(utxo) -> int:
            """Extract lovelace amount from UTXO amount list."""
            for asset in utxo.amount:
                if asset["unit"] == "lovelace":
                    return int(asset["quantity"])
            return 0

        total_lovelace = sum(get_lovelace_amount(utxo) for utxo in utxos)
        total_ada = total_lovelace / 1_000_000

        print(f"✅ Found {len(utxos)} UTXO(s)")
        print(
            f"💰 Total balance: {total_ada:.6f} ADA ({total_lovelace} lovelace)")

        for i, utxo in enumerate(utxos, 1):
            lovelace = get_lovelace_amount(utxo)
            print(f"   UTXO {i}: {lovelace:,} lovelace")

        results["utxos_count"] = len(utxos)
        results["balance_ada"] = total_ada
        results["balance_lovelace"] = total_lovelace

        # Convert UTXOInfo to UTXOInput format for transaction builder
        from decentralized_did.cardano.transaction import UTXOInput
        utxo_inputs = [
            UTXOInput(
                tx_hash=utxo.tx_hash,
                tx_index=utxo.tx_index,
                amount_lovelace=get_lovelace_amount(utxo),
                address=utxo.address
            )
            for utxo in utxos
        ]

        # Step 3: Create sample DID document
        print_section("Step 3: Create Sample Biometric DID")

        did_document = create_sample_did_document()
        print(f"✅ Created DID: {did_document['id']}")
        print(
            f"   Verification methods: {len(did_document['verificationMethod'])}")
        print(
            f"   Authentication methods: {len(did_document['authentication'])}")

        # Save DID document
        did_doc_path = keys_dir / "sample-did.json"
        with open(did_doc_path, "w") as f:
            json.dump(did_document, f, indent=2)
        print(f"   Saved to: {did_doc_path}")

        results["did"] = did_document["id"]
        results["verification_methods"] = len(
            did_document["verificationMethod"])

        # Step 4: Build transaction (dry-run first)
        print_section("Step 4: Build Transaction (Dry-Run)")

        builder = CardanoTransactionBuilder(
            network=Network.TESTNET,
            signing_key=signing_key,
            dry_run=True
        )

        print("🔨 Building transaction...")

        # Dry-run to estimate fees
        dry_result = builder.build_enrollment_transaction(
            did_document=did_document,
            available_utxos=utxo_inputs,
            storage_format="inline",  # Store DID inline for testing
            recipient_address=address,  # Send change back to ourselves
        )

        print(f"✅ Transaction validated (dry-run)")
        print(
            f"   Estimated fee: {dry_result.fee_ada:.6f} ADA ({dry_result.fee_lovelace} lovelace)")
        print(f"   Transaction size: {dry_result.tx_size} bytes")
        print(f"   Metadata size: {dry_result.metadata_size} bytes")

        results["estimated_fee_ada"] = dry_result.fee_ada
        results["estimated_fee_lovelace"] = dry_result.fee_lovelace
        results["tx_size"] = dry_result.tx_size
        results["metadata_size"] = dry_result.metadata_size

        # Check if we have enough funds
        min_required = dry_result.fee_lovelace + 1_000_000  # Fee + minimum output
        if total_lovelace < min_required:
            print(f"\n❌ Insufficient funds!")
            print(f"   Required: {min_required / 1_000_000:.6f} ADA")
            print(f"   Available: {total_ada:.6f} ADA")
            results["error"] = "Insufficient funds"
            return results

        # Stop here if dry-run only
        if dry_run:
            print("\n✅ Dry-run complete. Transaction is valid.")
            print("   Run without --dry-run to submit to testnet.")
            results["success"] = True
            results["dry_run"] = True
            return results

        # Step 5: Build and submit real transaction
        print_section("Step 5: Submit Transaction to Testnet")

        builder_real = CardanoTransactionBuilder(
            network=Network.TESTNET,
            signing_key=signing_key,
            dry_run=False
        )

        print("🔨 Building signed transaction...")

        tx_result = builder_real.build_enrollment_transaction(
            did_document=did_document,
            available_utxos=utxo_inputs,
            storage_format="inline",
            recipient_address=address,
        )

        print(f"✅ Transaction built and signed")
        print(
            f"   Actual fee: {tx_result.fee_ada:.6f} ADA ({tx_result.fee_lovelace} lovelace)")

        # Submit to testnet
        print("\n📡 Submitting to Cardano testnet...")

        # Convert bytes to hex string for Blockfrost
        tx_cbor_hex = tx_result.tx_bytes.hex()
        tx_hash = client.submit_transaction(tx_cbor_hex)

        print(f"✅ Transaction submitted successfully!")
        print(f"   TX Hash: {tx_hash}")
        print(
            f"   Explorer: https://preprod.cardanoscan.io/transaction/{tx_hash}")

        results["tx_hash"] = tx_hash
        results["actual_fee_ada"] = tx_result.fee_ada
        results["actual_fee_lovelace"] = tx_result.fee_lovelace
        results["success"] = True

        # Step 6: Wait for confirmation
        print_section("Step 6: Wait for Confirmation")

        print("⏳ Waiting for transaction confirmation...")
        print("   This usually takes 20-40 seconds (1-2 blocks)")

        max_attempts = 20
        for attempt in range(1, max_attempts + 1):
            time.sleep(10)

            try:
                status = client.get_transaction_status(tx_hash)

                if status.confirmed:
                    print(f"\n✅ Transaction confirmed!")
                    print(f"   Block: {status.block_height}")
                    print(f"   Slot: {status.slot}")

                    results["confirmed"] = True
                    results["block_height"] = status.block_height
                    results["slot"] = status.slot
                    break
                else:
                    print(
                        f"   Attempt {attempt}/{max_attempts}: Not yet confirmed...")
            except Exception as e:
                print(
                    f"   Attempt {attempt}/{max_attempts}: Checking... ({str(e)})")

        else:
            print(
                f"\n⚠️ Transaction not confirmed after {max_attempts * 10} seconds")
            print("   Check explorer for status (it may still confirm)")

        # Step 7: Verify metadata
        print_section("Step 7: Verify Metadata On-Chain")

        if results.get("confirmed"):
            try:
                metadata = client.get_transaction_metadata(tx_hash, label=674)

                if metadata:
                    print("✅ Metadata found on-chain!")
                    print(f"   Label: 674 (CIP-20 biometric DID)")
                    print(f"   DID: {metadata.get('did', 'N/A')}")
                    print(
                        f"   Verification methods: {len(metadata.get('verificationMethod', []))}")

                    results["metadata_verified"] = True
                    results["metadata"] = metadata
                else:
                    print("⚠️ Metadata not found (may need more time)")
            except Exception as e:
                print(f"⚠️ Error retrieving metadata: {e}")

        return results

    except Exception as e:
        print(f"\n❌ Error during deployment: {e}")
        import traceback
        traceback.print_exc()
        results["error"] = str(e)
        return results


def save_deployment_report(results: Dict[str, Any], output_dir: Path) -> Path:
    """
    Save deployment results to a JSON report.

    Args:
        results: Deployment results dictionary
        output_dir: Directory to save report

    Returns:
        Path to saved report file
    """
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    report_path = output_dir / f"testnet-deployment-{timestamp}.json"

    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    return report_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy biometric DID to Cardano testnet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use environment variable
  export BLOCKFROST_API_KEY="your_key"
  python3 scripts/deploy_testnet.py

  # Specify API key inline
  python3 scripts/deploy_testnet.py --api-key your_key

  # Dry-run only (validate without submitting)
  python3 scripts/deploy_testnet.py --dry-run

Get your free Blockfrost API key:
  https://blockfrost.io (50,000 requests/day free tier)

Get testnet ADA from faucet:
  https://docs.cardano.org/cardano-testnet/tools/faucet/
        """
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="Blockfrost API key for testnet (or set BLOCKFROST_API_KEY env var)"
    )

    parser.add_argument(
        "--keys-dir",
        type=Path,
        default=None,
        help="Directory to save payment keys (default: ./testnet-keys)"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("testnet-reports"),
        help="Directory to save deployment reports (default: ./testnet-reports)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate transaction without submitting to blockchain"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("BLOCKFROST_API_KEY")

    if not api_key:
        print("❌ Error: Blockfrost API key required")
        print("\nProvide via:")
        print("  1. --api-key flag: python3 scripts/deploy_testnet.py --api-key YOUR_KEY")
        print("  2. Environment variable: export BLOCKFROST_API_KEY=YOUR_KEY")
        print("\nGet your free API key: https://blockfrost.io")
        sys.exit(1)

    # Print header
    print_banner("🚀 CARDANO TESTNET DEPLOYMENT")
    print("Deploying sample biometric DID to Cardano preprod testnet")
    print(f"Network: testnet (preprod)")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE DEPLOYMENT'}")

    # Deploy
    results = deploy_to_testnet(
        api_key=api_key,
        keys_dir=args.keys_dir,
        dry_run=args.dry_run
    )

    # Save report
    if not args.dry_run or results.get("success"):
        report_path = save_deployment_report(results, args.output_dir)
        print(f"\n📄 Report saved: {report_path}")

    # Print summary
    print_banner("📊 DEPLOYMENT SUMMARY")

    if results.get("success"):
        print("✅ Status: SUCCESS")

        if results.get("dry_run"):
            print("   Mode: Dry-run (validation only)")
        else:
            print(f"   TX Hash: {results.get('tx_hash', 'N/A')}")
            print(
                f"   Explorer: https://preprod.cardanoscan.io/transaction/{results.get('tx_hash', '')}")

        print(f"   DID: {results.get('did', 'N/A')}")
        print(
            f"   Fee: {results.get('actual_fee_ada', results.get('estimated_fee_ada', 0)):.6f} ADA")
        print(f"   TX Size: {results.get('tx_size', 0)} bytes")
        print(f"   Metadata Size: {results.get('metadata_size', 0)} bytes")

        if results.get("confirmed"):
            print(f"   Block: {results.get('block_height', 'N/A')}")
            print(f"   Confirmed: ✅")
    else:
        print("❌ Status: FAILED")
        print(f"   Error: {results.get('error', 'Unknown error')}")

    print("\n" + "=" * 70 + "\n")

    sys.exit(0 if results.get("success") else 1)


if __name__ == "__main__":
    main()
