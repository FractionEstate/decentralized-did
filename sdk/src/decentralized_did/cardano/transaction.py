"""
Cardano Transaction Builder for Biometric DID Deployment

This module provides transaction construction functionality for deploying
biometric DIDs on the Cardano blockchain using PyCardano library.

Features:
- UTXO selection (largest-first algorithm)
- Fee estimation (155381 + 44 × size lovelace)
- CIP-20 metadata construction (label 674)
- Metadata schema v1.1 support (multi-controller, revocation, timestamps)
- Dry-run mode for validation
- Error handling and logging

Metadata Schema v1.1:
- Multi-controller support (multiple wallets per DID)
- Enrollment timestamps (ISO 8601)
- Revocation mechanism (revoked, revokedAt)
- Backward compatible with v1.0

License: Apache 2.0
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import cbor2

from pycardano import (
    Address,
    Network,
    PaymentSigningKey,
    PaymentVerificationKey,
    Transaction,
    TransactionBuilder,
    TransactionOutput,
    UTxO,
    Value,
    Metadata,
    AuxiliaryData,
    AlonzoMetadata,
)

logger = logging.getLogger(__name__)


# Constants
CIP20_LABEL = 674  # Label for biometric DID metadata (0x02AA in hex)
MIN_LOVELACE = 1_000_000  # Minimum ADA per UTXO (1 ADA)
FEE_CONSTANT = 155381  # Base fee in lovelace
FEE_COEFFICIENT = 44  # Fee per byte
METADATA_LIMIT = 16384  # 16 KB limit for transaction metadata


@dataclass
class TransactionResult:
    """Result of a transaction build/submission"""

    success: bool
    tx_hash: Optional[str] = None
    tx_bytes: Optional[bytes] = None
    tx_size: int = 0
    fee_lovelace: int = 0
    fee_ada: float = 0.0
    error: Optional[str] = None
    metadata_size: int = 0
    inputs_count: int = 0
    outputs_count: int = 0


@dataclass
class UTXOInput:
    """UTXO input for transaction building"""

    tx_hash: str
    tx_index: int
    amount_lovelace: int
    address: str


class CardanoTransactionBuilder:
    """
    Transaction builder for deploying biometric DIDs on Cardano.

    This class handles:
    1. UTXO selection from available inputs
    2. Transaction fee estimation
    3. CIP-20 metadata construction
    4. Transaction building and signing
    5. Dry-run validation (without blockchain submission)

    Example:
        >>> builder = CardanoTransactionBuilder(
    ...     network=Network.TESTNET,
    ...     signing_key=payment_skey,
    ... )
        >>> result = builder.build_enrollment_transaction(
        ...     did_document=did_doc,
        ...     helper_data_cid="Qm...",
        ...     recipient_address="addr_test1..."
        ... )
        >>> if result.success:
        ...     print(f"Transaction hash: {result.tx_hash}")
    """

    def __init__(
        self,
        network: Network = Network.TESTNET,
        signing_key: Optional[PaymentSigningKey] = None,
        dry_run: bool = False,
    ):
        """
        Initialize the transaction builder.

        Args:
            network: Cardano network (TESTNET or MAINNET)
            signing_key: Payment signing key for transaction signing
            dry_run: If True, build transaction without submitting
        """
        self.network = network
        self.signing_key = signing_key
        self.dry_run = dry_run

        # Derive verification key and address from signing key
        if signing_key:
            self.verification_key = PaymentVerificationKey.from_signing_key(
                signing_key)
            self.address = Address(
                payment_part=self.verification_key.hash(),
                network=network
            )
        else:
            self.verification_key = None
            self.address = None

        logger.info(
            f"CardanoTransactionBuilder initialized: "
            f"network={network.name}, dry_run={dry_run}"
        )

    def select_utxos(
        self,
        available_utxos: List[UTXOInput],
        required_lovelace: int,
    ) -> Tuple[List[UTXOInput], int]:
        """
        Select UTXOs using largest-first algorithm.

        This algorithm prioritizes larger UTXOs to minimize the number
        of inputs, which reduces transaction size and fees.

        Args:
            available_utxos: List of available UTXOs
            required_lovelace: Amount of lovelace needed (including estimated fee)

        Returns:
            Tuple of (selected_utxos, total_amount)

        Raises:
            ValueError: If insufficient funds available
        """
        if not available_utxos:
            raise ValueError("No UTXOs available")

        # Sort by amount (largest first)
        sorted_utxos = sorted(
            available_utxos,
            key=lambda u: u.amount_lovelace,
            reverse=True
        )

        selected: List[UTXOInput] = []
        total = 0

        for utxo in sorted_utxos:
            selected.append(utxo)
            total += utxo.amount_lovelace

            if total >= required_lovelace:
                break

        if total < required_lovelace:
            raise ValueError(
                f"Insufficient funds: have {total} lovelace, "
                f"need {required_lovelace} lovelace"
            )

        logger.info(
            f"Selected {len(selected)} UTXOs totaling {total} lovelace "
            f"(required: {required_lovelace})"
        )

        return selected, total

    def estimate_fee(
        self,
        inputs_count: int,
        outputs_count: int,
        metadata_size: int,
        witnesses_count: int = 1,
    ) -> int:
        """
        Estimate transaction fee.

        Fee formula: 155381 + 44 × size (lovelace)

        Size estimation:
        - Each input: ~150 bytes
        - Each output: ~50 bytes
        - Each witness: ~100 bytes
        - Metadata: actual CBOR size
        - Overhead: ~100 bytes

        Args:
            inputs_count: Number of transaction inputs
            outputs_count: Number of transaction outputs
            metadata_size: Size of metadata in bytes
            witnesses_count: Number of signatures (default: 1)

        Returns:
            Estimated fee in lovelace
        """
        estimated_size = (
            100 +  # Base overhead
            (inputs_count * 150) +
            (outputs_count * 50) +
            (witnesses_count * 100) +
            metadata_size
        )

        fee = FEE_CONSTANT + (FEE_COEFFICIENT * estimated_size)

        logger.debug(
            f"Fee estimation: size={estimated_size} bytes, "
            f"fee={fee} lovelace ({fee / 1_000_000:.6f} ADA)"
        )

        return fee

    @staticmethod
    def _chunk_string(s: str, chunk_size: int = 64) -> Any:
        """
        Split a string into chunks to comply with PyCardano's metadata size limits.

        PyCardano enforces a 64-byte limit per metadata string item.
        For strings exceeding this, return an array of chunks.

        Args:
            s: String to chunk
            chunk_size: Maximum bytes per chunk (default: 64)

        Returns:
            Original string if ≤64 bytes, otherwise list of chunks
        """
        s_bytes = s.encode('utf-8')
        if len(s_bytes) <= chunk_size:
            return s

        # Split into chunks
        chunks = []
        for i in range(0, len(s_bytes), chunk_size):
            chunk = s_bytes[i:i+chunk_size].decode('utf-8', errors='ignore')
            chunks.append(chunk)
        return chunks

    def build_metadata(
        self,
        did: str,
        wallet_address: str,
        digest: bytes,
        helper_data: Optional[Dict[str, Any]] = None,
        helper_data_cid: Optional[str] = None,
        storage_format: str = "inline",
        version: str = "1.1",
        controllers: Optional[List[str]] = None,
        enrollment_timestamp: Optional[str] = None,
        revoked: bool = False,
        revoked_at: Optional[str] = None,
    ) -> Tuple[AuxiliaryData, int]:
        """
        Build CIP-20 metadata for biometric DID (v1.1 schema).

        Metadata structure (label 674, v1.1):
        {
            "version": "1.1",
            "did": "did:cardano:mainnet:...",
            "controllers": ["addr1...", "addr2..."],
            "biometric": {
                "idHash": "base58_encoded_digest",
                "helperStorage": "inline" | "external",
                "helperData": { ... } | null,
                "helperUri": "ipfs://Qm..." | null
            },
            "enrollmentTimestamp": "2025-01-15T12:00:00Z",
            "revoked": false,
            "revokedAt": null
        }

        Args:
            did: DID identifier
            wallet_address: Primary controller wallet address
            digest: Biometric digest (32 bytes)
            helper_data: Inline helper data dict (optional)
            helper_data_cid: IPFS CID for external helper data (optional)
            storage_format: "inline" or "external" (IPFS)
            version: Metadata schema version ("1.0" or "1.1", default "1.1")
            controllers: List of controller wallet addresses (v1.1+)
            enrollment_timestamp: ISO 8601 timestamp (v1.1+)
            revoked: Whether DID is revoked (v1.1+)
            revoked_at: Revocation timestamp (v1.1+)

        Returns:
            Tuple of (auxiliary_data, metadata_size_bytes)

        Raises:
            ValueError: If metadata exceeds 16 KB limit

        Note:
            Schema v1.1 is RECOMMENDED for new deployments. It supports:
            - Multi-controller (multiple wallets controlling same DID)
            - Enrollment timestamps
            - Revocation mechanism
        """
        from datetime import datetime, timezone
        import base58

        # Build biometric section
        id_hash_str = base58.b58encode(digest).decode('ascii')
        biometric: Dict[str, Any] = {
            "idHash": self._chunk_string(id_hash_str),
            "helperStorage": storage_format,
        }

        # Add helper data (inline or external reference)
        if helper_data_cid:
            biometric["helperUri"] = f"ipfs://{helper_data_cid}"
        elif helper_data and storage_format == "inline":
            biometric["helperData"] = helper_data

        # Build metadata payload based on schema version
        if version == "1.0":
            # Legacy v1.0 schema (single controller)
            import warnings
            warnings.warn(
                "Metadata schema v1.0 is deprecated. Use v1.1 for multi-controller "
                "support, revocation, and enrollment timestamps.",
                DeprecationWarning,
                stacklevel=2
            )
            metadata_payload = {
                "version": 1,  # Numeric version for v1.0
                "did": self._chunk_string(did),
                "walletAddress": self._chunk_string(wallet_address),
                "biometric": biometric,
            }
        else:
            # v1.1 schema (RECOMMENDED)
            # Chunk controllers (wallet addresses can be long)
            chunked_controllers = [self._chunk_string(
                c) for c in (controllers or [wallet_address])]

            metadata_payload: Dict[str, Any] = {
                "version": version,
                "did": self._chunk_string(did),
                "controllers": chunked_controllers,
                "biometric": biometric,
            }

            # Add optional v1.1 fields
            if enrollment_timestamp:
                metadata_payload["enrollmentTimestamp"] = enrollment_timestamp
            else:
                # Auto-generate enrollment timestamp if not provided
                metadata_payload["enrollmentTimestamp"] = datetime.now(
                    timezone.utc).isoformat()

            if revoked:
                metadata_payload["revoked"] = revoked
                if revoked_at:
                    metadata_payload["revokedAt"] = revoked_at

        # Encode to CBOR to check size
        cbor_bytes = cbor2.dumps(metadata_payload)
        metadata_size = len(cbor_bytes)

        if metadata_size > METADATA_LIMIT:
            raise ValueError(
                f"Metadata size ({metadata_size} bytes) exceeds "
                f"16 KB limit ({METADATA_LIMIT} bytes). "
                f"Use external storage (IPFS) for large enrollments."
            )

        # Create PyCardano metadata structure
        metadata_dict = {
            CIP20_LABEL: metadata_payload
        }

        # Convert to PyCardano Metadata type
        auxiliary_data = AuxiliaryData(
            AlonzoMetadata(metadata=Metadata(metadata_dict))
        )

        logger.info(
            f"Built CIP-20 metadata: label={CIP20_LABEL}, version={version}, "
            f"size={metadata_size} bytes, format={storage_format}"
        )

        return auxiliary_data, metadata_size

    def build_enrollment_transaction(
        self,
        did: str,
        wallet_address: str,
        digest: bytes,
        helper_data: Optional[Dict[str, Any]] = None,
        helper_data_cid: Optional[str] = None,
        recipient_address: Optional[str] = None,
        available_utxos: Optional[List[UTXOInput]] = None,
        storage_format: str = "inline",
        version: str = "1.1",
        controllers: Optional[List[str]] = None,
        enrollment_timestamp: Optional[str] = None,
        revoked: bool = False,
        revoked_at: Optional[str] = None,
    ) -> TransactionResult:
        """
        Build a transaction to deploy a biometric DID on Cardano.

        Transaction structure:
        - Inputs: Selected UTXOs from sender
        - Outputs: Recipient address (or self) with min ADA
        - Metadata: CIP-20 label 674 with DID and biometric data
        - Fee: Calculated based on transaction size

        Args:
            did: DID identifier
            wallet_address: Primary controller wallet address
            digest: Biometric digest (32 bytes)
            helper_data: Inline helper data dict (optional)
            helper_data_cid: IPFS CID for helper data (optional)
            recipient_address: Recipient address (defaults to self)
            available_utxos: Available UTXOs for inputs (required if not dry_run)
            storage_format: "inline" or "external" storage
            version: Metadata schema version ("1.0" or "1.1", default "1.1")
            controllers: List of controller wallet addresses (v1.1+)
            enrollment_timestamp: ISO 8601 timestamp (v1.1+)
            revoked: Whether DID is revoked (v1.1+)
            revoked_at: Revocation timestamp (v1.1+)

        Returns:
            TransactionResult with success status and details
        """
        try:
            # Validate inputs
            if not self.dry_run and not available_utxos:
                return TransactionResult(
                    success=False,
                    error="available_utxos required when dry_run=False"
                )

            if not recipient_address:
                if not self.address:
                    return TransactionResult(
                        success=False,
                        error="recipient_address or signing_key required"
                    )
                recipient_address = str(self.address)

            # Build metadata
            auxiliary_data, metadata_size = self.build_metadata(
                did=did,
                wallet_address=wallet_address,
                digest=digest,
                helper_data=helper_data,
                helper_data_cid=helper_data_cid,
                storage_format=storage_format,
                version=version,
                controllers=controllers,
                enrollment_timestamp=enrollment_timestamp,
                revoked=revoked,
                revoked_at=revoked_at,
            )

            # Estimate fee (1 input, 1 output, 1 witness for initial estimate)
            estimated_fee = self.estimate_fee(
                inputs_count=1,
                outputs_count=1,
                metadata_size=metadata_size,
                witnesses_count=1,
            )

            # Calculate required amount (output + fee)
            required_lovelace = MIN_LOVELACE + estimated_fee

            # Select UTXOs
            if self.dry_run:
                # In dry-run mode, simulate with mock UTXOs
                selected_utxos = [
                    UTXOInput(
                        tx_hash="0" * 64,
                        tx_index=0,
                        amount_lovelace=required_lovelace,
                        address=recipient_address,
                    )
                ]
                total_input = required_lovelace
            else:
                # Type assertion: available_utxos is not None when dry_run=False
                assert available_utxos is not None
                selected_utxos, total_input = self.select_utxos(
                    available_utxos=available_utxos,
                    required_lovelace=required_lovelace,
                )

            # Recalculate fee with actual input count
            actual_fee = self.estimate_fee(
                inputs_count=len(selected_utxos),
                outputs_count=1,
                metadata_size=metadata_size,
                witnesses_count=1,
            )

            # Calculate change amount
            change_lovelace = total_input - MIN_LOVELACE - actual_fee

            if change_lovelace < 0:
                return TransactionResult(
                    success=False,
                    error=f"Insufficient funds after fee calculation: "
                          f"need {actual_fee + MIN_LOVELACE}, have {total_input}"
                )

            # In dry-run mode, return estimated result
            if self.dry_run:
                logger.info(
                    f"Dry-run transaction built successfully: "
                    f"fee={actual_fee} lovelace, metadata={metadata_size} bytes"
                )

                return TransactionResult(
                    success=True,
                    tx_hash="dry-run-" + "0" * 56,
                    tx_bytes=None,
                    tx_size=self._estimate_total_size(
                        len(selected_utxos), 1, metadata_size
                    ),
                    fee_lovelace=actual_fee,
                    fee_ada=actual_fee / 1_000_000,
                    metadata_size=metadata_size,
                    inputs_count=len(selected_utxos),
                    outputs_count=1,
                )

            # Build actual transaction with PyCardano (manual approach)
            from pycardano import (
                Transaction,
                TransactionBody,
                TransactionInput,
                TransactionOutput,
                TransactionWitnessSet,
                VerificationKeyWitness,
                Value,
            )

            # Validate available_utxos
            if not available_utxos:
                return TransactionResult(
                    success=False,
                    error="No UTXOs available for transaction building"
                )

            # Select UTXOs (returns tuple)
            selected_inputs, total_input = self.select_utxos(
                available_utxos=available_utxos,
                required_lovelace=MIN_LOVELACE + estimated_fee
            )

            # Create inputs
            tx_inputs = [
                TransactionInput.from_primitive([utxo.tx_hash, utxo.tx_index])
                for utxo in selected_inputs
            ]

            # Calculate change
            change_amount = total_input - estimated_fee

            # Create output (change back to sender)
            from pycardano import Address as PyAddress
            # Ensure recipient_address is string
            addr_str = str(recipient_address) if recipient_address else str(
                self.address)
            output_address = PyAddress.from_primitive(addr_str)
            tx_outputs = [
                TransactionOutput(output_address, Value(change_amount))
            ]

            # Create transaction body
            tx_body = TransactionBody(
                inputs=tx_inputs,
                outputs=tx_outputs,
                fee=estimated_fee,
                auxiliary_data_hash=auxiliary_data.hash() if auxiliary_data else None,
            )

            # Sign transaction
            witnesses = TransactionWitnessSet()
            if self.signing_key:
                signature = self.signing_key.sign(tx_body.hash())
                vkey_witness = VerificationKeyWitness(
                    self.signing_key.to_verification_key(),
                    signature
                )
                witnesses.vkey_witnesses = [vkey_witness]

            # Build final transaction
            tx = Transaction(
                transaction_body=tx_body,
                transaction_witness_set=witnesses,
                auxiliary_data=auxiliary_data,
            )

            tx_bytes = tx.to_cbor()

            logger.info(
                f"Transaction built successfully: "
                f"size={len(tx_bytes)} bytes, "
                f"fee={estimated_fee} lovelace"
            )

            return TransactionResult(
                success=True,
                tx_hash=str(tx_body.hash()),
                tx_bytes=tx_bytes,
                tx_size=len(tx_bytes),
                fee_lovelace=estimated_fee,
                fee_ada=estimated_fee / 1_000_000,
                metadata_size=metadata_size,
                inputs_count=len(selected_inputs),
                outputs_count=1,
            )

        except Exception as e:
            logger.error(f"Transaction build failed: {e}")
            return TransactionResult(
                success=False,
                error=str(e)
            )

    def _estimate_total_size(
        self,
        inputs_count: int,
        outputs_count: int,
        metadata_size: int,
    ) -> int:
        """Helper to estimate total transaction size."""
        return (
            100 +  # Overhead
            (inputs_count * 150) +
            (outputs_count * 50) +
            100 +  # Witness
            metadata_size
        )


# Utility functions

def create_payment_keys() -> Tuple[PaymentSigningKey, PaymentVerificationKey, Address]:
    """
    Generate new Cardano payment keys and address.

    Returns:
        Tuple of (signing_key, verification_key, address)

    Example:
        >>> skey, vkey, addr = create_payment_keys()
        >>> print(f"Address: {addr}")
    """
    skey = PaymentSigningKey.generate()
    vkey = PaymentVerificationKey.from_signing_key(skey)
    addr = Address(payment_part=vkey.hash(), network=Network.TESTNET)

    logger.info(f"Generated new payment keys: address={addr}")

    # Type cast for return (PyCardano types are compatible)
    return skey, vkey, addr  # type: ignore


def save_keys(
    signing_key: PaymentSigningKey,
    verification_key: PaymentVerificationKey,
    output_dir: str = ".",
) -> None:
    """
    Save payment keys to files.

    Args:
        signing_key: Payment signing key
        verification_key: Payment verification key
        output_dir: Directory to save keys (default: current directory)
    """
    import os

    skey_path = os.path.join(output_dir, "payment.skey")
    vkey_path = os.path.join(output_dir, "payment.vkey")

    with open(skey_path, "w") as f:
        f.write(signing_key.to_json())

    with open(vkey_path, "w") as f:
        f.write(verification_key.to_json())

    logger.info(f"Keys saved: {skey_path}, {vkey_path}")


def load_signing_key(key_path: str) -> PaymentSigningKey:
    """
    Load payment signing key from file.

    Args:
        key_path: Path to signing key file

    Returns:
        PaymentSigningKey
    """
    with open(key_path, "r") as f:
        key_json = f.read()

    skey = PaymentSigningKey.from_json(key_json)
    logger.info(f"Loaded signing key from {key_path}")

    return skey  # type: ignore
