from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from checker import CheckReport
from row_presenter import occurrences_text


def _row_group_label(r) -> str:
    """
    Keep CSV output consistent with the UI:
    - Prefer r.side (legacy)
    - Fallback to r.group (newer)
    """
    val = getattr(r, "side", None)
    if isinstance(val, str) and val.strip():
        return val
    val = getattr(r, "group", "")
    return val if isinstance(val, str) else ""


def export_report_csv(report: CheckReport, out_dir: Path, show_all_occurrences: bool = True) -> Path:
    """
    Writes a timestamped CSV report. One row per required measure.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"bypass_report_{report.recipe_name}_{report.recipe_id_3digit}_{ts}.csv"

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["RecipeName", report.recipe_name])
        w.writerow(["RecipeFolder", report.recipe_id_3digit])
        w.writerow(["KickoutList", report.kickout_filename])
        w.writerow([])

        w.writerow([
            "Status",
            "Measure(Master)",
            "Side",
            "NormalizedKey",
            "Expected",
            "Found",
            "BypassedCount",
            "Occurrences",
        ])

        for r in sorted(report.rows, key=lambda x: x.normalized_key):
            status = "PASS" if r.is_pass else "FAIL"
            w.writerow([
                status,
                r.display_name,
                _row_group_label(r),
                r.normalized_key,
                r.expected_count,
                r.found_count,
                len(r.bypassed_occurrences),
                occurrences_text(r, show_all=show_all_occurrences).replace("\n", " | "),
            ])

    return out_path