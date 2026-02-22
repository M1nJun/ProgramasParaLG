from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from mavin_fetcher.config import DEFAULT_DRIVES
from .path_convert import resolve_drive_root

def _mavin_rel(model: str, day: date) -> Path:
    return (
        Path("Files")
        / "Image"
        / (model or "JF2")
        / f"{day.year:04d}"
        / f"{day.month:02d}"
        / f"{day.day:02d}"
        / "Mavin"
    )

def find_mavin_root(
    *,
    ip: str,
    model: str,
    day: date,
    drives: Iterable[str] = DEFAULT_DRIVES,
) -> Optional[Path]:
    """Find ...\\Files\\Image\\<MODEL>\\YYYY\\MM\\DD\\Mavin on any shared drive."""
    rel = _mavin_rel(model, day)
    for d in drives:
        root = resolve_drive_root(ip, d)
        if root is None:
            continue
        cand = root / rel
        try:
            if cand.exists() and cand.is_dir():
                return cand
        except Exception:
            continue
    return None