from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .csv_reader import iter_rows

REGIONS = ["LOWER_B_L", "LOWER_B_R", "UPPER_B_L", "UPPER_B_R"]

# Your CSV has columns like:
#   LOWER_B_L-NAME, LOWER_B_R-NAME, UPPER_B_L-NAME, UPPER_B_R-NAME
# We use those primarily.
NAME_COLS = {r: f"{r}-NAME" for r in REGIONS}

CELL_ID_COL = "CELL-ID"


def normalize_class(name: str) -> Optional[str]:
    """
    Normalize class names to something stable for UI.

    Rules:
    - ignore OK_ANODE / OK_CATHODE / other OK_* except OK_ROI
    - keep NG_* as-is
    - allow "06_OK_ROI" or "OK_ROI" -> "OK_ROI"
    - allow "02_NG_TORN" -> "NG_TORN" (strip numeric prefix)
    """
    if not name:
        return None

    s = str(name).strip()
    if not s:
        return None

    # strip numeric prefix "02_..."
    if "_" in s and s.split("_", 1)[0].isdigit():
        s = s.split("_", 1)[1].strip()

    s_up = s.upper()

    if s_up in ("OK_ROI", "06_OK_ROI"):
        return "OK_ROI"

    # ignore OK_* except OK_ROI
    if s_up.startswith("OK_"):
        return None

    if s_up.startswith("NG_"):
        return s_up

    # fallback: show as-is (upper)
    return s_up


@dataclass
class BAreaSummary:
    total_rows: int
    total_cells: int
    # occurrences by class and region
    region_counts: Dict[str, Dict[str, int]]
    # unique cells by class
    cell_counts: Dict[str, int]


def summarize_b_area(paths: List[Path]) -> BAreaSummary:
    region_counts: Dict[str, Dict[str, int]] = {}
    cell_sets: Dict[str, Set[str]] = {}
    all_cells: Set[str] = set()
    total_rows = 0

    for p in paths:
        for row in iter_rows(p):
            total_rows += 1
            cell_id = (row.get(CELL_ID_COL) or "").strip()
            if cell_id:
                all_cells.add(cell_id)

            # collect classes hit for this cell (dedupe within row)
            classes_in_row: Set[str] = set()

            for region in REGIONS:
                raw_name = (row.get(NAME_COLS[region]) or "").strip()
                cls = normalize_class(raw_name)
                if not cls:
                    continue

                classes_in_row.add(cls)

                if cls not in region_counts:
                    region_counts[cls] = {r: 0 for r in REGIONS}
                region_counts[cls][region] += 1

            if cell_id:
                for cls in classes_in_row:
                    if cls not in cell_sets:
                        cell_sets[cls] = set()
                    cell_sets[cls].add(cell_id)

    cell_counts = {cls: len(s) for cls, s in cell_sets.items()}

    return BAreaSummary(
        total_rows=total_rows,
        total_cells=len(all_cells),
        region_counts=region_counts,
        cell_counts=cell_counts,
    )
