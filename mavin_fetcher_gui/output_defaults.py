from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from mavin_fetcher.area_spec import AreaSpec


DEFAULT_BASE_A = Path(r"D:\A_AREA_DL_REVIEW")
DEFAULT_BASE_B = Path(r"D:\B_AREA_DL_REVIEW")


def yyyymmdd(d: date) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def default_base_for_area(area: AreaSpec) -> Path:
    return DEFAULT_BASE_A if area.area_id == "A" else DEFAULT_BASE_B


def suggest_output_dir(
    *,
    area: AreaSpec,
    days: Optional[Iterable[date]] = None,
    base: Optional[Path] = None,
) -> Path:
    """
    Default output:
      A: D:\A_AREA_DL_REVIEW\<YYYYMMDD>\
      B: D:\B_AREA_DL_REVIEW\<YYYYMMDD>\
    """
    chosen: Optional[date] = None
    if days is not None:
        ds = list(days)
        if ds:
            chosen = min(ds)

    if chosen is None:
        chosen = date.today()

    real_base = base if base is not None else default_base_for_area(area)
    return real_base / yyyymmdd(chosen)