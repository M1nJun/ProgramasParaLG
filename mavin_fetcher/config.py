from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Set, Tuple

DEFAULT_MODEL = "JF2"

BASE_PARTS = ("Files", "Image")

DEFAULT_DRIVES: Tuple[str, ...] = tuple(chr(c) for c in range(ord("E"), ord("Z") + 1))

SOURCEMAP_SUFFIX = "SourceMap.jpg"


def _norm(name: str) -> str:
    return (name or "").strip().lower()


# B-area: keep existing behavior
EXCLUDED_CLASS_FOLDERS_B: Set[str] = {_norm("01_ok_anode"), _norm("01_ok_cathode")}

# A-area: ignore these (your new requirement)
EXCLUDED_CLASS_FOLDERS_A: Set[str] = {
    _norm("01_OK_TOP_ANODE"),
    _norm("02_OK_BACK_ANODE"),
    _norm("01_OK_TOP_CATHODE"),
    _norm("02_OK_BACK_CATHODE"),
}

# Backward-compatible default used by older scanner.py
EXCLUDED_CLASS_FOLDERS: Set[str] = set(EXCLUDED_CLASS_FOLDERS_B)


def excluded_class_folders_for_area(area_id: str) -> Set[str]:
    a = (area_id or "").strip().upper()
    if a == "A":
        return set(EXCLUDED_CLASS_FOLDERS_A)
    return set(EXCLUDED_CLASS_FOLDERS_B)


@dataclass(frozen=True)
class FoundRoot:
    drive: str
    path: Path