from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_BASE = Path(r"D:\B_AREA_DL_REVIEW")


def yyyymmdd(d: date) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def suggest_output_dir(*, days: Optional[Iterable[date]] = None, base: Path = DEFAULT_BASE) -> Path:
    """
    Default output: D:\B_AREA_DL_REVIEW\<YYYYMMDD>\
    - If days provided: uses the earliest selected day.
    - Else: uses today's date.
    """
    chosen: Optional[date] = None
    if days is not None:
        ds = list(days)
        if ds:
            chosen = min(ds)

    if chosen is None:
        chosen = date.today()

    return base / yyyymmdd(chosen)
