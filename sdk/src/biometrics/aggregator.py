"""Combine per-finger digests into a master biometric commitment."""
from __future__ import annotations

from hashlib import blake2b
from typing import Iterable, Sequence, Tuple

from .fuzzy_extractor import HelperData


PERSON_TAG = b"CARDANO_BIOID__"  # 16 bytes


def aggregate_finger_digests(digests: Sequence[Tuple[str, bytes]]) -> bytes:
    ordered = sorted(digests, key=lambda item: item[0])
    buffer = bytearray()
    for finger_id, digest in ordered:
        buffer.extend(finger_id.encode("utf-8"))
        buffer.append(0)
        buffer.extend(digest)
    return blake2b(buffer, digest_size=32, person=PERSON_TAG).digest()


def helpers_to_dict(helpers: Iterable[HelperData]) -> dict:
    payload = {}
    for helper in helpers:
        payload[helper.finger_id] = helper.to_dict()
    return payload
