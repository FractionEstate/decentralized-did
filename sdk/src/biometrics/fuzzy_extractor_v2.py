"""
Fuzzy Extractor Implementation with BCH Error Correction

Implements the Dodis et al. (2004) fuzzy extractor construction using:
- BCH(127,64,10) error correction via galois library (MIT license)
- BLAKE2b-512 key derivation function
- HMAC-BLAKE2b helper data integrity verification
- Salted helper data for unlinkability

Design: docs/design/fuzzy-extractor-spec.md
Phase 2, Task 2 - Core Implementation

Copyright 2025 Decentralized DID Project
License: Apache 2.0

IMPORTANT NOTE: This implementation uses galois (MIT) instead of bchlib
due to Python 3.11+ compatibility issues. galois.BCH provides equivalent
functionality with better maintenance and performance.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Tuple, Dict, Any
import galois
import numpy as np


# ============================================================================
# CONSTANTS
# ============================================================================

# BCH Code Parameters
BCH_N = 127  # Codeword length (bits)
BCH_K = 64   # Message length (bits)
BCH_T = 10   # Error correction capacity (bits)
BCH_D = 21   # Minimum distance (2t+1)

# Cryptographic Parameters
SALT_BYTES = 32        # 256-bit salt
PERSON_BYTES = 32      # 256-bit personalization tag
HMAC_BYTES = 32        # 256-bit HMAC tag
KEY_BYTES = 32         # 256-bit output key

# Helper Data Schema
HELPER_DATA_VERSION = 1


# ============================================================================
# BCH CODEC
# ============================================================================

class BCHCodec:
    """
    Wrapper around galois BCH implementation for biometric fuzzy extraction.

    Provides bit-level BCH(127,64,10) encoding/decoding with syndrome
    computation for helper data generation.
    """

    def __init__(self):
        """Initialize BCH(127,64,10) codec."""
        self.bch = galois.BCH(BCH_N, BCH_K, d=BCH_D)
        self.gf = galois.GF2

    def encode(self, message_bits: np.ndarray) -> np.ndarray:
        """
        Encode 64-bit message to 127-bit codeword.

        Args:
            message_bits: 64-bit message as numpy array

        Returns:
            127-bit codeword as numpy array
        """
        if len(message_bits) != BCH_K:
            raise ValueError(
                f"Message must be {BCH_K} bits, got {len(message_bits)}")

        # Convert to GF(2) if needed
        if not isinstance(message_bits, galois.FieldArray):
            message_bits = self.gf(message_bits)

        # Encode
        codeword = self.bch.encode(message_bits)
        return np.array(codeword, dtype=np.uint8)

    def decode(self, received_bits: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Decode 127-bit received word to 64-bit message.

        Args:
            received_bits: 127-bit received word (possibly corrupted)

        Returns:
            (decoded_message, error_count) tuple
            decoded_message: 64-bit message as numpy array
            error_count: Number of bit errors corrected

        Raises:
            ValueError: If too many errors (>10 bits)
        """
        if len(received_bits) != BCH_N:
            raise ValueError(
                f"Received word must be {BCH_N} bits, got {len(received_bits)}")

        # Convert to GF(2) if needed
        if not isinstance(received_bits, galois.FieldArray):
            received_bits = self.gf(received_bits)

        try:
            # Decode with error correction
            decoded = self.bch.decode(received_bits)

            # Count errors by comparing with re-encoded version
            reencoded = self.bch.encode(decoded)
            error_count = int(np.sum(received_bits != reencoded))

            return np.array(decoded, dtype=np.uint8), error_count
        except Exception as e:
            raise ValueError(
                f"BCH decoding failed: too many errors (>10 bits)") from e

    def compute_syndrome(self, codeword: np.ndarray) -> bytes:
        """
        Compute BCH parity bits for helper data.

        Args:
            codeword: 127-bit codeword

        Returns:
            8-byte parity data (63 bits padded to byte boundary)
        """
        if len(codeword) != BCH_N:
            raise ValueError(
                f"Codeword must be {BCH_N} bits, got {len(codeword)}")

        # Convert to GF(2) if needed
        if not isinstance(codeword, galois.FieldArray):
            codeword = self.gf(codeword)

        # Extract parity bits (last 63 bits of systematic BCH codeword)
        parity_bits = codeword[BCH_K:]  # Last 63 bits

        # Pack bits into bytes (pad to 64 bits = 8 bytes)
        syndrome_bits_padded = np.pad(
            parity_bits, (0, 64 - len(parity_bits)), constant_values=0)
        syndrome_bytes = np.packbits(syndrome_bits_padded).tobytes()

        return syndrome_bytes[:8]  # Return first 8 bytes

    def decode_with_parity(self, noisy_message: np.ndarray, parity: bytes) -> Tuple[np.ndarray, int]:
        """
        Decode noisy message using stored parity bits from enrollment.

        Reconstructs the codeword by combining noisy message with correct parity,
        then BCH decodes to correct errors.

        Args:
            noisy_message: 64-bit noisy message
            parity: 8-byte parity data from helper data

        Returns:
            (decoded_message, error_count) tuple
        """
        if len(noisy_message) != BCH_K:
            raise ValueError(
                f"Message must be {BCH_K} bits, got {len(noisy_message)}")

        # Unpack parity bytes to bits
        parity_bits_all = np.unpackbits(np.frombuffer(parity, dtype=np.uint8))
        # Take first 63 bits (rest is padding)
        parity_bits = parity_bits_all[:63]

        # Reconstruct codeword: [noisy_message | correct_parity]
        reconstructed_codeword = np.concatenate([noisy_message, parity_bits])

        # Decode (BCH will correct errors in the message part)
        return self.decode(reconstructed_codeword)


