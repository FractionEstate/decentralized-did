"""Simple fuzzy extractor built on top of quantized minutiae templates."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import blake2b, sha256
import base64
import hmac
import secrets
from typing import Dict, Tuple

from .feature_extractor import FingerTemplate


@dataclass(frozen=True)
class HelperData:
    finger_id: str
    salt_b64: str
    auth_b64: str
    grid_size: float
    angle_bins: int

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class FuzzyExtractor:
    """Deterministically derives digests + helper data from quantized templates."""

    def __init__(self, salt_bytes: int = 16, digest_size: int = 32) -> None:
        self.salt_bytes = salt_bytes
        self.digest_size = digest_size

    def _personalization(self, finger_id: str) -> bytes:
        encoded = finger_id.encode("utf-8")[:16]
        return encoded.ljust(16, b"\x00")

    def generate(self, template: FingerTemplate) -> Tuple[bytes, HelperData]:
        salt = secrets.token_bytes(self.salt_bytes)
        digest = blake2b(
            template.to_bytes() + salt,
            digest_size=self.digest_size,
            person=self._personalization(template.finger_id),
        ).digest()
        auth_tag = hmac.new(salt, template.to_bytes(), sha256).digest()[:16]
        helper = HelperData(
            finger_id=template.finger_id,
            salt_b64=base64.urlsafe_b64encode(salt).decode("ascii"),
            auth_b64=base64.urlsafe_b64encode(auth_tag).decode("ascii"),
            grid_size=template.grid_size,
            angle_bins=template.angle_bins,
        )
        return digest, helper

    def reproduce(self, template: FingerTemplate, helper: HelperData) -> bytes:
        salt = base64.urlsafe_b64decode(helper.salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(helper.auth_b64.encode("ascii"))
        auth_tag = hmac.new(salt, template.to_bytes(), sha256).digest()[: len(expected)]
        if not hmac.compare_digest(auth_tag, expected):
            raise ValueError("helper data validation failed for finger %s" % helper.finger_id)
        digest = blake2b(
            template.to_bytes() + salt,
            digest_size=self.digest_size,
            person=self._personalization(helper.finger_id),
        ).digest()
        return digest
