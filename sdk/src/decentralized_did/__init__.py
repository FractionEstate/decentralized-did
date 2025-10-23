"""Decentralized biometric DID toolkit for Cardano.

This SDK provides tools for generating decentralized identifiers (DIDs) from
biometric data using fuzzy extractors and Cardano blockchain integration.

Quick Start
-----------
>>> from decentralized_did import FuzzyExtractor, HelperData
>>> from decentralized_did.biometrics import aggregate_finger_digests
>>> from decentralized_did.did import build_did, build_metadata_payload
>>>
>>> # Enrollment: Generate helper data from biometric template
>>> extractor = FuzzyExtractor()
>>> template = FingerTemplate(...)  # Your biometric template
>>> digest, helper = extractor.generate(template)
>>>
>>> # Verification: Reproduce digest from noisy template
>>> noisy_template = FingerTemplate(...)  # Recaptured template
>>> verified_digest = extractor.reproduce(noisy_template, helper)
>>>
>>> # Multi-finger aggregation
>>> finger_digests = [("thumb", digest1), ("index", digest2)]
>>> aggregated = aggregate_finger_digests(finger_digests)
>>>
>>> # Generate DID
>>> wallet_addr = "addr1..."
>>> did = build_did(wallet_addr, aggregated)

Main Components
---------------
- biometrics: Fuzzy extractor, feature extraction, aggregation
- did: DID generation and metadata payload construction
- storage: Helper data storage backends (file, IPFS, inline)
- cardano: Cardano blockchain integration utilities
- cli: Command-line interface (use `dec-did` command)

See Also
--------
- Documentation: docs/
- Examples: examples/
- GitHub: https://github.com/FractionEstate/decentralized-did
"""

# Core biometric primitives
from .biometrics.fuzzy_extractor import FuzzyExtractor, HelperData
from .biometrics.aggregator import aggregate_finger_digests, helpers_to_dict
from .biometrics.feature_extractor import Minutia, FingerTemplate, minutiae_from_dicts

# DID generation
from .did.generator import build_did, build_metadata_payload, generate_deterministic_did

# Storage backends
from .storage.base import StorageBackend, StorageReference, StorageError
from .storage.inline import InlineStorage
from .storage.file import FileStorage
from .storage.ipfs import IPFSStorage

# CLI entry point (for backwards compatibility)
from .cli import main as cli_main

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",

    # Biometrics
    "FuzzyExtractor",
    "HelperData",
    "aggregate_finger_digests",
    "helpers_to_dict",
    "Minutia",
    "FingerTemplate",
    "minutiae_from_dicts",

    # DID generation
    "build_did",
    "build_metadata_payload",
    "generate_deterministic_did",

    # Storage
    "StorageBackend",
    "StorageReference",
    "StorageError",
    "InlineStorage",
    "FileStorage",
    "IPFSStorage",

    # CLI
    "cli_main",
]
