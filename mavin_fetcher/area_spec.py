from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AreaSpec:
    """
    Area definition for Mavin crops.

    area_id: "A" or "B"
    crop_dirname: "Crop_A" or "Crop_B"
    """
    area_id: str
    crop_dirname: str

    @property
    def display_name(self) -> str:
        return f"{self.area_id} Area"

    @property
    def regions(self) -> Tuple[str, str, str, str]:
        # Viewer/summary regions (no digit in the middle)
        # Matches your naming convention: LOWER_A_L, LOWER_A_R, UPPER_A_L, UPPER_A_R
        a = self.area_id
        return (f"LOWER_{a}_L", f"LOWER_{a}_R", f"UPPER_{a}_L", f"UPPER_{a}_R")


AREA_A = AreaSpec(area_id="A", crop_dirname="Crop_A")
AREA_B = AreaSpec(area_id="B", crop_dirname="Crop_B")


def normalize_area_id(area_id: str) -> str:
    a = (area_id or "").strip().upper()
    if a not in ("A", "B"):
        raise ValueError(f"Invalid area_id: {area_id!r} (expected 'A' or 'B')")
    return a


def area_from_id(area_id: str) -> AreaSpec:
    a = normalize_area_id(area_id)
    return AREA_A if a == "A" else AREA_B