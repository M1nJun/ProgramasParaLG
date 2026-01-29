from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from .b_area_summary import summarize_b_area, REGIONS

LogFn = Optional[Callable[[str], None]]
ProgressFn = Optional[Callable[[int, int], None]]  # (done_files, total_files)


@dataclass
class SummaryResult:
    text: str
    file_count: int
    data: dict  # structured summary for GUI


def _log(fn: LogFn, msg: str) -> None:
    if fn:
        fn(msg)


def _progress(fn: ProgressFn, done: int, total: int) -> None:
    if fn:
        fn(done, total)


def _format_text(summary: dict, top_n: int) -> str:
    """
    Simple readable text fallback.
    GUI will use the table.
    """
    classes = summary["classes"]
    # sort by cell count desc
    items = sorted(classes.items(), key=lambda kv: kv[1]["cells"], reverse=True)[:top_n]

    lines = []
    lines.append(f"[B-AREA] Total cells: {summary['total_cells']} | total rows: {summary['total_rows']}")
    lines.append("Top classes by CELLS:")
    for cls, payload in items:
        occ = payload["occurrences"]
        cells = payload["cells"]
        by_region = payload["by_region"]
        lines.append(f" - {cls}: cells={cells}, occurrences={occ}, "
                     f"LBL={by_region['LOWER_B_L']}, LBR={by_region['LOWER_B_R']}, "
                     f"UBL={by_region['UPPER_B_L']}, UBR={by_region['UPPER_B_R']}")
    return "\n".join(lines)


def summarize_files(
    *,
    paths: List[Path],
    top_n: int = 20,
    log: LogFn = None,
    progress: ProgressFn = None,
) -> SummaryResult:
    clean = [p.expanduser().resolve() for p in paths]
    total = len(clean)

    if total == 0:
        return SummaryResult(text="[CSV] No files provided.", file_count=0, data={})

    _log(log, f"[INFO] Summarizing {total} file(s)...")
    _progress(progress, 0, total)

    existing: List[Path] = []
    for i, p in enumerate(clean, start=1):
        if not p.exists():
            _log(log, f"[WARN] Missing file: {p}")
        else:
            _log(log, f"[INFO] Reading: {p.name}")
            existing.append(p)
        _progress(progress, i, total)

    b = summarize_b_area(existing)

    classes: dict = {}
    for cls, by_region in b.region_counts.items():
        occurrences = sum(by_region.get(r, 0) for r in REGIONS)
        cells = int(b.cell_counts.get(cls, 0))
        classes[cls] = {
            "cells": cells,
            "occurrences": occurrences,
            "by_region": dict(by_region),
        }

    data = {
        "total_rows": b.total_rows,
        "total_cells": b.total_cells,
        "regions": list(REGIONS),
        "classes": classes,  # {class: {cells, occurrences, by_region{region:count}}}
    }

    text = _format_text(data, top_n=int(top_n))
    _log(log, "[INFO] Summary computed.")
    return SummaryResult(text=text, file_count=len(existing), data=data)