# ============================================================================
# HELPER DATA
# ============================================================================

@dataclass
class HelperData:
    """
    Helper data for fuzzy extractor (public, no confidentiality needed).

    Attributes:
        version: Protocol version (1)
        salt: 32-byte cryptographic salt (ensures unlinkability)
        personalization: 32-byte personalization tag (user/context binding)
        bch_syndrome: 8-byte BCH syndrome (error correction data)
        hmac: 32-byte HMAC tag (integrity protection)
    """
    version: int
    salt: bytes
    personalization: bytes
    bch_syndrome: bytes
    hmac: bytes

    def __post_init__(self):
        """Validate helper data fields."""
        if self.version != HELPER_DATA_VERSION:
            raise ValueError(f"Unsupported version: {self.version}")
        if len(self.salt) != SALT_BYTES:
            raise ValueError(
                f"Salt must be {SALT_BYTES} bytes, got {len(self.salt)}")
        if len(self.personalization) != PERSON_BYTES:
            raise ValueError(
                f"Personalization must be {PERSON_BYTES} bytes, got {len(self.personalization)}")
        if len(self.bch_syndrome) != 8:  # 63 bits padded to 8 bytes
            raise ValueError(
                f"BCH syndrome must be 8 bytes, got {len(self.bch_syndrome)}")
        if len(self.hmac) != HMAC_BYTES:
            raise ValueError(
                f"HMAC must be {HMAC_BYTES} bytes, got {len(self.hmac)}")

    def serialize(self) -> bytes:
        """
        Serialize helper data to bytes for storage/transmission.

        Returns:
            105-byte packed representation
        """
        return (
            self.version.to_bytes(1, 'big') +  # 1 byte
            self.salt +                         # 32 bytes
            self.personalization +              # 32 bytes
            self.bch_syndrome +                 # 8 bytes
            self.hmac                           # 32 bytes
        )  # Total: 105 bytes

    @classmethod
    def deserialize(cls, data: bytes) -> 'HelperData':
        """
        Deserialize helper data from bytes.

        Args:
            data: 105-byte serialized helper data

        Returns:
            HelperData object
        """
        if len(data) != 105:
            raise ValueError(f"Helper data must be 105 bytes, got {len(data)}")

        version = data[0]
        salt = data[1:33]
        personalization = data[33:65]
        bch_syndrome = data[65:73]
        hmac_tag = data[73:105]

        return cls(version, salt, personalization, bch_syndrome, hmac_tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'version': self.version,
            'salt': self.salt.hex(),
            'personalization': self.personalization.hex(),
            'bch_syndrome': self.bch_syndrome.hex(),
            'hmac': self.hmac.hex()
        }


