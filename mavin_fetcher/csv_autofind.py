from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class CsvMatch:
    day: date
    path: Path


def yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")

def _is_ignored_csv(path: Path) -> bool:
    # Add more rules later if needed
    name = path.name.lower()
    return name.endswith("_defect.csv")



def find_csvs_for_day(csv_dir: Path, model: str, day: date) -> List[Path]:
    """
    Find all CSV files for a given day/model in csv_dir.

    Supports:
      #5-2 WELDING VISION(-)_JF2_20260127.csv
      #5-2 WELDING VISION(-)_JF2_20260127_1.csv
      #5-2 WELDING VISION(+)_JF2_20260127_2.csv
      etc.

    We intentionally do NOT require line name or (+)/(-).
    We match any "#*-* WELDING VISION" prefix, any polarity, exact model, exact date,
    and optional _N suffix.
    """
    csv_dir = Path(csv_dir).expanduser().resolve()
    model = (model or "").strip()
    if not model:
        raise ValueError("model is required (e.g., JF2)")

    d = yyyymmdd(day)

    # Pattern explanation:
    #   #*-* WELDING VISION(*)_<MODEL>_<DATE>.csv
    #   #*-* WELDING VISION(*)_<MODEL>_<DATE>_*.csv
    #
    # We use glob twice because Path.glob doesn't support {optional} patterns.
    pat_base = f"#*-* WELDING VISION(*)_{model}_{d}.csv"
    pat_suffix = f"#*-* WELDING VISION(*)_{model}_{d}_*.csv"

    hits = list(csv_dir.glob(pat_base)) + list(csv_dir.glob(pat_suffix))

    # Deduplicate and sort:
    # Prefer base file first, then _1, _2 ... by natural-ish sort.
    uniq = {p.resolve() for p in hits if p.is_file() and not _is_ignored_csv(p)}


    def sort_key(p: Path):
        name = p.name
        # try to extract trailing _N just before ".csv"
        n = 0
        stem = name[:-4] if name.lower().endswith(".csv") else name
        if "_" in stem:
            tail = stem.rsplit("_", 1)[-1]
            if tail.isdigit():
                n = int(tail)
        # base file should come first (n=0)
        return (n, name.lower())

    return sorted(uniq, key=sort_key)


def find_csvs_for_days(csv_dir: Path, model: str, days: List[date]) -> List[CsvMatch]:
    """
    For multiple days, return a flat list of (day, path) matches.
    Sorted by day then suffix order.
    """
    out: List[CsvMatch] = []
    for d in sorted(days):
        for p in find_csvs_for_day(csv_dir, model, d):
            out.append(CsvMatch(day=d, path=p))
    return out


def flatten_paths(matches: List[CsvMatch]) -> List[Path]:
    """
    Convenience: convert CsvMatch list into just paths (preserving order).
    """
    return [m.path for m in matches]
