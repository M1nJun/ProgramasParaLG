from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from .config import BASE_PARTS, PIPELINE_PARTS, FoundRoot
from .date_utils import ymd_parts


def find_crop_b_root(model: str, day: date, drives: Iterable[str]) -> Optional[FoundRoot]:
    """
    Returns the first existing Crop_B folder found across given drives.
    Example:
      E:\Files\Image\JF2\2026\01\27\Mavin\Crop_B
    """
    yyyy, mm, dd = ymd_parts(day)

    for drv in drives:
        # Normalize drive input like "E", "E:", "E:\"
        d = drv.strip().rstrip("\\/").rstrip(":").upper()
        if len(d) != 1 or not d.isalpha():
            continue

        root = Path(f"{d}:/")
        candidate = root
        for p in BASE_PARTS:
            candidate = candidate / p
        candidate = candidate / model / yyyy / mm / dd
        for p in PIPELINE_PARTS:
            candidate = candidate / p

        if candidate.exists() and candidate.is_dir():
            return FoundRoot(drive=d, path=candidate)

    return None
