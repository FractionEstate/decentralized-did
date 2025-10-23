"""Utilities for turning raw minutiae points into stable, quantized templates."""
from __future__ import annotations

from dataclasses import dataclass
from math import pi
from typing import Iterable, List, Sequence, Tuple
import struct


@dataclass(frozen=True)
class Minutia:
    """Single minutia point extracted from a fingerprint scan."""

    x: float
    y: float
    angle: float  # degrees or radians; normalized internally


class FingerTemplate:
    """Canonical representation of a single finger after quantization."""

    def __init__(
        self,
        finger_id: str,
        minutiae: Iterable[Minutia],
        grid_size: float = 0.05,
        angle_bins: int = 32,
    ) -> None:
        self.finger_id = finger_id
        self.grid_size = grid_size
        self.angle_bins = angle_bins
        self._quantized: Tuple[Tuple[int, int, int], ...] = self._quantize(list(minutiae))

    def _quantize(self, minutiae: Sequence[Minutia]) -> Tuple[Tuple[int, int, int], ...]:
        quantized: List[Tuple[int, int, int]] = []
        for m in minutiae:
            qx = round(m.x / self.grid_size)
            qy = round(m.y / self.grid_size)
            angle_rad = m.angle if m.angle <= 2 * pi else (m.angle / 180.0) * pi
            qa = round(((angle_rad % (2 * pi)) / (2 * pi)) * self.angle_bins) % self.angle_bins
            quantized.append((int(qx), int(qy), int(qa)))
        quantized.sort()
        return tuple(quantized)

    @property
    def quantized(self) -> Tuple[Tuple[int, int, int], ...]:
        return self._quantized

    def to_bytes(self) -> bytes:
        """Encode quantized minutiae into a deterministic byte string."""
        buf = bytearray()
        for qx, qy, qa in self._quantized:
            buf.extend(struct.pack(">hhH", qx, qy, qa))
        return bytes(buf)

    def distance(self, other: "FingerTemplate") -> int:
        """Symmetric difference distance between two quantized templates."""
        a = set(self._quantized)
        b = set(other._quantized)
        return len(a.symmetric_difference(b))

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._quantized)


def minutiae_from_dicts(items: Iterable[dict]) -> List[Minutia]:
    """Convert generic dict payloads into minutiae objects."""
    minutiae: List[Minutia] = []
    for item in items:
        x = float(item["x"])
        y = float(item["y"])
        angle = float(item.get("angle", 0.0))
        minutiae.append(Minutia(x=x, y=y, angle=angle))
    return minutiae