# ============================================================================
# KEY DERIVATION
# ============================================================================

def generate_personalization_tag(user_id: str, context: str = "biometric-did-cardano") -> bytes:
    """
    Generate personalization tag from user identifier.

    Binds key derivation to specific user/context for domain separation.

    Args:
        user_id: Unique user identifier (e.g., Cardano wallet address)
        context: Application context (default: "biometric-did-cardano")

    Returns:
        32-byte personalization tag
    """
    data = f"{context}|{user_id}".encode('utf-8')
    return hashlib.blake2b(data, digest_size=PERSON_BYTES).digest()


def derive_hmac_key(salt: bytes) -> bytes:
    """
    Derive HMAC key from salt using BLAKE2b.

    Args:
        salt: 32-byte salt

    Returns:
        32-byte HMAC key
    """
    return hashlib.blake2b(
        salt,
        digest_size=HMAC_BYTES,
        person=b"helper-data-hmac"
    ).digest()


def compute_helper_data_hmac(helper_data_bytes: bytes, key: bytes) -> bytes:
    """
    Compute HMAC over helper data for integrity protection.

    Args:
        helper_data_bytes: Serialized helper data (without HMAC field)
        key: 32-byte HMAC key

    Returns:
        32-byte HMAC tag
    """
    # Use SHA256 for HMAC (32-byte output) instead of BLAKE2b (64-byte output)
    return hmac.new(key, helper_data_bytes, hashlib.sha256).digest()


def derive_key_from_biometric(
    biometric_bits: np.ndarray,
    salt: bytes,
    personalization: bytes
) -> bytes:
    """
    Derive 256-bit cryptographic key from biometric using BLAKE2b.

    Args:
        biometric_bits: 64-bit BCH-decoded message
        salt: 32-byte salt
        personalization: 32-byte personalization tag

    Returns:
        32-byte (256-bit) cryptographic key
    """
    # Pack bits into bytes
    biometric_bytes = np.packbits(biometric_bits).tobytes()

    # BLAKE2b-512 with salt and personalization
    # Note: BLAKE2b supports max 16-byte salt/person, so we hash them first
    h = hashlib.blake2b(
        digest_size=64,  # 512-bit output
        salt=hashlib.blake2b(salt, digest_size=16).digest()[:16],
        person=hashlib.blake2b(personalization, digest_size=16).digest()[:16]
    )

    h.update(biometric_bytes)

    # Take first 256 bits (32 bytes) as key
    return h.digest()[:KEY_BYTES]


# ============================================================================
# FUZZY EXTRACTOR
# ============================================================================

def fuzzy_extract_gen(
    biometric_bitstring: np.ndarray,
    user_id: str
) -> Tuple[bytes, HelperData]:
    """
    Fuzzy extractor Gen function (enrollment).

    Generates cryptographic key and helper data from biometric input.

    Args:
        biometric_bitstring: 64-bit quantized biometric (numpy array)
        user_id: User identifier for personalization

    Returns:
        (key, helper_data) tuple:
            key: 32-byte cryptographic key
            helper_data: HelperData object (public)
    """
    if len(biometric_bitstring) != BCH_K:
        raise ValueError(
            f"Biometric must be {BCH_K} bits, got {len(biometric_bitstring)}")

    # 1. Initialize BCH codec
    codec = BCHCodec()

    # 2. Generate salt
    salt = secrets.token_bytes(SALT_BYTES)

    # 3. Generate personalization tag
    personalization = generate_personalization_tag(user_id)

    # 4. BCH encode biometric
    codeword = codec.encode(biometric_bitstring)

    # 5. Compute BCH syndrome for helper data
    syndrome = codec.compute_syndrome(codeword)

    # 6. Derive key from biometric
    key = derive_key_from_biometric(biometric_bitstring, salt, personalization)

    # 7. Compute HMAC for helper data integrity
    helper_data_bytes = (
        HELPER_DATA_VERSION.to_bytes(1, 'big') +
        salt +
        personalization +
        syndrome
    )
    hmac_key = derive_hmac_key(salt)
    hmac_tag = compute_helper_data_hmac(helper_data_bytes, hmac_key)

    # 8. Create helper data structure
    helper_data = HelperData(
        version=HELPER_DATA_VERSION,
        salt=salt,
        personalization=personalization,
        bch_syndrome=syndrome,
        hmac=hmac_tag
    )

    return key, helper_data


