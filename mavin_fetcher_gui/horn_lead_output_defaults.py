from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_BASE_HORN_LEAD = Path(r"D:\HORN_LEAD_DL_REVIEW")

def yyyymmdd(d: date) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"

def suggest_horn_lead_output_dir(
    *,
    days: Optional[Iterable[date]] = None,
    base: Optional[Path] = None,
) -> Path:
    """Default output: D:\\HORN_LEAD_DL_REVIEW\\<YYYYMMDD>\\ """
    chosen: Optional[date] = None
    if days is not None:
        ds = list(days)
        if ds:
            chosen = min(ds)
    if chosen is None:
        chosen = date.today()
    real_base = base if base is not None else DEFAULT_BASE_HORN_LEAD
    return real_base / yyyymmdd(chosen)