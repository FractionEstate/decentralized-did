"""Biometric processing primitives for decentralized DID generation.

This module provides core biometric processing components including:
- Fuzzy extractors for key derivation from noisy biometric data
- Feature extraction and minutiae processing
- Multi-finger aggregation for enhanced security

Components
----------
FuzzyExtractor : class
    Core primitive for generating reproducible keys from biometric templates
HelperData : class
    Helper data structure containing error correction information
aggregate_finger_digests : function
    Combine multiple finger digests into single aggregated digest
FingerTemplate : class
    Biometric template representation with minutiae data
Minutia : class
    Individual fingerprint minutia point (x, y, angle, type)

Examples
--------
>>> from decentralized_did.biometrics import FuzzyExtractor, aggregate_finger_digests, FingerTemplate
>>>
>>> # Single finger enrollment
>>> extractor = FuzzyExtractor()
>>> template = FingerTemplate(...)  # Your biometric template
>>> digest, helper = extractor.generate(template)
>>>
>>> # Verification
>>> noisy_template = FingerTemplate(...)  # Recaptured template
>>> verified = extractor.reproduce(noisy_template, helper)
>>> assert digest == verified  # Reproducible despite noise
>>>
>>> # Multi-finger aggregation
>>> fingers = [("thumb", digest1), ("index", digest2)]
>>> combined = aggregate_finger_digests(fingers)
"""

from .fuzzy_extractor import FuzzyExtractor, HelperData
from .aggregator import aggregate_finger_digests, helpers_to_dict
from .feature_extractor import Minutia, FingerTemplate, minutiae_from_dicts

__all__ = [
    # Fuzzy extractor
    "FuzzyExtractor",
    "HelperData",

    # Aggregation
    "aggregate_finger_digests",
    "helpers_to_dict",

    # Feature extraction
    "Minutia",
    "FingerTemplate",
    "minutiae_from_dicts",
]