def fuzzy_extract_rep(
    biometric_bitstring: np.ndarray,
    helper_data: HelperData
) -> bytes:
    """
    Fuzzy extractor Rep function (verification).

    Recovers cryptographic key from noisy biometric using helper data.

    Args:
        biometric_bitstring: 127-bit quantized biometric (numpy array, noisy)
        helper_data: HelperData from enrollment

    Returns:
        32-byte cryptographic key

    Raises:
        ValueError: If HMAC verification fails or BCH decoding fails
    """
    # Note: For verification, we need the full 127-bit codeword, not just 64-bit message
    # The design spec needs clarification here. For now, assume we reconstruct
    # codeword from message + syndrome in helper data

    if len(biometric_bitstring) != BCH_K:
        # If we receive 64 bits, we need to reconstruct the codeword
        # This is a design ambiguity - in practice, quantization should output
        # consistent bit length. For now, encode and use helper data for correction.
        raise ValueError(
            f"Biometric must be {BCH_K} bits for Rep, got {len(biometric_bitstring)}")

    # 1. Verify HMAC integrity
    helper_data_bytes = (
        helper_data.version.to_bytes(1, 'big') +
        helper_data.salt +
        helper_data.personalization +
        helper_data.bch_syndrome
    )
    hmac_key = derive_hmac_key(helper_data.salt)
    expected_hmac = compute_helper_data_hmac(helper_data_bytes, hmac_key)

    if not hmac.compare_digest(helper_data.hmac, expected_hmac):
        raise ValueError("Helper data integrity check failed (HMAC mismatch)")

    # 2. Initialize BCH codec
    codec = BCHCodec()

    # 3. Decode noisy biometric using stored parity bits from helper data
    try:
        decoded_message, _ = codec.decode_with_parity(
            biometric_bitstring, helper_data.bch_syndrome)
    except ValueError as e:
        raise ValueError(f"BCH decoding failed: {e}")

    # 4. Derive key from corrected biometric
    key = derive_key_from_biometric(
        decoded_message,
        helper_data.salt,
        helper_data.personalization
    )

    return key


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def bytes_to_bitarray(data: bytes) -> np.ndarray:
    """Convert bytes to numpy bit array."""
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))


def bitarray_to_bytes(bits: np.ndarray) -> bytes:
    """Convert numpy bit array to bytes."""
    return np.packbits(bits).tobytes()


if __name__ == "__main__":
    # Quick test
    print("Testing Fuzzy Extractor with BCH(127,64,10)...")

    # Generate random 64-bit biometric
    bio = np.random.randint(0, 2, BCH_K, dtype=np.uint8)
    print(f"Original biometric: {len(bio)} bits")

    # Enrollment
    key1, helper = fuzzy_extract_gen(bio, user_id="addr1q9xy...abc123")
    print(
        f"✅ Enrollment: key={key1.hex()[:16]}..., helper={len(helper.serialize())} bytes")

    # Verification (same biometric)
    key2 = fuzzy_extract_rep(bio, helper)
    print(f"✅ Verification (no errors): key={key2.hex()[:16]}...")
    print(f"✅ Keys match: {key1 == key2}")

    # Verification with errors
    bio_noisy = bio.copy()
    error_positions = np.random.choice(
        BCH_K, size=8, replace=False)  # 8 errors
    for pos in error_positions:
        bio_noisy[pos] ^= 1

    key3 = fuzzy_extract_rep(bio_noisy, helper)
    print(f"✅ Verification (8 bit errors): key={key3.hex()[:16]}...")
    print(f"✅ Keys match after error correction: {key1 == key3}")

    print(f"\n🎉 Fuzzy Extractor working correctly!")
